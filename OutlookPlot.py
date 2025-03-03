import geopandas as gpd
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import json

# Load the shapefile of Canada
canada_shapefile = gpd.read_file('./data/ler_000b16a_e.shp')

# Simplify the geometries to reduce complexity
canada_shapefile['geometry'] = canada_shapefile['geometry'].simplify(tolerance=0.01)

# Load the job outlook data
job_outlook_data = pd.read_excel('./data/20242026_outlook_n21_en_250117.xlsx')

# Ensure the ERUID is an integer for merging
canada_shapefile['ERUID'] = canada_shapefile['ERUID'].astype(int)

# Merge the data on the region code
merged_data = canada_shapefile.merge(job_outlook_data, left_on='ERUID', right_on='Economic Region Code')

# Convert the merged data to GeoJSON format
geojson_data = json.loads(merged_data.to_json())

# Initialize the Dash app
app = dash.Dash(__name__)

# Create a choropleth map
fig = px.choropleth(merged_data, 
                    geojson=geojson_data, 
                    locations=merged_data.index, 
                    color='Outlook', 
                    hover_name='Economic Region Name',
                    title='Job Outlook by Region in Canada')

# Define the layout of the app
app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label='Map', children=[
            dcc.Graph(figure=fig)
        ]),
        dcc.Tab(label='Job Specific Plot', children=[
            dcc.Dropdown(
                id='job-dropdown',
                options=[{'label': job, 'value': job} for job in job_outlook_data['NOC Title'].unique()],
                value=job_outlook_data['NOC Title'].unique()[0]
            ),
            dcc.Graph(id='job-specific-plot')
        ])
    ])
])

# Callback to update the job-specific plot
@app.callback(
    Output('job-specific-plot', 'figure'),
    [Input('job-dropdown', 'value')]
)
def update_job_specific_plot(selected_job):
    filtered_data = merged_data[merged_data['NOC Title'] == selected_job]
    geojson_filtered = json.loads(filtered_data.to_json())
    fig = px.choropleth(filtered_data, 
                        geojson=geojson_filtered, 
                        locations=filtered_data.index, 
                        color='Outlook', 
                        hover_name='Economic Region Name',
                        title=f'Job Outlook for {selected_job} by Region in Canada')
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)