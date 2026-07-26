import os
import boto3
from datetime import date, timedelta
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from providers import fh, fmp, tiingo
# from concurrent.futures import ThreadPoolExecutor
from cachetools import TTLCache

load_dotenv()
ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')

price_cache = TTLCache(maxsize=500, ttl=60*60*24) # hrs
feature_cache = TTLCache(maxsize=500, ttl=60*60*24) #24 hrs

s3 = boto3.client(
    service_name="s3",
    endpoint_url="https://f2050c9eff5c17ffb10f5e72a0a973b2.r2.cloudflarestorage.com",
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=SECRET_ACCESS_KEY,
    region_name="auto",
)


def upload_to_bucket(bucket: str, ticker: str, key: str):
    pass


def pull_from_bucket():
    pass


def check_bucket_data(bucket: str, ticker: str, key: str):
    try:
        response = s3.head_object(Bucket=bucket, Key=f'{key}/{ticker}.parquet')
        last_modified = response['LastModified']
        return last_modified #previously updated date
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f'Error: {ticker}.parquet not found')
        elif error_code == '403':
            print('Error: Access denied')
        else:
            print('An unexpected error occurred')
        return None


yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')

def pull_missing_prices(bucket: str, ticker: str):
    #first check historical price folder in bucket for existence of parquet file
    if not check_bucket_data(bucket, ticker, 'historical_price'):
        # historical info not present at all, so use tiingo to snag the full history
        price_json = tiingo.get_prices(ticker, '1980-01-01')
        # need to transform json to parquet here, then return it
    elif check_bucket_data(bucket, ticker, 'historical_price') < yesterday:
        price_json = tiingo.get_prices(ticker, yesterday)