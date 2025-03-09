import dash
from dash import dcc, html, Input, Output
import pandas as pd
import geopandas as gpd
import plotly.express as px

# Load the shapefile
gdf = gpd.read_file("./data/ler_000b16a_e.shp")
gdf = gdf.to_crs(epsg=4326)  # Ensure the coordinate reference system is WGS84

# Simplify geometries to improve performance
gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)

# Calculate centroids for each region
gdf['centroid'] = gdf.geometry.centroid

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
    df['Economic Region Name'] = df['Economic Region Name'].str.split(',').str[0]
    # Convert the 'Outlook' column to a categorical type with the defined order
    df['Outlook'] = pd.Categorical(df['Outlook'], categories=outlook_order, ordered=True)
    
    # Sort the DataFrame by 'NOC Title', 'Economic Region Name', and 'Outlook'
    sorted_df = df.sort_values(by=['NOC Title', 'Economic Region Name', 'Outlook'])
    
    # Merge the geographic data with the job outlook data
    merged_df = gdf[['ERNAME', 'centroid']].merge(sorted_df, left_on='ERNAME', right_on='Economic Region Name')
    
    # cache the data
    cached_data[language] = (merged_df, outlook_order, outlook_colors)
    
    return merged_df, outlook_order, outlook_colors

# Initialize the Dash app
app = dash.Dash(__name__)

# App layout
app.layout = html.Div([
    dcc.Dropdown(
        id='region-dropdown',
        options=[{'label': region, 'value': region} for region in gdf['ERNAME'].unique()],
        value=gdf['ERNAME'].iloc[0],  # Default value
        clearable=False
    ),
    dcc.Graph(id='map-plot')
])

# Callback to update the map plot based on dropdown selection
@app.callback(
    Output('map-plot', 'figure'),
    Input('region-dropdown', 'value')
)
def update_map(selected_region):
    filtered_gdf = gdf[gdf['ERNAME'] == selected_region]
    
    fig = px.choropleth_mapbox(
        filtered_gdf, geojson=filtered_gdf.geometry, locations=filtered_gdf.index, color="ERNAME",
        mapbox_style="carto-positron", center={"lat": filtered_gdf.centroid.y.mean(), "lon": filtered_gdf.centroid.x.mean()},
        zoom=6, hover_name='ERNAME', opacity=0.5  # Set opacity to 0.5
    )
    
    # Remove the legend
    fig.update_layout(showlegend=False)
    
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)