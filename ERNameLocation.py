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
        zoom=6, hover_name='ERNAME', opacity=0.5,  # Set opacity to 0.5
        hover_data={'index': False}  # Remove the index from the hover window
    )
    
    # Remove the legend
    fig.update_layout(showlegend=False)
    
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)