import streamlit as st
import pandas as pd
import datetime as dt
from lightweight_charts import Chart
import alpaca_trade_api as tradeapi

# Alpaca API setup
ALPACA_API_KEY = 'PK2JWDAACYPRZ2WO3HWZ'
ALPACA_SECRET_KEY = 'xvSR3aGN6xip3EUmFosRWxAltXxdVpElj2MRmady'
BASE_URL = 'https://paper-api.alpaca.markets/v2'

api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, BASE_URL, api_version='v2')

# Predefined support and resistance levels
predefined_levels = {
    "AAPL": {
        "support": [122.24, 124.69, 129.60, 132.78, 136.04, 138.12, 140.26, 142.10, 145.99, 150.13, 153.37, 157.21, 161.56, 165.70, 172.25, 176.60, 180.19, 182.22],
        "resistance": [186.01, 188.77, 194.51, 200.25, 206.21, 210.61, 215.52, 223.27]
    },
    "AMD": {
        "support": [88.84, 92.36, 100.07, 102.80, 107.62, 111.64, 116.78, 122.00, 125.17, 133.34, 140.05, 143.73, 147.57, 151.07],
        "resistance": [156.46, 160.29, 164.76, 170.46, 174.89, 179.96, 184.82, 190.95, 196.86, 200.80, 205.56, 212.39, 219.22, 226.94, 235.27, 240.78, 249.74, 258.10]
    },
    # Add other predefined levels here
}

# Streamlit app setup
st.set_page_config(page_title="Stock Chart with S/R Levels", layout="wide")
st.title("Real-Time Stock Chart with Support and Resistance Levels")

# Sidebar inputs
st.sidebar.header("Input Parameters")
selected_stock = st.sidebar.selectbox("Select a predefined stock", list(predefined_levels.keys()))
time_interval = st.sidebar.selectbox("Select Time Interval", ("5Min", "10Min", "15Min", "30Min", "1H", "1D"), index=5)

# Get support and resistance levels for the selected stock
support_levels = predefined_levels[selected_stock]["support"]
resistance_levels = predefined_levels[selected_stock]["resistance"]

# Fetch data from Alpaca
@st.cache_data
def fetch_data(symbol, interval):
    end_date = dt.datetime.now()
    start_date = end_date - dt.timedelta(days=365)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    timeframe = {
        '5Min': tradeapi.TimeFrame.Minute,
        '10Min': tradeapi.TimeFrame(10, tradeapi.TimeFrameUnit.Minute),
        '15Min': tradeapi.TimeFrame(15, tradeapi.TimeFrameUnit.Minute),
        '30Min': tradeapi.TimeFrame(30, tradeapi.TimeFrameUnit.Minute),
        '1H': tradeapi.TimeFrame.Hour,
        '1D': tradeapi.TimeFrame.Day
    }[interval]

    bars = api.get_bars(symbol, timeframe, start=start_date_str, end=end_date_str).df
    bars.reset_index(inplace=True)
    return bars

def prepare_chart_data(symbol, interval):
    df = fetch_data(symbol, interval)
    chart_data = []
    for i, row in df.iterrows():
        chart_data.append({
            'time': row['timestamp'].strftime('%Y-%m-%dT%H:%M:%S'),
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'close': row['close'],
            'volume': row['volume'],
        })
    return chart_data

if __name__ == '__main__':
    chart_data = prepare_chart_data(selected_stock, time_interval)

    # Initialize the chart
    chart = Chart({
        'width': 800,
        'height': 600,
        'layout': {
            'background': {
                'color': '#000000',
            },
            'textColor': '#FFFFFF',
        },
        'grid': {
            'vertLines': {
                'color': '#2B2B43',
            },
            'horzLines': {
                'color': '#363C4E',
            },
        },
    })

    # Add candlestick series to the chart
    candlestick_series = chart.add_candlestick_series()
    candlestick_series.set_data(chart_data)

    # Add support and resistance levels
    for level in support_levels:
        line_series = chart.add_line_series(color='green', lineWidth=1)
        line_series.set_data([{'time': chart_data[0]['time'], 'value': level}, {'time': chart_data[-1]['time'], 'value': level}])

    for level in resistance_levels:
        line_series = chart.add_line_series(color='red', lineWidth=1)
        line_series.set_data([{'time': chart_data[0]['time'], 'value': level}, {'time': chart_data[-1]['time'], 'value': level}])

    # Set up watermark
    chart.watermark({
        'color': 'rgba(180, 180, 240, 0.7)',
        'visible': True,
        'text': selected_stock,
        'fontSize': 48,
        'horzAlign': 'center',
        'vertAlign': 'center',
    })

    # Render the chart in Streamlit
    st.components.v1.html(chart.to_html(), height=700)
       