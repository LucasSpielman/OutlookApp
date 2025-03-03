import dash
import dash_table
import pandas as pd
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
from bs4 import BeautifulSoup
import dash_bootstrap_components as dbc
import json
import geopandas as gpd


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

# Load the Shapefile
shapefile_path = './data/your_shapefile.shp'
gdf = gpd.read_file(shapefile_path)

# Convert to GeoJSON
geojson_path = './data/canada_economic_regions.geojson'
gdf.to_file(geojson_path, driver='GeoJSON')

# Load the GeoJSON file for the economic regions in Canada
with open('./data/canada_economic_regions.geojson') as f:
    geojson = json.load(f)

# Get unique economic regions for the dropdown options and sort them alphabetically
economic_regions = sorted(data_frames['English']['Economic Region Name'].unique())

# Add "All Regions" option to the dropdown
all_regions_option = [{'label': 'All Regions', 'value': 'All Regions'}]
region_options = all_regions_option + [{'label': region, 'value': region} for region in economic_regions]

# Simple Dash app to display the DataFrame
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Home", href="/")),
            dbc.NavItem(dbc.NavLink("Geographical Graph", href="/graph")),
        ],
        brand="Economic Region Outlook Data",
        brand_href="/",
        color="primary",
        dark=True,
    ),
    html.Div(id='page-content')
], fluid=True)

home_layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Economic Region Outlook Data", className='text-center my-4'))
    ]),
    
    # Dropdown menu for selecting language
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='language-dropdown',
            options=[{'label': lang, 'value': lang} for lang in file_paths.keys()],
            value='English',  # Default value
            style={'width': '100%'}
        ), width=6, className='mx-auto')
    ]),
    
    # Dropdown menu for selecting economic region
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='region-dropdown',
            options=region_options,
            value='All Regions',  # Default value
            style={'width': '100%'}
        ), width=6, className='mx-auto')
    ]),
    
    # Input field for searching NOC Titles
    dbc.Row([
        dbc.Col(dcc.Input(
            id='search-input',
            type='text',
            placeholder='Search NOC Titles...',
            style={'width': '100%', 'margin-top': '20px'}
        ), width=6, className='mx-auto')
    ]),
    
    # DataTable to display the DataFrame
    dbc.Row([
        dbc.Col(dash_table.DataTable(
            id='datatable',
            columns=[{'name': col, 'id': col} for col in data_frames['English'].columns if col not in ['NOC_Code', 'Economic Region Code', 'Economic Region Name', 'LANG', 'Employment Trends']],
            data=data_frames['English'].to_dict('records'),  # Initial data
            style_table={'height': '400px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'center', 'padding': '10px'},
            style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
            row_selectable='single',
            selected_rows=[],
        ), width=12)
    ]),
    
    # Store to hold the selected row data
    dcc.Store(id='selected-row-data'),
    
    # Div to display the detailed information of the selected row
    dbc.Row([
        dbc.Col(html.Div(id='row-details', style={'margin-top': '20px'}), width=12)
    ]),
    
    # Footer with data source information
    dbc.Row([
        dbc.Col(html.Footer([
            html.P("Data sourced and provided by the Government of Canada."),
            html.A("Visit the website", href="https://www.statcan.gc.ca/en/subjects/standard/noc/2021/indexV1", target="_blank")
        ], className='text-center my-4'), width=12)
    ])
], fluid=True)

graph_layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Geographical Graph", className='text-center my-4'))
    ]),
    
    # Dropdown menu for selecting NOC Title
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='noc-title-dropdown',
            options=[{'label': title, 'value': title} for title in data_frames['English']['NOC Title'].unique()],
            value=data_frames['English']['NOC Title'].unique()[0],  # Default value
            style={'width': '100%'}
        ), width=6, className='mx-auto')
    ]),
    
    # Graph to display the geographical data
    dbc.Row([
        dbc.Col(dcc.Graph(id='geo-graph'), width=12)
    ])
], fluid=True)

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/graph':
        return graph_layout
    else:
        return home_layout

# Callback to update the DataTable based on the selected language, region, and search input
@app.callback(
    Output('datatable', 'data'),
    Output('datatable', 'columns'),
    Output('region-dropdown', 'options'),
    Output('region-dropdown', 'value'),
    Input('language-dropdown', 'value'),
    Input('region-dropdown', 'value'),
    Input('search-input', 'value')
)
def update_table(selected_language, selected_region, search_value):
    # Get the preloaded DataFrame based on the selected language
    df = data_frames[selected_language]
    
    # Get unique economic regions for the dropdown options and sort them alphabetically
    economic_regions = sorted(df['Economic Region Name'].unique())
    
    # Update the region dropdown options
    region_options = all_regions_option + [{'label': region, 'value': region} for region in economic_regions]
    
    # If the selected region is not in the new options, default to "All Regions"
    if selected_region not in economic_regions and selected_region != 'All Regions':
        selected_region = 'All Regions'
    
    # Filter the DataFrame based on the selected region
    if selected_region != 'All Regions':
        df_region_filtered = df.loc[df['Economic Region Name'] == selected_region]
    else:
        df_region_filtered = df
    
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
    columns = [{'name': col, 'id': col} for col in df.columns if col not in ['NOC_Code', 'Economic Region Code', 'Economic Region Name', 'LANG', 'Employment Trends']]
    
    return df_sorted_by_outlook.to_dict('records'), columns, region_options, selected_region

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

# Helper function to parse HTML content and convert it to Dash HTML components
def parse_html_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    children = []
    for element in soup.children:
        if element.name == 'p':
            children.append(html.P(element.text))
        elif element.name == 'ul':
            children.append(html.Ul([html.Li(li.text) for li in element.find_all('li')]))
    return children

# Callback to display the detailed information of the selected row
@app.callback(
    Output('row-details', 'children'),
    Input('selected-row-data', 'data')
)
def display_row_details(row_data):
    if row_data:
        employment_trends = row_data.get('Employment Trends', '')
        return html.Div([
            html.H3("Detailed Information"),
            html.P(f"Economic Region Name: {row_data.get('Economic Region Name', '')}"),
            html.P(f"Outlook: {row_data.get('Outlook', '')}"),
            html.Div(parse_html_content(employment_trends))
        ])
    return html.Div()

# Callback to update the geographical graph based on the selected NOC Title
@app.callback(
    Output('geo-graph', 'figure'),
    Input('noc-title-dropdown', 'value'),
    Input('language-dropdown', 'value')
)
def update_geo_graph(selected_noc_title, selected_language):
    # Get the preloaded DataFrame based on the selected language
    df = data_frames[selected_language]
    
    # Filter the DataFrame based on the selected NOC Title
    df_filtered = df[df['NOC Title'] == selected_noc_title]
    
    # Create the choropleth map
    fig = px.choropleth(
        df_filtered,
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
        title=f'Economic Region Outlooks for {selected_noc_title}'
    )
    fig.update_geos(fitbounds="locations", visible=False)
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)