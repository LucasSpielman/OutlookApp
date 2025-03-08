import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import geopandas as gpd
import os

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
    
    df['Outlook'] = pd.Categorical(df['Outlook'], categories=outlook_order, ordered=True)
    sorted_df = df.sort_values(by=['NOC Title', 'Economic Region Name', 'Outlook'])
    
    cached_data[language] = (sorted_df, outlook_order, outlook_colors)
    return sorted_df, outlook_order, outlook_colors

# Initialize the Dash app with the Minty theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])

app.layout = dbc.Container([
    dbc.Row([dbc.Col(html.H1("Canadian Job Market Outlook 2024-2026", style={'textAlign': 'center'}), width=12)]),
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='language-dropdown',
            options=[{'label': 'English', 'value': 'English'}, {'label': 'Français', 'value': 'French'}],
            value='English',
            multi=False,  # Changed to False since we want single selection
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
        dbc.Col(dcc.Graph(id='map-plot'), width=6),
        dbc.Col(dcc.Graph(id='bar-plot'), width=6)
    ]),
    dbc.Row([
        dbc.Col(dcc.Slider(
            id='page-slider',
            min=1,
            max=1,
            step=1,
            value=1,
            marks={1: '1'}
        ), width=12)
    ]),
    dbc.Row([
        dbc.Col(html.Footer([
            html.P("Data sourced and provided by the Government of Canada."),
            html.A("Visit the website", href="https://www.statcan.gc.ca/en/subjects/standard/noc/2021/indexV1", target="_blank")
        ], style={'text-align': 'center', 'margin-top': '20px'}), width=12)
    ])
], fluid=True)

@app.callback(
    [Output('region-dropdown', 'options'), Output('region-dropdown', 'value'),
     Output('outlook-dropdown', 'options'), Output('outlook-dropdown', 'value')],
    Input('language-dropdown', 'value')
)
def update_dropdowns(language):
    if not language:
        return [], None, [], None
    
    sorted_df, outlook_order, _ = load_data(language)
    region_options = [{'label': region, 'value': region} for region in sorted(sorted_df['Economic Region Name'].unique())]
    outlook_options = [{'label': outlook, 'value': outlook} for outlook in outlook_order]
    return region_options, sorted_df['Economic Region Name'].iloc[0], outlook_options, outlook_order[:2]

@app.callback(
    [Output('map-plot', 'figure'), Output('bar-plot', 'figure'),
     Output('page-slider', 'max'), Output('page-slider', 'marks')],
    [Input('region-dropdown', 'value'), Input('language-dropdown', 'value'),
     Input('outlook-dropdown', 'value'), Input('page-slider', 'value')]
)
def update_plots(selected_region, language, selected_outlooks, page):
    # Handle case where inputs are None
    if not selected_region or not language:
        empty_map = px.choropleth_mapbox(
            gdf,
            geojson=gdf.__geo_interface__,
            locations=gdf.index,
            mapbox_style="carto-positron",
            center={"lat": 56.1304, "lon": -106.3468},  # Center of Canada
            zoom=3,
            opacity=0.5
        )
        empty_bar = px.bar()
        return empty_map, empty_bar, 1, {1: '1'}

    sorted_df, outlook_order, outlook_colors = load_data(language)
    
    # Extract region name without province for mapping
    region_name = selected_region.split(',')[0] if selected_region else None
    
    # Map plot
    filtered_gdf = gdf[gdf['ERNAME'] == region_name].copy()
    
    # Handle case where no matching region is found
    if filtered_gdf.empty:
        map_fig = px.choropleth_mapbox(
            gdf,
            geojson=gdf.__geo_interface__,
            locations=gdf.index,
            mapbox_style="carto-positron",
            center={"lat": 56.1304, "lon": -106.3468},  # Center of Canada
            zoom=3,
            opacity=0.5
        )
    else:
        map_fig = px.choropleth_mapbox(
            filtered_gdf,
            geojson=filtered_gdf.__geo_interface__,
            locations=filtered_gdf.index,
            color_continuous_scale="Viridis",
            mapbox_style="carto-positron",
            center={"lat": filtered_gdf.geometry.centroid.y.iloc[0],
                   "lon": filtered_gdf.geometry.centroid.x.iloc[0]},
            zoom=6,
            opacity=0.5
        )

    # Update map layout
    map_fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox=dict(style="carto-positron"),
        showlegend=False
    )

    # Bar plot
    if not selected_outlooks:
        selected_outlooks = outlook_order

    filtered_df = sorted_df[
        (sorted_df['Economic Region Name'] == selected_region) &
        (sorted_df['Outlook'].isin(selected_outlooks))
    ].copy()

    # Handle empty filtered dataframe
    if filtered_df.empty:
        bar_fig = px.bar()
        return map_fig, bar_fig, 1, {1: '1'}

    filtered_df = filtered_df.drop_duplicates(subset=['NOC Title'])

    items_per_page = 10
    total_pages = max(1, (len(filtered_df) + items_per_page - 1) // items_per_page)

    # Ensure page is within valid range
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    paginated_df = filtered_df.iloc[start_idx:end_idx]

    bar_fig = px.bar(
        paginated_df,
        x='NOC Title',
        y='Outlook',
        color='Outlook',
        labels={'x': 'NOC Title', 'y': 'Outlook'},
        color_discrete_map=outlook_colors,
        category_orders={'Outlook': outlook_order},
        hover_data={'NOC Title': True}
    )

    bar_fig.update_yaxes(
        tickmode='array',
        tickvals=outlook_order,
        ticktext=outlook_order
    )

    bar_fig.update_layout(
        title=f"Job Outlooks in {selected_region}",
        legend_title="Outlook Categories",
        xaxis_tickangle=-45,
        legend=dict(
            x=0, y=1,
            xanchor="left",
            yanchor="top",
            bgcolor="rgba(255,255,255,0.6)",
            bordercolor="black",
            borderwidth=1
        )
    )

    slider_marks = {i: str(i) for i in range(1, total_pages + 1)}
    return map_fig, bar_fig, total_pages, slider_marks

if __name__ == '__main__':
    app.run_server(debug=True)
