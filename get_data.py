import yfinance as yf
import pandas as pd
import plotly
import plotly.express as px
import requests

############################################
def get_historical_data(tickers, time_period):
    ''' input: list of stock tickers and (yfinance supported) time period string
            1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max, etc
        output: dataframe with yfinance historical data
    '''

    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})


    tickers = [i.upper() for i in tickers]
    frames = []
    # df = yf.download(tickers, period=time_period)

    for stock in tickers:
        t = yf.Ticker(stock, session=session)
        df = t.history(period=time_period, auto_adjust=False)
        df.columns = pd.MultiIndex.from_product([df.columns, [stock]])

        #daily change
        df[('Delta', stock)] = df[('Close', stock)].pct_change()
        #simple moving average (10,50,200 day)
        df[('SMA10', stock)] = df[('Close', stock)].rolling(window=10).mean()
        df[('SMA50', stock)] = df[('Close', stock)].rolling(window=50).mean()
        df[('SMA200', stock)] = df[('Close', stock)].rolling(window=200).mean()
        #exponential moving average (more weight to recent prices)
        df[('EMA10', stock)] = df[('Close', stock)].ewm(span=10).mean()
        df[('EMA50', stock)] = df[('Close', stock)].ewm(span=50).mean()
        df[('EMA200', stock)] = df[('Close', stock)].ewm(span=200).mean()
        #Bollinger bands: 2 std devs above&below 20 day SMA
        df[('UpperBB', stock)] = df[('Close', stock)].rolling(window=20).mean() + (df[('Close', stock)].rolling(20).std() * 2)
        df[('LowerBB', stock)] = df[('Close', stock)].rolling(window=20).mean() - (df[('Close', stock)].rolling(20).std() * 2)

        frames.append(df)
    return pd.concat(frames, axis=1).sort_index(axis=1)

#############################################
def create_returns(dataframe):
    '''
        input: output from get_historical_data function, grabs the Delta columns to create returns
        output: dataframe with time series returns
    '''
    chosen_stocks = dataframe.columns.get_level_values(1).unique()
    returns_list = [dataframe['Delta'][stock].rename(stock) for stock in chosen_stocks]
    returns_df = pd.concat(returns_list, axis=1)
    return returns_df

#############################################
def generate_corr_plot(df, ticker_list, time_period_corr):
    '''
        input: list of tickers, time period
        output: correlation matrix plot to be passed to html
    '''
    # data = yf.download(ticker_list, period=time_period_corr)['Close']
    data = df['Close']
    data.dropna(axis=1, how='all', inplace=True)
    returns = data.pct_change().dropna()
    corr_matrix = returns.corr()

    fig = px.imshow(corr_matrix, text_auto=True,
                    color_continuous_scale='RdBu_r', zmin=-1, zmax=1,
                    title=f'Correlation: Historical Return ({time_period_corr})')
    fig.update_layout(paper_bgcolor='rgb(184, 201, 223)', coloraxis_colorbar = dict(x=1.0),
                      autosize=True, xaxis_title=None, yaxis_title=None, margin=dict(r=0))
    corr_plot = plotly.io.to_html(fig, full_html=False)
    return corr_plot

#############################################
def get_metrics(ticker_list):
    '''
        input: list of tickers
        output: dictionary w/ tickers as keys, list of metrics as corresponding values
    '''
    # metrics_info = ['currentPrice','beta','marketCap']
    metrics_info = ['regularMarketPrice','beta','marketCap','trailingPE','forwardPE']
    stock_names = []
    values_list = []

    for i in ticker_list:
        stock_names.append(yf.Ticker(i).info.get('shortName'))
        metric_list = [yf.Ticker(i).info.get(j) for j in metrics_info]
        try:
            earnings_element = yf.Ticker(i).calendar.get('Earnings Date')
            earnings_date = str(earnings_element[0])
        except Exception as e:
            earnings_date = 'None'
        metric_list.append(earnings_date)
        values_list.append(metric_list)
        
        final_dict = dict(zip(stock_names, values_list))
    
    for i in final_dict.values():
        if i[2] is not None and i[2] > 1000000000000:
            i[2] = f'{round(i[2] / 1000000000000, 2)}T'
        elif i[2] is not None and i[2] > 1000000000:
            i[2] = f'{round(i[2] / 1000000000,2)}B'
        elif i[2] is not None and i[2] > 1000000:
            i[2] = f'{round(i[2] / 1000000,2)}M'
        else:
            pass

    return final_dict

#############################################
def get_time_series(df, ticker, time_period):
    '''
        input: output from get_historical_data function, takes a single ticker and time period
        output: plotly time series line chart for unique ticker/time period with Closing Prices, 
                SMAs, EMAs, and Bollinger Bands
    '''
    df_flat = df.copy()
    df_flat.columns = ['-'.join(col).strip() for col in df.columns.values]
    fig = px.line(df_flat, x=df_flat.index, 
                  y=[f'Close-{ticker}', f'SMA10-{ticker}', f'SMA50-{ticker}', f'SMA200-{ticker}',
                    f'EMA10-{ticker}', f'EMA50-{ticker}', f'EMA200-{ticker}',
                    f'UpperBB-{ticker}', f'LowerBB-{ticker}'],
                  title=f'${ticker} Historical Pricing - {time_period}', 
                  labels={'value':'Price/Share ($)', 'variable':f'${ticker} Metrics'})
    
    fig.update_layout(paper_bgcolor='rgb(184, 201, 223)')
    
    legend_names = ['Close', 'SMA10', 'SMA50', 'SMA200', 
                    'EMA10', 'EMA50', 'EMA200', 'UpperBB', 'LowerBB']
    for trace, name in zip(fig.data, legend_names):
        trace.name = name
        trace.legendgroup = name
        trace.hovertemplate = trace.hovertemplate.replace(trace.name, name)

    for i, trace in enumerate(fig.data):
        trace.visible = True if i < 3 else "legendonly"

    time_series_plot = plotly.io.to_html(fig, full_html=False)
    return time_series_plot


if __name__ == '__main__':
    pass