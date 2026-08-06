#api limits: 500 unique symbols/month, 50/hr, 1000/day, 2GB/month
import os
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()
TIINGO_API_KEY = os.getenv('TIINGO_API_KEY')

session = requests.Session()


def get_prices(ticker: str, start_date=None, end_date=None) -> dict:
    url = f'https://api.tiingo.com/tiingo/daily/{ticker}/prices'
    params = {'token': TIINGO_API_KEY,
              'format': 'json'}
    
    if start_date:
        params['startDate'] = start_date
    if end_date:
        params['endDate'] = end_date
    
    response = session.get(url, params=params)
    df = calculate_features(response.json())

    cols = ['date','adjClose','adjHigh','adjLow','adjOpen','adjVolume','SMA10','SMA50','SMA200','EMA10','EMA50','EMA200','UpperBB','LowerBB']

    df = df[cols]

    return df


def calculate_features(prices_json: dict) -> pd.DataFrame:
    '''do the SMA, EMA, BB calcs here'''
    df = pd.DataFrame(prices_json)

    #simple moving average
    df['SMA10'] = df['adjClose'].rolling(window=10).mean()
    df['SMA50'] = df['adjClose'].rolling(window=50).mean()
    df['SMA200'] = df['adjClose'].rolling(window=200).mean()
    #exponential moving average (more weight to recent prices)
    df['EMA10'] = df['adjClose'].ewm(span=10).mean()
    df['EMA50'] = df['adjClose'].ewm(span=50).mean()
    df['EMA200'] = df['adjClose'].ewm(span=200).mean()
    #Bollinger bands: 2 std devs above&below 20 day SMA
    df['UpperBB'] = df['adjClose'].rolling(window=20).mean() + (df['adjClose'].rolling(20).std() * 2)
    df['LowerBB'] = df['adjClose'].rolling(window=20).mean() - (df['adjClose'].rolling(20).std() * 2)

    df['date'] = pd.to_datetime(df['date']).dt.date
    return df


# a = get_prices('AAPL', start_date='2026-07-27') #with no date arguments, you get just the most recent day of info
# print(a)