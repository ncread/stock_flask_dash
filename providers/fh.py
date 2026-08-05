#api limits: 30/second, 60/minute
import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta


load_dotenv()
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')

base_url = 'https://api.finnhub.io/api/v1'
session = requests.Session()

def _get(endpoint: str, params: dict) -> dict:
    params['token'] = FINNHUB_API_KEY

    response = session.get(f'{base_url}/{endpoint}', params=params, timeout=20)
    response.raise_for_status()

    return response.json()


def get_finnhub_price(ticker: str) -> dict:
    data = _get('quote', {'symbol': ticker})
    return {'price': data['c'], 'change': data['d'], 'percent_change': data['dp']}


def get_finnhub_metrics(ticker: str) -> dict:
    metrics = ['forwardPE','forwardPEG', 'peTTM', 'pegTTM']

    data = _get('stock/metric', {'symbol': ticker, 'metric': 'all'})
    metric_data = data['metric']

    return {metric: metric_data.get(metric) for metric in metrics}


def get_finnhub_earnings(ticker: str) -> dict:
    today = datetime.today()
    future = today + timedelta(days=90)

    data = _get('calendar/earnings', {'symbol': ticker, 
                                      'from': today.strftime("%Y-%m-%d"),
                                      'to': future.strftime("%Y-%m-%d")})
    earnings = data.get('earningsCalendar', [])
    if not earnings:
        return {}
    next_earnings = earnings[0]

    metrics = ['date','hour','epsEstimate']

    return {metric: next_earnings.get(metric) for metric in metrics}