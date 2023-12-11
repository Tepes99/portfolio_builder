import dash
from dash import html, dcc

dash.register_page(__name__, path='/')

layout = html.Div([
    dcc.Markdown('''
        # Teemu Saha 
        *Transforming Data to Value*

        ## Background
        I am a passionate data developer, living in Helsinki, Finland. In my current occupation, I build and maintain data pipelines, and mentor our newest team member.

        ### Education
        #### B.Sc School of Business
        - Major: Information and Service Management
        - Minor: Finance
                '''),
    html.Br(),  
    dcc.Markdown('''
            ## Projects on this site
            ### Portfolio Builder
            #### Description
            Small demo app where the user can build a portfolio consisting of financial instruments that are listed in Yahoo Finance. With the app the user can analyse possible future returns based on the Capital Asset Pricing Model, view visualizations and save the portfolio key figures to database where they can be retrieved back. (Has to be same session as there are no accounts on the demo app)

            #### Stack
            - Cloud platform: AWS
            - Main libraries: Dash, Pandas, yfinance, sqlalchemy
            - Database: PostgreSQL
            - Nice to know: The app uses sessions, allowing multiple users at the same time. Each refresh creates a new session since there are no user accounts in the demo app.

            ### Cars
            #### Description
            Small demo app where the user can analyse  the count of cars in Finland, divided by type and power source. Data preparation was done in Azure Databricks with Spark, as I wanted to learn more about the tech.

            #### Stack
            - Cloud platform: AWS, Microsoft Azure
            - Main libraries: Dash, Pandas, sqlalchemy
            - Database:  Moved from Azure serverless to AWS PostgreSQL on (11.12.2023)
            - Data preparation: Azure Databricks, Spark
            - Nice to know: Database was originally in Azure Databricks. It was moved for  cost reasons.
                 ''')
],style={'margin-left': '30%','margin-right': '30%','margin-top': '3%'})