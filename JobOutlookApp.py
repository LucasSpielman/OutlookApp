import dash
import dash_table
import pandas as pd
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px

# TODO: [DONE] Have df_region_filtered be filtered by the user's input
# TODO: [DONE] Have search for economic region be a dropdown menu
# TODO: Have the user input the file path for english or french
# TODO: Have search Functionality for specific NOC Titles
# TODO: Make it look prettier
# TODO: Make standalone app for for user download

# File paths for English and French Excel files
file_paths = {
    'English': "./data/20242026_outlook_n21_en_250117.xlsx",
    'French': "./data/20242026_outlook_n21_fr_250117.xlsx"
}

# Load the initial Excel file (default to English)
xls = pd.ExcelFile(file_paths['English'])

# Load sheet into DataFrame
display_name = xls.sheet_names[0]
df = pd.read_excel(xls, sheet_name=display_name)

# Outlook parameters for sorting. "Very good" is the best outlook, "undetermined" is the worst.
outlook_order = ['very good', 'good', 'fair', 'limited', 'undetermined']

# Get unique economic regions for the dropdown options
economic_regions = df['Economic Region Name'].unique()

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
    
    # DataTable to display the DataFrame
    dash_table.DataTable(
        id='datatable',
        columns=[{'name': col, 'id': col} for col in df.columns],
        style_table={'height': '400px', 'overflowY': 'auto'},
        style_cell={'textAlign': 'center', 'padding': '10px'},
        style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
    )
])

# Callback to update the DataTable based on the selected language and region
@app.callback(
    Output('datatable', 'data'),
    Output('region-dropdown', 'options'),
    Output('region-dropdown', 'value'),
    Input('language-dropdown', 'value'),
    Input('region-dropdown', 'value')
)
def update_table(selected_language, selected_region):
    # Load the appropriate Excel file based on the selected language
    xls = pd.ExcelFile(file_paths[selected_language])
    df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])
    
    # Get unique economic regions for the dropdown options
    economic_regions = df['Economic Region Name'].unique()
    
    # Update the region dropdown options
    region_options = [{'label': region, 'value': region} for region in economic_regions]
    
    # If the selected region is not in the new options, default to the first region
    if selected_region not in economic_regions:
        selected_region = economic_regions[0]
    
    # Filter and sort the DataFrame based on the selected region
    df_region_filtered = df.loc[df['Economic Region Name'] == selected_region]
    df_region_filtered['Outlook'] = pd.Categorical(df_region_filtered['Outlook'], categories=outlook_order, ordered=True)
    df_sorted_by_outlook = df_region_filtered.sort_values('Outlook')
    
    return df_sorted_by_outlook.to_dict('records'), region_options, selected_region

if __name__ == '__main__':
    app.run_server(debug=True)