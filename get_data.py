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


def get_features(ticker: str, bucket: str) -> dict:
    yesterday = (datetime.now(timezone.utc) - timedelta(hours=24))

    fh_price = fh.get_finnhub_price(ticker) #grab updated price regardless of cache/cloud situation

    if ticker in feature_cache: #if in cache, return contents
        print(f'Features for {ticker} present in cache')
        all_features = feature_cache[ticker] | fh_price
        return all_features
    
    print(f'Features for {ticker} NOT present in cache')

    #check cloud bucket
    exists, mod_date = storage.check_file_in_bucket(bucket, 'features', ticker, 'json')

    if exists and mod_date >= yesterday:
        print('JSON file exists in cloud and has been updated in the past 24 hrs. Loading it now...')
        #load from R2
        metrics = storage.load_json(bucket, f'features/{ticker}.json')
        feature_cache[ticker] = metrics
        all_features = metrics | fh_price
        print(f'{ticker}.json pulled from cloud and added to cache')
        return all_features
    
    else:
        print(f'JSON file is either outdated or not present. Fetching new features data for {ticker}...')
        fh_metrics = fh.get_finnhub_metrics(ticker)
        fh_earnings = fh.get_finnhub_earnings(ticker)
        fmp_metrics = fmp.get_fmp_profile(ticker)
        fresh_metrics = fh_metrics | fh_earnings | fmp_metrics
        print(f'{ticker} data successfully obtained')
        storage.save_json(bucket, f'features/{ticker}.json', json.dumps(fresh_metrics))
        feature_cache[ticker] = fresh_metrics
        all_features = fresh_metrics | fh_price
        print(f'Features for {ticker} successfully saved to cloud and cache')
        return all_features


def get_prices(ticker: str, bucket: str, time_period: str) -> pd.DataFrame:
    '''
    inputs: ticker, bucket, time period
    output: dataframe with historical pricing specified by the time period input
    '''
    time_minus_twelve = (datetime.now(timezone.utc) - timedelta(hours=12))

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
        print('Parquet file exists in cloud and has been updated in the past 12 hrs. Loading it now...')
        #load from R2
        df = storage.load_parquet(bucket, f'prices/{ticker}.parquet')
        price_cache[ticker] = df
        print(f'{ticker}.parquet pulled from cloud and added to cache')

        cutoff_date = df['date'].max() - timedelta(days=time_lookup[time_period]+1)
        return df[df['date'] >= cutoff_date]

    elif not exists:
        print(f'No parquet file exists for {ticker}. Fetching full price history now...')
        df_raw = tiingo.get_prices(ticker, start_date='1980-01-01')
        df = tiingo.compute_features(df_raw)
        price_cache[ticker] = df
        storage.save_parquet(bucket, f'prices/{ticker}.parquet', df)
        print(f'Full pricing history saved for {ticker}')

        cutoff_date = df['date'].max() - timedelta(days=time_lookup[time_period]+1)
        return df[df['date'] >= cutoff_date]
    
    else: #file has not been updated in the past 12 hrs
        print(f'Parquet file for {ticker} is out of date. Updating the price history now...', end='')
        stored_daily_prices = storage.load_parquet(bucket, f'prices/{ticker}.parquet')
        start_idx = len(stored_daily_prices) -1 #pre-concatenation, figuring out where to begin computing engineered features
        latest_date = stored_daily_prices['date'].max()
        # return latest_date + timedelta(hours=24)
        new_daily_prices = tiingo.get_prices(ticker, start_date=latest_date+timedelta(hours=24)) 

        if new_daily_prices.empty: #still no new pricing info, so just return what was already present
            print(f'No new available prices for {ticker}. Returning the stored data...')
            price_cache[ticker] = stored_daily_prices
            cutoff_date = stored_daily_prices['date'].max() - timedelta(days=time_lookup[time_period]+1)
            return stored_daily_prices[stored_daily_prices['date'] >= cutoff_date]

        new_latest_date = new_daily_prices['date'].max()
        print(f'Prices were saved through {latest_date}...Now updated through {new_latest_date}')

        updated_df = pd.concat([stored_daily_prices, new_daily_prices], ignore_index=True)
        updated_df = tiingo.compute_features(updated_df, start_idx)

        price_cache[ticker] = updated_df
        storage.save_parquet(bucket, f'prices/{ticker}.parquet', updated_df)
        print(f'Fetched updated prices, appended dataframe, saved to cloud and cache')

        cutoff_date = updated_df['date'].max() - timedelta(days=time_lookup[time_period]+1)
        return updated_df[updated_df['date'] >= cutoff_date]

# print(get_features('XYZ', 'stocks-r2'))