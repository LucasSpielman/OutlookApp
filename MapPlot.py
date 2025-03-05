import dash
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
    if language in cached_data:
        return cached_data[language]

    df = pd.read_excel(file_paths[language])

    if language == 'English':
        outlook_order = ['very good', 'good', 'moderate', 'limited', 'undetermined']
        outlook_colors = {
            'very good': 'green',
            'good': 'blue',
            'moderate': 'yellow',
            'limited': 'orange',
            'undetermined': 'red'
        }
    else:  # French
        outlook_order = ['très bonnes', 'bonnes', 'modérées', 'limitées', 'indéterminées']
        outlook_colors = {
            'très bonnes': 'green',
            'bonnes': 'blue',
            'modérées': 'yellow',
            'limitées': 'orange',
            'indéterminées': 'red'
        }

    df['Outlook'] = pd.Categorical(df['Outlook'], categories=outlook_order, ordered=True)
    sorted_df = df.sort_values(by=['NOC Title', 'Economic Region Name', 'Outlook'])
    cached_data[language] = (sorted_df, outlook_order, outlook_colors)
    
    return sorted_df, outlook_order, outlook_colors

# Load the shapefile
gdf = gpd.read_file("./data/ler_000b16a_e.shp")
gdf = gdf.to_crs(epsg=4326)  # Convert to WGS84 coordinate system

# Simplify geometries for performance
gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)

# Calculate centroids for each region
gdf['centroid'] = gdf.geometry.centroid

# Initialize the Dash app
app = dash.Dash(__name__)

# App layout
app.layout = html.Div(
    style={
        'display': 'flex',
        'flexDirection': 'column',
        'height': '100vh',
    },
    children=[
        html.H1("Canadian Job Market Outlook 2024-2026", style={'textAlign': 'left', 'marginLeft': '10px'}),

        dcc.Dropdown(
            id='noc-dropdown',
            value=None,
            multi=False,
            clearable=False
        ),

        dcc.Graph(id='map-plot', style={'height': '70vh'}),
        dcc.Graph(id='bar-plot', style={'height': '30vh'}),

        # Container for language dropdown positioned at the bottom right
        html.Div([
            dcc.Dropdown(
                id='language-dropdown',
                options=[{'label': 'English', 'value': 'English'}, {'label': 'Français', 'value': 'French'}],
                value='English',
                clearable=False
            )
        ], style={
            'position': 'absolute',
            'bottom': '10px',
            'right': '10px',
            'width': '200px'
        })
    ]
)

# Callback to update the NOC dropdown when language changes
@app.callback(
    [Output('noc-dropdown', 'options'), Output('noc-dropdown', 'value')],
    Input('language-dropdown', 'value')
)
def update_noc_dropdown(language):
    sorted_df, _, _ = load_data(language)
    options = [{'label': title, 'value': title} for title in sorted(sorted_df['NOC Title'].unique())]
    return options, sorted_df['NOC Title'].iloc[0]

# Callback to update both plots based on the selected NOC and language
@app.callback(
    [Output('map-plot', 'figure'), Output('bar-plot', 'figure')],
    [Input('noc-dropdown', 'value'), Input('language-dropdown', 'value')]
)
def update_plots(selected_noc, language):
    sorted_df, outlook_order, outlook_colors = load_data(language)

    # Merge with geographical data
    merged_df = gdf[['ERNAME', 'centroid']].merge(sorted_df, left_on='ERNAME', right_on='Economic Region Name')
    merged_df['lat'] = merged_df['centroid'].apply(lambda point: point.y)
    merged_df['lon'] = merged_df['centroid'].apply(lambda point: point.x)

    # Filter by selected NOC
    filtered_df = merged_df[merged_df['NOC Title'] == selected_noc]

    # Count occurrences of each outlook category
    outlook_counts = filtered_df.groupby('Outlook').size().reset_index(name='Outlook Value')

    # Ensure all outlook categories are present
    for outlook in outlook_order:
        if outlook not in outlook_counts['Outlook'].values:
            outlook_counts = outlook_counts.append({'Outlook': outlook, 'Outlook Value': 0}, ignore_index=True)

    # Add a small value to "undetermined" to make it visible
    outlook_counts.loc[outlook_counts['Outlook'] == 'undetermined', 'Outlook Value'] += 1

    # Bar plot
    bar_fig = px.bar(
        outlook_counts, x='Outlook', y='Outlook Value', color='Outlook',
        labels={'Outlook': 'Outlook Category', 'Outlook Value': 'Count'},
        category_orders={'Outlook': outlook_order},
        color_discrete_map=outlook_colors
    )

    # Ensure "undetermined" is always visible
    bar_fig.update_yaxes(range=[0, max(outlook_counts['Outlook Value'].max(), 1)])

    # Map plot
    map_fig = px.scatter_mapbox(
        filtered_df, lat='lat', lon='lon', color='Outlook', size_max=13, zoom=3,
        mapbox_style="carto-positron", center={"lat": 56.1304, "lon": -106.3468},
        category_orders={'Outlook': outlook_order},
        color_discrete_map=outlook_colors,
        hover_name='Economic Region Name',
        size=[6.5] * len(filtered_df)
    )

    # Sync legend across both plots
    map_fig.update_layout(showlegend=True, autosize=True, uirevision='constant')
    bar_fig.update_layout(showlegend=False)

    return map_fig, bar_fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)