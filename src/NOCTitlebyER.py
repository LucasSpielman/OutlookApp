import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd
import geopandas as gpd
from text_content import text_content as text_content_1

# Constants
FILE_PATHS = {
    'English': "./data/20242026_outlook_n21_en_250117.xlsx",
    'French': "./data/20242026_outlook_n21_fr_250117.xlsx"
}
GEOJSON_PATH = "./data/ler_000b16a_e.shp"
CACHED_DATA = {}

# Load geographical data
def load_geographical_data():
    gdf = gpd.read_file(GEOJSON_PATH)
    gdf = gdf.to_crs(epsg=4326)
    gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)
    gdf = gdf.to_crs(epsg=3857)  # Re-project to a projected CRS
    gdf['centroid'] = gdf['geometry'].centroid
    gdf = gdf.to_crs(epsg=4326)  # Convert back to geographic CRS
    return gdf

GDF = load_geographical_data()

# Load data based on language
def load_data(language):
    if language in CACHED_DATA:
        return CACHED_DATA[language]

    df = pd.read_excel(FILE_PATHS[language])
    outlook_order, outlook_colors = get_outlook_config(language)
    df['Economic Region Name'] = df['Economic Region Name'].str.split(',').str[0]
    df['Outlook'] = pd.Categorical(df['Outlook'], categories=outlook_order, ordered=True)
    merged_df = GDF[['ERNAME', 'centroid']].merge(df, left_on='ERNAME', right_on='Economic Region Name')
    CACHED_DATA[language] = (merged_df, outlook_order, outlook_colors)
    return merged_df, outlook_order, outlook_colors

# Get outlook configuration based on language
def get_outlook_config(language):
    if language == 'English':
        outlook_order = ['very good', 'good', 'moderate', 'limited', 'undetermined', 'None']
        outlook_colors = {
            'very good': {'color': '#30AD23', 'text': 'white'},
            'good': {'color': '#1E90FF', 'text': 'white'},
            'moderate': {'color': '#FFD700', 'text': 'black'},
            'limited': {'color': '#F08315', 'text': 'black'},
            'undetermined': {'color': '#BA110C', 'text': 'white'},
            'None': {'color': '#D3D3D3', 'text': 'black'},
        }
    else:
        outlook_order = ['très bonnes', 'bonnes', 'modérées', 'limitées', 'indéterminées', 'None']
        outlook_colors = {
            'très bonnes': {'color': '#30AD23', 'text': 'white'},
            'bonnes': {'color': '#1E90FF', 'text': 'white'},
            'modérées': {'color': '#FFD700', 'text': 'black'},
            'limitées': {'color': '#F08315', 'text': 'black'},
            'indéterminées': {'color': '#BA110C', 'text': 'white'},
            'None': {'color': '#D3D3D3', 'text': 'black'},
        }
    return outlook_order, outlook_colors

# Define the layout of the app
def create_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col(html.H1(id='app-title-1', style={'textAlign': 'Left', 'margin-top': '30px'}), width=10),
            dbc.Col(dbc.Button("Info", id="open-modal-1", color="primary"), width=2, style={'textAlign': 'right', 'margin-top': '15px'})
        ]),
        dbc.Row([
            dbc.Col(dcc.Dropdown(id='region-dropdown-1', value=None, clearable=False, style={'width': '100%', 'margin': 'left'}), width=3)
        ], justify='start'),
        dbc.Row([
            dbc.Col(dcc.Graph(id='map-plot-1', style={'height': '50vh'}), width=12)
        ]),
        dbc.Row([
            dbc.Col(dcc.Input(id='noc-title-input-1', type='text', placeholder='Search for Job Title...', style={'width': '100%', 'margin': 'auto'}), width=3)
        ], justify='start'),
        dbc.Row([
            dbc.Col(dcc.Dropdown(id='outlook-dropdown-1', value=None, multi=False, clearable=False, style={'width': '100%', 'margin': 'left'}), width=3)
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(id='bar-plot-1', style={'height': '400px'}), width=12)
        ]),
        dbc.Row([
            dbc.Col(dcc.Slider(id='page-slider-1', min=1, max=1, step=1, value=1, marks={1: '1'}), width=12)
        ]),
        dbc.Row([
            dbc.Col(html.Div([
                html.P(id='data-source-text-1'),
                html.A(id='visit-website-link-1', href="https://www.statcan.gc.ca/en/subjects/standard/noc/2021/indexV1", target="_blank"),
                html.Br(),
                html.A(id='open-data-link-1', href="https://open.canada.ca/data/en/dataset/b0e112e9-cf53-4e79-8838-23cd98debe5b?_gl=1*h2x1ic*_ga*MTc4Mjg5MzYwMi4xNjc4MTQ5Mjc1*_ga_S9JG8CZVYZ*MTczNDM4ODMyOC4xMi4xLjE3MzQzODg2OTUuNDkuMC4w", target="_blank")
            ], style={'text-align': 'center', 'margin-top': '20px'}), width=12)
        ]),
        dbc.Row([
            dbc.Col(html.Footer(), width=10),
            dbc.Col(dcc.Dropdown(id='language-dropdown-1', options=[{'label': 'English', 'value': 'English'}, {'label': 'Français', 'value': 'French'}], value='English', clearable=False, style={'width': '100%'}), width=1)
        ]),
        dbc.Row([
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("About This App")),
                dbc.ModalBody(dcc.Markdown(id='modal-info-text-1')),
                dbc.ModalFooter(dbc.Button("Close", id="close-modal-1", className="ms-auto", n_clicks=0)),
            ], id="modal-1", is_open=False),
        ], justify='start', style={'margin-top': '20px'}),
        html.Div(id='selected-noc-title-1', style={'display': 'none'}),
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Employment Trends")),
            dbc.ModalBody(id='employment-trends-body-1'),
            dbc.ModalFooter(dbc.Button("Close", id="close-trends-modal-1", className="ms-auto", n_clicks=0)),
        ], id="trends-modal-1", is_open=False, style={"maxWidth": "100%"})
    ], fluid=True)

# Initialize the Dash app
def init_app():
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])
    app.layout = create_layout()
    register_callbacks(app)
    return app

# Register all callbacks
def register_callbacks(app):
    @app.callback(
        [Output('app-title-1', 'children'),
        Output('data-source-text-1', 'children'),
        Output('visit-website-link-1', 'children'),
        Output('visit-website-link-1', 'href'),
        Output('open-data-link-1', 'children'),
        Output('open-data-link-1', 'href'),
        Output('modal-info-text-1', 'children'),
        Output('noc-title-input-1', 'placeholder')],
        Input('language-dropdown-1', 'value')
    )
    def update_text_content_1(language):
        content = text_content_1()[language]
        return (content['title'], content['data_source'], content['visit_website'], content['visit_website_link'], content['open_data'], content['open_data_link'], content['modal_info'], content['noc_title_placeholder'])

    @app.callback(
        [Output('region-dropdown-1', 'options'), Output('region-dropdown-1', 'value'),
        Output('outlook-dropdown-1', 'options'), Output('outlook-dropdown-1', 'value')],
        Input('language-dropdown-1', 'value')
    )
    def update_dropdowns(language):
        merged_df, outlook_order, _ = load_data(language)
        region_options = [{'label': region, 'value': region} for region in sorted(merged_df['ERNAME'].unique())]
        outlook_options = [{'label': outlook, 'value': outlook} for outlook in outlook_order]
        return region_options, merged_df['ERNAME'].iloc[0], outlook_options, outlook_order[0]

    @app.callback(
        [Output('map-plot-1', 'figure'), Output('bar-plot-1', 'figure'), Output('page-slider-1', 'max'), Output('page-slider-1', 'marks')],
        [Input('region-dropdown-1', 'value'), Input('language-dropdown-1', 'value'), Input('outlook-dropdown-1', 'value'), Input('noc-title-input-1', 'value'), Input('page-slider-1', 'value')]
    )
    def update_plots(selected_region, language, selected_outlook, noc_title, page):
        merged_df, outlook_order, outlook_colors = load_data(language)
        if not selected_outlook:
            selected_outlook = outlook_order[0]
        filtered_gdf = GDF[GDF['ERNAME'] == selected_region]
        filtered_data = merged_df[(merged_df['ERNAME'] == selected_region) & (merged_df['Outlook'] == selected_outlook)]
        if noc_title:
            filtered_data = filtered_data[filtered_data['NOC Title'].str.contains(noc_title, case=False, na=False)]
        items_per_page = 5
        total_pages = (len(filtered_data) + items_per_page - 1) // items_per_page
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        paginated_data = filtered_data.iloc[start_idx:end_idx]
        map_fig = px.choropleth_mapbox(
            filtered_gdf, geojson=filtered_gdf.geometry, locations=filtered_gdf.index, color="ERNAME",
            mapbox_style="carto-positron", center={"lat": filtered_gdf.centroid.y.mean(), "lon": filtered_gdf.centroid.x.mean()},
            zoom=6, hover_name='ERNAME', opacity=0.5
        )
        map_fig.update_layout(showlegend=False)
        bar_fig = px.bar(
            paginated_data,
            x='NOC Title',
            y='Outlook',
            color='Outlook',
            color_discrete_map={k: v['color'] for k, v in outlook_colors.items()},
            category_orders={'Outlook': outlook_order},
            hover_data={'NOC Title': True}
        )
        for data in bar_fig.data:
            data.textfont = dict(color=[outlook_colors[outlook]['text'] for outlook in data.y])
        bar_fig.update_yaxes(
            tickmode='array',
            tickvals=outlook_order,
            ticktext=outlook_order
        )
        bar_fig.update_layout(
            title=f"Job Outlooks in {selected_region}",
            showlegend=False,
            hoverlabel=dict(
                font_size=16,
                font_family="Arial"
            ),
            xaxis_tickangle=-5,
            xaxis=dict(
                title_font=dict(size=18),
                tickfont=dict(size=14)
            ),
            yaxis=dict(
                title_font=dict(size=18),
                tickfont=dict(size=14)
            )
        )
        slider_marks = {i: str(i) for i in range(1, total_pages + 1)}
        return map_fig, bar_fig, total_pages, slider_marks

    @app.callback(
        Output("modal-1", "is_open"),
        [Input("open-modal-1", "n_clicks"), Input("close-modal-1", "n_clicks")],
        [State("modal-1", "is_open")],
    )
    def toggle_modal(n1, n2, is_open):
        if n1 or n2:
            return not is_open
        return is_open

    @app.callback(
        Output('selected-noc-title-1', 'children'),
        Input('bar-plot-1', 'clickData')
    )
    def update_selected_noc_title(clickData):
        if clickData:
            return clickData['points'][0]['x']
        return ''

    @app.callback(
        Output("trends-modal-1", "is_open"),
        Output("employment-trends-body-1", "children"),
        [Input('selected-noc-title-1', 'children'), Input("close-trends-modal-1", "n_clicks")],
        [State("trends-modal-1", "is_open"), State('language-dropdown-1', 'value')]
    )
    def toggle_trends_modal(noc_title, n_clicks, is_open, language):
        if noc_title and not is_open:
            merged_df, _, _ = load_data(language)
            trends_data = merged_df[merged_df['NOC Title'] == noc_title]['Employment Trends'].values[0]
            trends_body = dcc.Markdown(trends_data, dangerously_allow_html=True)
            return True, trends_body
        if n_clicks:
            return False, ''
        return is_open, ''

# Run the app
if __name__ == '__main__':
    app = init_app()
    app.run_server(debug=True)