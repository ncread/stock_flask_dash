import pandas as pd
import numpy as np
import yfinance as yf
from matplotlib import pyplot  as plt
import seaborn as sns

def get_historical_data(tickers):
    #input: list of stock tickers
    #output: dataframe with all-time yahoo finance info

    tickers = [i.upper() for i in tickers]

    # try:
    df = yf.download(tickers, period='max')
    # except:
    #     print(f'{stock} data was not found. Fix symbol or try again.')

    for stock in tickers:
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
        
    return df

def create_returns(dataframe):
    """
        Takes the large dataframe and grabs the Delta columns to create a new dataframe solely 
        including delta (daily returns)
    """

    chosen_stocks = df.columns.get_level_values(1).unique()
    returns_list = [df['Delta'][stock].rename(stock) for stock in chosen_stocks]
    returns_df = pd.concat(returns_list, axis=1)
    return returns_df

def generate_corr_plot(dataframe):
    plt.figure(figsize=(8,6))

    #generate mask to strictly show the diagonal + everything below it on corr plot
    mask = np.triu(np.ones_like(dataframe.corr(), dtype=bool), k=1)
    fig = sns.heatmap(dataframe.corr(), mask=mask, vmin=-1, cmap='coolwarm', annot=True)
    plt.title('Historical Returns Correlation Matrix')
    plt.savefig('./assets/corr_plot.png')
    plt.show()
    return fig