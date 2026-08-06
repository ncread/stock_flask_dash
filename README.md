# Stock Information Project

A web application written in Python, leveraging the Flask framework.


## Overview

This web application receives user-inputted market tickers (AAPL, NVDA, etc.), a designated timeframe (6 months, 1 year, etc.) and displays the following:

* Correlation matrix including asset return correlations for provided tickers over the provided timeframe
* Table with current share price, 5-year beta value, market cap, trailing & forward price-to-earnings ratios, and upcoming earnings date (if applicable)
* time-series price graphs with share price, 10, 50 and 200-day simple and exponential moving average prices, and upper and lower Bollinger bands

Graphics on the webapp are plotly express images, able to be easily downloaded at the click of a button to share or use elsewhere. The time-series charts are interactive, allowing users to toggle metric charts on and off and to hover over each chart for specific prices.

## Project Structure
```
stock-flask-dash/
├── cache.py
├── get_data.py
├── main.py
├── Procfile
├── providers
│   ├── fh.py
│   ├── fmp.py
│   └── tiingo.py
├── pyproject.toml
├── README.md
├── requirements.txt
├── static
│   └── styles.css
├── storage.py
├── templates
│   └── index.html
└── uv.lock
```

## System Design
To abide by API limits set by the numerous data providers leveraged in this application, caching and cloud storage are implemented. More system design details coming soon.

