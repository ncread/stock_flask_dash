from flask import Flask, request, render_template, jsonify
import time
import get_data
import web_content


app = Flask(__name__)


@app.route('/healthz', methods = ['GET'])
def site_health_check():
    return jsonify({'status':'healthy'}), 200


@app.route('/', methods = ['GET','POST'])
def index():
    corr_chart_html = ''
    tickers = ''
    hist_fig_html = ''
    metrics = {}
    time_period = '6mo'

    if request.method == 'POST':

        if 'submission_form' in request.form:
            tickers_response = request.form['tickers']
            time_period = request.form['radio_option']

            tickers = [t.strip().upper() for t in tickers_response.split(",") if t.strip()]

            for _ in range(2):
                try:
                    df, missing_price = web_content.combine_historical_data(tickers, time_period)
                    corr_chart_html = web_content.get_corr_plot(df, time_period)
                except Exception as e:
                    print(f'Historical data error: {e}')
                    df = None
                    corr_chart_html = None
                    missing_price = None

                time_series_list = []
                if df is not None:
                    for ticker in tickers:
                        try:
                            chart = web_content.get_time_series(df, ticker, time_period)
                            time_series_list.append(chart)
                        except Exception as e:
                            print(f'Historical data error: {e}')

                try:
                    metrics, missing_feature = web_content.combine_metrics(tickers)
                except Exception as e:
                    print(f'Metrics error: {e}')
                    metrics = {}
                    missing_feature = None

            try:
                missing = missing_feature | missing_price
            except Exception as e:
                missing = None
                
    return render_template('index.html', corr_chart=corr_chart_html, 
                           hist_fig=hist_fig_html, tickers=tickers, 
                           time_period=time_period, metrics=metrics,
                           time_series_list=time_series_list, missing=missing)

if __name__ == '__main__':
    app.run(debug = True)