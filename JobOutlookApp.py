import dash
import dash_table
import pandas as pd
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import json

# TODO: [DONE] Have df_region_filtered be filtered by the user's input
# TODO: [DONE] Have search for economic region be a dropdown menu
# TODO: [DONE] Have the user input the file path for english or french
# TODO: [DONE] Fix the sorting for the french version, it is not sorting properly since it uses french words for the NOC Titles 
# TODO: [DONE] Have search Functionality for specific NOC Titles or names within the Titles (eg if I search teachers, I want all the NOC Titles with teachers in it)
# TODO: [DONE] Optimize the search functionality and the app in general. It is slow to load and search since it has to reload the entire DataFrame each time
# TODO: Make it look prettier
# TODO: Make standalone app for for user download or host it on a website somewhere? ideally for free for me
# TODO: Add a map of Canada with the economic regions and their outlooks
# TODO: Add some kind of chart of the outlooks for the selected region 


# File paths for English and French Excel files
file_paths = {
    'English': "./data/20242026_outlook_n21_en_250117.xlsx",
    'French': "./data/20242026_outlook_n21_fr_250117.xlsx"
}

# Outlook order mappings for English and French
outlook_orders = {
    'English': ['very good', 'good', 'fair', 'limited', 'undetermined'],
    'French': ['très bonnes', 'bonnes', 'modérées', 'indéterminées', 'limitées', 'très limitées']
}

# Load the initial Excel files and store them in a global variable
data_frames = {
    'English': pd.read_excel(file_paths['English'], sheet_name=0),
    'French': pd.read_excel(file_paths['French'], sheet_name=0)
}

# Load the GeoJSON file for the economic regions in Canada
with open('./data/canada_economic_regions.geojson') as f:
    geojson = json.load(f)

# Get unique economic regions for the dropdown options
economic_regions = data_frames['English']['Economic Region Name'].unique()

# Simple Dash app to display the DataFrame
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Economic Region Outlook Data", style={'text-align': 'center'}),
    
    # Dropdown menu for selecting language
    dcc.Dropdown(
        id='language-dropdown',
        options=[{'label': lang, 'value': lang} for lang in file_paths.keys()],
        value='English',  # Default value
        style={'width': '50%', 'margin': 'auto'}
    ),
    
    # Dropdown menu for selecting economic region
    dcc.Dropdown(
        id='region-dropdown',
        options=[{'label': region, 'value': region} for region in economic_regions],
        value=economic_regions[0],  # Default value
        style={'width': '50%', 'margin': 'auto'}
    ),
    
    # Input field for searching NOC Titles
    dcc.Input(
        id='search-input',
        type='text',
        placeholder='Search NOC Titles...',
        style={'width': '50%', 'margin': 'auto', 'margin-top': '20px'}
    ),
    
    # DataTable to display the DataFrame
    dash_table.DataTable(
        id='datatable',
        columns=[{'name': col, 'id': col} for col in data_frames['English'].columns if col != 'Employment Trends'],
        data=data_frames['English'].to_dict('records'),  # Initial data
        style_table={'height': '400px', 'overflowY': 'auto'},
        style_cell={'textAlign': 'center', 'padding': '10px'},
        style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
        row_selectable='single',
        selected_rows=[],
    ),
    
    # Store to hold the selected row data
    dcc.Store(id='selected-row-data'),
    
    # Div to display the detailed information of the selected row
    html.Div(id='row-details', style={'margin-top': '20px'}),
    
    # Div to display the map
    dcc.Graph(id='map')
])

# Callback to update the DataTable based on the selected language, region, and search input
@app.callback(
    Output('datatable', 'data'),
    Output('datatable', 'columns'),
    Output('region-dropdown', 'options'),
    Output('region-dropdown', 'value'),
    Output('map', 'figure'),
    Input('language-dropdown', 'value'),
    Input('region-dropdown', 'value'),
    Input('search-input', 'value')
)
def update_table(selected_language, selected_region, search_value):
    # Get the preloaded DataFrame based on the selected language
    df = data_frames[selected_language]
    
    # Get unique economic regions for the dropdown options
    economic_regions = df['Economic Region Name'].unique()
    
    # Update the region dropdown options
    region_options = [{'label': region, 'value': region} for region in economic_regions]
    
    # If the selected region is not in the new options, default to the first region
    if selected_region not in economic_regions:
        selected_region = economic_regions[0]
    
    # Filter the DataFrame based on the selected region
    df_region_filtered = df.loc[df['Economic Region Name'] == selected_region]
    
    # Filter the DataFrame based on the search input
    if search_value:
        df_region_filtered = df_region_filtered[df_region_filtered['NOC Title'].str.contains(search_value, case=False, na=False)]
    
    # Sort the DataFrame based on the outlook order
    df_region_filtered['Outlook'] = pd.Categorical(
        df_region_filtered['Outlook'], 
        categories=outlook_orders[selected_language], 
        ordered=True
    )
    df_sorted_by_outlook = df_region_filtered.sort_values('Outlook')
    
    # Update the DataTable columns based on the selected language
    columns = [{'name': col, 'id': col} for col in df.columns if col != 'Employment Trends']
    
    # Create the choropleth map
    fig = px.choropleth(
        df,
        geojson=geojson,
        locations='Economic Region Name',
        featureidkey='properties.Economic Region Name',
        color='Outlook',
        color_discrete_map={
            'very good': 'green',
            'good': 'lightgreen',
            'fair': 'yellow',
            'limited': 'orange',
            'undetermined': 'red',
            'très bonnes': 'green',
            'bonnes': 'lightgreen',
            'modérées': 'yellow',
            'limitées': 'orange',
            'très limitées': 'red',
            'indéterminées': 'grey'
        },
        title='Economic Region Outlooks in Canada'
    )
    fig.update_geos(fitbounds="locations", visible=False)
    
    return df_sorted_by_outlook.to_dict('records'), columns, region_options, selected_region, fig

# Callback to update the selected row data
@app.callback(
    Output('selected-row-data', 'data'),
    Input('datatable', 'selected_rows'),
    Input('datatable', 'data')
)
def update_selected_row_data(selected_rows, data):
    if selected_rows:
        return data[selected_rows[0]]
    return {}

# Callback to display the detailed information of the selected row
@app.callback(
    Output('row-details', 'children'),
    Input('selected-row-data', 'data')
)
def display_row_details(row_data):
    if row_data:
        return html.Div([
            html.H3("Detailed Information"),
            html.P(f"Economic Region Name: {row_data.get('Economic Region Name', '')}"),
            html.P(f"Outlook: {row_data.get('Outlook', '')}"),
            html.P(f"Employment Trends: {row_data.get('Employment Trends', '')}")
        ])
    return html.Div()

if __name__ == '__main__':
    app.run_server(debug=True)