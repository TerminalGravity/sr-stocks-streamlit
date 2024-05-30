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

# Function to fetch data from Alpaca
@st.cache_data
def fetch_data(symbol, interval='1D'):
    end_date = dt.datetime.now()
    start_date = end_date - dt.timedelta(days=365)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    timeframe = {
        '1D': tradeapi.TimeFrame.Day,
        '1H': tradeapi.TimeFrame.Hour,
        '30Min': tradeapi.TimeFrame(30, tradeapi.TimeFrameUnit.Minute),
        '15Min': tradeapi.TimeFrame(15, tradeapi.TimeFrameUnit.Minute),
        '10Min': tradeapi.TimeFrame(10, tradeapi.TimeFrameUnit.Minute),
        '5Min': tradeapi.TimeFrame(5, tradeapi.TimeFrameUnit.Minute)
    }[interval]

    bars = api.get_bars(symbol, timeframe, start=start_date_str, end=end_date_str, feed='iex').df
    bars.reset_index(inplace=True)
    bars['timestamp'] = bars['timestamp'].astype(str)  # Convert Timestamp to string
    return bars

# Function to create a candlestick chart
def create_candlestick_chart(df, title):
    chart = Chart()
    chart.set(df)
    return chart

# Streamlit app setup
st.set_page_config(page_title="Grid of 4 Stock Charts", layout="wide")
st.title("Grid of 4 Stock Charts")

# Sidebar inputs
st.sidebar.header("Input Parameters")
selected_stocks = st.sidebar.multiselect("Select up to 4 stocks", ["AAPL", "AMD", "GOOGL", "MSFT"], default=["AAPL", "AMD", "GOOGL", "MSFT"])
time_interval = st.sidebar.selectbox("Select Time Interval", ("5Min", "10Min", "15Min", "30Min", "1H", "1D"), index=5)

# Create a grid layout with 2 rows and 2 columns
if len(selected_stocks) == 4:
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    # Add charts to the grid
    with col1:
        df1 = fetch_data(selected_stocks[0], time_interval)
        chart1 = create_candlestick_chart(df1, selected_stocks[0])
        st.subheader(selected_stocks[0])
        st.components.v1.html(chart1.to_html(), height=350)
    with col2:
        df2 = fetch_data(selected_stocks[1], time_interval)
        chart2 = create_candlestick_chart(df2, selected_stocks[1])
        st.subheader(selected_stocks[1])
        st.components.v1.html(chart2.to_html(), height=350)
    with col3:
        df3 = fetch_data(selected_stocks[2], time_interval)
        chart3 = create_candlestick_chart(df3, selected_stocks[2])
        st.subheader(selected_stocks[2])
        st.components.v1.html(chart3.to_html(), height=350)
    with col4:
        df4 = fetch_data(selected_stocks[3], time_interval)
        chart4 = create_candlestick_chart(df4, selected_stocks[3])
        st.subheader(selected_stocks[3])
        st.components.v1.html(chart4.to_html(), height=350)
else:
    st.error("Please select exactly 4 stocks.")
