import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import pandas as pd
import geopandas as gpd
import plotly.express as px

# Load the shapefile
gdf = gpd.read_file("./data/ler_000b16a_e.shp")
gdf = gdf.to_crs(epsg=4326)  # Ensure coordinate reference system is WGS84
gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)
gdf['centroid'] = gdf.geometry.centroid

# Load the job outlook data
file_paths = {
    'English': "./data/20242026_outlook_n21_en_250117.xlsx",
    'French': "./data/20242026_outlook_n21_fr_250117.xlsx"
}
cached_data = {}

def load_data(language):
    if language in cached_data:
        return cached_data[language]
    
    df = pd.read_excel(file_paths[language])
    df['Economic Region Name'] = df.apply(lambda row: f"{row['Economic Region Name']}, {row['Province']}", axis=1)
    cached_data[language] = df
    return df

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])

# App layout
app.layout = dbc.Container([
    dbc.Row([dbc.Col(html.H1("Canadian Job Market Outlook 2024-2026", style={'textAlign': 'center'}), width=12)]),
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='language-dropdown',
            options=[{'label': 'English', 'value': 'English'}, {'label': 'Français', 'value': 'French'}],
            value='English',
            clearable=False,
            style={'width': '35%', 'margin': 'auto'}
        ), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Dropdown(id='region-dropdown', clearable=False, style={'width': '50%', 'margin': 'auto'}), width=12)
    ]),
    dbc.Row([dbc.Col(dcc.Graph(id='map-plot', style={'height': '60vh'}), width=12)]),
    dbc.Row([dbc.Col(dcc.Graph(id='bar-plot', style={'height': '50vh'}), width=12)])
], fluid=True)

# Callbacks
@app.callback(
    [Output('region-dropdown', 'options'), Output('region-dropdown', 'value')],
    Input('language-dropdown', 'value')
)
def update_dropdown(language):
    df = load_data(language)
    region_options = [{'label': region, 'value': region} for region in sorted(df['Economic Region Name'].unique())]
    return region_options, region_options[0]['value']

@app.callback(
    [Output('map-plot', 'figure'), Output('bar-plot', 'figure')],
    [Input('region-dropdown', 'value'), Input('language-dropdown', 'value')]
)
def update_visuals(selected_region, language):
    df = load_data(language)
    filtered_gdf = gdf[gdf['ERNAME'] == selected_region]
    filtered_df = df[df['Economic Region Name'] == selected_region]
    
    map_fig = px.choropleth_mapbox(
        filtered_gdf, geojson=filtered_gdf.geometry, locations=filtered_gdf.index, color="ERNAME",
        mapbox_style="carto-positron", center={"lat": filtered_gdf.centroid.y.mean(), "lon": filtered_gdf.centroid.x.mean()},
        zoom=6, hover_name='ERNAME', opacity=0.5
    )
    map_fig.update_layout(showlegend=False)
    
    bar_fig = px.bar(
        filtered_df, x='NOC Title', y='Outlook', color='Outlook',
        labels={'x': 'NOC Title', 'y': 'Outlook'},
        hover_data={'NOC Title': True}
    )
    
    return map_fig, bar_fig

if __name__ == '__main__':
    app.run_server(debug=True)
