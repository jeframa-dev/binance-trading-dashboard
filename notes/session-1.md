# Session 1 — Sept 25, 2026

## What we built
- Flask + CCXT + Lightweight Charts trading dashboard
- Auto-refresh (3s), candle/line toggle, multi-symbol

## Files
- app.py (backend)
- js.js (frontend)
- .env (keys)
- requirements.txt
- README.md

## Key lessons
- Zorin OS = Ubuntu-based
- Old CPU (no AVX) → can't run pandas/pyarrow/Streamlit
- Use Flask instead of Streamlit
- Use gedit, not nano (terminal eats HTML on paste)
- .env for secrets, never hardcode keys
- requirements.txt for reproducible installs

## Next steps
- Add balance/positions display
- Deposit $100 → enable Trade permission
- Add order placement form
- Add indicators (RSI, EMA)
- Build hybrid diagnostic tool (local + cloud LLM)

## Hardware notes
- Current: Dell OptiPlex 580 (no AVX)
- Upgrade target: Framework 13 or MacBook M4 Pro 36GB   
