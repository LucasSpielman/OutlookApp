import dash  # Import Dash for creating the web application
import dash_bootstrap_components as dbc  # Import Bootstrap components for styling
from dash import dcc, html, Input, Output  # Import core Dash components and callback functions
import plotly.express as px  # Import Plotly Express for creating plots
import pandas as pd  # Import pandas for data manipulation
import geopandas as gpd  # Import GeoPandas for handling geographical data

# Load the shapefile for geographical data
gdf = gpd.read_file("./data/ler_000b16a_e.shp")
gdf = gdf.to_crs(epsg=4326)  # Ensure the coordinate reference system is WGS84

# Simplify geometries to improve performance
gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)

# Calculate centroids for each region
gdf['centroid'] = gdf.geometry.centroid

# Load the Excel file paths for English and French data
file_paths = {
    'English': "./data/20242026_outlook_n21_en_250117.xlsx",
    'French': "./data/20242026_outlook_n21_fr_250117.xlsx"
}

# Global storage for cached data to avoid reloading it multiple times
cached_data = {}

def load_data(language):
    """
    Load the data from the Excel file based on the selected language.
    Cache the data to avoid reloading it multiple times.

    Parameters:
    language (str): The selected language ('English' or 'French').

    Returns:
    tuple: A tuple containing the merged DataFrame, outlook order, and outlook colors.
    """
    # Check if data is already cached
    if language in cached_data:
        return cached_data[language]

    # Read the Excel file
    df = pd.read_excel(file_paths[language])

    # Define the outlook order and colors based on the language
    if language == 'English':
        outlook_order = ['very good', 'good', 'moderate', 'limited', 'undetermined', 'bazinga']
        outlook_colors = {
            'very good': '#30AD23',  # Warm green
            'good': '#1E90FF',  # Dodger Blue
            'moderate': '#FFD700',  # Gold
            'limited': '#F08315',  # Warm Orange
            'undetermined': '#BA110C',  # Dark Red
            'bazinga': '#D3D3D3',  # Light Grey
        }
    else:  # French
        outlook_order = ['très bonnes', 'bonnes', 'modérées', 'limitées', 'indéterminées', 'bazinga']
        outlook_colors = {
            'très bonnes': '#30AD23',  # Warm Green
            'bonnes': '#1E90FF',  # Dodger Blue
            'modérées': '#FFD700',  # Gold
            'limitées': '#F08315',  # Warm Orange
            'indéterminées': '#BA110C',  # Dark Red
            'bazinga': '#D3D3D3',  # Light Grey
        }

    # Extract the first part of 'Economic Region Name' before the comma
    df['Economic Region Name'] = df['Economic Region Name'].str.split(',').str[0]

    # Convert the 'Outlook' column to a categorical type with the defined order
    df['Outlook'] = pd.Categorical(df['Outlook'], categories=outlook_order, ordered=True)

    # Merge the sorted DataFrame with the geographical data
    merged_df = gdf[['ERNAME', 'centroid']].merge(df, left_on='ERNAME', right_on='Economic Region Name')

    # Cache the data
    cached_data[language] = (merged_df, outlook_order, outlook_colors)
    return merged_df, outlook_order, outlook_colors

# Initialize the Dash app with the Minty theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])

# Define the layout of the app
app.layout = dbc.Container([
    # Title row
    dbc.Row([
        dbc.Col(html.H1("Canadian Job Outlook sorted by Economic Region 2024-2026", style={'textAlign': 'left', 'margin-top': '20px'}), width=12)
    ]),
    # Region dropdown row
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='region-dropdown',
            options=[{'label': region, 'value': region} for region in gdf['ERNAME'].unique()],
            value=gdf['ERNAME'].iloc[0],
            clearable=False
        ), width=12)
    ]),
    # Map plot row
    dbc.Row([
        dbc.Col(dcc.Graph(id='map-plot'), width=12)
    ]),
    # Bar plot row
    dbc.Row([
        dbc.Col(dcc.Graph(id='bar-plot'), width=12)
    ])
], fluid=True)

# Callback to update the plots based on the selected region
@app.callback(
    [Output('map-plot', 'figure'), Output('bar-plot', 'figure')],
    [Input('region-dropdown', 'value')]
)
def update_plots(selected_region):
    """
    Update the map and bar plots based on the selected region.

    Parameters:
    selected_region (str): The selected economic region.

    Returns:
    tuple: A tuple containing the updated map and bar plot figures.
    """
    # Load the data for the selected language (English in this case)
    merged_df, outlook_order, outlook_colors = load_data('English')

    # Filter the geographical data for the selected region
    filtered_gdf = gdf[gdf['ERNAME'] == selected_region]

    # Filter the merged data for the selected region
    filtered_data = merged_df[merged_df['ERNAME'] == selected_region]

    # Create the map plot
    map_fig = px.choropleth_mapbox(
        filtered_gdf, geojson=filtered_gdf.geometry, locations=filtered_gdf.index, color="ERNAME",
        mapbox_style="carto-positron", center={"lat": filtered_gdf.centroid.y.mean(), "lon": filtered_gdf.centroid.x.mean()},
        zoom=6, hover_name='ERNAME', opacity=0.5
    )
    map_fig.update_layout(showlegend=False)

    # Create the bar plot with descending order for 'Outlook'
    bar_fig = px.bar(
        filtered_data,
        x='NOC Title',
        y='Outlook',
        color='Outlook',
        color_discrete_map=outlook_colors,
        category_orders={'Outlook': outlook_order[::1]}  # Reverse the order for descending sorting
    )

    return map_fig, bar_fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)