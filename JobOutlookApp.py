import dash
import dash_table
import pandas as pd
from dash import dcc, html
import plotly.express as px

# TODO: Have df_region_filtered be filtered by the user's input
# TODO: Have search for economic region be a dropdown menu
# TODO: Have the user input the file path for english or french
# TODO: Have search Functionality for specific NOC Titles
# TODO: Make it look prettier
# TODO: Make standalone app for for user download

# Load the Excel file
file_path = "./data/20242026_outlook_n21_en_250117.xlsx"
xls = pd.ExcelFile(file_path)

# Load sheet into DataFrame
display_name = xls.sheet_names[0]
df = pd.read_excel(xls, sheet_name=display_name)

# Outlook paramaters for sorting. "Very good" is the best outlook, "undetermined" is the worst.
outlook_order = ['very good', 'good', 'fair', 'limited', 'undetermined']

# Filter the dataframe by Economic Region
economic_region_filter = 'British Columbia'  # Replace with the desired economic region, we want to have the user input this

# Use .loc to filter the DataFrame by the Economic Region
df_region_filtered = df.loc[df['Economic Region Name'] == economic_region_filter]

# Convert 'Outlook' to a categorical type with the specified order
df_region_filtered['Outlook'] = pd.Categorical(df_region_filtered['Outlook'], categories=outlook_order, ordered=True)

# Now sort by 'Outlook' in the defined order
df_sorted_by_outlook = df_region_filtered.sort_values('Outlook')

# simple dash app to display the DataFrame
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Economic Region Outlook Data for {economic_region_filter}", style={'text-align': 'center'}),
    
    # DataTable to display the DataFrame
    dash_table.DataTable(
        id='datatable',
        columns=[
            {'name': col, 'id': col} for col in df_sorted_by_outlook.columns
        ],
        data=df_sorted_by_outlook.to_dict('records'),
        style_table={'height': '400px', 'overflowY': 'auto'},
        style_cell={'textAlign': 'center', 'padding': '10px'},
        style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)