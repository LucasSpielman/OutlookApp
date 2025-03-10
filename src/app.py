import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc

# Import your two existing Dash app layouts and callbacks
from ERbyNOCTitle import create_layout as create_layout1
from ERbyNOCTitle import register_callbacks as register_callbacks1

from NOCTitlebyER import create_layout as create_layout2
from NOCTitlebyER import register_callbacks as register_callbacks2

# Initialize the main Dash app with the Minty theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY], suppress_callback_exceptions=True)
app.title = 'Combined Dash App'

# Cache the layouts
cached_layouts = {
    'tab1': create_layout1(),
    'tab2': create_layout2()
}

# Define the layout with tabs
app.layout = html.Div([
    dcc.Tabs(id='tabs', value='tab1', children=[
        dcc.Tab(label='Canadian Job Market Outlook', value='tab1'),
        dcc.Tab(label='Canadian Economic Region Outlook', value='tab2')
    ]),
    html.Div(id='tabs-content')
])

# Define the callback to switch tabs
@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value')
)
def render_content(tab):
    return cached_layouts[tab]

# Register callbacks for each app
register_callbacks1(app)
register_callbacks2(app)

# Run the server
if __name__ == '__main__':
    app.run_server(debug=True)