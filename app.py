from flask import Flask, render_template_string, jsonify, request, send_from_directory
import ccxt
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

ex = ccxt.okx({
    'apiKey': os.getenv('OKX_KEY'),
    'secret': os.getenv('OKX_SECRET'),
    'password': os.getenv('OKX_PASS')
})   


HTML = """<!DOCTYPE html>
<html>
<head>
    <title>OKX Dashboard</title>
    <script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        body { font-family: monospace; background: #1a1a2e; color: #eee; padding: 20px; }
        h1 { color: #4fc3f7; }
        h3 { color: #81c784; }
        table { border-collapse: collapse; margin: 10px 0; }
        td, th { padding: 4px 12px; border: 1px solid #333; text-align: left; }
        th { background: #16213e; }
        .metric { font-size: 1.5em; margin: 10px 0; }
        .buy { color: #81c784; }
        .sell { color: #e57373; }
        select { padding: 6px 12px; background: #16213e; color: #eee; border: 1px solid #4fc3f7; font-size: 1em; margin-right: 10px; }
        .controls { margin: 15px 0; }
        #status { color: #666; font-size: 0.8em; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>OKX Dashboard</h1>
    <div class="controls">
        <select id="symbol">
            <option value="BTC/USDT">BTC/USDT</option>
            <option value="ETH/USDT">ETH/USDT</option>
            <option value="SOL/USDT">SOL/USDT</option>
            <option value="XRP/USDT">XRP/USDT</option>
            <option value="DOGE/USDT">DOGE/USDT</option>
        </select>
        <select id="timeframe">
            <option value="1m">1m</option>
            <option value="5m">5m</option>
            <option value="15m">15m</option>
            <option value="1h" selected>1h</option>
            <option value="4h">4h</option>
            <option value="1d">1d</option>
        </select>
    </div>
    <button id="chartToggle" style="padding:6px 12px;background:#16213e;color:#eee;border:1px solid #4fc3f7;cursor:pointer;">📊 Candle</button>   
    <div id="chart" style="height:400px;margin:15px 0;"></div>
    <p class="metric" id="ticker">Loading...</p>
    <h3>Order Book</h3>
    <table id="book"></table>
    <h3>Recent Trades</h3>
    <table id="trades"></table>
    <h3>Journal</h3>
<div id="journal-balance"></div>
<table id="journal-trades"></table>
<div id="journal-orders"></div>   
    <p id="status"></p>
    <script src="/js.js"></script>
</body>
</html>"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/js.js')
def serve_js():
    return send_from_directory('.', 'js.js')

@app.route('/api/data')
def api_data():
    symbol = request.args.get('symbol', 'BTC/USDT')
    ticker = ex.fetch_ticker(symbol)
    ob = ex.fetch_order_book(symbol, limit=5)
    trades = ex.fetch_trades(symbol, limit=10)
    book = list(zip(ob['bids'][:5], ob['asks'][:5]))
    return jsonify({
        'ticker': {'last': ticker['last'], 'bid': ticker['bid'], 'ask': ticker['ask']},
        'book': book,
        'trades': [{'side': t['side'], 'amount': t['amount'], 'price': t['price']} for t in trades]
    })

@app.route('/api/candles')
def api_candles():
    symbol = request.args.get('symbol', 'BTC/USDT')
    timeframe = request.args.get('timeframe', '1h')
    ohlcv = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=100)
    return jsonify([
        {'time': int(t[0] / 1000), 'open': t[1], 'high': t[2], 'low': t[3], 'close': t[4], 'volume': t[5]}
        for t in ohlcv
    ])
    
@app.route('/api/journal')
def api_journal():
    balance = ex.fetch_balance()
    trades = ex.fetch_my_trades('BTC/USDT', limit=20)
    open_orders = ex.fetch_open_orders('BTC/USDT')
    return jsonify({
        'balance': {
            'usdt_free': balance.get('USDT', {}).get('free', 0),
            'usdt_total': balance.get('USDT', {}).get('total', 0),
            'btc_free': balance.get('BTC', {}).get('free', 0),
            'btc_total': balance.get('BTC', {}).get('total', 0),
        },
        'trades': [
            {'side': t['side'], 'amount': t['amount'], 'price': t['price'], 'cost': t.get('cost', 0), 'fee': t.get('fee', {}).get('cost', 0) if t.get('fee') else 0, 'time': t['timestamp']}
            for t in trades
        ],
        'open_orders': [
            {'side': o['side'], 'amount': o['amount'], 'price': o['price'], 'type': o['type']}
            for o in open_orders
        ]
    })       

if __name__ == '__main__':
    app.run(port=8501)   
