import pandas as pd
import numpy as np
import yfinance as yf
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# Access databse environment variables
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

def get_raw_price_data(tickers:list) -> (pd.DataFrame, set):
    # ACWI or All Country Wide Index is an index with global equity exposure
    # and used here as the market
    tickers.append('ACWI')
    prices5y = yf.download(tickers=tickers, period='5y')
    prices = prices5y['Adj Close'].dropna(axis=1, how='all').dropna(axis=0)
    not_found_tickers = set(tickers).difference(set(prices.columns))
    prices.rename(columns={'ACWI':'Market'}, inplace = True)

    if all(ticker in prices.columns for ticker in tickers):
        return prices, not_found_tickers
    else:
        return prices, not_found_tickers

def calculate_key_figures(contribution:pd.Series) -> (pd.DataFrame, set):
    prices, not_found_tickers = get_raw_price_data(contribution.index.tolist())
    # One month historcal volatility using 21 trading days per month
    daily_returns = prices.pct_change().dropna()
    vol_scale_1mo= np.sqrt(21)
    historical_volatility_1mo =  daily_returns.std() * vol_scale_1mo

    # Capital Asset Pricing Model
    risk_free_rate = yf.download('^IRX', period='1mo')['Adj Close'].values[-1] / 100
    mean_daily_returns = daily_returns.mean()
    mean_annual_returns = (1 + mean_daily_returns)**252 - 1
    returns_correlation_matrix = daily_returns.corr()
    betas = returns_correlation_matrix['Market'] * ( daily_returns.var() / daily_returns['Market'].var())
    expected_returns = risk_free_rate + betas * (mean_annual_returns['Market'] - risk_free_rate)

    contribution = contribution[~contribution.index.isin(not_found_tickers)]
    weights = contribution / contribution.sum()

    key_figures = pd.DataFrame({
        'historical_return': mean_annual_returns,
        'historical_volatility': historical_volatility_1mo,
        'beta': betas,
        'expected_return': expected_returns,
        'risk_free_rate': [risk_free_rate] * len(prices.columns),
        'weight': weights,
        'amount': contribution
    })
    key_figures = key_figures.drop(index='Market')

    # Portfolio values
    daily_returns_no_market = daily_returns.loc[:, daily_returns.columns !='Market']
    covariance_matrix = daily_returns_no_market.cov()
    portfolio_historical_returns = (key_figures['historical_return'] * weights).sum()
    portfolio_historical_volatility = np.sqrt(weights.T.dot(covariance_matrix).dot(weights))*np.sqrt(21)
    portfolio_beta = (key_figures['beta'] * weights).sum()
    portfolio_expected_returns = (key_figures['expected_return'] * weights).sum()
    
    key_figures.loc['Portfolio'] = {
        'historical_return': portfolio_historical_returns,
        'historical_volatility': portfolio_historical_volatility,
        'beta': portfolio_beta,
        'expected_return': portfolio_expected_returns,
        'risk_free_rate': risk_free_rate,
        'weight': 1.0,
        'amount': contribution.sum()
    }
    return key_figures, not_found_tickers

def calculate_expected_returns(currentPrice, expectedReturn, volatility, periodLenghtInYears, z) -> (np.ndarray, np.ndarray, np.ndarray):
    """
    Returns the mean, lower bound and higher bound for future prices based on
    geometric brownian motion.

    example: calculate_expected_returns(10,8.0,0.2,10,1.96)
    """
    expectedReturn = expectedReturn
    periodLenghtinDays = int(periodLenghtInYears*365.25)
 
    futurePricesLn = np.array([np.log(currentPrice)]*periodLenghtinDays)
    confidenceIntervalsLn = np.array([z*volatility] * periodLenghtinDays)
    futurePricesLn = futurePricesLn + (np.arange(1, periodLenghtinDays+1)/365.25)*(expectedReturn - (volatility**2)/2)
    confidenceIntervalsLn = confidenceIntervalsLn * np.sqrt(np.arange(1,periodLenghtinDays+1)/365.25)
    futurePrices = np.exp(futurePricesLn)
    confidenceIntervalLow = np.exp(futurePricesLn - confidenceIntervalsLn)
    confidenceIntervalHigh = np.exp(futurePricesLn + confidenceIntervalsLn)
    return futurePrices, confidenceIntervalLow, confidenceIntervalHigh

def get_saved_portfolio(portfolio_name:str, session_id:str) -> pd.DataFrame:
    query = f"""
        with session_portfolios as (
        select 
        portfolio_id,
        ticker,
        historical_return,
        historical_volatility,
        beta,
        expected_return,
        risk_free_rate,
        weight,
        amount
        from portfolio_builder.portfolios
        where session_id = '{session_id}'
        ),

        union_portfolios AS (
            select *
            from portfolio_builder.example_portfolios
            union
            select *
            from session_portfolios
        )

        select *
        from union_portfolios
        where portfolio_id = '{portfolio_name}'
        order by amount asc
    """
    return pd.read_sql(query, con=engine)

def get_portfolio_names(session_id:str) -> pd.DataFrame:
    query = f"""
        with session_portfolios as (
        select distinct portfolio_id from portfolio_builder.portfolios
        where session_id = '{session_id}'
        )

        select distinct portfolio_id from portfolio_builder.example_portfolios
        union
        select * from session_portfolios

    """
    return pd.read_sql(query, con=engine)

def save_portfolio_to_db(contribution:pd.Series, portfolio_id:str, session_id:str):
    key_figures, not_found_tickers = calculate_key_figures(contribution=contribution)
    if len(key_figures) > 1:
        key_figures = key_figures.reset_index()
        key_figures.rename(columns={'index': 'ticker'}, inplace=True)
        key_figures.insert(0, 'portfolio_id', portfolio_id)
        key_figures.insert(0, 'session_id', session_id)
        key_figures.to_sql('portfolios', engine,schema='portfolio_builder', if_exists='append', index=False)
        return not_found_tickers
    return not_found_tickers

def remove_portfolio_from_db(portfolio_id:str, session_id:str):
    remove_query = text(f"delete from portfolio_builder.portfolios where portfolio_id = '{portfolio_id}' and session_id = '{session_id}';")
    with engine.connect() as connection:
        connection.execute(remove_query)
        connection.commit()

def remove_all_portfolios_from_db(session_id:str):
    truncate_query = text(f"delete from portfolio_builder.portfolios where session_id = '{session_id}';")
    with engine.connect() as connection:
        connection.execute(truncate_query)
        connection.commit()

def get_cars_table()-> pd.DataFrame:
    return pd.read_sql("select * from cars_demo.cars", con=engine)