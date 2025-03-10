import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd
import geopandas as gpd

# Import functions and data from both apps
from ERbyNOCTitle import load_data as load_data_app1
from NOCTitlebyER import load_data as load_data_app2

# Initialize the Dash app
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
    sorted_df, outlook_order, outlook_colors = load_data_app1(language)
    # Plot generation logic can be copied from app1.py
    # Placeholder response
    return px.scatter(), px.bar()

# Callbacks for Dashboard 2
@app.callback(
    [Output('map-plot2', 'figure'), Output('bar-plot2', 'figure')],
    Input('language-dropdown2', 'value')
)
def update_dashboard2(language):
    merged_df, outlook_order, outlook_colors = load_data_app2(language)
    # Plot generation logic can be copied from NOCTitlebyEconomicRegion.py
    # Placeholder response
    return px.scatter(), px.bar()

if __name__ == '__main__':
    app.run_server(debug=True)