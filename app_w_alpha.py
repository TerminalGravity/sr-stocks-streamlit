import streamlit as st
import alpaca_trade_api as tradeapi
import pandas as pd
import json
from datetime import datetime, timedelta

# Set up Alpaca API
ALPACA_API_KEY = 'PKUPDBVUS9YDGW82GOPD'
ALPACA_SECRET_KEY = 'qPFdQVs081qcEpU0kpAbC6ZNJ4EfNCmb4PPkSQty'
BASE_URL = 'https://paper-api.alpaca.markets'

api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, BASE_URL, api_version='v2')

# Streamlit app setup
st.set_page_config(page_title="Stock Chart with S/R Levels", layout="wide")
st.title("Real-Time Stock Chart with Support and Resistance Levels")

# Sidebar inputs
st.sidebar.header("Input Parameters")
stock_symbol = st.sidebar.text_input("Enter Stock Symbol (e.g., AAPL)", value="AAPL")
support_levels_input = st.sidebar.text_area("Enter Support Levels (comma separated)", "122.24, 124.69, 129.60, 132.78, 136.04, 138.12, 140.26, 142.10, 145.99, 150.13, 153.37, 157.21, 161.56, 165.70, 172.25, 176.60, 180.19, 182.22")
resistance_levels_input = st.sidebar.text_area("Enter Resistance Levels (comma separated)", "186.01, 188.77, 194.51, 200.25, 206.21, 210.61, 215.52, 223.27")

# Validate input
try:
    support_levels = [float(level) for level in support_levels_input.split(",")]
    resistance_levels = [float(level) for level in resistance_levels_input.split(",")]
except ValueError:
    st.sidebar.error("Please enter valid support and resistance levels separated by commas.")
    support_levels = []
    resistance_levels = []

# Fetch daily data from Alpaca
@st.cache_data
def fetch_daily_data(symbol):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    bars = api.get_bars(symbol, tradeapi.TimeFrame.Day, start=start_date_str, end=end_date_str).df
    return bars

# Add moving averages
def add_moving_averages(df, windows=[10, 50, 200]):
    for window in windows:
        df[f'SMA_{window}'] = df['close'].rolling(window=window).mean()
    return df

# Prepare data for LightweightCharts
def prepare_chart_data(symbol, support_levels, resistance_levels):
    bars = fetch_daily_data(symbol)
    bars = add_moving_averages(bars)
    
    chart_data = []
    for index, row in bars.iterrows():
        chart_data.append({
            'time': index.strftime('%Y-%m-%d'),
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'close': row['close'],
        })
    
    return chart_data, support_levels, resistance_levels

# Embed JavaScript in Streamlit
def render_chart(chart_data, support_levels, resistance_levels):
    price_bars_json = json.dumps(chart_data)
    support_levels_json = json.dumps(support_levels)
    resistance_levels_json = json.dumps(resistance_levels)

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://unpkg.com/lightweight-charts@3.5.1/dist/lightweight-charts.standalone.production.js"></script>
        <script>
        document.addEventListener('DOMContentLoaded', function () {{
            const chartData = {price_bars_json};
            const supportLevels = {support_levels_json};
            const resistanceLevels = {resistance_levels_json};
            
            const chart = LightweightCharts.createChart(document.body, {{
                width: 800,
                height: 600,
                layout: {{
                    backgroundColor: '#FFFFFF',
                    textColor: '#000',
                }},
                grid: {{
                    vertLines: {{
                        color: '#E0E3EB',
                    }},
                    horzLines: {{
                        color: '#E0E3EB',
                    }},
                }},
                priceScale: {{
                    borderColor: '#B2B5BE',
                }},
                timeScale: {{
                    borderColor: '#B2B5BE',
                }},
            }});

            const candlestickSeries = chart.addCandlestickSeries({{
                upColor: '#4CAF50',
                downColor: '#F44336',
                borderDownColor: '#F44336',
                borderUpColor: '#4CAF50',
                wickDownColor: '#F44336',
                wickUpColor: '#4CAF50',
            }});

            candlestickSeries.setData(chartData);

            supportLevels.forEach(level => {{
                chart.addLineSeries().setData([{{ time: chartData[0].time, value: level }}, {{ time: chartData[chartData.length - 1].time, value: level }}]);
            }});

            resistanceLevels.forEach(level => {{
                chart.addLineSeries().setData([{{ time: chartData[0].time, value: level }}, {{ time: chartData[chartData.length - 1].time, value: level }}]);
            }});
        }});
        </script>
    </head>
    <body>
    </body>
    </html>
    """

    st.components.v1.html(html_template, height=700)

# Display chart and download button
if stock_symbol and support_levels and resistance_levels:
    chart_data, support_levels, resistance_levels = prepare_chart_data(stock_symbol, support_levels, resistance_levels)
    render_chart(chart_data, support_levels, resistance_levels)

else:
    st.warning("Please enter a valid stock symbol and support/resistance levels.")
