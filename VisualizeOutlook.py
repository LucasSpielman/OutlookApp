import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

# Load the Excel file
file_paths = {
    'English': "./data/20242026_outlook_n21_en_250117.xlsx",
    'French': "./data/20242026_outlook_n21_fr_250117.xlsx"
}

# Open the English xlsx file
english_df = pd.read_excel(file_paths['English'])

# Define the custom order and color scale for the 'Outlook' column
outlook_order = ['very good', 'good', 'moderate', 'limited', 'undetermined']
outlook_colors = {
    'very good': 'green',
    'good': 'blue',
    'moderate': 'yellow',
    'limited': 'orange',
    'undetermined': 'red'
}

# Sort the DataFrame based on the custom order
english_df['Outlook'] = pd.Categorical(english_df['Outlook'], categories=outlook_order, ordered=True)
sorted_df = english_df.sort_values(by=['NOC Title', 'Economic Region Name', 'Outlook'])

# Initialize the Dash app
app = dash.Dash(__name__)

# App layout
app.layout = html.Div([
    dcc.Dropdown(
        id='noc-dropdown',
        options=[{'label': title, 'value': title} for title in sorted_df['NOC Title'].unique()],
        value=[sorted_df['NOC Title'].iloc[0]],  # Default value
        multi=True,  # Allow multiple selections
        clearable=False
    ),
    dcc.Input(
        id='region-search',
        type='text',
        placeholder='Search for a region...',
        style={'margin-top': '10px', 'margin-bottom': '10px'}
    ),
    dcc.Graph(id='scatter-plot')
])

# Callback to update the scatter plot based on dropdown selection and search query
@app.callback(
    Output('scatter-plot', 'figure'),
    [Input('noc-dropdown', 'value'),
     Input('region-search', 'value')]
)
def update_scatter(selected_nocs, search_query):
    filtered_df = sorted_df[sorted_df['NOC Title'].isin(selected_nocs)]
    
    if search_query:
        filtered_df = filtered_df[filtered_df['Economic Region Name'].str.contains(search_query, case=False, na=False)]
    
    filtered_df = filtered_df.sort_values(by='Outlook')
    
    fig = px.scatter(
        filtered_df, x='Economic Region Name', y='NOC Title', color='Outlook',
        title='Career Outlook for Canadian Economic Regions 2024-2026',
        category_orders={'Outlook': outlook_order},
        color_discrete_map=outlook_colors
    )
    
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)