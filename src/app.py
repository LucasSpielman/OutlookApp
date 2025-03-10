# app.py
import dash
from dash import dcc, html
from NOCTitlebyER import app as NOC_app  # Import NOC_app
from ERbyNOCTitle import app as ER_app  # Import ER_app

# Create your main Dash app
app = dash.Dash(__name__)

# Define the layout with Tabs
app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label='Dashboard 1', children=[NOC_app.layout]),  # Use the layout from NOC_app
        dcc.Tab(label='Dashboard 2', children=[ER_app.layout])    # Use the layout from ER_app
    ])
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)