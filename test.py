import pandas as pd
from lightweight_charts import Chart

# Sample OHLCV data in a DataFrame
data = {
    'time': ['2023-05-19', '2023-05-20', '2023-05-21', '2023-05-22', '2023-05-23'],
    'open': [10.0, 10.5, 10.3, 10.8, 11.0],
    'high': [10.5, 10.7, 10.8, 11.2, 11.3],
    'low': [9.8, 10.2, 10.0, 10.5, 10.7],
    'close': [10.2, 10.3, 10.7, 10.9, 11.1],
    'volume': [1000, 1500, 2000, 2500, 3000]
}

df = pd.DataFrame(data)

if __name__ == '__main__':
    chart = Chart()

    # Assuming the library supports candlestick series, though this may need checking
    candlestick_series = chart.add_series('Candlestick', df[['time', 'open', 'high', 'low', 'close']].to_dict('records'))

    chart.show(block=True)
