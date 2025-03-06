import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import geopandas as gpd

# Load the Excel file paths
file_paths = {
    'English': "./data/20242026_outlook_n21_en_250117.xlsx",
    'French': "./data/20242026_outlook_n21_fr_250117.xlsx"
}

# Global storage for cached data
cached_data = {}

def load_data(language):
    """
    Load the data from the Excel file based on the selected language.
    Cache the data to avoid reloading it multiple times.

    Parameters:
    language (str): The selected language ('English' or 'French').

    Returns:
    tuple: A tuple containing the sorted DataFrame, outlook order, and outlook colors.
    """
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
    
    # Convert the 'Outlook' column to a categorical type with the defined order
    df['Outlook'] = pd.Categorical(df['Outlook'], categories=outlook_order, ordered=True)
    
    # Sort the DataFrame by 'NOC Title', 'Economic Region Name', and 'Outlook'
    sorted_df = df.sort_values(by=['NOC Title', 'Economic Region Name', 'Outlook'])
    
    # Cache the data
    cached_data[language] = (sorted_df, outlook_order, outlook_colors)
    
    return sorted_df, outlook_order, outlook_colors

# Load the shapefile
gdf = gpd.read_file("./data/ler_000b16a_e.shp")
gdf = gdf.to_crs(epsg=4326)  # Ensure the coordinate reference system is WGS84

# Simplify geometries to improve performance
gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)

# Calculate centroids for each region
gdf['centroid'] = gdf.geometry.centroid

# Initialize the Dash app with the Minty theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Canadian Job Market Outlook 2024-2026", style={'textAlign': 'center'}), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='language-dropdown',
            options=[{'label': 'English', 'value': 'English'}, {'label': 'Français', 'value': 'French'}],
            value='English',
            clearable=False,
            style={'width': '50%', 'margin': 'auto'}
        ), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='noc-dropdown',
            value=None,  # Default to None until data loads
            multi=False,  # Single selection only
            clearable=False,
            style={'width': '50%', 'margin': 'auto'}
        ), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='map-plot', style={'height': '70vh'}), width=12)  # Adjusted height
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='bar-plot', style={'height': '20vh'}), width=12)  # Adjusted height
    ]),

], fluid=True)

# Callback to update data when language is switched
@app.callback(
    [Output('noc-dropdown', 'options'), Output('noc-dropdown', 'value')],
    Input('language-dropdown', 'value')
)
def update_noc_dropdown(language):
    """
    Update the NOC dropdown options and value based on the selected language.

    Parameters:
    language (str): The selected language ('English' or 'French').

    Returns:
    tuple: A tuple containing the dropdown options and the first NOC title as the default value.
    """
    sorted_df, _, _ = load_data(language)
    options = [{'label': title, 'value': title} for title in sorted(sorted_df['NOC Title'].unique())]
    return options, sorted_df['NOC Title'].iloc[0]

# Callback to update both plots based on dropdown selection
@app.callback(
    [Output('map-plot', 'figure'), Output('bar-plot', 'figure')],
    [Input('noc-dropdown', 'value'), Input('language-dropdown', 'value')]
)
def update_plots(selected_noc, language):
    """
    Update the map and bar plots based on the selected NOC title and language.

    Parameters:
    selected_noc (str): The selected NOC title.
    language (str): The selected language ('English' or 'French').

    Returns:
    tuple: A tuple containing the updated map and bar plot figures.
    """
    sorted_df, outlook_order, outlook_colors = load_data(language)
    
    # Merge the sorted DataFrame with the geographical data
    merged_df = gdf[['ERNAME', 'centroid']].merge(sorted_df, left_on='ERNAME', right_on='Economic Region Name')
    merged_df['lat'] = merged_df['centroid'].apply(lambda point: point.y)
    merged_df['lon'] = merged_df['centroid'].apply(lambda point: point.x)
    
    # Filter the DataFrame by the selected NOC title
    filtered_df = merged_df[merged_df['NOC Title'] == selected_noc]
    
    # Create the map plot
    map_fig = px.scatter_mapbox(
        filtered_df, lat='lat', lon='lon', color='Outlook', size_max=13, zoom=3,
        mapbox_style="carto-positron", center={"lat": 56.1304, "lon": -106.3468},
        category_orders={'Outlook': outlook_order},
        color_discrete_map=outlook_colors,
        hover_name='Economic Region Name',
        size=[6.5] * len(filtered_df)
    )
    
    # Create the bar plot
    bar_fig = px.bar(
        filtered_df, x='Economic Region Name', y='Outlook', color='Outlook',
        labels={'x': 'Economic Region Name', 'y': 'Outlook'},
        category_orders={'Outlook': outlook_order},
        color_discrete_map=outlook_colors
    )
    
    # Sync legend across both plots
    map_fig.update_layout(
        showlegend=True,
        # height=900,  # Adjusted height
        legend=dict(
            x=0.01,
            y=0.99,
            traceorder='normal',
            bgcolor='rgba(255, 255, 255, 0.7)',
            bordercolor='rgba(0, 0, 0, 0.1)',
            borderwidth=1
        )
    )
    bar_fig.update_layout(showlegend=False, 
    # height=275 # Adjusted height, legend removed
    )  
    
    return map_fig, bar_fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)