import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd
import geopandas as gpd

# Load the Excel files
file_paths = {
    'English': "./data/20242026_outlook_n21_en_250117.xlsx",
    'French': "./data/20242026_outlook_n21_fr_250117.xlsx"
}

# Function to load and process data
def load_data(language):
    df = pd.read_excel(file_paths[language])
    outlook_order = ['very good', 'good', 'moderate', 'limited', 'undetermined']
    outlook_colors = {
        'very good': 'green',
        'good': 'blue',
        'moderate': 'yellow',
        'limited': 'orange',
        'undetermined': 'red'
    }
    df['Outlook'] = pd.Categorical(df['Outlook'], categories=outlook_order, ordered=True)
    sorted_df = df.sort_values(by=['NOC Title', 'Economic Region Name', 'Outlook'])
    return sorted_df, outlook_order, outlook_colors

# Load the shapefile
gdf = gpd.read_file("./data/ler_000b16a_e.shp")
gdf = gdf.to_crs(epsg=4326)  # Ensure the coordinate reference system is WGS84
gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)
gdf['centroid'] = gdf.geometry.centroid

# Initialize the Dash app
app = dash.Dash(__name__)

# App layout
app.layout = html.Div([
    html.H1("Career Outlook for Canadian Economic Regions 2024-2026", style={'textAlign': 'center'}),
    dcc.Dropdown(
        id='noc-dropdown',
        multi=True,  # Allow multiple selections
        clearable=False
    ),
    dcc.Graph(id='map-plot', style={"width": "100vw", "height": "45vh"}),
    dcc.Graph(id='scatter-plot', style={"width": "100vw", "height": "45vh"}),
    html.Div([
        dcc.Dropdown(
            id='language-dropdown',
            options=[
                {'label': 'English', 'value': 'English'},
                {'label': 'French', 'value': 'French'}
            ],
            value='English',  # Default value
            clearable=False
        )
    ], style={"position": "absolute", "bottom": "10px", "right": "10px", "width": "200px"})
], style={"width": "100vw", "height": "100vh", "margin": "0", "padding": "0"})

# Combined callback to update the dropdown options and plots based on language selection and NOC Titles
@app.callback(
    [Output('noc-dropdown', 'options'),
     Output('noc-dropdown', 'value'),
     Output('map-plot', 'figure'),
     Output('scatter-plot', 'figure')],
    [Input('language-dropdown', 'value'),
     Input('noc-dropdown', 'value')]
)
def update_content(language, selected_nocs):
    sorted_df, outlook_order, outlook_colors = load_data(language)
    options = [{'label': title, 'value': title} for title in sorted_df['NOC Title'].unique()]
    if not selected_nocs:
        selected_nocs = [sorted_df['NOC Title'].iloc[0]]  # Default value
    merged_df = gdf[['ERNAME', 'centroid']].merge(sorted_df, left_on='ERNAME', right_on='Economic Region Name')
    merged_df['lat'] = merged_df['centroid'].apply(lambda point: point.y)
    merged_df['lon'] = merged_df['centroid'].apply(lambda point: point.x)
    filtered_df = merged_df[merged_df['NOC Title'].isin(selected_nocs)]
    
    map_fig = px.scatter_mapbox(
        filtered_df, lat='lat', lon='lon', color='Outlook', size_max=15, zoom=3,
        mapbox_style="carto-positron", center={"lat": 56.1304, "lon": -106.3468},
        category_orders={'Outlook': outlook_order},
        color_discrete_map=outlook_colors,
        hover_name='Economic Region Name'
    )
    map_fig.update_layout(
        autosize=True,
        margin={"r":0,"t":0,"l":0,"b":0}
    )
    
    filtered_df = sorted_df[sorted_df['NOC Title'].isin(selected_nocs)]
    scatter_fig = px.scatter(
        filtered_df, x='Economic Region Name', y='NOC Title', color='Outlook',
        category_orders={'Outlook': outlook_order},
        color_discrete_map=outlook_colors
    )
    
    return options, selected_nocs, map_fig, scatter_fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)