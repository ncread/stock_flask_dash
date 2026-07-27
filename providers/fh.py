#api limits: 30/second, 60/minute
import os
import finnhub
from dotenv import load_dotenv
from datetime import datetime, timedelta


load_dotenv()
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')

client = finnhub.Client(api_key=FINNHUB_API_KEY)


def get_finnhub_price(ticker: str):
    features = {}
    quote = client.quote(ticker)
    features['price'] = quote['c']
    features['change'] = quote['d']
    features['percent_change'] = quote['dp']

    return features

def get_finnhub_metrics(ticker: str) -> dict:
    '''
    Extracts forward PE ratio, forward PEG ratio, PE TTM (trailing 12 months), PEG TTM
    inputs: Finnhub client connection, ticker
    output: dictionary (metric: value)
    '''

    fh_results = {}
    fh_metrics = ['forwardPE','forwardPEG', 'peTTM', 'pegTTM']
    data = client.company_basic_financials(ticker, 'all')
    fh_data = data['metric']
    for metric in fh_metrics:
        fh_results[metric] = fh_data.get(metric)

    return fh_results


def get_finnhub_earnings(ticker: str):
    '''
    Extracts the upcoming earnings information for the next 90 days and grabs the next earnings date, if it's before open or after close, and the estimated earnings per share
    inputs: Finnhub client connection, ticker
    outputs: dictionary (metric: value)
    '''

    today = datetime.today()
    future = today + timedelta(days=90)

    fh_metrics = ['date','hour','epsEstimate']

    data = client.earnings_calendar(_from=today.strftime("%Y-%m-%d"),to=future.strftime("%Y-%m-%d"),symbol=ticker)
    fh_earnings = data['earningsCalendar'][0]

    return {metric:value for metric,value in fh_earnings.items() if metric in fh_metrics}