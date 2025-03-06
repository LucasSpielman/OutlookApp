import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

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
    
    cached_data[language] = (sorted_df, outlook_order, outlook_colors)
    return sorted_df, outlook_order, outlook_colors

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
        dbc.Col(dcc.Graph(id='bar-plot', style={'height': '600vh'}), width=12)
    ]),
    dbc.Row([
        dbc.Col(html.Footer([
            html.P("Data sourced and provided by the Government of Canada."),
            html.A("Visit the website", href="https://www.statcan.gc.ca/en/subjects/standard/noc/2021/indexV1", target="_blank")
        ], style={'text-align': 'center', 'margin-top': '20px'}), width=12)
    ])
], fluid=True)

@app.callback(
    [Output('region-dropdown', 'options'), Output('region-dropdown', 'value')],
    Input('language-dropdown', 'value')
)
def update_region_dropdown(language):
    sorted_df, _, _ = load_data(language)
    options = [{'label': region, 'value': region} for region in sorted(sorted_df['Economic Region Name'].unique())]
    return options, sorted_df['Economic Region Name'].iloc[0]

@app.callback(
    Output('bar-plot', 'figure'),
    [Input('region-dropdown', 'value'), Input('language-dropdown', 'value')]
)
def update_bar_plot(selected_region, language):
    sorted_df, outlook_order, outlook_colors = load_data(language)
    filtered_df = sorted_df[sorted_df['Economic Region Name'] == selected_region]
    
    bar_fig = px.bar(
        filtered_df, x='NOC Title', y='Outlook', color='Outlook',
        labels={'x': 'NOC Title', 'y': 'Outlook'},
        category_orders={'Outlook': outlook_order},
        color_discrete_map=outlook_colors
    )
    
    bar_fig.update_layout(
        showlegend=True,
        # height=800,
        legend=dict(title="Outlook"),
        legend_itemclick="toggle",
        legend_itemdoubleclick="toggleothers"
    )
    
    return bar_fig

if __name__ == '__main__':
    app.run_server(debug=True)
