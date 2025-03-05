import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import geopandas as gpd
from functools import lru_cache

# File paths
file_paths = {
    'English': "./data/20242026_outlook_n21_en_250117.xlsx",
    'French': "./data/20242026_outlook_n21_fr_250117.xlsx"
}

# Load the shapefile (done once at startup)
gdf = gpd.read_file("./data/ler_000b16a_e.shp").to_crs(epsg=4326)
gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)
gdf['centroid'] = gdf.geometry.centroid

# Cache function to load and process data
@lru_cache(maxsize=2)
def load_data(language):
    df = pd.read_excel(file_paths[language])

    outlook_map = {
        'English': (['very good', 'good', 'moderate', 'limited', 'undetermined'],
                    {'very good': 'green', 'good': 'blue', 'moderate': 'yellow', 'limited': 'orange', 'undetermined': 'red'}),
        'French': (['très bonnes', 'bonnes', 'modérées', 'limitées', 'indéterminées'],
                   {'très bonnes': 'green', 'bonnes': 'blue', 'modérées': 'yellow', 'limitées': 'orange', 'indéterminées': 'red'})
    }

    outlook_order, outlook_colors = outlook_map[language]
    df['Outlook'] = pd.Categorical(df['Outlook'], categories=outlook_order, ordered=True)
    
    # Sort NOC Titles alphabetically
    noc_titles = sorted(df['NOC Title'].unique())

    return df, outlook_order, outlook_colors, noc_titles

# Dash app initialization
app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Dropdown(id='language-dropdown',
        options=[{'label': 'English', 'value': 'English'}, {'label': 'Français', 'value': 'French'}],
        value='English', clearable=False
    ),
    dcc.Dropdown(id='noc-dropdown', value=None, clearable=False),
    dcc.Graph(id='map-plot'),
    dcc.Graph(id='bar-plot')
])

# Callback to update NOC dropdown
@app.callback(
    [Output('noc-dropdown', 'options'), Output('noc-dropdown', 'value')],
    Input('language-dropdown', 'value')
)
def update_noc_dropdown(language):
    _, _, _, noc_titles = load_data(language)
    options = [{'label': title, 'value': title} for title in noc_titles]
    return options, noc_titles[0]

# Callback to update both plots
@app.callback(
    [Output('map-plot', 'figure'), Output('bar-plot', 'figure')],
    [Input('noc-dropdown', 'value'), Input('language-dropdown', 'value')]
)
def update_plots(selected_noc, language):
    df, outlook_order, outlook_colors, _ = load_data(language)
    
    # Merge and filter data only once
    merged_df = gdf[['ERNAME', 'centroid']].merge(df, left_on='ERNAME', right_on='Economic Region Name')
    merged_df[['lat', 'lon']] = merged_df['centroid'].apply(lambda point: pd.Series([point.y, point.x]))
    filtered_df = merged_df[merged_df['NOC Title'] == selected_noc]

    # Map plot (with legend)
    map_fig = px.scatter_mapbox(
        filtered_df, lat='lat', lon='lon', color='Outlook', size_max=13, zoom=3,
        mapbox_style="carto-positron", center={"lat": 56.1304, "lon": -106.3468},
        title='Career Outlook for Canadian Economic Regions 2024-2026',
        category_orders={'Outlook': outlook_order},
        color_discrete_map=outlook_colors,
        hover_name='Economic Region Name',
        size=[6.5] * len(filtered_df)
    )
    map_fig.update_layout(showlegend=True)

    # Bar plot (no legend, but colors still match)
    bar_fig = px.bar(
        filtered_df, x='Economic Region Name', y=[1] * len(filtered_df), color='Outlook',
        title='Outlook Distribution by Economic Region',
        labels={'x': 'Economic Region Name', 'y': 'Count'},
        category_orders={'Outlook': outlook_order},
        color_discrete_map=outlook_colors
    )
    bar_fig.update_layout(showlegend=False)

    return map_fig, bar_fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
