#api limits: 250/day, 0.5GB/month
import os
import requests
from dotenv import load_dotenv

load_dotenv()
FMP_API_KEY = os.getenv('FMP_API_KEY')

session = requests.Session()


def format_metric(metric: int) -> str:
    '''
    Adds labels (trillion/billion/million) to raw market cap and trading volume numbers
    input: integer
    output: string of number + label (T/B/M)
    '''

    if metric > 1000000000000:
        return f'{round(metric / 1000000000000, 2)}T'
    elif metric > 1000000000:
        return f'{round(metric / 1000000000,2)}B'
    elif metric > 1000000:
        return f'{round(metric / 1000000,2)}M'
    else:
        return str(metric)


def get_fmp_profile(ticker: str):
    '''
    Hits the /profile FMP endpoint for full company name, current price, market cap, and beta features
    inputs: requests session, ticker, FMP api key
    output: dictionary {metric:value}
    '''

    fmp_results = {}
    # 'price','change','changePercentage'
    fmp_profile_metrics = ['companyName','marketCap','beta','range','averageVolume']
    profile_url = 'https://financialmodelingprep.com/stable/profile'
    params = {'symbol': ticker,
              'apikey': FMP_API_KEY}
    profile_response = session.get(profile_url, params=params)
    profile_data = profile_response.json()[0]

    for metric in fmp_profile_metrics:
        fmp_results[metric] = profile_data[metric]

    fmp_results['marketCap'] = format_metric(fmp_results['marketCap'])
    fmp_results['averageVolume'] = format_metric(fmp_results['averageVolume'])
    
    return fmp_results