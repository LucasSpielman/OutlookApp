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

# Load the shapefile
gdf = gpd.read_file("./data/ler_000b16a_e.shp")
gdf = gdf.to_crs(epsg=4326)

# Simplify geometries to improve performance
gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)

gdf['centroid'] = gdf.geometry.centroid

# Global storage for cached data
cached_data = {}

# Mapbox token (optional but improves map appearance)
mapbox_token = "pk.eyJ1IjoieW91cm1hcGJveHRva2VuIiwiYSI6ImNraW5nYXJ0NzA0MjMzcW82amR3bm5jN2gifQ.fKQcLJ2TVGNHJUMneRoOXA"


def load_data(language):
    if language in cached_data:
        return cached_data[language]
    
    df = pd.read_excel(file_paths[language])
    
    if language == 'English':
        outlook_order = ['very good', 'good', 'moderate', 'limited', 'undetermined', 'bazinga']
        outlook_colors = {
            'very good': '#30AD23',
            'good': '#1E90FF',
            'moderate': '#FFD700',
            'limited': '#F08315',
            'undetermined': '#BA110C',
            'bazinga': '#D3D3D3',
        }
    else:
        outlook_order = ['très bonnes', 'bonnes', 'modérées', 'limitées', 'indéterminées', 'bazinga']
        outlook_colors = {
            'très bonnes': '#30AD23',
            'bonnes': '#1E90FF',
            'modérées': '#FFD700',
            'limitées': '#F08315',
            'indéterminées': '#BA110C',
            'bazinga': '#D3D3D3',
        }
    
    df['Economic Region Name'] = df.apply(lambda row: f"{row['Economic Region Name']}, {row['Province']}", axis=1)
    df['Outlook'] = pd.Categorical(df['Outlook'], categories=outlook_order, ordered=True)
    sorted_df = df.sort_values(by=['NOC Title', 'Economic Region Name', 'Outlook'])
    
    # Merge with geographical data
    merged_df = pd.merge(sorted_df, gdf, left_on='Economic Region Name', right_on='ERNAME', how='left')

    cached_data[language] = (merged_df, outlook_order, outlook_colors)
    return merged_df, outlook_order, outlook_colors

# Initialize the Dash app with the Minty theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])

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
        dbc.Col(dcc.Dropdown(id='region-dropdown', value=None, clearable=False, style={'width': '50%', 'margin': 'auto'}), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='outlook-dropdown', 
            value=None, 
            multi=True,
            clearable=False, 
            style={'width': '50%', 'margin': 'auto'}
        ), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='bar-plot', style={'height': '50vh'}), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='map-plot', style={'height': '60vh'}), width=12)
    ])
], fluid=True)

@app.callback(
    [Output('region-dropdown', 'options'), Output('region-dropdown', 'value'),
     Output('outlook-dropdown', 'options'), Output('outlook-dropdown', 'value')],
    Input('language-dropdown', 'value')
)
def update_dropdowns(language):
    sorted_df, outlook_order, _ = load_data(language)
    region_options = [{'label': region, 'value': region} for region in sorted(sorted_df['Economic Region Name'].unique())]
    outlook_options = [{'label': outlook, 'value': outlook} for outlook in outlook_order]

    return region_options, sorted_df['Economic Region Name'].iloc[0], outlook_options, outlook_order[:2]

@app.callback(
    Output('bar-plot', 'figure'),
    [Input('region-dropdown', 'value'), Input('language-dropdown', 'value'), Input('outlook-dropdown', 'value')]
)
def update_bar_plot(selected_region, language, selected_outlooks):
    sorted_df, outlook_order, outlook_colors = load_data(language)

    if not selected_outlooks:
        selected_outlooks = outlook_order

    filtered_df = sorted_df[
        (sorted_df['Economic Region Name'] == selected_region) & 
        (sorted_df['Outlook'].isin(selected_outlooks))
    ].drop_duplicates(subset=['NOC Title'])

    bar_fig = px.bar(
        filtered_df,
        x='NOC Title',
        y='Outlook',
        color='Outlook',
        color_discrete_map=outlook_colors,
        category_orders={'Outlook': outlook_order},
    )

    return bar_fig

@app.callback(
    Output('map-plot', 'figure'),
    [Input('region-dropdown', 'value'), Input('language-dropdown', 'value')]
)
def update_map(selected_region, language):
    sorted_df, _, _ = load_data(language)

    filtered_gdf = gdf[gdf['ERNAME'] == selected_region]

    fig = px.choropleth_mapbox(
        filtered_gdf,
        geojson=filtered_gdf.geometry.__geo_interface__,
        locations=filtered_gdf.index,
        color="ERNAME",
        mapbox_style="carto-positron",
        center={"lat": filtered_gdf.centroid.y.mean(), "lon": filtered_gdf.centroid.x.mean()},
        zoom=6,
        hover_name='ERNAME',
        opacity=0.5
    )

    fig.update_layout(mapbox_accesstoken=mapbox_token)

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)