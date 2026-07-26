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
    return response.json()


def calculate_features(prices_json: dict) -> pd.DataFrame:
    '''do the SMA, EMA, BB calcs here'''
    pass


# print(get_prices('NVDA')) #with no date arguments, you get the most recent day of info
