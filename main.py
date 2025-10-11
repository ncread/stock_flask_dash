from flask import Flask, request, render_template, jsonify
from get_data import *

app = Flask(__name__)

@app.route('/healthz', methods = ['GET'])
def site_health_check():
    return jsonify({'status':'healthy'}), 200

@app.route('/', methods = ['GET','POST'])
def index():
    corr_chart_html = ''
    tickers = ''
    hist_ticker = ''
    hist_fig_html = ''
    metrics = {}
    time_period = '6mo'
    # time_series_html = ''
    time_series_list = []

    if request.method == 'POST':

        if 'submission_form' in request.form:
            tickers = request.form['tickers']
            time_period = request.form['radio_option']

            ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]

            try:
                corr_chart_html = generate_corr_plot(ticker_list, time_period)

                metrics = get_metrics(ticker_list)
                
                df = get_historical_data(ticker_list, time_period)
                for stock in ticker_list:
                    time_series_list.append(get_time_series(df, stock, time_period))
            except Exception as e:
                # corr_chart_html = f'<p>Error fetching data. Please check the inputted tickers and try again.</p>'
                corr_chart_html = e
                metrics = {}
    
    return render_template('index.html', corr_chart=corr_chart_html, 
                           hist_fig=hist_fig_html, tickers=tickers, 
                           time_period=time_period, metrics=metrics,
                           time_series_list=time_series_list)

if __name__ == '__main__':
    app.run()