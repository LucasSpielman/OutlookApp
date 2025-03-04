import dash
from dash import dcc, html
import dash_leaflet as dl
import geopandas as gpd
import json
import pandas as pd

# Load shapefile
gdf = gpd.read_file("./data/ler_000b16a_e.shp")

gdf = gdf.to_crs(epsg=4326)

# Convert to GeoJSON
geojson = json.loads(gdf.to_json())

job_outlook_data = pd.read_excel('./data/20242026_outlook_n21_en_250117.xlsx')

app = dash.Dash(__name__)

# Define colors for each outlook
outlook_colors = {
    'very good': 'green',
    'good': 'blue',
    'fair': 'yellow',
    'limited': 'orange',
    'undetermined': 'red'
}

# Filter job_outlook_data based on Outlook values
filtered_data = job_outlook_data[job_outlook_data['Outlook'].isin(outlook_colors.keys())]

# Extract coordinates for each Economic Region Name
region_coords = gdf[['ERNAME', 'geometry']].set_index('ERNAME').to_dict()['geometry']

# Create markers for each region
markers = []
for _, row in filtered_data.iterrows():
    region_name = row['Economic Region Name']
    outlook = row['Outlook']
    if region_name in region_coords:
        coords = region_coords[region_name].centroid.coords[0]
        markers.append(dl.Marker(position=[coords[1], coords[0]], children=dl.Tooltip(region_name), icon={
            "iconUrl": f"http://maps.google.com/mapfiles/ms/icons/{outlook_colors[outlook]}-dot.png"
        }))

# Add shaded background for provinces/territories
shaded_regions = []
for region_name, geometry in region_coords.items():
    shaded_regions.append(dl.GeoJSON(data=json.loads(gpd.GeoSeries([geometry]).to_json()), style={
        "fillColor": "grey",
        "fillOpacity": 0.2,
        "color": "grey",
        "weight": 1
    }))

# Create a legend manually
legend = html.Div([
    html.Div([html.Span(style={'backgroundColor': color, 'display': 'inline-block', 'width': '20px', 'height': '20px'}), html.Span(f' {outlook}')]) 
    for outlook, color in outlook_colors.items()
], style={'position': 'absolute', 'bottom': '10px', 'left': '10px', 'backgroundColor': 'white', 'padding': '10px', 'border': '1px solid black'})

# Update the app layout to include the new markers, shaded regions, and legend
app.layout = html.Div([
    dl.Map([
        dl.TileLayer(),
        dl.LayerGroup(markers),
        dl.LayerGroup(shaded_regions),
        dl.GeoJSON(data=geojson, style={"color": "grey", "weight": 2}),
    ], center=[gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()], zoom=5, style={"height": "600px"}),
    legend
])

if __name__ == "__main__":
    app.run_server(debug=True)