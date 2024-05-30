

Use alpaca markets to fetch market data (for stocks), use streamlit (future work: use good charting library and nice CSS styling) to plot daily chart of watchlist stocks (future work; implement time frame slectors to see different interval of the stock chart), populate stocks with levels dictionary, run a buy low sell high backest - demo performance with that

Lots to - do 

python -m venv stock-app
source stock-app/bin/activate
pip install streamlit alpaca-trade-api plotly pandas
pip install lightweight-charts


pip install streamlit alpaca-trade-api plotly



pip install streamlit alpaca-trade-api bokeh==2.4.3 pandas --force-reinstall --no-deps


TypeError: Chart.__init__() got an unexpected keyword argument 'options'
Traceback:
File "/Users/jackfelke/anaconda3/lib/python3.11/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 535, in _run_script
    exec(code, module.__dict__)
File "/Users/jackfelke/Repos/stock-streamlit/app_w_alpha.py", line 54, in <module>
    chart = Chart(options={
            ^^^^^^^^^^^^^^^


https://github.com/louisnw01/lightweight-charts-python