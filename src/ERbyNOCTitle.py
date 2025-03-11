import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd
import geopandas as gpd
from text_content import text_content_er

# Load the Excel file paths
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
    gdf['centroid'] = gdf.geometry.centroid
    return gdf

GDF = load_geographical_data()

# Load data based on language
def load_data(language):
    if language in CACHED_DATA:
        return CACHED_DATA[language]
    
    df = pd.read_excel(FILE_PATHS[language])
    outlook_order, outlook_colors = get_outlook_config(language)
    df['Outlook'] = pd.Categorical(df['Outlook'], categories=outlook_order, ordered=True)
    sorted_df = df.sort_values(by=['NOC Title', 'Economic Region Name', 'Outlook'])
    CACHED_DATA[language] = (sorted_df, outlook_order, outlook_colors)
    return sorted_df, outlook_order, outlook_colors

# Get outlook configuration based on language
def get_outlook_config(language):
    if language == 'English':
        outlook_order = ['very good', 'good', 'moderate', 'limited', 'undetermined', 'None']
        outlook_colors = {
            'very good': '#30AD23',
            'good': '#1E90FF',
            'moderate': '#FFD700',
            'limited': '#F08315',
            'undetermined': '#BA110C',
            'None': '#D3D3D3',
        }
    else:
        outlook_order = ['très bonnes', 'bonnes', 'modérées', 'limitées', 'indéterminées', 'None']
        outlook_colors = {
            'très bonnes': '#30AD23',
            'bonnes': '#1E90FF',
            'modérées': '#FFD700',
            'limitées': '#F08315',
            'indéterminées': '#BA110C',
            'None': '#D3D3D3',
        }
    return outlook_order, outlook_colors

def create_title_row():
    return dbc.Row([
        dbc.Col(html.H1(id='dashboard-title', style={'textAlign': 'left', 'margin-top': '20px'}), width=10),
        dbc.Col(dbc.Button("Info", id="open-info-modal", color="primary"), width=2, style={'textAlign': 'right', 'margin-top': '20px'})
    ], style={'margin-left': '0', 'margin-right': '0'})

def create_noc_dropdown_row():
    return dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='noc-dropdown',
            value=None,
            multi=False,
            clearable=False,
            style={'width': '100%', 'margin-top': '20px'}
        ), width=3)
    ], style={'margin-left': '0', 'margin-right': '0'})

def create_map_plot_row():
    return dbc.Row([
        dbc.Col(dcc.Graph(id='map-plot', style={'height': '55vh'}), width=12)
    ], style={'margin-left': '0', 'margin-right': '0'})

def create_region_dropdown_row():
    return dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='region-dropdown',
            value=['All'],
            multi=True,
            clearable=True,
            placeholder="Select Economic Region",
            style={'width': '100%', 'margin-top': '20px'}
        ), width=3)
    ], style={'margin-left': '0', 'margin-right': '0'})

def create_bar_plot_row():
    return dbc.Row([
        dbc.Col(dcc.Graph(id='bar-plot', style={'height': '20vh'}), width=12)
    ], style={'margin-left': '0', 'margin-right': '0'})

def create_data_source_row():
    return dbc.Row([
        dbc.Col(html.P(id='data-source', style={'text-align': 'center', 'margin-top': '20px'}), width=12, style={'position': 'absolute', 'bottom': '20px', 'width': '100%'})
    ], style={'margin-left': '0', 'margin-right': '0'})

def create_language_dropdown_row():
    return dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='language-dropdown',
            options=[{'label': 'English', 'value': 'English'}, {'label': 'Français', 'value': 'French'}],
            value='English',
            clearable=False,
            style={'width': '100%', 'margin-right': 'auto', 'margin-left': 'auto'}
        ), width=1, style={'margin-left': 'auto'})
    ], style={'position': 'absolute', 'bottom': '20px', 'width': '100%', 'left': '0', 'right': '0'})

def create_info_modal():
    return dbc.Modal([
        dbc.ModalHeader(id="info-modal-header"),
        dbc.ModalBody(dcc.Markdown(id="info-modal-body")),
        dbc.ModalFooter(
            dbc.Button(id="close-info-modal", className="ml-auto")
        )
    ], id="info-modal", is_open=False)

def create_trends_modal():
    return dbc.Modal([
        dbc.ModalHeader("Employment Trends"),
        dbc.ModalBody(dcc.Markdown(id="employment-trends-body", dangerously_allow_html=True)),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-trends-modal", className="ml-auto")
        )
    ], id="trends-modal", is_open=False)

def toggle_info_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

def create_layout():
    return dbc.Container([
        dcc.Store(id='previous-values', data={'noc': None, 'region': None, 'language': 'English'}),
        create_title_row(),
        create_noc_dropdown_row(),
        create_map_plot_row(),
        create_region_dropdown_row(),
        create_bar_plot_row(),
        # create_data_source_row(),
        create_language_dropdown_row(),
        create_info_modal(),
        create_trends_modal()
    ], fluid=True)

def update_dropdowns(language):
    sorted_df, _, _ = load_data(language)
    noc_options = [{'label': title, 'value': title} for title in sorted(sorted_df['NOC Title'].unique())]
    region_options = [{'label': 'All', 'value': 'All'}] + [{'label': region, 'value': region} for region in sorted(sorted_df['Economic Region Name'].unique())]
    title, info_header, info_body, close_button, data_source = get_language_content(language)
    return noc_options, sorted_df['NOC Title'].iloc[0], region_options, title, info_header, info_body, close_button, data_source

def text_content():
    return text_content_er()

def get_language_content(language):
    content = text_content()[language]
    title = content['title']
    info_header = "About This App" if language == 'English' else "À propos de cette application"
    info_body = content['modal_info']
    close_button = "Close" if language == 'English' else "Fermer"
    data_source = [
        content['data_source'],
        html.Br(),
        html.A(content['visit_website'], href=content['visit_website_link'], target="_blank"),
        html.Br(),
        html.A(content['open_data'], href=content['open_data_link'], target="_blank")
    ]
    return title, info_header, info_body, close_button, data_source

def update_plots(selected_noc, selected_regions, language):
    sorted_df, outlook_order, outlook_colors = load_data(language)
    
    merged_df = GDF[['ERNAME', 'centroid']].merge(sorted_df, left_on='ERNAME', right_on='Economic Region Name')
    merged_df['lat'] = merged_df['centroid'].apply(lambda point: point.y)
    merged_df['lon'] = merged_df['centroid'].apply(lambda point: point.x)
    
    filtered_df = merged_df[merged_df['NOC Title'] == selected_noc]
    if selected_regions and 'All' not in selected_regions:
        filtered_df = filtered_df[filtered_df['Economic Region Name'].isin(selected_regions)]
    
    map_fig = create_map_plot(filtered_df, outlook_order, outlook_colors)
    bar_fig = create_bar_plot(filtered_df, outlook_order, outlook_colors, language)
    
    return map_fig, bar_fig

def create_map_plot(filtered_df, outlook_order, outlook_colors):
    return px.scatter_mapbox(
        filtered_df, lat='lat', lon='lon', color='Outlook', size_max=13, zoom=3,
        mapbox_style="carto-positron", center={"lat": 60.0, "lon": -106.3468},
        category_orders={'Outlook': outlook_order},
        color_discrete_map=outlook_colors,
        hover_name='Economic Region Name',
        size=[6.5] * len(filtered_df)
    ).update_layout(
        showlegend=True,
        legend=dict(
            x=0.01,
            y=0.99,
            traceorder='normal',
            bgcolor='rgba(255, 255, 255, 0.7)',
            bordercolor='rgba(0, 0, 0, 0.1)',
            borderwidth=1
        )
    )

def create_bar_plot(filtered_df, outlook_order, outlook_colors, language):
    bar_labels = {'x': ' ', 'y': 'Outlook'} if language == 'English' else {'x': ' ', 'y': 'Perspectives'}
    return px.bar(
        filtered_df, x='Economic Region Name', y='Outlook', color='Outlook',
        labels=bar_labels,
        category_orders={'Outlook': outlook_order},
        color_discrete_map=outlook_colors
    ).update_layout(
        showlegend=False,
        xaxis_title=''  # Remove x-axis label
    )

def display_trends_modal(map_click, bar_click, close_click, is_open, language):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, ""
    
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger == "close-trends-modal":
        return False, ""
    
    if trigger == "map-plot" and map_click:
        region_name = map_click['points'][0]['hovertext']
    elif trigger == "bar-plot" and bar_click:
        region_name = bar_click['points'][0]['x']
    else:
        return is_open, ""
    
    sorted_df, _, _ = load_data(language)
    employment_trends = sorted_df[sorted_df['Economic Region Name'] == region_name]['Employment Trends'].values[0]
    
    return True, employment_trends

def register_callbacks(app):
    app.callback(
        Output("info-modal", "is_open"),
        [Input("open-info-modal", "n_clicks"), Input("close-info-modal", "n_clicks")],
        [State("info-modal", "is_open")]
    )(toggle_info_modal)

    app.callback(
        [Output('noc-dropdown', 'options'), Output('noc-dropdown', 'value'), Output('region-dropdown', 'options'), Output('dashboard-title', 'children'), Output('info-modal-header', 'children'), Output('info-modal-body', 'children'), Output('close-info-modal', 'children'), Output('data-source', 'children')],
        Input('language-dropdown', 'value')
    )(update_dropdowns)

    app.callback(
        [Output('map-plot', 'figure'), Output('bar-plot', 'figure'), Output('previous-values', 'data')],
        [Input('noc-dropdown', 'value'), Input('region-dropdown', 'value'), Input('language-dropdown', 'value')],
        [State('previous-values', 'data')]
    )(update_plots)

    app.callback(
        Output("trends-modal", "is_open"),
        Output("employment-trends-body", "children"),
        [Input("map-plot", "clickData"), Input("bar-plot", "clickData"), Input("close-trends-modal", "n_clicks")],
        [State("trends-modal", "is_open"), State("language-dropdown", "value")]
    )(display_trends_modal)

def update_plots(selected_noc, selected_regions, language, previous_values):
    if (selected_noc == previous_values['noc'] and
        selected_regions == previous_values['region'] and
        language == previous_values['language']):
        raise dash.exceptions.PreventUpdate

    sorted_df, outlook_order, outlook_colors = load_data(language)
    
    merged_df = GDF[['ERNAME', 'centroid']].merge(sorted_df, left_on='ERNAME', right_on='Economic Region Name')
    merged_df['lat'] = merged_df['centroid'].apply(lambda point: point.y)
    merged_df['lon'] = merged_df['centroid'].apply(lambda point: point.x)
    
    filtered_df = merged_df[merged_df['NOC Title'] == selected_noc]
    if selected_regions and 'All' not in selected_regions:
        filtered_df = filtered_df[filtered_df['Economic Region Name'].isin(selected_regions)]
    
    map_fig = create_map_plot(filtered_df, outlook_order, outlook_colors)
    bar_fig = create_bar_plot(filtered_df, outlook_order, outlook_colors, language)
    
    return map_fig, bar_fig, {'noc': selected_noc, 'region': selected_regions, 'language': language}

def init_app():
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])
    app.layout = create_layout()
    register_callbacks(app)
    return app

# Run the app
if __name__ == '__main__':
    init_app().run_server(debug=True)