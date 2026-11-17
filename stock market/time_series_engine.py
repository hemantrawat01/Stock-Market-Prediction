import math
import random
from datetime import datetime, timedelta

# ==========================================
# 1. Technical Analysis & Indicator Engine
# ==========================================

def calculate_sma(prices: list[float], window: int) -> list[float | None]:
    result = []
    for i in range(len(prices)):
        if i < window - 1:
            result.append(None)
        else:
            avg = sum(prices[i - window + 1 : i + 1]) / window
            result.append(round(avg, 2))
    return result

def calculate_ema(prices: list[float], window: int) -> list[float | None]:
    result = []
    k = 2.0 / (window + 1.0)
    ema = None
    for i, p in enumerate(prices):
        if i < window - 1:
            result.append(None)
        elif i == window - 1:
            ema = sum(prices[:window]) / window
            result.append(round(ema, 2))
        else:
            ema = (p * k) + (ema * (1.0 - k))
            result.append(round(ema, 2))
    return result

def calculate_rsi(prices: list[float], window: int = 14) -> list[float | None]:
    if len(prices) <= window:
        return [None] * len(prices)
        
    rsi = [None] * len(prices)
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))
        
    avg_gain = sum(gains[:window]) / window
    avg_loss = sum(losses[:window]) / window
    
    if avg_loss == 0:
        rsi[window] = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi[window] = round(100.0 - (100.0 / (1.0 + rs)), 2)
        
    for i in range(window + 1, len(prices)):
        gain = gains[i - 1]
        loss = losses[i - 1]
        avg_gain = (avg_gain * (window - 1) + gain) / window
        avg_loss = (avg_loss * (window - 1) + loss) / window
        
        if avg_loss == 0:
            rsi[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[i] = round(100.0 - (100.0 / (1.0 + rs)), 2)
            
    return rsi

def calculate_macd(prices: list[float], fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    
    macd_line = []
    for i in range(len(prices)):
        if ema_fast[i] is None or ema_slow[i] is None:
            macd_line.append(None)
        else:
            macd_line.append(round(ema_fast[i] - ema_slow[i], 2))
            
    # Calculate signal line (EMA of MACD line)
    clean_macd = [x for x in macd_line if x is not None]
    clean_signal = calculate_ema(clean_macd, signal)
    
    signal_line = [None] * (len(prices) - len(clean_signal)) + clean_signal
    
    histogram = []
    for i in range(len(prices)):
        if macd_line[i] is None or signal_line[i] is None:
            histogram.append(None)
        else:
            histogram.append(round(macd_line[i] - signal_line[i], 2))
            
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }

def calculate_bollinger_bands(prices: list[float], window: int = 20, num_std: float = 2.0):
    sma = calculate_sma(prices, window)
    upper = []
    lower = []
    
    for i in range(len(prices)):
        if sma[i] is None:
            upper.append(None)
            lower.append(None)
        else:
            window_slice = prices[i - window + 1 : i + 1]
            mean = sma[i]
            variance = sum((p - mean) ** 2 for p in window_slice) / window
            std_dev = math.sqrt(variance)
            upper.append(round(mean + (num_std * std_dev), 2))
            lower.append(round(mean - (num_std * std_dev), 2))
            
    return {
        'middle': sma,
        'upper': upper,
        'lower': lower
    }

def calculate_indicators_pack(candles: list[dict]) -> dict:
    closes = [c['close'] for c in candles]
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    dates = [c['date'] for c in candles]
    
    sma_20 = calculate_sma(closes, 20)
    sma_50 = calculate_sma(closes, 50)
    sma_200 = calculate_sma(closes, 200)
    ema_12 = calculate_ema(closes, 12)
    ema_26 = calculate_ema(closes, 26)
    rsi_14 = calculate_rsi(closes, 14)
    macd_pack = calculate_macd(closes, 12, 26, 9)
    bb = calculate_bollinger_bands(closes, 20, 2.0)
    
    # Pivot points & Support / Resistance
    last_h = highs[-1]
    last_l = lows[-1]
    last_c = closes[-1]
    pivot = (last_h + last_l + last_c) / 3.0
    r1 = 2 * pivot - last_l
    s1 = 2 * pivot - last_h
    r2 = pivot + (last_h - last_l)
    s2 = pivot - (last_h - last_l)
    
    # Quantitative Technical Score (-100 to +100)
    score = 0
    signals = []
    
    # RSI analysis
    curr_rsi = rsi_14[-1] if rsi_14[-1] is not None else 50.0
    if curr_rsi < 30:
        score += 35
        signals.append("RSI is Oversold (<30) - High probability reversal / accumulation zone.")
    elif curr_rsi > 70:
        score -= 35
        signals.append("RSI is Overbought (>70) - Risk of near-term consolidation or pullback.")
    else:
        signals.append(f"RSI is neutral at {curr_rsi:.1f}.")
        
    # Moving Average Golden/Death Cross analysis
    if sma_20[-1] and sma_50[-1]:
        if sma_20[-1] > sma_50[-1]:
            score += 25
            signals.append("Short-term SMA 20 is trading above SMA 50 (Bullish Momentum).")
        else:
            score -= 25
            signals.append("Short-term SMA 20 is trading below SMA 50 (Bearish Momentum).")
            
    # MACD momentum analysis
    curr_hist = macd_pack['histogram'][-1]
    prev_hist = macd_pack['histogram'][-2] if len(macd_pack['histogram']) > 1 else None
    if curr_hist is not None:
        if curr_hist > 0:
            score += 20
            if prev_hist and curr_hist > prev_hist:
                score += 10
                signals.append("MACD Histogram expanding positively (Strong Bullish Acceleration).")
            else:
                signals.append("MACD is positive above signal line.")
        else:
            score -= 20
            if prev_hist and curr_hist < prev_hist:
                score -= 10
                signals.append("MACD Histogram expanding negatively (Bearish Selling Pressure).")
            else:
                signals.append("MACD is below signal line.")
                
    # Bollinger Bands Position
    if bb['upper'][-1] and bb['lower'][-1]:
        b_upper = bb['upper'][-1]
        b_lower = bb['lower'][-1]
        if last_c >= b_upper:
            score -= 10
            signals.append("Price testing Upper Bollinger Band resistance.")
        elif last_c <= b_lower:
            score += 10
            signals.append("Price testing Lower Bollinger Band support.")
            
    # Classify Consensus Verdict
    if score >= 40:
        verdict = "Strong Buy"
        color = "#10B981" # Green
    elif score >= 15:
        verdict = "Buy"
        color = "#34D399" # Light green
    elif score <= -40:
        verdict = "Strong Sell"
        color = "#EF4444" # Red
    elif score <= -15:
        verdict = "Sell"
        color = "#F87171" # Light red
    else:
        verdict = "Neutral / Hold"
        color = "#F59E0B" # Amber
        
    return {
        'dates': dates,
        'sma_20': sma_20,
        'sma_50': sma_50,
        'sma_200': sma_200,
        'ema_12': ema_12,
        'ema_26': ema_26,
        'rsi_14': rsi_14,
        'macd': macd_pack['macd'],
        'macd_signal': macd_pack['signal'],
        'macd_hist': macd_pack['histogram'],
        'bb_upper': bb['upper'],
        'bb_middle': bb['middle'],
        'bb_lower': bb['lower'],
        'levels': {
            'pivot': round(pivot, 2),
            'r1': round(r1, 2),
            'r2': round(r2, 2),
            's1': round(s1, 2),
            's2': round(s2, 2)
        },
        'technical_score': max(-100, min(100, score)),
        'verdict': verdict,
        'verdict_color': color,
        'signals': signals
    }


# ==========================================
# 2. Time Series Forecasting Algorithms
# ==========================================

def solve_linear_system_2x2(a11, a12, a21, a22, b1, b2):
    det = a11 * a22 - a12 * a21
    if abs(det) < 1e-9:
        return 0.0, 0.0
    x1 = (b1 * a22 - b2 * a12) / det
    x2 = (a11 * b2 - a21 * b1) / det
    return x1, x2

def solve_ols_matrix(X: list[list[float]], y: list[float], l2_reg: float = 1e-4) -> list[float]:
    """Pure-python Ridge / Ordinary Least Squares solver with Gaussian elimination."""
    n_samples = len(X)
    n_features = len(X[0])
    
    # Compute X^T * X + lambda * I
    XtX = [[0.0] * n_features for _ in range(n_features)]
    for i in range(n_features):
        for j in range(n_features):
            val = sum(X[k][i] * X[k][j] for k in range(n_samples))
            if i == j:
                val += l2_reg
            XtX[i][j] = val
            
    # Compute X^T * y
    Xty = [sum(X[k][i] * y[k] for k in range(n_samples)) for i in range(n_features)]
    
    # Solve via Gaussian Elimination with partial pivoting
    A = [row[:] for row in XtX]
    b = Xty[:]
    
    for i in range(n_features):
        max_row = i
        for k in range(i + 1, n_features):
            if abs(A[k][i]) > abs(A[max_row][i]):
                max_row = k
        A[i], A[max_row] = A[max_row], A[i]
        b[i], b[max_row] = b[max_row], b[i]
        
        pivot = A[i][i]
        if abs(pivot) < 1e-12:
            pivot = 1e-6
            
        for k in range(i + 1, n_features):
            factor = A[k][i] / pivot
            for j in range(i, n_features):
                A[k][j] -= factor * A[i][j]
            b[k] -= factor * b[i]
            
    weights = [0.0] * n_features
    for i in range(n_features - 1, -1, -1):
        s = sum(A[i][j] * weights[j] for j in range(i + 1, n_features))
        weights[i] = (b[i] - s) / (A[i][i] if abs(A[i][i]) > 1e-12 else 1e-6)
        
    return weights


def forecast_arima(prices: list[float], horizon: int, p: int = 3, d: int = 1, q: int = 1):
    """
    ARIMA(p, d, q) Time Series Model
    - Differencing of order d=1 to achieve stationarity
    - AR(p) autoregression on differences
    - MA(q) moving average on innovation residuals
    - Cumulative reconstruction to original price scale with confidence bounds
    """
    diffs = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    if len(diffs) < p + 5:
        p = 1
        
    # Build lagged feature matrix for AR(p)
    X = []
    y = []
    for i in range(p, len(diffs)):
        row = [1.0] # intercept
        for lag in range(1, p + 1):
            row.append(diffs[i - lag])
        X.append(row)
        y.append(diffs[i])
        
    weights = solve_ols_matrix(X, y, l2_reg=0.01)
    
    # Calculate in-sample residuals for MA(q)
    residuals = []
    for i in range(len(X)):
        pred = sum(X[i][j] * weights[j] for j in range(len(weights)))
        residuals.append(y[i] - pred)
        
    # Estimate residual variance
    res_var = sum(r * r for r in residuals) / max(len(residuals) - len(weights), 1)
    res_std = math.sqrt(max(res_var, 1e-5))
    
    # MA(q) coefficient estimate (first-order autocorrelation of residuals)
    theta_1 = 0.0
    if len(residuals) > 2 and q > 0:
        cov = sum(residuals[k] * residuals[k - 1] for k in range(1, len(residuals)))
        theta_1 = max(-0.8, min(0.8, cov / (sum(r*r for r in residuals) + 1e-6)))
        
    # Multi-step ahead forecasting of differences
    recent_diffs = diffs[-p:]
    curr_diffs = recent_diffs[:]
    curr_res = residuals[-1] if residuals else 0.0
    
    pred_diffs = []
    for step in range(horizon):
        # AR component
        pred_d = weights[0]
        for lag in range(1, p + 1):
            pred_d += weights[lag] * curr_diffs[-lag]
            
        # MA component on immediate step
        if step == 0 and q > 0:
            pred_d += theta_1 * curr_res
            
        pred_diffs.append(pred_d)
        curr_diffs.append(pred_d)
        
    # Reconstruct integrated prices: y_{t+h} = y_t + sum(diffs)
    last_price = prices[-1]
    forecast_prices = []
    lower_bounds = []
    upper_bounds = []
    
    running_price = last_price
    for step, d_val in enumerate(pred_diffs, start=1):
        running_price += d_val
        forecast_prices.append(round(running_price, 2))
        
        # Analytic confidence interval expands with sqrt(step)
        uncertainty = 1.96 * res_std * math.sqrt(step) * (1.0 + 0.03 * step)
        lower_bounds.append(round(max(0.5, running_price - uncertainty), 2))
        upper_bounds.append(round(running_price + uncertainty, 2))
        
    return forecast_prices, lower_bounds, upper_bounds, res_std


def forecast_holt_linear(prices: list[float], horizon: int, alpha: float = 0.35, beta: float = 0.15, phi: float = 0.96):
    """
    Holt's Damped Linear Exponential Smoothing
    - Level: L_t = alpha * Y_t + (1 - alpha) * (L_{t-1} + phi * T_{t-1})
    - Trend: T_t = beta * (L_t - L_{t-1}) + (1 - beta) * phi * T_{t-1}
    - Forecast: Y_{t+h} = L_t + sum_{i=1}^h (phi^i * T_t)
    """
    L = prices[0]
    T = prices[1] - prices[0] if len(prices) > 1 else 0.0
    
    errors = []
    for t in range(1, len(prices)):
        y_val = prices[t]
        pred = L + phi * T
        errors.append(y_val - pred)
        
        L_prev = L
        L = alpha * y_val + (1.0 - alpha) * (L_prev + phi * T)
        T = beta * (L - L_prev) + (1.0 - beta) * phi * T
        
    error_variance = sum(e * e for e in errors) / max(len(errors), 1)
    std_err = math.sqrt(error_variance)
    
    forecast_prices = []
    lower_bounds = []
    upper_bounds = []
    
    trend_accum = 0.0
    for h in range(1, horizon + 1):
        trend_accum += (phi ** h) * T
        pred_price = L + trend_accum
        forecast_prices.append(round(pred_price, 2))
        
        # Standard error expansion
        margin = 1.96 * std_err * math.sqrt(1.0 + (h - 1) * (alpha ** 2))
        lower_bounds.append(round(max(0.5, pred_price - margin), 2))
        upper_bounds.append(round(pred_price + margin, 2))
        
    return forecast_prices, lower_bounds, upper_bounds, std_err


def forecast_ml_lag_regression(prices: list[float], horizon: int):
    """
    Supervised Machine Learning Autoregressive Multi-Lag Feature Model
    Features: Lags (1, 2, 3, 5, 10), Rolling Mean, Rolling Momentum, Trend Index
    """
    n = len(prices)
    max_lag = 10
    if n < max_lag + 10:
        max_lag = 3
        
    X = []
    y = []
    for i in range(max_lag, n):
        # Features
        t_norm = i / n
        lag_features = [prices[i - 1], prices[i - 2], prices[i - 3], prices[i - 5 if i >= 5 else i - 1]]
        roll_mean_5 = sum(prices[i-5:i]) / 5.0 if i >= 5 else prices[i-1]
        momentum_5 = (prices[i-1] - prices[i-5]) / prices[i-5] if i >= 5 else 0.0
        
        row = [1.0, t_norm, roll_mean_5, momentum_5] + lag_features
        X.append(row)
        y.append(prices[i])
        
    weights = solve_ols_matrix(X, y, l2_reg=0.05)
    
    # In-sample residuals
    residuals = [y[k] - sum(X[k][j] * weights[j] for j in range(len(weights))) for k in range(len(X))]
    std_err = math.sqrt(sum(r * r for r in residuals) / max(len(residuals) - len(weights), 1))
    
    # Recursive multi-step prediction
    curr_prices = prices[:]
    forecast_prices = []
    lower_bounds = []
    upper_bounds = []
    
    for step in range(1, horizon + 1):
        idx = len(curr_prices)
        t_norm = idx / n
        roll_5 = sum(curr_prices[-5:]) / 5.0
        mom_5 = (curr_prices[-1] - curr_prices[-5]) / curr_prices[-5]
        
        feat = [
            1.0, t_norm, roll_5, mom_5,
            curr_prices[-1], curr_prices[-2], curr_prices[-3], curr_prices[-5]
        ]
        pred = sum(feat[j] * weights[j] for j in range(len(weights)))
        
        # Damping extreme runaway extrapolations
        pred = max(curr_prices[-1] * 0.7, min(curr_prices[-1] * 1.3, pred))
        
        forecast_prices.append(round(pred, 2))
        curr_prices.append(pred)
        
        margin = 1.96 * std_err * math.sqrt(step)
        lower_bounds.append(round(max(0.5, pred - margin), 2))
        upper_bounds.append(round(pred + margin, 2))
        
    return forecast_prices, lower_bounds, upper_bounds, std_err


def forecast_monte_carlo(prices: list[float], horizon: int, num_simulations: int = 150):
    """
    Monte Carlo Simulation using Geometric Brownian Motion (GBM)
    dS = S * (mu * dt + sigma * dW)
    Returns: Median Path, 10th percentile (Bear), 90th percentile (Bull), and 5 sample trajectories
    """
    n = len(prices)
    returns = [math.log(prices[i] / prices[i - 1]) for i in range(1, n)]
    
    # Historical drift and daily volatility
    dt = 1.0 # 1 day step
    mu = sum(returns) / len(returns)
    variance = sum((r - mu) ** 2 for r in returns) / (len(returns) - 1)
    sigma = math.sqrt(variance)
    
    drift = (mu - 0.5 * (sigma ** 2)) * dt
    vol_scale = sigma * math.sqrt(dt)
    
    last_price = prices[-1]
    
    all_simulations = []
    rng = random.Random(42)
    
    for _ in range(num_simulations):
        path = []
        p = last_price
        for _ in range(horizon):
            z = rng.gauss(0, 1)
            p = p * math.exp(drift + vol_scale * z)
            path.append(round(p, 2))
        all_simulations.append(path)
        
    # Aggregate statistics per day
    median_path = []
    lower_10th = []
    upper_90th = []
    
    for h in range(horizon):
        day_values = sorted([sim[h] for sim in all_simulations])
        med_val = day_values[len(day_values) // 2]
        p10 = day_values[int(len(day_values) * 0.10)]
        p90 = day_values[int(len(day_values) * 0.90)]
        
        median_path.append(med_val)
        lower_10th.append(p10)
        upper_90th.append(p90)
        
    # Select 5 sample paths to visualize individual trajectories
    sample_paths = [all_simulations[i] for i in [0, 25, 50, 75, 100]]
    
    return median_path, lower_10th, upper_90th, sample_paths, sigma * math.sqrt(252)


def compute_metrics(actual: list[float], predicted: list[float]) -> dict:
    """Calculates quantitative performance metrics: RMSE, MAE, MAPE, R2, Directional Accuracy %."""
    k = min(len(actual), len(predicted))
    if k == 0:
        return {'rmse': 0.0, 'mae': 0.0, 'mape': 0.0, 'r2': 0.0, 'dir_acc': 50.0}
        
    act = actual[:k]
    pred = predicted[:k]
    
    # MAE & RMSE & MAPE
    mae = sum(abs(a - p) for a, p in zip(act, pred)) / k
    rmse = math.sqrt(sum((a - p) ** 2 for a, p in zip(act, pred)) / k)
    mape = (sum(abs((a - p) / (a if a != 0 else 1.0)) for a, p in zip(act, pred)) / k) * 100.0
    
    # R-squared
    mean_act = sum(act) / k
    ss_tot = sum((a - mean_act) ** 2 for a in act)
    ss_res = sum((a - p) ** 2 for a, p in zip(act, pred))
    r2 = 1.0 - (ss_res / (ss_tot + 1e-6)) if ss_tot > 0 else 0.0
    r2 = max(-1.0, min(0.99, r2))
    
    # Directional Accuracy (Next-day sign match)
    dir_matches = 0
    total_dirs = 0
    for i in range(1, k):
        act_dir = 1 if act[i] >= act[i-1] else -1
        pred_dir = 1 if pred[i] >= pred[i-1] else -1
        if act_dir == pred_dir:
            dir_matches += 1
        total_dirs += 1
    dir_acc = (dir_matches / total_dirs * 100.0) if total_dirs > 0 else 50.0
    
    return {
        'rmse': round(rmse, 2),
        'mae': round(mae, 2),
        'mape': round(mape, 2),
        'r2': round(r2, 3),
        'directional_accuracy': round(dir_acc, 1)
    }


def generate_future_dates(start_date_str: str, horizon: int) -> list[str]:
    start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
    dates = []
    curr = start_dt + timedelta(days=1)
    while len(dates) < horizon:
        if curr.weekday() < 5: # Monday to Friday
            dates.append(curr.strftime('%Y-%m-%d'))
        curr += timedelta(days=1)
    return dates


def run_time_series_prediction(candles: list[dict], model_name: str = 'ensemble', horizon: int = 14) -> dict:
    """
    Main orchestration function for time series analysis & forecasting.
    Supports models:
    - 'arima': ARIMA(p,d,q)
    - 'holt': Holt's Damped Linear Exponential Smoothing
    - 'ml_regression': Multi-lag Supervised Regression
    - 'monte_carlo': Geometric Brownian Motion (GBM)
    - 'ensemble': Dynamic Variance-Weighted Multi-Model Blend
    """
    closes = [c['close'] for c in candles]
    last_date = candles[-1]['date']
    last_price = closes[-1]
    
    future_dates = generate_future_dates(last_date, horizon)
    sample_paths = []
    
    # Run in-sample backtest to compute realistic evaluation metrics
    test_len = min(20, max(5, int(len(closes) * 0.15)))
    train_slice = closes[:-test_len]
    test_actual = closes[-test_len:]
    
    if model_name == 'arima':
        forecast_prices, lower_bounds, upper_bounds, _ = forecast_arima(closes, horizon)
        # Backtest for metrics
        bt_preds, _, _, _ = forecast_arima(train_slice, test_len)
        model_display = "ARIMA (AutoRegressive Integrated Moving Average)"
        model_desc = "Captures non-stationary price trends via differencing, autoregressive momentum lags, and moving average residual corrections."
        
    elif model_name == 'holt':
        forecast_prices, lower_bounds, upper_bounds, _ = forecast_holt_linear(closes, horizon)
        bt_preds, _, _, _ = forecast_holt_linear(train_slice, test_len)
        model_display = "Holt's Damped Linear Trend"
        model_desc = "Double exponential smoothing modeling adaptive price levels with damped trend growth projection."
        
    elif model_name == 'ml_regression':
        forecast_prices, lower_bounds, upper_bounds, _ = forecast_ml_lag_regression(closes, horizon)
        bt_preds, _, _, _ = forecast_ml_lag_regression(train_slice, test_len)
        model_display = "Multi-Lag Feature Regression"
        model_desc = "Supervised machine learning regressor leveraging lagged price steps, rolling momentum, and volatility features."
        
    elif model_name == 'monte_carlo':
        median_path, lower_10th, upper_90th, sample_paths, ann_vol = forecast_monte_carlo(closes, horizon)
        forecast_prices = median_path
        lower_bounds = lower_10th
        upper_bounds = upper_90th
        # Backtest
        bt_preds, _, _, _, _ = forecast_monte_carlo(train_slice, test_len)
        model_display = "Monte Carlo Simulation (Geometric Brownian Motion)"
        model_desc = f"Simulates 150 probabilistic stochastic paths using historical drift and annualized volatility ({ann_vol:.1f}%)."
        
    else: # ensemble (default)
        arima_f, arima_l, arima_u, arima_err = forecast_arima(closes, horizon)
        holt_f, holt_l, holt_u, holt_err = forecast_holt_linear(closes, horizon)
        ml_f, ml_l, ml_u, ml_err = forecast_ml_lag_regression(closes, horizon)
        
        # Inverse-variance weighting
        w_arima = 1.0 / (arima_err + 1e-5)
        w_holt = 1.0 / (holt_err + 1e-5)
        w_ml = 1.0 / (ml_err + 1e-5)
        total_w = w_arima + w_holt + w_ml
        
        w_arima /= total_w
        w_holt /= total_w
        w_ml /= total_w
        
        forecast_prices = [
            round(w_arima * arima_f[i] + w_holt * holt_f[i] + w_ml * ml_f[i], 2)
            for i in range(horizon)
        ]
        lower_bounds = [
            round(w_arima * arima_l[i] + w_holt * holt_l[i] + w_ml * ml_l[i], 2)
            for i in range(horizon)
        ]
        upper_bounds = [
            round(w_arima * arima_u[i] + w_holt * holt_u[i] + w_ml * ml_u[i], 2)
            for i in range(horizon)
        ]
        
        # Backtest for ensemble
        bt_a, _, _, _ = forecast_arima(train_slice, test_len)
        bt_h, _, _, _ = forecast_holt_linear(train_slice, test_len)
        bt_m, _, _, _ = forecast_ml_lag_regression(train_slice, test_len)
        bt_preds = [
            round(w_arima * bt_a[i] + w_holt * bt_h[i] + w_ml * bt_m[i], 2)
            for i in range(test_len)
        ]
        
        model_display = "Ensemble Consensus Model"
        model_desc = "Optimal dynamic inverse-variance blend of ARIMA, Holt's Trend, and Lag Regression for superior generalization."
        
    metrics = compute_metrics(test_actual, bt_preds)
    
    target_price = forecast_prices[-1]
    expected_change = round(target_price - last_price, 2)
    expected_change_pct = round((expected_change / last_price) * 100, 2)
    
    # Classify trajectory
    if expected_change_pct > 3.0:
        trend_call = "Bullish Uptrend"
        trend_call_color = "#10B981"
    elif expected_change_pct < -3.0:
        trend_call = "Bearish Downtrend"
        trend_call_color = "#EF4444"
    else:
        trend_call = "Sideways / Rangebound"
        trend_call_color = "#F59E0B"
        
    return {
        'model_name': model_name,
        'model_display': model_display,
        'model_description': model_desc,
        'horizon_days': horizon,
        'last_price': last_price,
        'target_price': target_price,
        'expected_change': expected_change,
        'expected_change_pct': expected_change_pct,
        'trend_call': trend_call,
        'trend_call_color': trend_call_color,
        'future_dates': future_dates,
        'forecast_prices': forecast_prices,
        'lower_bounds': lower_bounds,
        'upper_bounds': upper_bounds,
        'sample_paths': sample_paths,
        'metrics': metrics
    }
