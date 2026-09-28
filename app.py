from flask import Flask, render_template_string, jsonify, request, send_from_directory
import ccxt
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

ex = ccxt.binance({
    'apiKey': os.getenv('OKX_KEY'),
    'secret': os.getenv('OKX_SECRET'),
    })   
ex.set_sandbox_mode(True)

HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Binance Dashboard</title>
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
    <h1>Binance Dashboard</h1>
    <span id="mode-badge" style="font-size:0.7em;padding:3px 8px;border-radius:4px;margin-left:10px;"></span>   
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
<button onclick="exportJournalCSV()" style="padding:6px 12px;background:#16213e;color:#eee;border:1px solid #4fc3f7;cursor:pointer;margin:10px 0;">⬇ Export CSV</button>   
<div id="journal-orders"></div>   
<h3>P&L</h3>
<div id="pnl-stats"></div>
<div id="equity-chart" style="height:250px;margin:15px 0;"></div>
<table id="pnl-trades"></table> 
<button onclick="exportPnLCSV()" style="padding:6px 12px;background:#16213e;color:#eee;border:1px solid #4fc3f7;cursor:pointer;margin:10px 0;">⬇ Export P&L CSV</button>     
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
    
@app.route('/api/pnl')
def api_pnl():
    trades = ex.fetch_my_trades('BTC/USDT', limit=100)   
    trades.sort(key=lambda t: t['timestamp'])

    # Pair entries (buy) with exits (sell) for spot long
    open_position = None
    closed_trades = []
    equity = 0  # cumulative P&L in USDT

    for t in trades:
        if t['side'] == 'buy' and open_position is None:
            open_position = {'entry_price': t['price'], 'amount': t['amount'], 'entry_time': t['timestamp'], 'fee': t.get('cost', 0) * 0.001}
        elif t['side'] == 'sell' and open_position is not None:
            amount = min(t['amount'], open_position['amount'])
            pnl = (t['price'] - open_position['entry_price']) * amount - (open_position['fee'] + t['cost'] * 0.001)
            equity += pnl
            closed_trades.append({
                'entry_price': open_position['entry_price'],
                'exit_price': t['price'],
                'amount': amount,
                'pnl': round(pnl, 4),
                'entry_time': open_position['entry_time'],
                'exit_time': t['timestamp'],
                'equity': round(equity, 4),
                'win': pnl > 0
            })
            if t['amount'] > open_position['amount']:
                open_position = {'entry_price': t['price'], 'amount': t['amount'] - 			open_position['amount'], 'entry_time': t['timestamp'], 'fee': 0}
            else:
                open_position = None

    # Stats
    wins = [t for t in closed_trades if t['win']]
    losses = [t for t in closed_trades if not t['win']]
    stats = {
        'total_trades': len(closed_trades),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': round(len(wins) / len(closed_trades) * 100, 1) if closed_trades else 0,
        'total_pnl': round(equity, 4),
        'avg_win': round(sum(t['pnl'] for t in wins) / len(wins), 4) if wins else 0,
        'avg_loss': round(sum(t['pnl'] for t in losses) / len(losses), 4) if losses else 0,
        'max_drawdown': round(min((t['equity'] for t in closed_trades), default=0), 4) if closed_trades else 0,
        'profit_factor': round(sum(t['pnl'] for t in wins) / abs(sum(t['pnl'] for t in losses)), 2) if losses and sum(t['pnl'] for t in losses) != 0 else 0
    }

    # Equity curve data
    equity_curve = [{'time': int(t['exit_time'] / 1000), 'value': t['equity']} for t in closed_trades]

    return jsonify({
        'stats': stats,
        'closed_trades': closed_trades,
        'equity_curve': equity_curve,
        'open_position': open_position
    })  
    
@app.route('/api/mode')
def api_mode():
    return jsonify({'mode': 'DEMO' if ex.sandbox else 'LIVE'})           

if __name__ == '__main__':
    app.run(port=8502)
