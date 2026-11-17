# QuantPulse AI - Stock Market Time Series Prediction System (₹ INR) 📈

A modern full-stack web application for stock and financial market forecasting powered by **Time Series Analysis**, fully denominated in **Indian Rupees (₹ / INR)**, featuring a **togglable Dark & Light theme**, **Gmail-based user authentication with editable passwords**, and an **interactive UI with cursor-reactive buttons**.

---

## 🏆 The 10 Featured Trades & Trading Categories

All markets are dynamically tracked and quoted directly in **Indian Rupees (`₹`)**:

| # | Market | Trading Category | Currency / Unit | Example Quote |
|---|---|---|---|---|
| **1** | **NIFTY 50** | Indian indices | Points (₹) | `₹25,387.40` |
| **2** | **BANK NIFTY** | Index trading | Points (₹) | `₹62,273.25` |
| **3** | **SENSEX** | Indian indices | Points (₹) | `₹82,532.19` |
| **4** | **Gold (XAU/USD)** | Commodities | ₹ per 10 grams | `₹1,16,175.00` |
| **5** | **Silver (XAG/USD)** | Commodities | ₹ per 1 kg | `₹1,42,400.00` |
| **6** | **Crude Oil** | Commodities | ₹ per Barrel | `₹8,076.00` |
| **7** | **Bitcoin (BTC/USD)** | Crypto | ₹ per Coin | `₹59,44,168.00` |
| **8** | **Ethereum (ETH/USD)** | Crypto | ₹ per Coin | `₹1,65,858.00` |
| **9** | **USD/INR** | Forex | ₹ per 1 USD | `₹93.46` |
| **10** | **NASDAQ 100** | Global indices | Points (₹) | `₹26,753.00` |

---

## 🌟 Key Features

### 1. 🔮 Advanced Time Series Analysis & Forecasting
- **Ensemble Consensus Model**: Optimal dynamic inverse-variance blend of multiple statistical time-series algorithms for superior generalization.
- **ARIMA (AutoRegressive Integrated Moving Average)**: Classical time series forecasting modeling stationarity differencing ($d=1$), autoregressive momentum ($p$), and moving average innovation errors ($q$) with analytical 95% confidence intervals.
- **Holt's Damped Linear Trend**: Double exponential smoothing with adaptive levels and trend damping ($\phi$).
- **Multi-Lag Supervised ML Regression**: Evaluates lagged pricing ($t-1, \dots, t-5$), rolling momentum, and volatility features.
- **Monte Carlo Simulation (Geometric Brownian Motion)**: Simulates 150+ probabilistic future price paths with median, 10th percentile (bear case), 90th percentile (bull case), and visible sample trajectories.
- **Horizon Flexibility**: Forecast 7, 14, 30, 60, or 90 trading days into the future.
- **Quantitative Model Evaluation Scorecard**: Out-of-sample backtest measuring **RMSE**, **MAE**, **MAPE (%)**, **$R^2$ Goodness of Fit**, and **Directional Hit Rate (%)**.

### 2. 🌓 Togglable Dark & Light Mode
- Smooth, instant transitions between **Dark Mode** (cyber-financial aesthetic with glowing cyan accents) and **Light Mode** (clean executive financial terminal).
- Persistent theme preference saved in `localStorage` and synced with the backend profile.
- Dynamic Chart.js canvas restyling without reloading or losing state.

### 3. 🔐 Gmail-Based Authentication & Editable Password System
- **Gmail Username Standard**: User accounts are registered with their Gmail address (e.g., `user@gmail.com`).
- **Editable Password**:
  - In-app **Account Security / Edit Password** modal allows users to change their password anytime with current password verification.
  - **Direct Password Reset** tab on the login screen for easy password updates.
- **1-Click Quick Demo Login**: Instant access button (`trader@gmail.com`) for testing.
- **Secure Hashing**: Military-grade PBKDF2-HMAC-SHA256 password hashing with unique per-user cryptographic salts.

### 4. 🧲 Cursor-Reactive Interactive UI & Micro-Interactions
- **Cursor-Tracking Spotlight**: Every button and interactive card projects a dynamic luminous radial spotlight under the cursor tip (`(x, y)` coordinate tracking).
- **Magnetic Proximity Pull**: Buttons gently track towards the cursor upon approach with spring damping.
- **Coordinate-based Click Ripple**: Fluid expanding wave radiates from the exact mouse click position.
- **Ambient Cursor Follower**: Silky smooth glowing orb that follows cursor movement and expands over buttons.
- **Tactile Audio Feedback**: High-frequency micro-haptic click audio using Web Audio API (toggleable in navbar).

### 5. 🟢 Real-Time Live Market Streaming & Continuous Live Prediction
- **Continuous 24/7 Live Ticking**: Real-time order-flow engine streams live bids, asks, and trade ticks across all 10 featured trades and custom assets.
- **Micro-Volatility Price Action in Indian Rupees (₹)**:
  - Realistic stochastic tick-by-tick drift calibrated to each asset category (Indices, Commodities, Crypto, Forex).
  - Dynamic visual tick alerts: real-time emerald green flash (`tick-flash-up`) when price rises, radiant rose flash (`tick-flash-down`) when price drops.
- **Live Time Series Re-Prediction on Every Tick**:
  - Automatically re-runs Time Series Analysis (Ensemble Consensus, ARIMA, Holt's Trend, ML Regression) live with every market tick.
  - Dynamically recalculates the projected target price in ₹ INR, expected return %, directional trend call, and 95% analytical confidence bands in real time (<20ms latency).
- **60 FPS Non-Destructive Chart Streaming**:
  - Live charts update the current candle and forecast trajectory smoothly using `chart.update('none')` without canvas destruction or jarring flickering.
- **Interactive Live Controls**:
  - **Live Streaming Toggle**: Switch between `🟢 LIVE STREAMING` and `⏸️ PAUSED`.
  - **Configurable Speed Intervals**: `⚡ 2s`, `⏱️ 3s (Default)`, or `🕒 5s`.
  - **Countdown Pulse Ring & Tick Counter**: Visual feedback of incoming ticks and cumulative streaming count.
  - **Manual Instant Tick Button (`⚡ Tick Now`)**: Forces an immediate market tick and forecast re-computation.
  - **Live Auto-Predict Toggle (`⚡ Live Re-Predict on Tick`)**: Enable or disable continuous model re-forecasting.

### 6. 📊 Real-Time Market Data & Technical Indicators
- Real-time market feed with support for popular tickers (AAPL, NVDA, TSLA, MSFT, GOOGL, AMZN, BTC-USD, RELIANCE.NS, SPY, QQQ) plus a universal ticker search.
- **Technical Indicators**:
  - RSI (Relative Strength Index 14) with overbought (>70) and oversold (<30) thresholds.
  - MACD (12, 26, 9) with signal line crossovers and divergence histogram bars.
  - Bollinger Bands (20, 2) upper/lower bands with shaded envelope.
  - Moving Averages: SMA 20, SMA 50, SMA 200, EMA 12, EMA 26.
  - Pivot Point Support (S1, S2) and Resistance (R1, R2) levels.
  - Algorithmic Momentum Score (-100 to +100) and Recommendation Badge (Strong Buy, Buy, Neutral, Sell, Strong Sell).
- **Personal Watchlist**: Add/remove tickers with persistent storage per user.
- **Export Reports**: Download prediction and time-series forecast data as JSON or CSV.

---

## 🚀 How to Run the Project

### Prerequisites
- Python 3.10+ (Python 3.13 / 3.14 recommended)

### Step 1: Start the Server
Open a terminal in the project directory (`stock market`) and run:

```powershell
py -3.13 app.py
```
*(or `python app.py`)*

### Step 2: Open in Browser
Visit in your web browser:
```
http://localhost:8080
# or
http://127.0.0.1:8080
```
*(You can also pass any custom port, e.g.: `py -3.13 app.py 5050` or `py -3.13 app.py 8000`)*

---

## 📁 Directory Structure
```
stock market/
├── app.py                     # Flask web server & REST API
├── database.py                # SQLite auth, user sessions, watchlists, predictions
├── stock_service.py           # Real-time stock data fetcher & fallback simulation engine
├── time_series_engine.py      # ARIMA, Holt-Winters, ML Regressor, Monte Carlo, Indicators
├── templates/
│   └── index.html             # Responsive single-page application UI
├── static/
│   ├── css/
│   │   ├── style.css          # Dark/Light theme CSS variables, layouts, glassmorphism
│   │   └── reactive.css       # Cursor spotlights, magnetic pull, click ripples
│   └── js/
│       ├── cursor-fx.js       # Cursor interaction engine & Web Audio feedback
│       ├── auth.js            # Gmail login, registration, editable password modal
│       ├── charts.js          # Chart.js time-series & technical visualizations
│       └── app.js             # Stock switcher, prediction controls, watchlist
└── README.md                  # Project documentation
```
