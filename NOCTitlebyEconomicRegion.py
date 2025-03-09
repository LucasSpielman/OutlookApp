import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import geopandas as gpd

# Load the shapefile
gdf = gpd.read_file("./data/ler_000b16a_e.shp")
gdf = gdf.to_crs(epsg=4326)

gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)
gdf['centroid'] = gdf.geometry.centroid

# Load the Excel file paths
file_paths = {
    'English': "./data/20242026_outlook_n21_en_250117.xlsx",
    'French': "./data/20242026_outlook_n21_fr_250117.xlsx"
}

cached_data = {}

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

    df['Economic Region Name'] = df['Economic Region Name'].str.split(',').str[0]
    df['Outlook'] = pd.Categorical(df['Outlook'], categories=outlook_order, ordered=True)
    merged_df = gdf[['ERNAME', 'centroid']].merge(df, left_on='ERNAME', right_on='Economic Region Name')

    cached_data[language] = (merged_df, outlook_order, outlook_colors)
    return merged_df, outlook_order, outlook_colors

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])

app.layout = dbc.Container([
    dcc.Dropdown(
        id='region-dropdown',
        options=[{'label': region, 'value': region} for region in gdf['ERNAME'].unique()],
        value=gdf['ERNAME'].iloc[0],
        clearable=False
    ),
    dcc.Graph(id='map-plot'),
    dcc.Graph(id='bar-plot')
])

@app.callback(
    [Output('map-plot', 'figure'), Output('bar-plot', 'figure')],
    [Input('region-dropdown', 'value')]
)
def update_plots(selected_region):
    merged_df, _, outlook_colors = load_data('English')
    filtered_gdf = gdf[gdf['ERNAME'] == selected_region]
    filtered_data = merged_df[merged_df['ERNAME'] == selected_region]

    map_fig = px.choropleth_mapbox(
        filtered_gdf, geojson=filtered_gdf.geometry, locations=filtered_gdf.index, color="ERNAME",
        mapbox_style="carto-positron", center={"lat": filtered_gdf.centroid.y.mean(), "lon": filtered_gdf.centroid.x.mean()},
        zoom=6, hover_name='ERNAME', opacity=0.5
    )
    map_fig.update_layout(showlegend=False)

    bar_fig = px.bar(
        filtered_data,
        x='NOC Title',
        y='Outlook',
        color='Outlook',
        color_discrete_map=outlook_colors
    )

    return map_fig, bar_fig

if __name__ == '__main__':
    app.run_server(debug=True)
