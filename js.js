let chart, candleSeries;
let useCandle = true;

function initChart() {   
    const c = document.getElementById('chart');
    chart = LightweightCharts.createChart(c, {
        height: 400,
        layout: { background: { color: '#1a1a2e' }, textColor: '#eee' },
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

initChart();
fetchCandles();
fetchData();
setInterval(() => { fetchData(); fetchCandles(); }, 3000);   
