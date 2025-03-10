# app.py
import dash
from dash import dcc, html
from NOCTitlebyER import app as NOC_app  # Import NOC_app
from NOCTitlebyER import load_data as NOC_load_data  # Import NOC_load_data
from ERbyNOCTitle import app as ER_app # Import ER_app
from ERbyNOCTitle import load_data as ER_load_data  # Import ER_load_data
import geopandas as gpd

# Load the shapefile for geographical data
gdf_1 = gpd.read_file("./data/ler_000b16a_e.shp")
gdf_1 = gdf_1.to_crs(epsg=4326)  # Ensure the coordinate reference system is WGS84

# Simplify geometries to improve performance
gdf_1['geometry'] = gdf_1['geometry'].simplify(tolerance=0.01, preserve_topology=True)

# Calculate centroids for each region
gdf_1['centroid'] = gdf_1.geometry.centroid

# Load the Excel file paths for English and French data

# Global storage for cached data to avoid reloading it multiple times
cached_data_1 = {}

# Create your main Dash app
app = dash.Dash(__name__)

# Define the layout with Tabs
app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label='Dashboard 1', children=[NOC_app.layout]),  # Use the layout from NOC_app
        dcc.Tab(label='Dashboard 2', children=[ER_app.layout])    # Use the layout from ER_app
    ])
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)