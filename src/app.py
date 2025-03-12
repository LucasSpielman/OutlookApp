import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

from text_content import text_content_noc

# Import your two existing Dash app layouts and callbacks
from ERbyNOCTitle import create_layout as create_layout1
from ERbyNOCTitle import register_callbacks as register_callbacks1

from NOCTitlebyER import create_layout as create_layout2
from NOCTitlebyER import register_callbacks as register_callbacks2

# Initialize the main Dash app with the Minty theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY], suppress_callback_exceptions=True)
app.title = 'Combined Dash App'

# Define the login layout
login_layout = html.Div([
    dcc.Location(id='url_login', refresh=True),
    html.Div([
        html.H2('Log In:', id='h1'),
        dcc.Input(placeholder='Enter your username', type='text', id='uname-box'),
        dcc.Input(placeholder='Enter your password', type='password', id='pwd-box'),
        html.Button(children='Login', n_clicks=0, type='submit', id='login-button'),
        html.Div(children='', id='output-state')
    ], style={'textAlign': 'center', 'width': '300px', 'margin': 'auto', 'padding': '50px', 'border': '1px solid #ccc', 'borderRadius': '10px', 'boxShadow': '0 0 10px rgba(0, 0, 0, 0.1)'})
], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'height': '100vh'})

# Define the main layout with tabs
main_layout = html.Div([
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
    if tab == 'tab1':
        return create_layout1()
    elif tab == 'tab2':
        return create_layout2()

# Define the callback for the login button
@app.callback(
    Output('url_login', 'pathname'),
    Output('output-state', 'children'),
    Input('login-button', 'n_clicks'),
    State('uname-box', 'value'),
    State('pwd-box', 'value')
)
def update_output(n_clicks, input1, input2):
    if n_clicks > 0:
        if input1 == 'admin' and input2 == '3525061':  # Replace with your own authentication logic
            return '/main', ''
        else:
            return '/login', 'Incorrect username or password'
    else:
        return '/login', ''

# Define the callback to update the layout based on the URL
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/main':
        return main_layout
    else:
        return login_layout

# Define the app layout with a location component
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Register callbacks for each app
register_callbacks1(app)
register_callbacks2(app)

# Run the server
if __name__ == '__main__':
    app.run_server(debug=True)