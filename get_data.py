import json
import pandas as pd
from datetime import date, datetime, timedelta, timezone

#other files
from providers import fh, fmp, tiingo
import storage
from cache import price_cache, feature_cache



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

yesterday = (datetime.now(timezone.utc) - timedelta(hours=24))
time_minus_twelve = (datetime.now(timezone.utc) - timedelta(hours=12))


def get_features(ticker: str, bucket: str) -> dict:

    if ticker in feature_cache: #if in cache, return contents
        print(f'Features for {ticker} present in cache')
        return {ticker: feature_cache[ticker]}
    
    print(f'Features for {ticker} NOT present in cache')

    #check cloud bucket
    exists, mod_date = storage.check_file_in_bucket(bucket, 'features', ticker, 'json')

    if exists and mod_date >= yesterday:
        print('File exists in cloud and has been updated in the past 24 hrs. Loading it now...')
        #load from R2
        # response = s3.get_object(Bucket=bucket, Key=f'features/{ticker}.json')
        # metrics = json.loads(response['Body'].read().decode('utf-8'))
        metrics = storage.load_json(bucket, f'features/{ticker}.json')
        feature_cache[ticker] = metrics
        print(f'{ticker}.json pulled from cloud and added to cache')
        return {ticker: metrics}
    else:
        print(f'File is either outdated or not present. Fetching new features data for {ticker}...')
        fh_metrics = fh.get_finnhub_metrics(ticker)
        fh_earnings = fh.get_finnhub_earnings(ticker)
        fmp_metrics = fmp.get_fmp_profile(ticker)
        fresh_metrics = fh_metrics | fh_earnings | fmp_metrics
        print(f'{ticker} data successfully obtained')
        # s3.put_object(Bucket=bucket, Key=f'features/{ticker}.json', Body=json.dumps(fresh_metrics), ContentType='application/json')
        storage.save_json(bucket, f'features/{ticker}.json', json.dumps(fresh_metrics))
        feature_cache[ticker] = fresh_metrics
        print(f'Features for {ticker} successfully saved to cloud and cache')
        return {ticker: fresh_metrics}


def get_prices(ticker: str, bucket: str, time_period: str):
    '''
    In
    '''
    ticker = ticker.upper()

    if ticker in price_cache:
        print(f'Historical prices for {ticker} present in cache')
        df = price_cache[ticker]
        cutoff_date = df['date'].max() - timedelta(days=time_lookup[time_period]+1)
        return df[df['date'] >= cutoff_date]

    print(f'Historical prices for {ticker} NOT present in cache')

    #check cloud bucket
    exists, mod_date = storage.check_file_in_bucket(bucket, 'prices', ticker, 'parquet')

    if exists and mod_date >= time_minus_twelve:
        print('File exists in cloud and has been updated in the past 12 hrs. Loading it now...')
        #load from R2
        df = storage.load_parquet(bucket, f'prices/{ticker}.parquet')
        price_cache[ticker] = df
        print(f'{ticker}.parquet pulled from cloud and added to cache')

        cutoff_date = df['date'].max() - timedelta(days=time_lookup[time_period]+1)
        return df[df['date'] >= cutoff_date]

    elif not exists:
        print(f'No parquet file exists for {ticker}. Fetching full price history now...')
        df = tiingo.get_prices(ticker, start_date='1980-01-01')
        price_cache[ticker] = df
        storage.save_parquet(bucket, f'prices/{ticker}.parquet', df)
        print(f'Full pricing history saved for {ticker}')

        cutoff_date = df['date'].max() - timedelta(days=time_lookup[time_period]+1)
        return df[df['date'] >= cutoff_date]
    
    else:
        print(f'File for {ticker} is out of date. Updating the price history now...', end='')
        stored_daily_prices = storage.load_parquet(bucket, f'prices/{ticker}.parquet')
        start_idx = len(stored_daily_prices) -1 #pre-concatenation, figuring out where to begin computing engineered features
        latest_date = stored_daily_prices['date'].max()

        new_daily_prices = tiingo.get_prices(ticker, start_date=latest_date+timedelta(hours=24))
        new_latest_date = new_daily_prices['date'].max()
        print(f'Prices were saved through {latest_date}...Now updated through {new_latest_date}')

        updated_df = pd.concat([stored_daily_prices, new_daily_prices], ignore_index=True)
        updated_df = tiingo.compute_appended_features(updated_df, start_idx)
        price_cache[ticker] = updated_df
        storage.save_parquet(bucket, f'prices/{ticker}.parquet', updated_df)
        print(f'Fetched updated prices, appended dataframe, saved to cloud and cache')

        cutoff_date = updated_df['date'].max() - timedelta(days=time_lookup[time_period]+1)
        return updated_df[updated_df['date'] >= cutoff_date]


# print('NVDA Run 1')
# print(get_features('NVDA', 'stocks-r2'))
# print(get_prices('IBM', 'stocks-r2', '1mo'))


