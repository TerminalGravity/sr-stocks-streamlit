import time, datetime
from gpt4o_technical_analyst import analyze_chart
import queue
import pandas as pd
from threading import Thread
from lightweight_charts import Chart

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.client import Contract, Order, ScannerSubscription
from ibapi.tag_value import TagValue

# Create a queue for data coming from Interactive Brokers API
data_queue = queue.Queue()

# A list for keeping track of any indicator lines
current_lines = []

# Initial chart symbol to show
INITIAL_SYMBOL = "TSM"

# Settings for live trading vs. paper trading mode
LIVE_TRADING = False
LIVE_TRADING_PORT = 7496
PAPER_TRADING_PORT = 7497
TRADING_PORT = PAPER_TRADING_PORT
if LIVE_TRADING:
    TRADING_PORT = LIVE_TRADING_PORT

# These defaults are fine
DEFAULT_HOST = '127.0.0.1'
DEFAULT_CLIENT_ID = 1

# Client for connecting to Interactive Brokers
class PTLClient(EWrapper, EClient):
     
    def __init__(self, host, port, client_id):
        EClient.__init__(self, self) 
        self.connect(host, port, client_id)
        thread = Thread(target=self.run)
        thread.start()

    def error(self, req_id, code, msg, misc):
        if code in [2104, 2106, 2158]:
            print(msg)
        else:
            print('Error {}: {}'.format(code, msg))

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.order_id = orderId
        print(f"Next valid id is {self.order_id}")

    def historicalData(self, req_id, bar):
        t = datetime.datetime.fromtimestamp(int(bar.date))
        data = {
            'date': t,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': int(bar.volume)
        }
        data_queue.put(data)

    def historicalDataEnd(self, reqId, start, end):
        print(f"End of data {start} {end}")
        update_chart()

    def orderStatus(self, order_id, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print(f"Order status {order_id} {status} {filled} {remaining} {avgFillPrice}")    

    def scannerData(self, req_id, rank, details, distance, benchmark, projection, legsStr):
        super().scannerData(req_id, rank, details, distance, benchmark, projection, legsStr)
        print("Got scanner data")
        print(details.contract)
        data = {
            'secType': details.contract.secType,
            'secId': details.contract.secId,
            'exchange': details.contract.primaryExchange,
            'symbol': details.contract.symbol
        }
        data_queue.put(data)

def get_bar_data(symbol, timeframe):
    print(f"Getting bar data for {symbol} {timeframe}")
    contract = Contract()
    contract.symbol = symbol
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    what_to_show = 'TRADES'
    chart.spinner(True)
    client.reqHistoricalData(2, contract, '', '30 D', timeframe, what_to_show, True, 2, False, [])
    time.sleep(1)
    chart.watermark(symbol)

def take_screenshot(key):
    img = chart.screenshot()
    t = time.time()
    chart_filename = f"screenshots/screenshot-{t}.png"
    analysis_filename = f"screenshots/screenshot-{t}.md"

    with open(chart_filename, 'wb') as f:
        f.write(img)

    analysis = analyze_chart(chart_filename)

    print(analysis)

    with open(analysis_filename, "w") as text_file:
        text_file.write(analysis)

def place_order(key):
    symbol = chart.topbar['symbol'].value
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.currency = "USD"
    contract.exchange = "SMART"
    order = Order()
    order.orderType = "MKT"
    order.totalQuantity = 1
    client.reqIds(-1)
    time.sleep(2)
    if key == 'O':
        print("Buy order")
        order.action = "BUY"
    if key == 'P':
        print("Sell order")
        order.action = "SELL"
    if client.order_id:
        print("Got order id, placing order")
        client.placeOrder(client.order_id, contract, order)

def do_scan(scan_code):
    scannerSubscription = ScannerSubscription()
    scannerSubscription.instrument = "STK"
    scannerSubscription.locationCode = "STK.US.MAJOR"
    scannerSubscription.scanCode = scan_code
    tagValues = [TagValue("optVolumeAbove", "1000"), TagValue("avgVolumeAbove", "10000")]
    client.reqScannerSubscription(7002, scannerSubscription, [], tagValues)
    time.sleep(1)
    display_scan()
    client.cancelScannerSubscription(7002)

def on_search(chart, searched_string):
    get_bar_data(searched_string, chart.topbar['timeframe'].value)
    chart.topbar['symbol'].set(searched_string)

def on_timeframe_selection(chart):
    print("Selected timeframe")
    print(chart.topbar['symbol'].value, chart.topbar['timeframe'].value)
    get_bar_data(chart.topbar['symbol'].value, chart.topbar['timeframe'].value)

def on_horizontal_line_move(chart, line):
    print(f'Horizontal line moved to: {line.price}')

def display_scan():
    def on_row_click(row):
        chart.topbar['symbol'].set(row['symbol'])
        get_bar_data(row['symbol'], '5 mins')
    table = chart.create_table(width=0.4, height=0.5, headings=('symbol', 'value'), widths=(0.7, 0.3), alignments=('left', 'center'), position='left', func=on_row_click)
    try:
        while True:
            data = data_queue.get_nowait()
            table.new_row(data['symbol'], '')
    except queue.Empty:
        print("Empty queue")
    finally:
        print("Done")

def update_chart():
    global current_lines
    try:
        bars = []
        while True:
            data = data_queue.get_nowait()
            bars.append(data)
    except queue.Empty:
        print("Empty queue")
    finally:
        df = pd.DataFrame(bars)
        print(df)
        chart.set(df)
        if not df.empty:
            chart.horizontal_line(df['high'].max(), func=on_horizontal_line_move)
            if current_lines:
                for l in current_lines:
                    l.delete()
            current_lines = []
            line = chart.create_line(name='SMA 50')
            line.set(pd.DataFrame({'time': df['date'], 'SMA 50': df['close'].rolling(window=50).mean()}).dropna())
            current_lines.append(line)
            chart.spinner(False)

if __name__ == '__main__':
    client = PTLClient(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)
    chart = Chart(toolbox=True, width=1000, inner_width=0.6, inner_height=1)
    chart.hotkey('shift', 'O', place_order)
    chart.hotkey('shift', 'P', place_order)
    chart.legend(True)
    chart.events.search += on_search
    chart.topbar.textbox('symbol', INITIAL_SYMBOL)
    chart.topbar.switcher('timeframe', ('5 mins', '15 mins', '1 hour'), default='5 mins', func=on_timeframe_selection)
    get_bar_data(INITIAL_SYMBOL, '5 mins')
    do_scan("HOT_BY_VOLUME")
    chart.topbar.button('screenshot', 'Screenshot', func=take_screenshot)
    chart.show(block=True)
