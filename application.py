import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

app = Dash(__name__, prevent_initial_callbacks=False, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
application = app.server
app.layout = html.Div([
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Cars", href="/cars-demo")),
            dbc.NavItem(dbc.NavLink("Portfolio Builder", href="/pf-builder")),
            dbc.NavItem(dbc.NavLink("B.Sc Thesis", href="https://aaltodoc.aalto.fi/server/api/core/bitstreams/16fe675d-0aed-4d77-bbf1-a6d042209113/content")),
            
        ],
        brand="Home",
        brand_href="/",
        color="primary",
        dark=True,
    ),
    dash.page_container
])



if __name__ == '__main__':
    #app.run_server(debug=True)
    application.run(debug=False, port=8080)