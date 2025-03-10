import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd
import geopandas as gpd

# Load the Excel file paths
file_paths = {
    'English': "./data/20242026_outlook_n21_en_250117.xlsx",
    'French': "./data/20242026_outlook_n21_fr_250117.xlsx"
}

# Global storage for cached data
cached_data = {}

def load_data1(language):
    """
    Load the data from the Excel file based on the selected language.
    Cache the data to avoid reloading it multiple times.

    Parameters:
    language (str): The selected language ('English' or 'French').

    Returns:
    tuple: A tuple containing the sorted DataFrame, outlook order, and outlook colors.
    """
    if language in cached_data:
        return cached_data[language]
    
    # Read the Excel file
    df = pd.read_excel(file_paths[language])
    
    # Define the outlook order and colors based on the language
    if language == 'English':
        outlook_order = ['very good', 'good', 'moderate', 'limited', 'undetermined', ' ']
        outlook_colors = {
            'very good': '#30AD23',  # Warm green 
            'good': '#1E90FF',  # Dodger Blue
            'moderate': '#FFD700',  # Gold
            'limited': '#F08315',  # Warm Orange
            'undetermined': '#BA110C',  # Dark Red
            ' ': '#D3D3D3',  # Light Grey
        }
    else:  # French
        outlook_order = ['très bonnes', 'bonnes', 'modérées', 'limitées', 'indéterminées', ' ']
        outlook_colors = {
            'très bonnes': '#30AD23',  # Warm Green
            'bonnes': '#1E90FF',  # Dodger Blue
            'modérées': '#FFD700',  # Gold
            'limitées': '#F08315',  # Warm Orange
            'indéterminées': '#BA110C',  # Dark Red
            ' ': '#D3D3D3',  # Light Grey
        }
    
    # Convert the 'Outlook' column to a categorical type with the defined order
    df['Outlook'] = pd.Categorical(df['Outlook'], categories=outlook_order, ordered=True)
    
    # Sort the DataFrame by 'NOC Title', 'Economic Region Name', and 'Outlook'
    sorted_df = df.sort_values(by=['NOC Title', 'Economic Region Name', 'Outlook'])
    
    # Cache the data
    cached_data[language] = (sorted_df, outlook_order, outlook_colors)
    
    return sorted_df, outlook_order, outlook_colors

# Load the shapefile
gdf = gpd.read_file("./data/ler_000b16a_e.shp")
gdf = gdf.to_crs(epsg=4326)  # Ensure the coordinate reference system is WGS84

# Simplify geometries to improve performance
gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)

# Calculate centroids for each region
gdf['centroid'] = gdf.geometry.centroid

# Initialize the Dash app with the Minty theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])
app.title = 'Combined Dashboards'

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(dbc.Button("Dashboard 1", id="btn-dashboard1", color="primary"), width=2),
        dbc.Col(dbc.Button("Dashboard 2", id="btn-dashboard2", color="secondary"), width=2)
    ], style={'margin-top': '20px'}),

    html.Div(id='content')
], fluid=True)

# Define callbacks to switch between dashboards
@app.callback(
    Output('content', 'children'),
    [Input('btn-dashboard1', 'n_clicks'), Input('btn-dashboard2', 'n_clicks')]
)
def switch_dashboard(n1, n2):
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = 'btn-dashboard1'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'btn-dashboard1':
        return get_dashboard1()
    elif button_id == 'btn-dashboard2':
        return get_dashboard2()

# Function to render Dashboard 1
def get_dashboard1():
    return html.Div([
        html.H3("Dashboard 1 - Canadian Job Market Outlook"),
        dcc.Dropdown(id='language-dropdown1', options=[
            {'label': 'English', 'value': 'English'},
            {'label': 'Français', 'value': 'French'}
        ], value='English'),
        dcc.Graph(id='map-plot1'),
        dcc.Graph(id='bar-plot1')
    ])

# Function to render Dashboard 2
def get_dashboard2():
    return html.Div([
        html.H3("Dashboard 2 - Economic Region Outlook"),
        dcc.Dropdown(id='language-dropdown2', options=[
            {'label': 'English', 'value': 'English'},
            {'label': 'Français', 'value': 'French'}
        ], value='English'),
        dcc.Graph(id='map-plot2'),
        dcc.Graph(id='bar-plot2')
    ])

# Callbacks for Dashboard 1
@app.callback(
    [Output('map-plot1', 'figure'), Output('bar-plot1', 'figure')],
    Input('language-dropdown1', 'value')
)
def update_dashboard1(language):
    sorted_df, outlook_order, outlook_colors = load_data(language)
    # Plot generation logic can be copied from ERbyNOCTitle.py
    # Placeholder response
    return px.scatter(), px.bar()

# Callbacks for Dashboard 2
@app.callback(
    [Output('map-plot2', 'figure'), Output('bar-plot2', 'figure')],
    Input('language-dropdown2', 'value')
)
def update_dashboard2(language):
    sorted_df, outlook_order, outlook_colors = load_data(language)
    # Plot generation logic can be copied from NOCTitlebyER.py
    # Placeholder response
    return px.scatter(), px.bar()

if __name__ == '__main__':
    app.run_server(debug=True)