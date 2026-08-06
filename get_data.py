import os
import json
import boto3
import pandas as pd
from datetime import date, datetime, timedelta, timezone
from dotenv import load_dotenv
from botocore.exceptions import ClientError

from providers import fh, fmp, tiingo
import storage
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

#fix this, it counts these as market open days, so 1mo will include 30 market days, which is about a month and a half
time_lookup = {'5d': 5, 
               '1mo': 30, 
               '3mo': 90, 
               '6mo': 182, 
               '1y': 365, 
               'ytd': date.today().timetuple().tm_yday, 
               '2y': 730, 
               '5y': 1825, 
               '10y': 3650}

ticker_list = ['NVDA','AAPL','RGTI']
yesterday = (datetime.now(timezone.utc) - timedelta(hours=24))

def get_features(ticker, bucket):
    ticker = ticker.upper()
    if ticker in feature_cache: #if in cache, return contents
        print(f'Features for {ticker} present in cache')
        return feature_cache[ticker]
    
    print(f'Features for {ticker} NOT present in cache')

    #check cloud bucket
    exists, mod_date = check_file_in_bucket(bucket, 'features', ticker, 'json')

    if exists and mod_date >= yesterday:
        print('File exists in cloud and has been updated in the past 24 hrs. Loading it now...')
        #load from R2
        response = s3.get_object(Bucket=bucket, Key=f'features/{ticker}.json')
        features = json.loads(response['Body'].read().decode('utf-8'))
        feature_cache[ticker] = features
        print(f'{ticker}.json pulled from cloud and added to cache')
        return features
    else:
        print(f'File is either outdated or not present. Fetching new features data for {ticker}...')
        fh_metrics = fh.get_finnhub_metrics(ticker)
        fh_earnings = fh.get_finnhub_earnings(ticker)
        fmp_metrics = fmp.get_fmp_profile(ticker)
        fresh_metrics = fh_metrics | fh_earnings | fmp_metrics
        print(f'{ticker} data successfully obtained')
        s3.put_object(Bucket=bucket, Key=f'features/{ticker}.json', Body=json.dumps(fresh_metrics), ContentType='application/json')
        feature_cache[ticker] = fresh_metrics
        print(f'Features for {ticker} successfully saved to cloud and cache')
        return fresh_metrics


def get_prices(ticker, bucket, time_period):
    #this function needs to incorporate the time aspect, checking the most recent price date of the content within the bucket parquet file and only pulling the missing info, then adding that info to the parquet file. But also, the user inputs a time period, so based on that input, the output contains only the time range specified.
    ticker = ticker.upper()

    if ticker in price_cache:
        print(f'Historical prices for {ticker} present in cache')
        return price_cache[ticker].iloc[-(time_lookup[time_period]):]

    print(f'Historical prices for {ticker} NOT present in cache')

    #check cloud bucket
    exists, mod_date = check_file_in_bucket(bucket, 'prices', ticker, 'parquet')

    if exists and mod_date >= yesterday: #prices are updated as 
        print('File exists in cloud and has been updated in the past 24 hrs. Loading it now...')
        #load from R2
        df = storage.load_parquet(f'prices/{ticker}.parquet', s3, bucket)
        price_cache[ticker] = df
        print(f'{ticker}.parquet pulled from cloud and added to cache')
        return df.iloc[-(time_lookup[time_period]):]

    elif not exists:
        print(f'No parquet file exists for {ticker}. Fetching full price history now...')
        df = tiingo.get_prices(ticker, start_date='1900-01-01')
        price_cache[ticker] = df
        storage.save_parquet(df, f'prices/{ticker}.parquet', s3, bucket)
        return df.iloc[-(time_lookup[time_period]):]
    
    else:
        stored_daily_prices = storage.load_parquet(f'prices/{ticker}.parquet', s3, bucket)
        latest_date = stored_daily_prices['date'].max()
        print(f'Updated through {latest_date}. Fetching most recent prices...')
        new_daily_prices = tiingo.get_prices(ticker, start_date=latest_date+timedelta(hours=24))

        updated_df = pd.concat(stored_daily_prices, new_daily_prices)
        price_cache[ticker] = updated_df
        storage.save_parquet(updated_df, f'prices/{ticker}.parquet', s3, bucket)
        print(f'Fetched updated prices, appended dataframe, saved to cloud and cache')
        return updated_df.iloc[-(time_lookup[time_period]):]




###BUCKET FUNCTIONS------
# def push_to_bucket(bucket: str, ticker: str, key: str):
#     pass


# def pull_from_bucket():
#     pass

def check_file_in_bucket(bucket, key, ticker, file_type):
    try:
        response = s3.head_object(Bucket=bucket, Key=f'{key}/{ticker}.{file_type}')
        return True, response['LastModified']
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f'{ticker}.parquet NOT found in R2')
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

# print('NVDA Run 1')
# print(get_features('NVDA', 'stocks-r2'))
print(get_prices('AAPL', 'stocks-r2', '1mo'))
