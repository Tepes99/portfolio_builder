#%%
import pandas as pd
import numpy as np
import datetime as dt
import yfinance as yf

#All_country_world_index = yf.download(tickers='ACWI', period='5y')['Adj Close']

def get_raw_price_data(tickers:list)-> pd.DataFrame:
    # ACWI or All Country Wide Index is an index with global equity exposure
    # and used here as the market
    tickers.append('ACWI')
    prices5y = yf.download(tickers=tickers, period='5y')
    prices = prices5y['Adj Close']
    prices.rename(columns={'ACWI':'Market'}, inplace = True)
    return prices

#%%
def calculate_key_figures(contribution:pd.Series) -> pd.DataFrame:
    prices = get_raw_price_data(contribution.index.tolist())
    # One month historcal volatility using 21 trading days per month
    daily_returns = prices.pct_change().dropna()
    vol_scale_1mo= np.sqrt(21)
    historical_volatility_1mo =  daily_returns.std() * vol_scale_1mo

    # Capital Asset Pricing Model
    risk_free_rate = yf.download('^IRX', period='1d')['Adj Close'].values[0] / 100
    mean_daily_returns = daily_returns.mean()
    mean_annual_returns = (1 + mean_daily_returns)**252 - 1
    returns_correlation_matrix = daily_returns.corr()
    betas = returns_correlation_matrix['Market'] * ( daily_returns.var() / daily_returns['Market'].var())
    expected_returns = risk_free_rate + betas * (mean_annual_returns['Market'] - risk_free_rate)

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
    return key_figures

# %%
tlist=['MSFT', 'AAPL', 'SPY', 'F', 'TSLA']
pf = get_raw_price_data(tickers=tlist)
# %%
contribution = pd.Series({
    'MSFT':100,
    'AAPL':500,
    'SPY':200,
    'F':100,
    'TSLA':50,
})
# %%
key_figures = calculate_key_figures(contribution)
# %%
