from dash import Dash, html, dcc, callback, callback_context, Output, Input, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import datetime as dt

import ETL as etl

portfolio_assets = pd.DataFrame(columns=['Ticker Symbol', 'Amount'])

saved_pf_ids = etl.get_portfolio_names()
saved_pf_ids.loc['current'] = 'Current'

application = Dash(__name__, prevent_initial_callbacks=False, external_stylesheets=[dbc.themes.LUX])
server = application.server
application.layout = dbc.Container(html.Div([
    html.H1(children='Portfolio Builder', style={'textAlign':'center'}),

    dcc.Markdown('''
    #### To add items to your current portfolio:
    1. Input valid ticker symbol and planned purchase amount
    2. Press add asset
    3. Repeat till satisfied
    4. Use remove and clear to clear mistakes
    5. You can now save the portfolio by giving it a name or plot it by choosing "Current from the dropdown-menu below"

    '''),

    dbc.Row(dbc.Col(html.Div(["Stock ticker: ",
        dbc.Input(id="ticker",value="SPY",type= "text")]),
                width=12
    )),
    html.Div(["Purchase Amount: ",
        dbc.Input(id="purchaseAmount",value="10000",type= "text")]),

    dbc.Button(id='addAssetButton', n_clicks=0, children='Add Asset'),
    dbc.Button(id='deleteAssetButton', n_clicks=0, children='Delete Asset'),
    dbc.Button(id='clearButton', n_clicks=0, children='Clear Portfolio'),
    
    html.Br(),
    html.Br(),

    dcc.Markdown('''
    ###### Chosen assets:
    '''),
    dbc.Row(dbc.Col(html.Div(id="components"),
                width=12
    )),

    dbc.Row(dbc.Col(html.Div(["Name of your portfolio: ",
        dbc.Input(id="pf_name",value="my_portfolio",type= "text")]),
                width=3
    )),


    dbc.Button(id='save_portfolio', n_clicks=0, children='Save Portfolio'),
    dbc.Button(id='remove_portfolio', n_clicks=0, children='Remove Portfolio'),
    dbc.Button(id='remove_all_portfolios', n_clicks=0, children='Remove All Portfolios'),
    html.Div(id='remove_pf'),
    html.Div(id='remove_all_pfs'),

    html.Br(),

    dcc.Markdown('''
    #### To plot your portfolio:
    1. Select "Current" from dropdown-menu to use the portfolio you have build above. To use saved one, you can choose any of the other portfolios shown in the menu.
    2. Input how many years to the future you cant to project
    3. Choose the confidence interval for projection
    4. Press Plot Portfolio
    '''),

    dbc.Row(dbc.Col(html.Div(["Years: ",
        dbc.Input(id="years",value="10",type= "text")]),
                width=3
    )),

    dbc.Row(dbc.Col(html.Div(["Confidence level: ",
                              dcc.Dropdown(
        id='confidence',
        options=[
            {'label': 'Confidence level 50%', 'value': '50%'},
            {'label': 'Confidence level 90%', 'value': '90%'},
            {'label': 'Confidence level 95%', 'value': '95%'},
            {'label': 'Confidence level 99%', 'value': '99%'}
        ],
        value='90%')]), width=3
    )),
    dbc.Row(dbc.Col(html.Div(["Portfolio name: ",
        dcc.Dropdown(
            id='portfolio_id',
            options=[{'label': f'{id}', 'value': id} for id in saved_pf_ids['portfolio_id']],
            value='example1')]), width=3
    )),
    dbc.Button(id='createPortfolio', n_clicks=0, children='Plot Portfolio'),
    html.Div(id="not_found_tickers"),
    html.Div(id="not_found_tickers_save"),
    html.Div(id="already_exists_error"),
    

    dbc.Row([
        dbc.Col(dbc.Spinner(children=[dcc.Graph(id="graph")], color="success"),
                width=6),
        dbc.Col(dbc.Spinner(children=[dcc.Graph(id="pie-chart")], color="success"),
                width=6)
    ]),

    dbc.Row(dbc.Col(dbc.Spinner(children=[html.Div(id="breakdown")], color="success"),
                width=12)),

    dcc.Markdown('''
    
    ###### The math

    1. Expected returns are based on the Capital Asset Pricing Model. [AWCI](https://www.msci.com/acwi) is used as a market portfolio.

    2. Daily data from  [yahoo finance](https://finance.yahoo.com) is used for the calculations.

    3. Confidence levels follow log-normal distribution.

    
    @Teemu Saha.
    [LinkedIn](https://linkedin.com/in/teemu-saha-18090b19b)
    [GitHub](https://github.com/Tepes99/portfolio_builder)

    '''),

]),fluid=True)

@application.callback(
    Output(component_id= "components", component_property= "children"),
    [Input('addAssetButton', 'n_clicks')],
    [Input('deleteAssetButton', 'n_clicks')],
    [Input('clearButton', 'n_clicks')],
    [State(component_id= "ticker",component_property= "value"),
    State(component_id= "purchaseAmount",component_property= "value")]
)
def update_asset_list(add, delete, clear, ticker, amount):
    ctx = callback_context
    buttonPressed = ctx.triggered[0]['prop_id'].split('.')[0]
    if buttonPressed == "addAssetButton":
        if ticker in portfolio_assets.index:
            portfolio_assets.loc[ticker] = [ticker, int(amount) + portfolio_assets.loc[ticker, 'Amount']]
        else:
            portfolio_assets.loc[ticker] = [ticker, int(amount)]
    if buttonPressed == "deleteAssetButton":
        portfolio_assets.drop(ticker, inplace=True)
    if buttonPressed == "clearButton":
        portfolio_assets.drop(portfolio_assets.index, inplace=True)

    return dbc.Table.from_dataframe(
        portfolio_assets,
        striped=True,
        bordered=True,
        hover=True,
        size='sm'
        )

# Callback for saving the portfolio
@application.callback(
            Output('portfolio_id', 'options'),
            Output('not_found_tickers_save', 'children'),
            Output('already_exists_error', 'children'),
            [State('pf_name', 'value'),
            Input('save_portfolio', 'n_clicks'),
            Input('remove_portfolio', 'n_clicks'),
            Input('remove_all_portfolios', 'n_clicks')])

def save_portfolio(pf_name, save, remove, remove_all):
    not_found_tickers = set()
    saved_pf_ids = etl.get_portfolio_names()
    saved_pf_ids.loc['current'] = 'Current'
    no_tickers_error = None
    already_exists_error = None

    ctx = callback_context
    buttonPressed = ctx.triggered[0]['prop_id'].split('.')[0]
    if buttonPressed == "save_portfolio":
        if pf_name not in saved_pf_ids.values:
            not_found_tickers = etl.save_portfolio_to_db(contribution=portfolio_assets['Amount'], portfolio_id=pf_name)
            saved_pf_ids = etl.get_portfolio_names()
            saved_pf_ids.loc['current'] = 'Current'
        else:
            already_exists_error = f'Error when saving the portfolio > Portfolio {pf_name} already exists'

        if len(not_found_tickers):
            no_tickers_error = f'Error when saving the portfolio > Could not find ticker(s): {not_found_tickers}'
        else:
            no_tickers_error = None
    
    if buttonPressed == "remove_portfolio":
        etl.remove_portfolio_from_db(pf_name)
        saved_pf_ids = etl.get_portfolio_names()
        saved_pf_ids.loc['current'] = 'Current'
    if buttonPressed == "remove_all_portfolios":
        etl.remove_all_portfolios_from_db()
        saved_pf_ids = etl.get_portfolio_names()
        saved_pf_ids.loc['current'] = 'Current'
    return [{'label': f'{id}', 'value': id} for id in saved_pf_ids['portfolio_id']], dcc.Markdown(no_tickers_error), dcc.Markdown(already_exists_error)


# Callback for the graphs and data table
@application.callback(
    Output(component_id= "graph", component_property= "figure"),
    Output(component_id= "breakdown", component_property= "children"),
    Output(component_id="pie-chart", component_property="figure"),
    Output(component_id="not_found_tickers", component_property="children"),
    [Input('createPortfolio', 'n_clicks'),
    State(component_id= "years", component_property= "value"),
    State(component_id= "confidence", component_property= "value"),
    State(component_id= "portfolio_id",component_property= "value")])

def updatePlot(update, years, confidence, portfolio_id):
    startDate = dt.datetime.now()
    endDate = startDate + dt.timedelta(days= int(years)*365)
    #Confidence level
    if confidence == '50%':
        z = 0.675
    if confidence == '90%':
        z = 1.645
    if confidence == '95%':
        z = 1.960
    if confidence == '99%':
        z = 2.576

    
    if portfolio_id == 'Current':
        portfolio, not_found_tickers = etl.calculate_key_figures(portfolio_assets['Amount'])
        portfolio = portfolio.reset_index()
        portfolio.index = portfolio['index']
        portfolio.rename(columns={'index': 'ticker'}, inplace=True)
    else:
        portfolio = etl.get_saved_portfolio(portfolio_name=portfolio_id)
        portfolio.index = portfolio['ticker']
        portfolio.drop('portfolio_id', axis=1, inplace=True)
        not_found_tickers = set()
    growthRate = portfolio.loc["Portfolio","expected_return"]             
    purchaseAmount = portfolio.loc["Portfolio","amount"]
    volatility = portfolio.loc["Portfolio","historical_volatility"]

    futurePrices, confidenceIntervalLow, confidenceIntervalHigh = etl.calculate_expected_returns(purchaseAmount,growthRate,volatility,int(years),z)
    #plotting
    x = pd.date_range(startDate,endDate).tolist()
    x_rev = x[::-1]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x= x+x_rev,
        y=list(confidenceIntervalLow)+list(futurePrices)[::-1],
        fill='toself',
        fillcolor='rgba(100,0,0,0.2)',
        line_color='rgba(255,255,255,0)',
        showlegend=False,
        name= confidence +'Confidence level',
    ))

    fig.add_trace(go.Scatter(
        x= x+x_rev,
        y=list(confidenceIntervalHigh)+list(futurePrices)[::-1],
        fill='toself',
        fillcolor='rgba(0,100,80,0.2)',
        line_color='rgba(255,255,255,0)',
        showlegend=False,
        name= confidence +'Confidence level',
    ))

    fig.add_trace(go.Scatter(
        x=x, y=futurePrices,
        line_color='rgb(0,100,80)',
        name='Portfolio',
    ))

    fig.add_trace(go.Scatter(
        x=x, y=confidenceIntervalLow,
        line_color='rgb(200,0,0)',
        name='Lower bound',
    ))

    fig.add_trace(go.Scatter(
        x=x, y=confidenceIntervalHigh,
        line_color='rgb(0,200,160)',
        name='Upper bound',
    ))

    fig.update_traces(mode='lines')

    portfolio = portfolio.round(4)
    pieData = portfolio.drop('Portfolio')

    pie = go.Figure(go.Pie(
        name = "Portfolio composition",
        values = pieData['amount'],
        labels = pieData['historical_volatility']*100,
        showlegend= False,
        #hover_data= ['assetCAPM', 'volatility', 'beta'],
        customdata= pieData['expected_return'],
        text= pieData.index,
        hole= 0.5,
        hovertemplate = "Expected return:%{customdata}: <br>Contribution: %{value} </br>Volatility:%{label}<br>Ticker:%{text}",
        
    ))
    if len(not_found_tickers):
        error_message = f'Error when plotting the portfolio > Could not find ticker(s): {not_found_tickers}'
    else:
        error_message = None
    return fig, dbc.Table.from_dataframe(
        portfolio,
        striped=True,
        bordered=True,
        hover=True,
        size='sm'
        ), pie, dcc.Markdown(error_message)


if __name__ == '__main__':
    application.run_server(debug=False)