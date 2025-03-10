import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
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

def load_data(language):
    """
    Load the data from the Excel file based on the selected language.
    Cache the data to avoid reloading it multiple times.

    Parameters:
    language (str): The selected language ('English' or 'French').

    Returns:
    tuple: A tuple containing the sorted DataFrame, outlook order, and outlook colors.
    """
    # Check if data is already cached
    if language in cached_data:
        return cached_data[language]
    
    # Read the Excel file
    df = pd.read_excel(file_paths[language])
    
    # Define the outlook order and colors based on the language
    if language == 'English':
        outlook_order = ['very good', 'good', 'moderate', 'limited', 'undetermined', 'bazinga']
        outlook_colors = {
            'very good': '#30AD23',  # Warm green
            'good': '#1E90FF',  # Dodger Blue
            'moderate': '#FFD700',  # Gold
            'limited': '#F08315',  # Warm Orange
            'undetermined': '#BA110C',  # Dark Red
            'bazinga': '#D3D3D3',  # Light Grey
        }
    else:  # French
        outlook_order = ['très bonnes', 'bonnes', 'modérées', 'limitées', 'indéterminées', 'bazinga']
        outlook_colors = {
            'très bonnes': '#30AD23',  # Warm Green
            'bonnes': '#1E90FF',  # Dodger Blue
            'modérées': '#FFD700',  # Gold
            'limitées': '#F08315',  # Warm Orange
            'indéterminées': '#BA110C',  # Dark Red
            'bazinga': '#D3D3D3',  # Light Grey
        }
    
    # Combine 'Economic Region Name' and 'Province' into a single column
    df['Economic Region Name'] = df.apply(lambda row: f"{row['Economic Region Name']}, {row['Province']}", axis=1)
    
    # Convert the 'Outlook' column to a categorical type with the defined order
    df['Outlook'] = pd.Categorical(df['Outlook'], categories=outlook_order, ordered=True)
    
    # Sort the DataFrame by 'NOC Title', 'Economic Region Name', and 'Outlook'
    sorted_df = df.sort_values(by=['NOC Title', 'Economic Region Name', 'Outlook'])
    
    # Cache the data
    cached_data[language] = (sorted_df, outlook_order, outlook_colors)
    
    return sorted_df, outlook_order, outlook_colors

# Load the shapefile for geographical data
gdf = gpd.read_file("./data/ler_000b16a_e.shp")
gdf = gdf.to_crs(epsg=4326)  # Ensure the coordinate reference system is WGS84

# Simplify geometries to improve performance
gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)

# Calculate centroids for each region
gdf['centroid'] = gdf.geometry.centroid

# Initialize the Dash app with the Minty theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])

# Define the layout of the app
app.layout = dbc.Container([
    # Title row
    dbc.Row([dbc.Col(html.H1("Canadian Job Market Outlook 2024-2026", style={'textAlign': 'center'}), width=12)]),
    
    # Language dropdown row
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='language-dropdown',
            options=[{'label': 'English', 'value': 'English'}, {'label': 'Français', 'value': 'French'}],
            value='English',
            clearable=False,
            style={'width': '35%', 'margin': 'auto'}
        ), width=12)
    ]),
    
    # Region dropdown row
    dbc.Row([
        dbc.Col(dcc.Dropdown(id='region-dropdown', value=None, clearable=False, style={'width': '50%', 'margin': 'auto'}), width=12)
    ]),
    
    # Outlook dropdown row
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='outlook-dropdown', 
            value=None, 
            multi=True,  # Allow multiple selections
            clearable=False, 
            style={'width': '50%', 'margin': 'auto'}
        ), width=12)
    ]),
    
    # Bar plot row
    dbc.Row([
        dbc.Col(dcc.Graph(id='bar-plot', style={'height': '50vh'}), width=12)
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
    
    # Footer row
    dbc.Row([
        dbc.Col(html.Footer([
            html.P("Data sourced and provided by the Government of Canada."),
            html.A("Visit the website", href="https://www.statcan.gc.ca/en/subjects/standard/noc/2021/indexV1", target="_blank")
        ], style={'text-align': 'center', 'margin-top': '20px'}), width=12)
    ])
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
    sorted_df, outlook_order, _ = load_data(language)
    
    # Create options for region dropdown
    region_options = [{'label': region, 'value': region} for region in sorted(sorted_df['Economic Region Name'].unique())]
    
    # Create options for outlook dropdown
    outlook_options = [{'label': outlook, 'value': outlook} for outlook in outlook_order]

    # Default select first region and first 2 outlooks
    return region_options, sorted_df['Economic Region Name'].iloc[0], outlook_options, outlook_order[:2]

# Callback to update bar plot and page slider based on selected inputs
@app.callback(
    [Output('bar-plot', 'figure'), Output('page-slider', 'max'), Output('page-slider', 'marks')],
    [Input('region-dropdown', 'value'), Input('language-dropdown', 'value'), Input('outlook-dropdown', 'value'), Input('page-slider', 'value')]
)
def update_bar_plot(selected_region, language, selected_outlooks, page):
    """
    Update the bar plot and page slider based on the selected region, language, outlooks, and page.

    Parameters:
    selected_region (str): The selected economic region.
    language (str): The selected language ('English' or 'French').
    selected_outlooks (list): The selected outlook categories.
    page (int): The current page number.

    Returns:
    tuple: A tuple containing the updated bar plot figure, maximum page number, and slider marks.
    """
    sorted_df, outlook_order, outlook_colors = load_data(language)
    
    # Ensure selected_outlooks is a list
    if not selected_outlooks:
        selected_outlooks = outlook_order  # Default to all outlooks
    
    # Filter data based on region and selected outlooks
    filtered_df = sorted_df[
        (sorted_df['Economic Region Name'] == selected_region) & 
        (sorted_df['Outlook'].isin(selected_outlooks))
    ].copy()  # Make a copy to avoid modifying original data
    
    # Remove duplicate NOC Titles
    filtered_df = filtered_df.drop_duplicates(subset=['NOC Title'])
    
    # Pagination logic
    items_per_page = 10
    total_pages = (len(filtered_df) + items_per_page - 1) // items_per_page
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    paginated_df = filtered_df.iloc[start_idx:end_idx]
    
    # Create the bar chart with a fixed category order
    bar_fig = px.bar(
        paginated_df,
        x='NOC Title',
        y='Outlook',
        color='Outlook',
        labels={'x': 'NOC Title', 'y': 'Outlook'},
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
            borderwidth=1,
            itemclick="toggleothers"  # Ensure only one Outlook can be selected at a time
        ),
        hoverlabel=dict(
            font_size=16,  # Larger hover text
            font_family="Arial"
        ),
        xaxis_tickangle=-45,  # Rotate labels to avoid overlap
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
    
    return bar_fig, total_pages, slider_marks

if __name__ == '__main__':
    app.run_server(debug=True)