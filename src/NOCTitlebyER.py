import dash 
import dash_bootstrap_components as dbc 
from dash import dcc, html, Input, Output, State
import plotly.express as px 
import pandas as pd
import geopandas as gpd

# Load the shapefile for geographical data
gdf_1 = gpd.read_file("./data/ler_000b16a_e.shp")
gdf_1 = gdf_1.to_crs(epsg=4326)  # Ensure the coordinate reference system is WGS84

# Simplify geometries to improve performance
gdf_1['geometry'] = gdf_1['geometry'].simplify(tolerance=0.01, preserve_topology=True)

# Calculate centroids for each region
gdf_1['centroid'] = gdf_1.geometry.centroid

# Load the Excel file paths for English and French data
file_paths_1 = {
    'English': "./data/20242026_outlook_n21_en_250117.xlsx",
    'French': "./data/20242026_outlook_n21_fr_250117.xlsx"
}

# Global storage for cached data to avoid reloading it multiple times
cached_data_1 = {}

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
    if language in cached_data_1:
        return cached_data_1[language]

    # Read the Excel file
    df = pd.read_excel(file_paths_1[language])

    # Define the outlook order and colors based on the language
    if language == 'English':
        outlook_order = ['very good', 'good', 'moderate', 'limited', 'undetermined', 'None']
        outlook_colors = {
            'very good': {'color': '#30AD23', 'text': 'white'},  # Warm green
            'good': {'color': '#1E90FF', 'text': 'white'},  # Dodger Blue
            'moderate': {'color': '#FFD700', 'text': 'black'},  # Gold
            'limited': {'color': '#F08315', 'text': 'black'},  # Warm Orange
            'undetermined': {'color': '#BA110C', 'text': 'white'},  # Dark Red
            'None': {'color': '#D3D3D3', 'text': 'black'},  # Light Grey
        }
    else:  # French
        outlook_order = ['très bonnes', 'bonnes', 'modérées', 'limitées', 'indéterminées', 'None']
        outlook_colors = {
            'très bonnes': {'color': '#30AD23', 'text': 'white'},  # Warm Green
            'bonnes': {'color': '#1E90FF', 'text': 'white'},  # Dodger Blue
            'modérées': {'color': '#FFD700', 'text': 'black'},  # Gold
            'limitées': {'color': '#F08315', 'text': 'black'},  # Warm Orange
            'indéterminées': {'color': '#BA110C', 'text': 'white'},  # Dark Red
            'None': {'color': '#D3D3D3', 'text': 'black'},  # Light Grey
        }

    # Extract the first part of 'Economic Region Name' before the comma
    df['Economic Region Name'] = df['Economic Region Name'].str.split(',').str[0]

    # Convert the 'Outlook' column to a categorical type with the defined order
    df['Outlook'] = pd.Categorical(df['Outlook'], categories=outlook_order, ordered=True)

    # Merge the sorted DataFrame with the geographical data
    merged_df = gdf_1[['ERNAME', 'centroid']].merge(df, left_on='ERNAME', right_on='Economic Region Name')

    # Cache the data
    cached_data_1[language] = (merged_df, outlook_order, outlook_colors)
    return merged_df, outlook_order, outlook_colors

# Initialize the Dash app with the Minty theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])

# Define text content for both languages
text_content_1 = {
    'English': {
        'title': "Canadian Job Market Outlook 2024-2026",
        'data_source': "Data sourced and provided by the Government of Canada.",
        'visit_website': "Visit the website",
        'visit_website_link': "https://www.statcan.gc.ca/en/subjects/standard/noc/2021/indexV1",
        'open_data': "Open Canada Data",
        'open_data_link': "https://open.canada.ca/data/en/dataset/b0e112e9-cf53-4e79-8838-23cd98debe5b?_gl=1*h2x1ic*_ga*MTc4Mjg5MzYwMi4xNjc4MTQ5Mjc1*_ga_S9JG8CZVYZ*MTczNDM4ODMyOC4xMi4xLjE3MzQzODg2OTUuNDkuMC4w",
        'noc_title_placeholder': "Search for Job Title...",
        'modal_info': """
            This Dash app provides an overview of the Canadian job market outlook for 2024-2026. 
            The data is sourced from the Government of Canada and provides insights into job outlooks 
            across various economic regions. The outlook categories include 'very good', 'good', 
            'moderate', 'limited', 'undetermined', and 'None'. 

            **Features:**

            - **Region Dropdown:** Select an economic region to view its job outlook.
            - **NOC Title Search:** Search for specific job titles within the selected region.
            - **Outlook Dropdown:** Filter job titles based on their outlook category.
            - **Map Plot:** Visual representation of the selected region.
            - **Bar Plot:** Displays job titles and their outlooks in the selected region.
            - **Pagination:** Navigate through job titles using the page slider.
            - **Language Selection:** Switch between English and French data.

            **How to Use:**

            1. Select a region from the 'Region Dropdown'.
            2. Optionally, search for a specific job title using the 'NOC Title Search' input.
            3. Filter the results by selecting an outlook category from the 'Outlook Dropdown'.
            4. View the map and bar plots to analyze the job outlooks.
            5. Click on a job title in the bar plot to view detailed employment trends.
            6. Use the 'Page Slider' to navigate through multiple pages of job titles.
            7. Switch the language using the 'Language Dropdown' to view data in English or French.
        """
    },
    'French': {
        'title': "Perspectives du marché du travail canadien 2024-2026",
        'data_source': "Données fournies par le gouvernement du Canada.",
        'visit_website': "Visitez le site web",
        'visit_website_link': "https://www.statcan.gc.ca/fr/sujets/norme/cnp/2021/indexV1",
        'open_data': "Données ouvertes du Canada",
        'open_data_link': "https://ouvert.canada.ca/data/fr/dataset/b0e112e9-cf53-4e79-8838-23cd98debe5b?_gl=1*h2x1ic*_ga*MTc4Mjg5MzYwMi4xNjc4MTQ5Mjc1*_ga_S9JG8CZVYZ*MTczNDM4ODMyOC4xMi4xLjE3MzQzODg2OTUuNDkuMC4w",
        'noc_title_placeholder': "Recherchez un titre d'emploi...",
        'modal_info': """
            Cette application Dash fournit un aperçu des perspectives du marché du travail canadien pour 2024-2026. 
            Les données sont fournies par le gouvernement du Canada et offrent des informations sur les perspectives d'emploi 
            dans diverses régions économiques. Les catégories de perspectives incluent 'très bonnes', 'bonnes', 
            'modérées', 'limitées', 'indéterminées' et 'Aucune'. 

            **Caractéristiques:**

            - **Menu déroulant des régions:** Sélectionnez une région économique pour voir ses perspectives d'emploi.
            - **Recherche de titre NOC:** Recherchez des titres d'emploi spécifiques dans la région sélectionnée.
            - **Menu déroulant des perspectives:** Filtrez les titres d'emploi en fonction de leur catégorie de perspectives.
            - **Carte:** Représentation visuelle de la région sélectionnée.
            - **Graphique en barres:** Affiche les titres d'emploi et leurs perspectives dans la région sélectionnée.
            - **Pagination:** Naviguez à travers les titres d'emploi en utilisant le curseur de page.
            - **Sélection de la langue:** Passez des données en anglais aux données en français.

            **Comment utiliser:**'
            1. Sélectionnez une région dans le 'Menu déroulant des régions'.
            2. Facultativement, recherchez un titre d'emploi spécifique en utilisant le champ de recherche 'Recherche de titre NOC'.
            3. Filtrez les résultats en sélectionnant une catégorie de perspectives dans le 'Menu déroulant des perspectives'.
            4. Consultez la carte et les graphiques en barres pour analyser les perspectives d'emploi.
            5. Cliquez sur un titre d'emploi dans le graphique en barres pour voir les tendances d'emploi détaillées.
            6. Utilisez le 'Curseur de page' pour naviguer à travers plusieurs pages de titres d'emploi.
            7. Changez la langue en utilisant le 'Menu déroulant des langues' pour voir les données en anglais ou en français.
        """
    }
}

# Define the layout of the app
app.layout = dbc.Container([
    # Title row
    dbc.Row([
        dbc.Col(html.H1(id='app-title-1', style={'textAlign': 'Left', 'margin-top': '30px'}), width=10),
        dbc.Col(dbc.Button("Info", id="open-modal-1", color="primary"), width=2, style={'textAlign': 'right', 'margin-top': '15px'})
    ]),
    
    # Region dropdown row
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='region-dropdown-1', 
            value=None, 
            clearable=False, 
            style={'width': '100%', 'margin': 'left'}
        ), width=3)  # Adjust the width to 4
    ], justify='start'),
    
    # Map plot row
    dbc.Row([
        dbc.Col(dcc.Graph(id='map-plot-1', style={'height': '50vh'}), width=12)
    ]),
    
    # NOC title search row
    dbc.Row([
        dbc.Col(dcc.Input(
            id='noc-title-input-1',
            type='text',
            placeholder='Search for Job Title...',
            style={'width': '100%', 'margin': 'auto'}
        ), width=3)
    ], justify='start'),
    
    # Outlook dropdown row
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='outlook-dropdown-1', 
            value=None, 
            multi=False,  # Allow only one selection
            clearable=False, 
            style={'width': '100%', 'margin': 'left'}
        ), width=3)
    ]),
    
    # Bar plot row
    dbc.Row([
        dbc.Col(dcc.Graph(id='bar-plot-1', style={'height': '400px'}), width=12)
    ]),
    
    # Page slider row
    dbc.Row([
        dbc.Col(dcc.Slider(
            id='page-slider-1',
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
            html.P(id='data-source-text-1'),
            html.A(id='visit-website-link-1', href="https://www.statcan.gc.ca/en/subjects/standard/noc/2021/indexV1", target="_blank"),
            html.Br(),
            html.A(id='open-data-link-1', href="https://open.canada.ca/data/en/dataset/b0e112e9-cf53-4e79-8838-23cd98debe5b?_gl=1*h2x1ic*_ga*MTc4Mjg5MzYwMi4xNjc4MTQ5Mjc1*_ga_S9JG8CZVYZ*MTczNDM4ODMyOC4xMi4xLjE3MzQzODg2OTUuNDkuMC4w", target="_blank")
        ], style={'text-align': 'center', 'margin-top': '20px'}), width=12)
    ]),
    
    # Footer row
    dbc.Row([
        dbc.Col(html.Footer(), width=10),
        dbc.Col(dcc.Dropdown(
            id='language-dropdown-1',
            options=[{'label': 'English', 'value': 'English'}, {'label': 'Français', 'value': 'French'}],
            value='English',
            clearable=False,
            style={'width': '100%'}
        ), width=1)
    ]),
    
    # Modal button and modal page
    dbc.Row([
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("About This App")),
                dbc.ModalBody(dcc.Markdown(id='modal-info-text-1')),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-modal-1", className="ms-auto", n_clicks=0)
                ),
            ],
            id="modal-1",
            is_open=False,
        ),
    ], justify='start', style={'margin-top': '20px'}),
    
    # Hidden div to store selected NOC Title
    html.Div(id='selected-noc-title-1', style={'display': 'none'}),
    
    # Modal for Employment Trends
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Employment Trends")),
            dbc.ModalBody(id='employment-trends-body-1'),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-trends-modal-1", className="ms-auto", n_clicks=0)
            ),
        ],
        id="trends-modal-1",
        is_open=False,
        style={"maxWidth": "100%"}  # Adjust the width of the modal
    ),
], fluid=True)

# Callback to update text content based on selected language
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
    content = text_content_1[language]
    return (content['title'], content['data_source'], content['visit_website'], content['visit_website_link'], content['open_data'], content['open_data_link'], content['modal_info'], content['noc_title_placeholder'])

# Callback to update dropdown options based on selected language
@app.callback(
    [Output('region-dropdown-1', 'options'), Output('region-dropdown-1', 'value'),
    Output('outlook-dropdown-1', 'options'), Output('outlook-dropdown-1', 'value')],
    Input('language-dropdown-1', 'value')
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
    [Output('map-plot-1', 'figure'), Output('bar-plot-1', 'figure'), Output('page-slider-1', 'max'), Output('page-slider-1', 'marks')],
    [Input('region-dropdown-1', 'value'), Input('language-dropdown-1', 'value'), Input('outlook-dropdown-1', 'value'), Input('noc-title-input-1', 'value'), Input('page-slider-1', 'value')]
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
    filtered_gdf_1 = gdf_1[gdf_1['ERNAME'] == selected_region]

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

    # Create the map plot
    map_fig = px.choropleth_mapbox(
        filtered_gdf_1, geojson=filtered_gdf_1.geometry, locations=filtered_gdf_1.index, color="ERNAME",
        mapbox_style="carto-positron", center={"lat": filtered_gdf_1.centroid.y.mean(), "lon": filtered_gdf_1.centroid.x.mean()},
        zoom=6, hover_name='ERNAME', opacity=0.5
    )
    map_fig.update_layout(showlegend=False)

    # Create the bar plot with descending order for 'Outlook'
    bar_fig = px.bar(
        paginated_data,
        x='NOC Title',
        y='Outlook',
        color='Outlook',
        color_discrete_map={k: v['color'] for k, v in outlook_colors.items()},
        category_orders={'Outlook': outlook_order},
        hover_data={'NOC Title': True}  # Ensure full text is shown on hover
    )

    # Update text color for bars
    for data in bar_fig.data:
        data.textfont = dict(color=[outlook_colors[outlook]['text'] for outlook in data.y])

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
        xaxis_tickangle=-5,  # Rotate labels to avoid overlap
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
    Output("modal-1", "is_open"),
    [Input("open-modal-1", "n_clicks"), Input("close-modal-1", "n_clicks")],
    [State("modal-1", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

# Callback to update the hidden div with the selected NOC Title
@app.callback(
    Output('selected-noc-title-1', 'children'),
    Input('bar-plot-1', 'clickData')
)
def update_selected_noc_title(clickData):
    if clickData:
        return clickData['points'][0]['x']
    return ''

# Callback to toggle the Employment Trends modal and display the data
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

# # Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
