import streamlit as st
import alpaca_trade_api as tradeapi
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, Span
from bokeh.io import export_png
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import io

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

# Plot stock data with support and resistance levels using Bokeh
def plot_stock_levels(symbol, support_levels, resistance_levels):
    bars = fetch_daily_data(symbol)
    bars = add_moving_averages(bars)
    
    source = ColumnDataSource(bars)

    p = figure(x_axis_type='datetime', title=f"Real-Time Chart for {symbol}", sizing_mode="stretch_width", height=500)
    p.xaxis.axis_label = 'Time'
    p.yaxis.axis_label = 'Price'

    # Candlestick chart
    inc = bars['close'] > bars['open']
    dec = bars['open'] > bars['close']
    width = 12*60*60*1000  # half day in ms

    p.segment(bars.index, bars['high'], bars.index, bars['low'], color="black")
    p.vbar(bars.index[inc], width, bars['open'][inc], bars['close'][inc], fill_color="green", line_color="black")
    p.vbar(bars.index[dec], width, bars['open'][dec], bars['close'][dec], fill_color="red", line_color="black")

    # Moving averages
    colors = ['blue', 'orange', 'purple']
    for i, window in enumerate([10, 50, 200]):
        p.line(bars.index, bars[f'SMA_{window}'], color=colors[i], legend_label=f'SMA {window}')

    # Support and resistance levels
    for level in support_levels:
        span = Span(location=level, dimension='width', line_color='green', line_dash='dashed', line_width=1)
        p.add_layout(span)
        p.add_layout(p.text(bars.index[-1], level, text=[str(level)], text_color='green', text_align='right'))

    for level in resistance_levels:
        span = Span(location=level, dimension='width', line_color='red', line_dash='dashed', line_width=1)
        p.add_layout(span)
        p.add_layout(p.text(bars.index[-1], level, text=[str(level)], text_color='red', text_align='right'))

    p.legend.location = "top_left"
    p.add_tools(HoverTool(
        tooltips=[
            ("Date", "@date{%F}"),
            ("Open", "@open{0.2f}"),
            ("High", "@high{0.2f}"),
            ("Low", "@low{0.2f}"),
            ("Close", "@close{0.2f}"),
        ],
        formatters={
            '@date': 'datetime',
        },
        mode='vline'
    ))

    return p

# Backtest support and resistance levels
def backtest_levels(symbol, support_levels, resistance_levels, transaction_cost=0.01, take_profit=0.05, stop_loss=0.02):
    bars = fetch_daily_data(symbol)
    initial_balance = 10000
    balance = initial_balance
    position = 0  # 1 for long, -1 for short, 0 for no position
    entry_price = 0
    trades = []

    for index, row in bars.iterrows():
        close_price = row['close']
        
        # Check for buy signal (support level)
        if position == 0:
            for support in support_levels:
                if close_price <= support:
                    position = 1
                    entry_price = close_price
                    trades.append({'type': 'buy', 'price': entry_price, 'date': index})
                    break
        
        # Check for sell signal (resistance level or trailing stop-loss/take-profit)
        elif position == 1:
            for resistance in resistance_levels:
                if close_price >= resistance:
                    position = 0
                    exit_price = close_price
                    profit = exit_price - entry_price - transaction_cost * (entry_price + exit_price)
                    balance += profit
                    trades.append({'type': 'sell', 'price': exit_price, 'date': index, 'profit': profit})
                    break
            # Check for trailing stop-loss
            if close_price <= entry_price * (1 - stop_loss):
                position = 0
                exit_price = close_price
                profit = exit_price - entry_price - transaction_cost * (entry_price + exit_price)
                balance += profit
                trades.append({'type': 'sell', 'price': exit_price, 'date': index, 'profit': profit})
            # Check for take-profit
            elif close_price >= entry_price * (1 + take_profit):
                position = 0
                exit_price = close_price
                profit = exit_price - entry_price - transaction_cost * (entry_price + exit_price)
                balance += profit
                trades.append({'type': 'sell', 'price': exit_price, 'date': index, 'profit': profit})

    return balance, trades

# Display chart and download button
if stock_symbol and support_levels and resistance_levels:
    p = plot_stock_levels(stock_symbol, support_levels, resistance_levels)
    st.bokeh_chart(p, use_container_width=True)

    # Backtesting
    st.subheader("Backtesting Results")
    final_balance, trades = backtest_levels(stock_symbol, support_levels, resistance_levels)
    net_profit = final_balance - 10000
    win_trades = [trade for trade in trades if trade.get('profit', 0) > 0]
    loss_trades = [trade for trade in trades if trade.get('profit', 0) <= 0]
    win_rate = len(win_trades) / len(trades) if trades else 0
    avg_profit = np.mean([trade.get('profit', 0) for trade in trades]) if trades else 0
    max_drawdown = np.min([trade.get('profit', 0) for trade in trades]) if trades else 0
    sharpe_ratio = np.mean([trade.get('profit', 0) for trade in trades]) / np.std([trade.get('profit', 0) for trade in trades]) if len(trades) > 1 else 0

    st.write(f"Initial Balance: $10000")
    st.write(f"Final Balance: ${final_balance:.2f}")
    st.write(f"Net Profit: ${net_profit:.2f}")
    st.write(f"Win Rate: {win_rate:.2%}")
    st.write(f"Average Profit per Trade: ${avg_profit:.2f}")
    st.write(f"Maximum Drawdown: ${max_drawdown:.2f}")
    st.write(f"Sharpe Ratio: {sharpe_ratio:.2f}")

    # Display trades
    st.write("Trade History:")
    trade_df = pd.DataFrame(trades)
    st.write(trade_df)

    # Save chart as PNG and offer download
    buffer = io.BytesIO()
    export_png(p, filename="temp_chart.png")
    with open("temp_chart.png", "rb") as f:
        buffer.write(f.read())
    buffer.seek(0)
    st.download_button(label="Download Chart as PNG", data=buffer, file_name=f"{stock_symbol}_chart.png", mime="image/png")
else:
    st.warning("Please enter a valid stock symbol and support/resistance levels.")
