import dash  # Import Dash for creating the web application
import dash_bootstrap_components as dbc  # Import Bootstrap components for styling
from dash import dcc, html, Input, Output, State  # Import core Dash components and callback functions
import plotly.express as px  # Import Plotly Express for creating plots
import pandas as pd  # Import pandas for data manipulation
import geopandas as gpd  # Import GeoPandas for handling geographical data

# Load the shapefile for geographical data
gdf = gpd.read_file("./data/ler_000b16a_e.shp")
gdf = gdf.to_crs(epsg=4326)  # Ensure the coordinate reference system is WGS84

# Simplify geometries to improve performance
gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)

# Calculate centroids for each region
gdf['centroid'] = gdf.geometry.centroid

# Load the Excel file paths for English and French data
file_paths = {
    'English': "./data/20242026_outlook_n21_en_250117.xlsx",
    'French': "./data/20242026_outlook_n21_fr_250117.xlsx"
}

# Global storage for cached data to avoid reloading it multiple times
cached_data = {}

def load_data(language):
    """
    Load the data from the Excel file based on the selected language.
    Cache the data to avoid reloading it multiple times.

    Parameters:
    language (str): The selected language ('English' or 'French').

    Returns:
    tuple: A tuple containing the merged DataFrame, outlook order, and outlook colors.
    """
    # Check if data is already cached
    if language in cached_data:
        return cached_data[language]

    # Read the Excel file
    df = pd.read_excel(file_paths[language])

    # Define the outlook order and colors based on the language
    if language == 'English':
        outlook_order = ['very good', 'good', 'moderate', 'limited', 'undetermined', 'None']
        outlook_colors = {
            'very good': '#30AD23',  # Warm green
            'good': '#1E90FF',  # Dodger Blue
            'moderate': '#FFD700',  # Gold
            'limited': '#F08315',  # Warm Orange
            'undetermined': '#BA110C',  # Dark Red
            'None': '#D3D3D3',  # Light Grey
        }
    else:  # French
        outlook_order = ['très bonnes', 'bonnes', 'modérées', 'limitées', 'indéterminées', 'None']
        outlook_colors = {
            'très bonnes': '#30AD23',  # Warm Green
            'bonnes': '#1E90FF',  # Dodger Blue
            'modérées': '#FFD700',  # Gold
            'limitées': '#F08315',  # Warm Orange
            'indéterminées': '#BA110C',  # Dark Red
            'None': '#D3D3D3',  # Light Grey
        }

    # Extract the first part of 'Economic Region Name' before the comma
    df['Economic Region Name'] = df['Economic Region Name'].str.split(',').str[0]

    # Convert the 'Outlook' column to a categorical type with the defined order
    df['Outlook'] = pd.Categorical(df['Outlook'], categories=outlook_order, ordered=True)

    # Merge the sorted DataFrame with the geographical data
    merged_df = gdf[['ERNAME', 'centroid']].merge(df, left_on='ERNAME', right_on='Economic Region Name')

    # Cache the data
    cached_data[language] = (merged_df, outlook_order, outlook_colors)
    return merged_df, outlook_order, outlook_colors

# Initialize the Dash app with the Minty theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])

# Define the layout of the app
app.layout = dbc.Container([
    # Title row
    dbc.Row([dbc.Col(html.H1("Canadian Job Market Outlook 2024-2026", style={'textAlign': 'Left'}), width=12)]),
    
    # Region dropdown row
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='region-dropdown', 
            value=None, 
            clearable=False, 
            style={'width': '100%', 'margin': 'left'}
        ), width=6)
    ], justify='start'),
    
    # Map plot row
    dbc.Row([
        dbc.Col(dcc.Graph(id='map-plot', style={'height': '50vh'}), width=12)
    ]),
    
    # NOC title search row
    dbc.Row([
        dbc.Col(dcc.Input(
            id='noc-title-input',
            type='text',
            placeholder='Search for Job Title...',
            style={'width': '100%', 'margin': 'auto'}
        ), width=6)
    ], justify='start'),
    
    # Outlook dropdown row
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='outlook-dropdown', 
            value=None, 
            multi=False,  # Allow only one selection
            clearable=False, 
            style={'width': '100%', 'margin': 'left'}
        ), width=6)
    ]),
    
    # Bar plot row
    dbc.Row([
        dbc.Col(dcc.Graph(id='bar-plot', style={'height': '400px'}), width=12)
    ]),
    
    # Page slider row
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
    
    # Data source row
    dbc.Row([
        dbc.Col(html.Div([
            html.P("Data sourced and provided by the Government of Canada."),
            html.A("Visit the website", href="https://www.statcan.gc.ca/en/subjects/standard/noc/2021/indexV1", target="_blank")
        ], style={'text-align': 'center', 'margin-top': '20px'}), width=12)
    ]),
    
    # Footer row
    dbc.Row([
        dbc.Col(html.Footer(), width=10),
        dbc.Col(dcc.Dropdown(
            id='language-dropdown',
            options=[{'label': 'English', 'value': 'English'}, {'label': 'Français', 'value': 'French'}],
            value='English',
            clearable=False,
            style={'width': '100%'}
        ), width=2)
    ]),
    
    # Modal button and modal
    dbc.Row([
        dbc.Col(dbc.Button("About", id="open-modal", color="primary"), width=2),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("About This App")),
                dbc.ModalBody(
                    """
                    This Dash app provides an overview of the Canadian job market outlook for 2024-2026. 
                    The data is sourced from the Government of Canada and provides insights into job outlooks 
                    across various economic regions. The outlook categories include 'very good', 'good', 
                    'moderate', 'limited', 'undetermined', and 'None'. The methodology behind the outlook 
                    can be found on the Job Bank website.
                    """
                ),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-modal", className="ms-auto", n_clicks=0)
                ),
            ],
            id="modal",
            is_open=False,
        ),
    ], justify='start', style={'margin-top': '20px'}),
    
    # Hidden div to store selected NOC Title
    html.Div(id='selected-noc-title', style={'display': 'none'}),
    
    # Modal for Employment Trends
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Employment Trends")),
            dbc.ModalBody(id='employment-trends-body'),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-trends-modal", className="ms-auto", n_clicks=0)
            ),
        ],
        id="trends-modal",
        is_open=False,
    ),
], fluid=True)

# Callback to update dropdown options based on selected language
@app.callback(
    [Output('region-dropdown', 'options'), Output('region-dropdown', 'value'),
     Output('outlook-dropdown', 'options'), Output('outlook-dropdown', 'value')],
    Input('language-dropdown', 'value')
)
def update_dropdowns(language):
    """
    Update the region and outlook dropdown options based on the selected language.

    Parameters:
    language (str): The selected language ('English' or 'French').

    Returns:
    tuple: A tuple containing the dropdown options and default values.
    """
    merged_df, outlook_order, _ = load_data(language)
    
    # Create options for region dropdown
    region_options = [{'label': region, 'value': region} for region in sorted(merged_df['ERNAME'].unique())]
    
    # Create options for outlook dropdown
    outlook_options = [{'label': outlook, 'value': outlook} for outlook in outlook_order]

    # Default select first region and first outlook
    return region_options, merged_df['ERNAME'].iloc[0], outlook_options, outlook_order[0]

# Callback to update the plots based on the selected region
@app.callback(
    [Output('map-plot', 'figure'), Output('bar-plot', 'figure'), Output('page-slider', 'max'), Output('page-slider', 'marks')],
    [Input('region-dropdown', 'value'), Input('language-dropdown', 'value'), Input('outlook-dropdown', 'value'), Input('noc-title-input', 'value'), Input('page-slider', 'value')]
)
def update_plots(selected_region, language, selected_outlook, noc_title, page):
    """
    Update the map and bar plots based on the selected region.

    Parameters:
    selected_region (str): The selected economic region.
    language (str): The selected language ('English' or 'French').
    selected_outlook (str): The selected outlook category.
    noc_title (str): The NOC title to search for.
    page (int): The current page number.

    Returns:
    tuple: A tuple containing the updated map and bar plot figures, maximum page number, and slider marks.
    """
    merged_df, outlook_order, outlook_colors = load_data(language)

    # Ensure selected_outlook is a string
    if not selected_outlook:
        selected_outlook = outlook_order[0]  # Default to the first outlook

    # Filter the geographical data for the selected region
    filtered_gdf = gdf[gdf['ERNAME'] == selected_region]

    # Filter the merged data for the selected region and outlook
    filtered_data = merged_df[(merged_df['ERNAME'] == selected_region) & (merged_df['Outlook'] == selected_outlook)]

    # Filter by NOC title if provided
    if noc_title:
        filtered_data = filtered_data[filtered_data['NOC Title'].str.contains(noc_title, case=False, na=False)]

    # Pagination logic
    items_per_page = 5
    total_pages = (len(filtered_data) + items_per_page - 1) // items_per_page
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    paginated_data = filtered_data.iloc[start_idx:end_idx]

    # Truncate NOC Title to 38 characters
    # paginated_data['NOC Title'] = paginated_data['NOC Title'].apply(lambda x: x if len(x) <= 38 else x[:35] + '...')

    # Create the map plot
    map_fig = px.choropleth_mapbox(
        filtered_gdf, geojson=filtered_gdf.geometry, locations=filtered_gdf.index, color="ERNAME",
        mapbox_style="carto-positron", center={"lat": filtered_gdf.centroid.y.mean(), "lon": filtered_gdf.centroid.x.mean()},
        zoom=6, hover_name='ERNAME', opacity=0.5
    )
    map_fig.update_layout(showlegend=False)

    # Create the bar plot with descending order for 'Outlook'
    bar_fig = px.bar(
        paginated_data,
        x='NOC Title',
        y='Outlook',
        color='Outlook',
        color_discrete_map=outlook_colors,
        category_orders={'Outlook': outlook_order},
        hover_data={'NOC Title': True}  # Ensure full text is shown on hover
    )

    # Force the y-axis to display all categories even if there is no data for some
    bar_fig.update_yaxes(
        tickmode='array',
        tickvals=outlook_order,
        ticktext=outlook_order
    )

    # Update layout for hover text and hide the legend
    bar_fig.update_layout(
        title=f"Job Outlooks in {selected_region}",
        showlegend=False,  # Hide the legend
        hoverlabel=dict(
            font_size=16,  # Larger hover text
            font_family="Arial"
        ),
        xaxis_tickangle=0,  # Rotate labels to avoid overlap
        xaxis=dict(
            title_font=dict(size=18),  # Increase x-axis title font size
            tickfont=dict(size=14)  # Increase x-axis tick font size
        ),
        yaxis=dict(
            title_font=dict(size=18),  # Increase y-axis title font size
            tickfont=dict(size=14)  # Increase y-axis tick font size
        )
    )

    # Update slider marks
    slider_marks = {i: str(i) for i in range(1, total_pages + 1)}

    return map_fig, bar_fig, total_pages, slider_marks

# Callback to toggle the modal
@app.callback(
    Output("modal", "is_open"),
    [Input("open-modal", "n_clicks"), Input("close-modal", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

# Callback to update the hidden div with the selected NOC Title
@app.callback(
    Output('selected-noc-title', 'children'),
    Input('bar-plot', 'clickData')
)
def update_selected_noc_title(clickData):
    if clickData:
        return clickData['points'][0]['x']
    return ''

# Callback to toggle the Employment Trends modal and display the data
@app.callback(
    Output("trends-modal", "is_open"),
    Output("employment-trends-body", "children"),
    [Input('selected-noc-title', 'children'), Input("close-trends-modal", "n_clicks")],
    [State("trends-modal", "is_open"), State('language-dropdown', 'value')]
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
    app.run_server(debug=True)