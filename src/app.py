import dash
from dash import dcc, html
from src.pages.NOCTitlebyER import app1_layout
from src.pages.ERbyNOCTitle import app2_layout

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Tabs(id='tabs', value='tab1', children=[
        dcc.Tab(label='App 1', value='tab1'),
        dcc.Tab(label='App 2', value='tab2'),
    ]),
    html.Div(id='tabs-content')
])

@app.callback(
    dash.dependencies.Output('tabs-content', 'children'),
    [dash.dependencies.Input('tabs', 'value')]
)
def render_content(tab):
    if tab == 'tab1':
        return app1_layout
    elif tab == 'tab2':
        return app2_layout

if __name__ == '__main__':
    app.run_server(debug=True)