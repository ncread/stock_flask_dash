import os
import boto3
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from providers import fh, fmp, tiingo
# from concurrent.futures import ThreadPoolExecutor
from cache import price_cache, feature_cache


load_dotenv()
ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')


s3 = boto3.client(
    service_name="s3",
    endpoint_url="https://f2050c9eff5c17ffb10f5e72a0a973b2.r2.cloudflarestorage.com",
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=SECRET_ACCESS_KEY,
    region_name="auto",
)


ticker_list = ['NVDA','AAPL','RGTI']
yesterday = (datetime.now() - timedelta(hours=24))

def get_features(ticker):
    if ticker in feature_cache: #if in cache, return contents
        print(f'Features for {ticker} present in cache.')
        return feature_cache[ticker]
    
    print(f'Features for {ticker} not present in cache.')

    exists, mod_date = check_file_in_bucket('stocks-r2', 'features', ticker, 'json')

    if exists and mod_date >= yesterday:
        print('File exists in cloud and has been updated in the past 24 hrs. Loading it now...')
        #load from R2
        #save to cache
    else:
        print('File is either outdated or not present. Fetching new data...')
        fh_metrics = fh.get_finnhub_metrics(ticker)
        fh_earnings = fh.get_finnhub_earnings(ticker)
        fmp_metrics = fmp.get_fmp_profile(ticker)
        metrics = fh_metrics | fh_earnings | fmp_metrics
        #save to R2 
        # feature_cache[ticker] = metrics #save to cache





###BUCKET FUNCTIONS------
def push_to_bucket(bucket: str, ticker: str, key: str):
    pass


def pull_from_bucket():
    pass

def check_file_in_bucket(bucket, key, ticker, file_type):
    try:
        response = s3.head_object(Bucket=bucket, Key=f'{key}/{ticker}.{file_type}')
        return True, response['LastModified']
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f'Error: {ticker}.parquet not found')
        elif error_code == '403':
            print('Error: Access denied')
        else:
            print('An unexpected error occurred')
        return False, None


# def pull_from_bucket(bucket: str, ticker: str, key: str):
#     #first check historical price folder in bucket for existence of parquet file
#     if not check_bucket(bucket, ticker, 'historical_price'):
#         # historical info not present at all, so use tiingo to snag the full history
#         price_json = tiingo.get_prices(ticker, '1980-01-01')
#         # need to transform json to parquet here, then return it
#     elif check_bucket(bucket, ticker, 'historical_price') < yesterday:
#         price_json = tiingo.get_prices(ticker, yesterday)