from dash import html, dcc, callback, callback_context, Output, Input, State
import dash_bootstrap_components as dbc
import dash
from dash import callback
import pandas as pd
import AZURE_ETL as aetl


dash.register_page(__name__)

data = aetl.query_db('select * from cars_demo_public;')
df = pd.DataFrame(data)
df.columns = df.columns.str.replace('_', ' ').str.capitalize()

layout = dbc.Container(html.Div([
    html.H1("Car Data by Power and Type",style={'textAlign':'center'}),

    html.Div(["Power type: ",
        dcc.Dropdown(
            id='car-type-dropdown',
            options=[
                {'label': 'All Cars', 'value': 'All'},
                {'label': 'Hybrid', 'value': 'Hybrid'},
                {'label': 'Electric', 'value': 'Electric'}],
            value='All')
            ]
    ),

    dcc.Graph(
        id='cars-line-chart',
    ),

    dcc.Slider(
        id='year-slider',
        min=df['Year'].min(),
        max=df['Year'].max(),
        marks={str(year): str(year) for year in df['Year'].unique()},
        value=df['Year'].max(),
        step=None
    ),

    dbc.Row(
        [
            dbc.Col(
                [
                    html.Div(
                        dcc.Graph(
                            id='electric-pie-chart',
                        ),
                    )
                ],
                width=4
            ),
            dbc.Col(
                [
                    html.Div(
                        dcc.Graph(
                            id='hybrid-pie-chart',
                        ),
                    )
                ],
                width=4
            ),
            dbc.Col(
                [
                    html.Div(
                        dcc.Graph(
                            id='all-pie-chart',
                        ),
                    )
                ],
                width=4
            ),
        ]
    )
],style={'margin-left': '5%','margin-right': '5%',}),fluid=True
)


@callback(
    Output('electric-pie-chart', 'figure'),
    Output('hybrid-pie-chart', 'figure'),
    Output('all-pie-chart', 'figure'),
    [Input('year-slider', 'value')]
)
def update_pie_chart(selected_year):
    filtered_df = df[df['Year'] == selected_year]

    electric_cars = {
        'data': [
            {
                'labels': df.columns[[1,3,5,7]],
                'values': filtered_df.iloc[0,[1,3,5,7]],
                'type': 'pie',
                'name': 'Electric Cars'
            }
        ],
        'layout': {
            'title': f'Battery Electric Cars Distribution for {selected_year}'
        }
    }

    hybrid_cars = {
        'data': [
            {
                'labels': df.columns[[2,4,6,8]],
                'values': filtered_df.iloc[0, [2,4,6,8]],
                'type': 'pie',
                'name': 'Hybrid Cars'
            }
        ],
        'layout': {
            'title': f'Plug-in Hybrid Cars Distribution for {selected_year}'
        }
    }

    all_cars = {
        'data': [
            {
                'labels': df.columns[9:13],
                'values': filtered_df.iloc[0, 9:13],
                'type': 'pie',
                'name': 'All Cars'
            }
        ],
        'layout': {
            'title': f'Cars Distribution for {selected_year}'
        }
    }
    
    return electric_cars, hybrid_cars, all_cars

@callback(
    Output('cars-line-chart', 'figure'),
    [Input('car-type-dropdown', 'value')]
)
def update_line_chart(selected_type):
    
    if selected_type == 'Electric':
        columns =[
            'Battery electric passenger cars',
            'Battery electric vans',
            'Battery electric trucks',
            'Battery electric buses',
        ]
        line_chart_data = [
            {
                'x': df['Year'],
                'y': df[column],
                'type': 'line',
                'name': column
            } for column in columns
        ]
    elif selected_type == 'Hybrid':
        columns =[
            'Plug-in hybrid passenger cars',
            'Plug-in hybrid vans',
            'Plug-in hybrid trucks',
            'Plug-in hybrid buses',
        ]
        line_chart_data = [
                {
                    'x': df['Year'],
                    'y': df[column],
                    'type': 'line',
                    'name': column
                } for column in columns
            ]
    else:
        line_chart_data = [
                {
                    'x': df['Year'],
                    'y': df[column],
                    'type': 'line',
                    'name': column
                } for column in df.columns[9:14]
            ]

    line_chart_figure = {
        'data': line_chart_data,
        'layout': {
            'title': 'Car Type Count Over the Years'
        }
    }
    return line_chart_figure