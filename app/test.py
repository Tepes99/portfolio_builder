#%%
import pandas as pd
import numpy as np
import datetime as dt
import yfinance as yf
import ETL
#%%
#All_country_world_index = yf.download(tickers='ACWI', period='5y')['Adj Close']

def get_raw_price_data1(tickers:list)-> pd.DataFrame:
    # ACWI or All Country Wide Index is an index with global equity exposure
    # and used here as the market
    tickers.append('ACWI')
    prices5y = yf.download(tickers=tickers, period='5y')
    prices = prices5y['Adj Close']
    prices.rename(columns={'ACWI':'Market'}, inplace = True)
    return prices

#%%
def calculate_key_figures(contribution:pd.Series) -> pd.DataFrame:
    prices, not_found_tickers = get_raw_price_data(contribution.index.tolist())
    # One month historcal volatility using 21 trading days per month
    daily_returns = prices.pct_change().dropna()
    vol_scale_1mo= np.sqrt(21)
    historical_volatility_1mo =  daily_returns.std() * vol_scale_1mo

    # Capital Asset Pricing Model
    risk_free_rate = yf.download('^IRX', period='1mo')['Adj Close'].values[0] / 100
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

# %%
tlist=['MSFT', 'AAPL', 'SPY', 'F', 'TSLA']
pf = get_raw_price_data1(tickers=tlist)
# %%
contribution = pd.Series({
    'AAPL':100,
    'BRK-A':500,
    'ASD':200,
    'AXP':100,
    'KO':50,
})
# %%
key_figures, not_found = calculate_key_figures(contribution)

# %%
import numpy as np
def calculate_expected_returns(currentPrice, expectedReturn, volatility, periodLenghtInYears, z) -> (np.ndarray,np.ndarray,np.ndarray):
    """
    Returns the mean, lower bound and higher bound for future prices based on
    geometric brownian motion.

    example: calculate_expected_returns(10,8.0,0.2,10,1.96)
    """
    expectedReturn = expectedReturn/100
    periodLenghtinDays = int(periodLenghtInYears*365.25)
 
    futurePricesLn = np.array([np.log(currentPrice)]*periodLenghtinDays)
    confidenceIntervalsLn = np.array([z*volatility] * periodLenghtinDays)
    futurePricesLn = futurePricesLn + (np.arange(1, periodLenghtinDays+1)/365.25)*(expectedReturn - (volatility**2)/2)
    confidenceIntervalsLn = confidenceIntervalsLn * np.sqrt(np.arange(1,periodLenghtinDays+1)/365.25)
    futurePrices = np.exp(futurePricesLn)
    confidenceIntervalLow = np.exp(futurePricesLn - confidenceIntervalsLn)
    confidenceIntervalHigh = np.exp(futurePricesLn + confidenceIntervalsLn)
    return futurePrices, confidenceIntervalLow, confidenceIntervalHigh

# %%
fprices, ci_low, ci_high = ETL.calculate_expected_returns(10,8.0,0.2,10,1.96)
# %%
import yfinance as yf
yf.download('^IRX', period='1mo')['Adj Close'][-1] / 100
# %%
import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
# %%
load_dotenv()

# Access environment variables
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

# Create a Pandas DataFrame and SQLAlchemy engine as before
data = {
    'portfolio_id': ['portfolio2', 'portfolio3'],
    'ticker': ['AAPL', 'GOOGL'],
    'historical_return': [0.15, 0.12],
    'historical_volatility': [0.25, 0.18],
    'beta': [1.2, 0.9],
    'expected_return': [0.12, 0.11],
    'risk_free_rate': [0.03, 0.02],
    'weight': [0.2, 0.3],
    'amount': [10000.0, 15000.0]
}
df = pd.DataFrame(data)

engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

# Insert the DataFrame into the PostgreSQL database
table_name = 'portfolios'
df.to_sql(table_name, engine,schema='portfolio_builder', if_exists='append', index=False)
# %%

query = 'select distinct portfolio_id from portfolio_builder.portfolios'

saved_portfolios = pd.read_sql(query, con=engine)
# %%
example_pf = key_figures.reset_index()
example_pf.rename(columns={'index': 'ticker'}, inplace=True)
example_pf.insert(0, 'portfolio_id', 'example2')
# %%
example_pf.to_sql('example_portfolios', engine,schema='portfolio_builder', if_exists='append', index=False)
# %%
def get_saved_portfolio(portfolio_name:str) -> pd.DataFrame:
    query = f"""
        select * from (
        select * from portfolio_builder.example_portfolios
        union
        select * from portfolio_builder.portfolios) t
        where portfolio_id = '{portfolio_name}'
    """
    return pd.read_sql(query, con=engine)
# %%
ex1 = get_saved_portfolio('example1')
# %%
def get_portfolio_names() -> pd.DataFrame:
    query = f"""
        select distinct portfolio_id from portfolio_builder.example_portfolios
        union
        select distinct portfolio_id from portfolio_builder.portfolios
    """
    return pd.read_sql(query, con=engine)
# %%
def save_portfolio_to_db(contribution:pd.Series, portfolio_id:str):
    key_figures = calculate_key_figures(contribution=contribution)
    key_figures = key_figures.reset_index()
    key_figures.rename(columns={'index': 'ticker'}, inplace=True)
    key_figures.insert(0, 'portfolio_id', portfolio_id)
    key_figures.to_sql('portfolios', engine,schema='portfolio_builder', if_exists='append', index=False)
# %%
import yfinance as yf
tickers = ['AAPL', 'ASD', 'GOOGL', 'XYZ']  # Replace with your list of tickers
not_found_tickers = []

for ticker in tickers:
    try:
        data = yf.download(ticker, start="2023-01-01", end="2023-08-01")  # Adjust the date range as needed
    except Exception as e:
        print(f"Ticker {ticker} not found: {e}")
        not_found_tickers.append(ticker)
print("Tickers not found:", not_found_tickers)


# %%
data = yf.download(tickers)['Adj Close']
# %%
def get_raw_price_data(tickers:list):
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


# %%
from sqlalchemy import create_engine, text
import os
import pandas as pd
from dotenv import load_dotenv
# %%
load_dotenv()

# Access environment variables
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')
def remove_all_portfolios_from_db():
    truncate_query = text(f"truncate portfolio_builder.portfolios;")
    with engine.connect() as connection:
        connection.execute(truncate_query)
        connection.commit()
# %%