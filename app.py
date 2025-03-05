import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import geopandas as gpd

# Load the Excel file paths
file_paths = {
    'English': "./data/20242026_outlook_n21_en_250117.xlsx",
    'French': "./data/20242026_outlook_n21_fr_250117.xlsx"
}

# Global storage for data
data_cache = {}

# Function to load and cache data
def load_and_cache_data():
    global data_cache
    for language in file_paths:
        df = pd.read_excel(file_paths[language])

        if language == 'English':
            outlook_order = ['very good', 'good', 'moderate', 'limited', 'undetermined']
            outlook_colors = {
                'very good': 'green',
                'good': 'blue',
                'moderate': 'yellow',
                'limited': 'orange',
                'undetermined': 'red'
            }
        else:  # French
            outlook_order = ['très bonnes', 'bonnes', 'modérées', 'limitées', 'indéterminées']
            outlook_colors = {
                'très bonnes': 'green',
                'bonnes': 'blue',
                'modérées': 'yellow',
                'limitées': 'orange',
                'indéterminées': 'red'
            }

        df['Outlook'] = pd.Categorical(df['Outlook'], categories=outlook_order, ordered=True)
        sorted_df = df.sort_values(by=['NOC Title', 'Economic Region Name', 'Outlook'])

        data_cache[language] = {
            "df": sorted_df,
            "outlook_order": outlook_order,
            "outlook_colors": outlook_colors
        }

# Load the shapefile globally
gdf = gpd.read_file("./data/ler_000b16a_e.shp")
gdf = gdf.to_crs(epsg=4326)  # Ensure the coordinate reference system is WGS84

# Simplify geometries to improve performance
gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)

# Calculate centroids for each region
gdf['centroid'] = gdf.geometry.centroid

# Load data once at startup
load_and_cache_data()

# Initialize the Dash app
app = dash.Dash(__name__)

# App layout
app.layout = html.Div([
    dcc.Dropdown(
        id='language-dropdown',
        options=[{'label': 'English', 'value': 'English'}, {'label': 'Français', 'value': 'French'}],
        value='English',
        clearable=False
    ),
    dcc.Dropdown(
        id='noc-dropdown',
        value=None,  # Default to None until data loads
        multi=False,
        clearable=False
    ),
    dcc.Graph(id='map-plot'),
    dcc.Graph(id='bar-plot')
])

# Callback to update NOC dropdown
@app.callback(
    [Output('noc-dropdown', 'options'), Output('noc-dropdown', 'value')],
    Input('language-dropdown', 'value')
)
def update_noc_dropdown(language):
    sorted_df = data_cache[language]["df"]
    options = [{'label': title, 'value': title} for title in sorted_df['NOC Title'].unique()]
    return options, sorted_df['NOC Title'].iloc[0]

# Callback to update both plots
@app.callback(
    [Output('map-plot', 'figure'), Output('bar-plot', 'figure')],
    [Input('noc-dropdown', 'value'), Input('language-dropdown', 'value')]
)
def update_plots(selected_noc, language):
    sorted_df = data_cache[language]["df"]
    outlook_order = data_cache[language]["outlook_order"]
    outlook_colors = data_cache[language]["outlook_colors"]

    merged_df = gdf[['ERNAME', 'centroid']].merge(sorted_df, left_on='ERNAME', right_on='Economic Region Name')
    merged_df['lat'] = merged_df['centroid'].apply(lambda point: point.y)
    merged_df['lon'] = merged_df['centroid'].apply(lambda point: point.x)
    filtered_df = merged_df[merged_df['NOC Title'] == selected_noc]

    # Map plot
    map_fig = px.scatter_mapbox(
        filtered_df, lat='lat', lon='lon', color='Outlook', size_max=13, zoom=3,
        mapbox_style="carto-positron", center={"lat": 56.1304, "lon": -106.3468},
        title='Career Outlook for Canadian Economic Regions 2024-2026',
        category_orders={'Outlook': outlook_order},
        color_discrete_map=outlook_colors,
        hover_name='Economic Region Name',
        size=[6.5] * len(filtered_df)
    )

    # Bar plot
    bar_fig = px.bar(
        filtered_df, x='Economic Region Name', y=[1] * len(filtered_df), color='Outlook',
        # title='Outlook Distribution by Economic Region',
        labels={'x': 'Economic Region Name', 'y': 'Count'},
        category_orders={'Outlook': outlook_order},
        color_discrete_map=outlook_colors
    )

    # Sync legend across both plots
    map_fig.update_layout(showlegend=True)
    bar_fig.update_layout(showlegend=True, legend=dict(title='Outlook'))

    return map_fig, bar_fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
