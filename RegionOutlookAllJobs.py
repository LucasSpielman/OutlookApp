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
        dbc.Col(dcc.Dropdown(
            id='outlook-dropdown', 
            value=None, 
            multi=True,  # Allow multiple selections
            clearable=False, 
            style={'width': '50%', 'margin': 'auto'}
        ), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='bar-plot', style={'height': '50vh'}), width=12)
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
    sorted_df, outlook_order, _ = load_data(language)
    region_options = [{'label': region, 'value': region} for region in sorted(sorted_df['Economic Region Name'].unique())]
    outlook_options = [{'label': outlook, 'value': outlook} for outlook in outlook_order]

    return region_options, sorted_df['Economic Region Name'].iloc[0], outlook_options, outlook_order[:2]  # Default select first 2 outlooks

@app.callback(
    Output('bar-plot', 'figure'),
    [Input('region-dropdown', 'value'), Input('language-dropdown', 'value'), Input('outlook-dropdown', 'value')]
)
def update_bar_plot(selected_region, language, selected_outlooks):
    sorted_df, outlook_order, outlook_colors = load_data(language)
    
    # Ensure selected_outlooks is a list
    if not selected_outlooks:
        selected_outlooks = outlook_order  # Default to all outlooks
    
    # Filter data based on region and selected outlooks
    filtered_df = sorted_df[
        (sorted_df['Economic Region Name'] == selected_region) & 
        (sorted_df['Outlook'].isin(selected_outlooks))
    ].copy()  # Make a copy to avoid modifying original data
    
    # Truncate x-axis labels to max 30 characters
    filtered_df['NOC Title'] = filtered_df['NOC Title'].apply(lambda x: x[:27] + '...' if len(x) > 30 else x)
    
    # Create the bar chart with a fixed category order
    bar_fig = px.bar(
        filtered_df,
        x='NOC Title',
        y='Outlook',
        color='Outlook',
        labels={'x': 'NOC Title', 'y': 'Outlook'},
        color_discrete_map=outlook_colors,
        category_orders={'Outlook': outlook_order}
    )
    
    # Force the y-axis to display all categories even if there is no data for some
    bar_fig.update_yaxes(
        tickmode='array',
        tickvals=outlook_order,
        ticktext=outlook_order
    )
    
    # Update layout for hover text and legend dynamically fitting in the top-left corner
    bar_fig.update_layout(
        title=f"Job Outlooks in {selected_region}",
        legend_title="Outlook Categories",
        legend=dict(
            x=0,  # Aligns the legend to the left
            y=1,  # Aligns the legend to the top
            xanchor="left",  # Ensures left alignment
            yanchor="top",   # Ensures top alignment
            bgcolor="rgba(255,255,255,0.6)",  # Adds a semi-transparent white background
            bordercolor="black",
            borderwidth=1
        ),
        hoverlabel=dict(
            font_size=16,  # Larger hover text
            font_family="Arial"
        ),
        xaxis_tickangle=-45  # Rotate labels to avoid overlap
    )
    
    return bar_fig



if __name__ == '__main__':
    app.run_server(debug=True)