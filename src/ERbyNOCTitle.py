import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd
import geopandas as gpd

def create_dash_app(server):

    # Load the Excel file paths
    file_paths = {
        'English': "./data/20242026_outlook_n21_en_250117.xlsx",
        'French': "./data/20242026_outlook_n21_fr_250117.xlsx"
    }

    # Global storage for cached data
    cached_data = {}

    def load_data(language):
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
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY], server=server)

    # App layout
    app.layout = dbc.Container([
        # Title and Info button row
        dbc.Row([
            dbc.Col(html.H1(id='dashboard-title', style={'textAlign': 'left', 'margin-top': '20px'}), width=10),
            dbc.Col(dbc.Button("Info", id="open-info-modal", color="primary"), width=2, style={'textAlign': 'right', 'margin-top': '20px'})
        ], style={'margin-left': '0', 'margin-right': '0'}),
        
        # NOC Title dropdown row
        dbc.Row([
            dbc.Col(dcc.Dropdown(
                id='noc-dropdown',
                value=None,  # Default to None until data loads
                multi=False,  # Single selection only
                clearable=False,
                style={'width': '100%', 'margin-top': '20px'}
            ), width=3)
        ], style={'margin-left': '0', 'margin-right': '0'}),
        
        # Map plot row
        dbc.Row([
            dbc.Col(dcc.Graph(id='map-plot', style={'height': '55vh'}), width=12)  # Adjusted height
        ], style={'margin-left': '0', 'margin-right': '0'}),
        
        # Economic Region dropdown row
        dbc.Row([
            dbc.Col(dcc.Dropdown(
                id='region-dropdown',
                value=['All'],  # Default to 'All'
                multi=True,  # Allow multiple selections
                clearable=True,
                placeholder="Select Economic Region",
                style={'width': '100%', 'margin-top': '20px'}
            ), width=12)
        ], style={'margin-left': '0', 'margin-right': '0'}),
        
        # Bar plot row
        dbc.Row([
            dbc.Col(dcc.Graph(id='bar-plot', style={'height': '20vh'}), width=12)  # Adjusted height
        ], style={'margin-left': '0', 'margin-right': '0'}),
        
        # Data source row
        dbc.Row([
            dbc.Col(html.P(id='data-source', style={'text-align': 'center', 'margin-top': '20px'}), width=12, style={'position': 'absolute', 'bottom': '20px', 'width': '100%'})
        ], style={'margin-left': '0', 'margin-right': '0'}),
        
        # Footer with language dropdown
        dbc.Row([
            dbc.Col(dcc.Dropdown(
                id='language-dropdown',
                options=[{'label': 'English', 'value': 'English'}, {'label': 'Français', 'value': 'French'}],
                value='English',
                clearable=False,
                style={'width': '150px', 'margin-right': 'auto', 'margin-left': 'auto'}  # Normal width
            ), width=3, style={'margin-left': 'auto'})
        ], style={'position': 'absolute', 'bottom': '20px', 'width': '100%', 'left': '0', 'right': '0'}),
        
        # Info modal
        dbc.Modal([
            dbc.ModalHeader(id="info-modal-header"),
            dbc.ModalBody(dcc.Markdown(id="info-modal-body")),
            dbc.ModalFooter(
                dbc.Button(id="close-info-modal", className="ml-auto")
            )
        ], id="info-modal", is_open=False),
        
        # Employment Trends modal
        dbc.Modal([
            dbc.ModalHeader("Employment Trends"),
            dbc.ModalBody(dcc.Markdown(id="employment-trends-body", dangerously_allow_html=True)),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-trends-modal", className="ml-auto")
            )
        ], id="trends-modal", is_open=False)
    ], fluid=True)

    # Callback to toggle the info modal
    @app.callback(
        Output("info-modal", "is_open"),
        [Input("open-info-modal", "n_clicks"), Input("close-info-modal", "n_clicks")],
        [State("info-modal", "is_open")]
    )
    def toggle_info_modal(n1, n2, is_open):
        if n1 or n2:
            return not is_open
        return is_open

    # Callback to update data when language is switched
    @app.callback(
        [Output('noc-dropdown', 'options'), Output('noc-dropdown', 'value'), Output('region-dropdown', 'options'), Output('dashboard-title', 'children'), Output('info-modal-header', 'children'), Output('info-modal-body', 'children'), Output('close-info-modal', 'children'), Output('data-source', 'children')],
        Input('language-dropdown', 'value')
    )
    def update_dropdowns(language):
        """
        Update the NOC and region dropdown options and values based on the selected language.

        Parameters:
        language (str): The selected language ('English' or 'French').

        Returns:
        tuple: A tuple containing the dropdown options and the first NOC title as the default value.
        """
        sorted_df, _, _ = load_data(language)
        noc_options = [{'label': title, 'value': title} for title in sorted(sorted_df['NOC Title'].unique())]
        region_options = [{'label': 'All', 'value': 'All'}] + [{'label': region, 'value': region} for region in sorted(sorted_df['Economic Region Name'].unique())]
        if language == 'English':
            title = "Canadian Job Market Outlook 2024-2026"
            info_header = "About This App"
            info_body = (
                "This dashboard provides an outlook on the Canadian job market for 2024-2026. \n\n"
                "### Features:\n"
                "- **NOC Title Dropdown:** Select a National Occupational Classification (NOC) title to view its job outlook.\n"
                "- **Region Dropdown:** Select one or more economic regions to filter the data.\n"
                "- **Map Plot:** Displays the geographical distribution of job outlooks across selected regions.\n"
                "- **Bar Plot:** Shows the job outlook for various economic regions.\n"
                "- **Language Selection:** Switch between English and French data.\n\n"
                "### How to Use:\n"
                "1. Select a NOC title from the 'NOC Title Dropdown'.\n"
                "2. Optionally, select one or more economic regions from the 'Region Dropdown'.\n"
                "3. View the map and bar plots to analyze the job outlooks.\n"
                "4. Click on a region in the map or bar plot to view detailed employment trends.\n"
                "5. Use the 'Language Dropdown' to switch between English and French data.\n\n"
            )
            close_button = "Close"
            data_source = [
                "Data sourced and provided by the Government of Canada. ",
                html.Br(),
                html.A("Visit the website", href="https://www.statcan.gc.ca/en/subjects/standard/noc/2021/indexV1", target="_blank"),
                html.Br(),
                html.A("Open Canada Data", href="https://open.canada.ca/data/en/dataset/b0e112e9-cf53-4e79-8838-23cd98debe5b?_gl=1*h2x1ic*_ga*MTc4Mjg5MzYwMi4xNjc4MTQ5Mjc1*_ga_S9JG8CZVYZ*MTczNDM4ODMyOC4xMi4xLjE3MzQzODg2OTUuNDkuMC4w", target="_blank")
            ]
        else:
            title = "Perspectives du marché du travail canadien 2024-2026"
            info_header = "À propos de cette application"
            info_body = (
                "Ce tableau de bord fournit des perspectives sur le marché du travail canadien pour 2024-2026. \n\n"
                "### Caractéristiques:\n"
                "- **Menu déroulant des titres NOC:** Sélectionnez un titre de Classification nationale des professions (CNP) pour voir ses perspectives d'emploi.\n"
                "- **Menu déroulant des régions:** Sélectionnez une ou plusieurs régions économiques pour filtrer les données.\n"
                "- **Carte:** Affiche la répartition géographique des perspectives d'emploi dans les régions sélectionnées.\n"
                "- **Graphique en barres:** Affiche les perspectives d'emploi pour diverses régions économiques.\n"
                "- **Sélection de la langue:** Passez des données en anglais aux données en français.\n\n"
                "### Comment utiliser:\n"
                "1. Sélectionnez un titre NOC dans le 'Menu déroulant des titres NOC'.\n"
                "2. Facultativement, sélectionnez une ou plusieurs régions économiques dans le 'Menu déroulant des régions'.\n"
                "3. Consultez la carte et les graphiques en barres pour analyser les perspectives d'emploi.\n"
                "4. Cliquez sur une région dans la carte ou le graphique en barres pour voir les tendances d'emploi détaillées.\n"
                "5. Utilisez le 'Menu déroulant des langues' pour passer des données en anglais aux données en français.\n\n"
                "Pour plus d'informations, visitez le site Web de StatCAN."
            )
            close_button = "Fermer"
            data_source = [
                "Données fournies par le gouvernement du Canada. ",
                html.Br(),
                html.A("Visitez le site Web", href="https://www.statcan.gc.ca/fr/sujets/norme/cnp/2021/indexV1", target="_blank"),
                html.Br(),
                html.A("Données ouvertes Canada", href="https://ouvert.canada.ca/data/fr/dataset/b0e112e9-cf53-4e79-8838-23cd98debe5b?_gl=1*h2x1ic*_ga*MTc4Mjg5MzYwMi4xNjc4MTQ5Mjc1*_ga_S9JG8CZVYZ*MTczNDM4ODMyOC4xMi4xLjE3MzQzODg2OTUuNDkuMC4w", target="_blank")
            ]
        return noc_options, sorted_df['NOC Title'].iloc[0], region_options, title, info_header, info_body, close_button, data_source

    # Callback to update both plots based on dropdown selection
    @app.callback(
        [Output('map-plot', 'figure'), Output('bar-plot', 'figure')],
        [Input('noc-dropdown', 'value'), Input('region-dropdown', 'value'), Input('language-dropdown', 'value')]
    )
    def update_plots(selected_noc, selected_regions, language):
        """
        Update the map and bar plots based on the selected NOC title, regions, and language.

        Parameters:
        selected_noc (str): The selected NOC title.
        selected_regions (list): The selected economic regions.
        language (str): The selected language ('English' or 'French').

        Returns:
        tuple: A tuple containing the updated map and bar plot figures.
        """
        sorted_df, outlook_order, outlook_colors = load_data(language)
        
        # Merge the sorted DataFrame with the geographical data
        merged_df = gdf[['ERNAME', 'centroid']].merge(sorted_df, left_on='ERNAME', right_on='Economic Region Name')
        merged_df['lat'] = merged_df['centroid'].apply(lambda point: point.y)
        merged_df['lon'] = merged_df['centroid'].apply(lambda point: point.x)
        
        # Filter the DataFrame by the selected NOC title and regions
        filtered_df = merged_df[merged_df['NOC Title'] == selected_noc]
        if selected_regions and 'All' not in selected_regions:
            filtered_df = filtered_df[filtered_df['Economic Region Name'].isin(selected_regions)]
        
        # Create the map plot
        map_fig = px.scatter_mapbox(
            filtered_df, lat='lat', lon='lon', color='Outlook', size_max=13, zoom=3,
            mapbox_style="carto-positron", center={"lat": 60.0, "lon": -106.3468},
            category_orders={'Outlook': outlook_order},
            color_discrete_map=outlook_colors,
            hover_name='Economic Region Name',
            size=[6.5] * len(filtered_df)
        )
        
        # Create the bar plot
        bar_labels = {'x': 'Economic Region Name', 'y': 'Outlook'} if language == 'English' else {'x': 'Nom de la région économique', 'y': 'Perspectives'}
        bar_fig = px.bar(
            filtered_df, x='Economic Region Name', y='Outlook', color='Outlook',
            labels=bar_labels,
            category_orders={'Outlook': outlook_order},
            color_discrete_map=outlook_colors
        )
        
        # Sync legend across both plots
        map_fig.update_layout(
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
        bar_fig.update_layout(
            showlegend=False
        )  
        
        return map_fig, bar_fig

    # Callback to display employment trends modal
    @app.callback(
        Output("trends-modal", "is_open"),
        Output("employment-trends-body", "children"),
        [Input("map-plot", "clickData"), Input("bar-plot", "clickData"), Input("close-trends-modal", "n_clicks")],
        [State("trends-modal", "is_open"), State("language-dropdown", "value")]
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

    # Run the app
    if __name__ == '__main__':
        app.run_server(debug=True)

    return app