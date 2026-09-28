let chart, candleSeries;
let useCandle = true;

function initChart() {   
    const c = document.getElementById('chart');
    chart = LightweightCharts.createChart(c, {
    autoSize: true,
    layout: {
        background: { color: '#1a1a2e' },
        textColor: '#eee',
        fontSize: 11,
        fontFamily: 'monospace'
    },
    timeScale: {
        minimumHeight: 40,
    },
    grid: { vertLines: { color: '#2a2a4e' }, horzLines: { color: '#2a2a4e' } }
});
    createPriceSeries();
}

function createPriceSeries() {
    if (candleSeries) { chart.removeSeries(candleSeries); }
    if (useCandle) {
        candleSeries = chart.addCandlestickSeries();
    } else {
        candleSeries = chart.addLineSeries({ color: '#4fc3f7', lineWidth: 2 });
    }
}

function fetchCandles() {
    const s = document.getElementById('symbol').value;
    const t = document.getElementById('timeframe').value;
    fetch('/api/candles?symbol=' + encodeURIComponent(s) + '&timeframe=' + t)
        .then(r => r.json())
        .then(d => {
            if (useCandle) {
                candleSeries.setData(d);
            } else {
                candleSeries.setData(d.map(c => ({ time: c.time, value: c.close })));
            }
            chart.timeScale().fitContent();

            
        });
}

document.getElementById('chartToggle').addEventListener('click', function() {
    useCandle = !useCandle;
    this.textContent = useCandle ? '📈 Line' : '📊 Candle';
    createPriceSeries();
    fetchCandles();
});   

function fetchData() {
    const s = document.getElementById('symbol').value;
    const t = document.getElementById('timeframe').value;
    fetch('/api/data?symbol=' + encodeURIComponent(s) + '&timeframe=' + t)
        .then(r => r.json())
        .then(d => {
            document.getElementById('ticker').textContent =
                'Last: ' + d.ticker.last + ' | Bid: ' + d.ticker.bid + ' | Ask: ' + d.ticker.ask;
            let b = '<tr><th>Bid</th><th>Size</th><th>Ask</th><th>Size</th></tr>';
            d.book.forEach(r => {
                b += '<tr><td>' + r[0][0] + '</td><td>' + r[0][1] + '</td><td>' + r[1][0] + '</td><td>' + r[1][1] + '</td></tr>';
            });
            document.getElementById('book').innerHTML = b;
            let tr = '<tr><th>Side</th><th>Amount</th><th>Price</th></tr>';
            d.trades.forEach(t => {
                const cls = t.side === 'buy' ? 'buy' : 'sell';
                tr += '<tr><td class="' + cls + '">' + t.side + '</td><td>' + t.amount + '</td><td>' + t.price + '</td></tr>';
            });
            document.getElementById('trades').innerHTML = tr;
            document.getElementById('status').textContent = 'Updated: ' + new Date().toLocaleTimeString();
        });
}

document.getElementById('symbol').addEventListener('change', () => { fetchCandles(); fetchData(); });
document.getElementById('timeframe').addEventListener('change', () => { fetchCandles(); fetchData(); });

function fetchJournal() {
    fetch('/api/journal')
        .then(r => r.json())
        .then(d => {
            document.getElementById('journal-balance').innerHTML =
                '<p style="font-size:1.1em;margin:10px 0;">' +
                'USDT: ' + d.balance.usdt_free + ' free / ' + d.balance.usdt_total + ' total' +
                ' &nbsp;|&nbsp; ' +
                'BTC: ' + d.balance.btc_free + ' free / ' + d.balance.btc_total + ' total' +
                '</p>';

            let t = '<tr><th>Time</th><th>Side</th><th>Amount</th><th>Price</th><th>Cost</th><th>Fee</th></tr>';
            d.trades.forEach(tr => {
                const cls = tr.side === 'buy' ? 'buy' : 'sell';
                const time = new Date(tr.time).toLocaleString();
                t += '<tr><td>' + time + '</td><td class="' + cls + '">' + tr.side + '</td><td>' + tr.amount + '</td><td>' + tr.price + '</td><td>' + tr.cost.toFixed(2) + '</td><td>' + tr.fee + '</td></tr>';
            });
            document.getElementById('journal-trades').innerHTML = t;

            let o = '';
            if (d.open_orders.length > 0) {
                o = '<p style="color:#f0b90b;margin:10px 0;">Open Orders:</p>';
                d.open_orders.forEach(ord => {
                    o += '<p>' + ord.side + ' ' + ord.amount + ' @ ' + ord.price + ' (' + ord.type + ')</p>';
                });
            } else {
                o = '<p style="color:#666;">No open orders.</p>';
            }
            document.getElementById('journal-orders').innerHTML = o;
        });
}

fetchJournal();   

initChart();
fetchCandles();
fetchData();
setInterval(() => { fetchData(); fetchCandles(); fetchJournal(); }, 3000);   
