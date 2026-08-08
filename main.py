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
    time_series_list = []

    if request.method == 'POST':

        if 'submission_form' in request.form:
            tickers_response = request.form['tickers']
            time_period = request.form['radio_option']

            tickers = [t.strip().upper() for t in tickers_response.split(",") if t.strip()]

            for _ in range(2):
                try:
                    df = web_content.combine_historical_data(tickers, time_period)

                    metrics = web_content.combine_metrics(tickers)

                    corr_chart_html = web_content.get_corr_plot(df, time_period)
                    
                    for ticker in tickers:
                        time_series_list.append(web_content.get_time_series(df, ticker, time_period))
                    time.sleep(2)
                    break
                except Exception as e:
                    # corr_chart_html = f'<p>Error fetching data from Yahoo Finance. Please try again.</p>'
                    corr_chart_html = f'{e}'
                    metrics = {}
                    time.sleep(2)
    
    return render_template('index.html', corr_chart=corr_chart_html, 
                           hist_fig=hist_fig_html, tickers=tickers, 
                           time_period=time_period, metrics=metrics,
                           time_series_list=time_series_list)

if __name__ == '__main__':
    app.run(debug=True)