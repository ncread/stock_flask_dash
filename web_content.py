#this holds functions to construct the correlation plot (plot), metrics table (dict), and time series plot (plot)

import pandas as pd
import plotly
import plotly.express as px
import get_data

bucket = 'stocks-r2'


def combine_historical_data(tickers: list, time_period: str) -> pd.DataFrame:
    '''
        input: list of tickers inputted by user and specified time period
        output: dataframe constructed from concatenated individual ticker dataframes
    '''

    df_list = []
    for ticker in tickers:
        df = get_data.get_prices(ticker, bucket, time_period)
        df = df.set_index('date')
        df.columns = pd.MultiIndex.from_product([df.columns, [ticker]])
        df_list.append(df)

    return pd.concat(df_list, axis=1).sort_index(axis=1)


def combine_metrics(tickers: list) -> dict:
    combined = {}
    for ticker in tickers:
        combined.update(get_data.get_features(ticker, bucket))

    return combined


def get_corr_plot(df: pd.DataFrame, time_period: str):
    df = df['adjClose']
    df.dropna(axis=1, how='all', inplace=True)

    returns = df.pct_change().dropna()
    corr_matrix = returns.corr()
    fig = px.imshow(corr_matrix, text_auto=True,
                    color_continuous_scale='RdBu_r', zmin=-1, zmax=1,
                    title=f'Correlation: Historical Return ({time_period})')
    fig.update_layout(paper_bgcolor='rgb(184, 201, 223)', coloraxis_colorbar = dict(x=1.0),
                        autosize=True, xaxis_title=None, yaxis_title=None, margin=dict(r=0))
    corr_plot = plotly.io.to_html(fig, full_html=False)
    return corr_plot


def get_time_series(df: pd.DataFrame, ticker: str, time_period: str):
    df_flat = df.copy()
    df_flat.columns = ['-'.join(col).strip() for col in df.columns.values]

    fig = px.line(df_flat, x=df_flat.index, 
                  y=[f'adjClose-{ticker}', f'SMA10-{ticker}', f'SMA50-{ticker}', f'SMA200-{ticker}',
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