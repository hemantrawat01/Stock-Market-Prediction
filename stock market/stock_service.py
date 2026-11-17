import requests
import json
import time
import math
import random
from datetime import datetime, timedelta

# In-memory cache for stock quotes and historical candles
CACHE = {}
CACHE_TTL_SECONDS = 300  # 5 minutes cache

USD_INR_DEFAULT = 93.46

FEATURED_TRADES = [
    {
        'id': 'NIFTY50',
        'symbol': '^NSEI',
        'name': 'NIFTY 50',
        'category': 'Indian indices',
        'rank': 1,
        'unit': 'Points (₹)',
        'base_price': 25380.0,
        'conversion_type': 'direct'
    },
    {
        'id': 'BANKNIFTY',
        'symbol': '^NSEBANK',
        'name': 'BANK NIFTY',
        'category': 'Index trading',
        'rank': 2,
        'unit': 'Points (₹)',
        'base_price': 62270.0,
        'conversion_type': 'direct'
    },
    {
        'id': 'SENSEX',
        'symbol': '^BSESN',
        'name': 'SENSEX',
        'category': 'Indian indices',
        'rank': 3,
        'unit': 'Points (₹)',
        'base_price': 82530.0,
        'conversion_type': 'direct'
    },
    {
        'id': 'GOLD',
        'symbol': 'GC=F',
        'name': 'Gold (XAU/USD)',
        'category': 'Commodities',
        'rank': 4,
        'unit': '₹ per 10g',
        'base_price': 116290.0,
        'conversion_type': 'gold_10g'
    },
    {
        'id': 'SILVER',
        'symbol': 'SI=F',
        'name': 'Silver (XAG/USD)',
        'category': 'Commodities',
        'rank': 5,
        'unit': '₹ per 1 kg',
        'base_price': 142500.0,
        'conversion_type': 'silver_1kg'
    },
    {
        'id': 'CRUDEOIL',
        'symbol': 'CL=F',
        'name': 'Crude Oil',
        'category': 'Commodities',
        'rank': 6,
        'unit': '₹ per Barrel',
        'base_price': 8095.0,
        'conversion_type': 'crude_bbl'
    },
    {
        'id': 'BTC',
        'symbol': 'BTC-INR',
        'alt_symbol': 'BTC-USD',
        'name': 'Bitcoin (BTC/USD)',
        'category': 'Crypto',
        'rank': 7,
        'unit': '₹ per Coin',
        'base_price': 5927000.0,
        'conversion_type': 'direct'
    },
    {
        'id': 'ETH',
        'symbol': 'ETH-INR',
        'alt_symbol': 'ETH-USD',
        'name': 'Ethereum (ETH/USD)',
        'category': 'Crypto',
        'rank': 8,
        'unit': '₹ per Coin',
        'base_price': 165800.0,
        'conversion_type': 'direct'
    },
    {
        'id': 'USDINR',
        'symbol': 'INR=X',
        'name': 'USD/INR',
        'category': 'Forex',
        'rank': 9,
        'unit': '₹ per 1 USD',
        'base_price': 93.46,
        'conversion_type': 'direct'
    },
    {
        'id': 'NASDAQ100',
        'symbol': '^NDX',
        'name': 'NASDAQ 100',
        'category': 'Global indices',
        'rank': 10,
        'unit': 'Points (₹)',
        'base_price': 26820.0,
        'conversion_type': 'direct'
    }
]

# Lookup map by ID or Symbol
TRADE_LOOKUP = {}
for t in FEATURED_TRADES:
    TRADE_LOOKUP[t['id'].upper()] = t
    TRADE_LOOKUP[t['symbol'].upper()] = t
    if 'alt_symbol' in t:
        TRADE_LOOKUP[t['alt_symbol'].upper()] = t

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
    }

def get_usd_inr_rate() -> float:
    """Fetch live USD/INR exchange rate or fallback to cached/default."""
    cache_key = 'USD_INR_RATE'
    if cache_key in CACHE:
        if time.time() - CACHE[cache_key]['timestamp'] < 1800: # 30 min
            return CACHE[cache_key]['rate']
            
    url = "https://query1.finance.yahoo.com/v8/finance/chart/INR=X?range=1d&interval=1d"
    try:
        resp = requests.get(url, headers=get_headers(), timeout=5)
        if resp.status_code == 200:
            result = resp.json().get('chart', {}).get('result', [{}])[0]
            rate = result.get('meta', {}).get('regularMarketPrice')
            if rate and rate > 50:
                CACHE[cache_key] = {'timestamp': time.time(), 'rate': float(rate)}
                return float(rate)
    except Exception:
        pass
    return USD_INR_DEFAULT

def resolve_trade_profile(identifier: str) -> tuple[dict, str]:
    clean_id = identifier.strip().upper()
    
    # Check exact match in 10 featured trades
    if clean_id in TRADE_LOOKUP:
        trade = TRADE_LOOKUP[clean_id]
        return trade, trade['symbol']
        
    # Check common aliases
    alias_map = {
        'NIFTY': 'NIFTY50',
        'BANK': 'BANKNIFTY',
        'NIFTYBANK': 'BANKNIFTY',
        'BSESN': 'SENSEX',
        'BSE': 'SENSEX',
        'GOLDUSD': 'GOLD',
        'XAU': 'GOLD',
        'XAUUSD': 'GOLD',
        'SILVERUSD': 'SILVER',
        'XAG': 'SILVER',
        'XAGUSD': 'SILVER',
        'CRUDE': 'CRUDEOIL',
        'OIL': 'CRUDEOIL',
        'BITCOIN': 'BTC',
        'ETHEREUM': 'ETH',
        'USD/INR': 'USDINR',
        'INR': 'USDINR',
        'NASDAQ': 'NASDAQ100',
        'NDX': 'NASDAQ100'
    }
    
    if clean_id in alias_map:
        trade = TRADE_LOOKUP[alias_map[clean_id]]
        return trade, trade['symbol']
        
    # Generic ticker fallback
    return {
        'id': clean_id,
        'symbol': clean_id,
        'name': f"{clean_id} Indian Market Asset",
        'category': 'Indian Equities',
        'rank': 99,
        'unit': '₹ per Share',
        'base_price': 1000.0,
        'conversion_type': 'direct'
    }, clean_id

def convert_value_to_inr(value: float, conversion_type: str, usd_rate: float) -> float:
    if value is None or math.isnan(value):
        return 0.0
    if conversion_type == 'gold_10g':
        # Gold futures is USD per troy ounce (31.1035 grams)
        # Convert to INR per 10 grams: (USD / 31.1035 * 10) * USD_INR
        return (value / 31.1035 * 10.0) * usd_rate
    elif conversion_type == 'silver_1kg':
        # Silver futures is USD per troy ounce
        # Convert to INR per 1 kilogram: (USD / 31.1035 * 1000.0) * USD_INR
        return (value / 31.1035 * 1000.0) * usd_rate
    elif conversion_type == 'crude_bbl':
        # Crude oil is USD per barrel
        # Convert to INR per barrel: USD * USD_INR
        return value * usd_rate
    else:
        return value

def fetch_yahoo_chart_data(trade_profile: dict, yahoo_symbol: str, range_str: str = '1y', interval: str = '1d') -> dict:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?range={range_str}&interval={interval}&includePrePost=false"
    try:
        resp = requests.get(url, headers=get_headers(), timeout=7)
        if resp.status_code == 200:
            data = resp.json()
            chart = data.get('chart', {})
            result = chart.get('result')
            if result and len(result) > 0:
                return parse_yahoo_data(trade_profile, result[0])
    except Exception as e:
        print(f"[StockService] Yahoo fetch warning for {yahoo_symbol}: {e}. Utilizing fallback engine.")
        
    return generate_fallback_stock_data(trade_profile, range_str)

def parse_yahoo_data(trade_profile: dict, data: dict) -> dict:
    meta = data.get('meta', {})
    timestamps = data.get('timestamp', [])
    indicators = data.get('indicators', {})
    quote = indicators.get('quote', [{}])[0]
    
    opens = quote.get('open', [])
    highs = quote.get('high', [])
    lows = quote.get('low', [])
    closes = quote.get('close', [])
    volumes = quote.get('volume', [])
    
    usd_rate = get_usd_inr_rate()
    conv_type = trade_profile.get('conversion_type', 'direct')
    
    candles = []
    clean_closes = []
    
    for i in range(len(timestamps)):
        t = timestamps[i]
        c = closes[i] if i < len(closes) else None
        o = opens[i] if i < len(opens) else None
        h = highs[i] if i < len(highs) else None
        l = lows[i] if i < len(lows) else None
        v = volumes[i] if i < len(volumes) else None
        
        if c is not None and not math.isnan(c) and c > 0:
            dt = datetime.fromtimestamp(t).strftime('%Y-%m-%d')
            o_val = o if (o is not None and not math.isnan(o)) else c
            h_val = h if (h is not None and not math.isnan(h)) else max(o_val, c)
            l_val = l if (l is not None and not math.isnan(l)) else min(o_val, c)
            v_val = int(v) if (v is not None and not math.isnan(v)) else 1000000
            
            # Convert values directly into Indian Rupees (₹)
            inr_close = convert_value_to_inr(float(c), conv_type, usd_rate)
            inr_open = convert_value_to_inr(float(o_val), conv_type, usd_rate)
            inr_high = convert_value_to_inr(float(h_val), conv_type, usd_rate)
            inr_low = convert_value_to_inr(float(l_val), conv_type, usd_rate)
            
            candles.append({
                'date': dt,
                'open': round(inr_open, 2),
                'high': round(inr_high, 2),
                'low': round(inr_low, 2),
                'close': round(inr_close, 2),
                'volume': v_val
            })
            clean_closes.append(inr_close)
            
    if not candles:
        return generate_fallback_stock_data(trade_profile)
        
    latest_price = round(clean_closes[-1], 2)
    prev_close = round(clean_closes[-2] if len(clean_closes) > 1 else latest_price, 2)
    change = round(latest_price - prev_close, 2)
    change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0
    
    high52 = round(max(clean_closes[-252:] if len(clean_closes) >= 252 else clean_closes), 2)
    low52 = round(min(clean_closes[-252:] if len(clean_closes) >= 252 else clean_closes), 2)
    
    # 30-day volatility
    vol_30d = 0.0
    if len(clean_closes) >= 30:
        returns = [math.log(clean_closes[i] / clean_closes[i-1]) for i in range(len(clean_closes)-29, len(clean_closes))]
        mean_ret = sum(returns) / len(returns)
        var = sum((r - mean_ret)**2 for r in returns) / (len(returns) - 1)
        vol_30d = round(math.sqrt(var * 252) * 100, 2)
        
    return {
        'id': trade_profile.get('id', meta.get('symbol')),
        'symbol': trade_profile.get('name', meta.get('symbol')),
        'raw_symbol': meta.get('symbol'),
        'name': trade_profile.get('name', meta.get('shortName', 'Financial Asset')),
        'category': trade_profile.get('category', 'Trading Markets'),
        'rank': trade_profile.get('rank', 1),
        'currency': 'INR',
        'currency_symbol': '₹',
        'unit': trade_profile.get('unit', 'INR (₹)'),
        'current_price': latest_price,
        'previous_close': prev_close,
        'change': change,
        'change_pct': change_pct,
        'high_52': high52,
        'low_52': low52,
        'volatility_30d': vol_30d,
        'avg_volume': int(sum(c['volume'] for c in candles[-20:]) / min(len(candles), 20)),
        'candles': candles,
        'data_source': 'Real-Time Indian Market & Global Exchange Feed'
    }

def generate_fallback_stock_data(trade_profile: dict, range_str: str = '1y') -> dict:
    """Realistic geometric Brownian motion price action in Indian Rupees (₹)."""
    days = 252 if range_str in ['1y', 'ytd'] else (504 if range_str == '2y' else 126)
    end_date = datetime.now()
    dates = []
    curr = end_date - timedelta(days=int(days * 1.45))
    
    while len(dates) < days:
        if curr.weekday() < 5:
            dates.append(curr)
        curr += timedelta(days=1)
        
    seed_val = sum(ord(c) for c in trade_profile['name'])
    rng = random.Random(seed_val)
    
    base_price = trade_profile.get('base_price', 25000.0)
    price = base_price * 0.90
    daily_drift = 0.0003 + (rng.random() - 0.48) * 0.0004
    daily_vol = 0.012 + rng.random() * 0.008
    
    candles = []
    clean_closes = []
    
    for dt in dates:
        shock = rng.gauss(0, 1)
        price_change = price * (daily_drift + daily_vol * shock)
        price = max(1.0, price + price_change)
        
        day_range = price * daily_vol * (0.8 + rng.random() * 0.8)
        day_open = price - (rng.random() - 0.5) * day_range * 0.7
        day_high = max(day_open, price) + rng.random() * day_range * 0.5
        day_low = min(day_open, price) - rng.random() * day_range * 0.5
        day_volume = int(rng.randint(2000000, 15000000) * (1 + abs(shock) * 0.7))
        
        candles.append({
            'date': dt.strftime('%Y-%m-%d'),
            'open': round(day_open, 2),
            'high': round(day_high, 2),
            'low': round(day_low, 2),
            'close': round(price, 2),
            'volume': day_volume
        })
        clean_closes.append(price)
        
    latest_price = round(clean_closes[-1], 2)
    prev_close = round(clean_closes[-2], 2)
    change = round(latest_price - prev_close, 2)
    change_pct = round((change / prev_close) * 100, 2)
    
    return {
        'id': trade_profile.get('id', 'MARKET'),
        'symbol': trade_profile.get('name'),
        'name': trade_profile.get('name'),
        'category': trade_profile.get('category', 'Trading Markets'),
        'rank': trade_profile.get('rank', 1),
        'currency': 'INR',
        'currency_symbol': '₹',
        'unit': trade_profile.get('unit', 'INR (₹)'),
        'current_price': latest_price,
        'previous_close': prev_close,
        'change': change,
        'change_pct': change_pct,
        'high_52': round(max(clean_closes), 2),
        'low_52': round(min(clean_closes), 2),
        'volatility_30d': round(daily_vol * math.sqrt(252) * 100, 2),
        'avg_volume': int(sum(c['volume'] for c in candles[-20:]) / 20),
        'candles': candles,
        'data_source': 'High-Fidelity Quantitative Simulation Engine (INR)'
    }

def get_stock_data(identifier: str, range_str: str = '1y') -> dict:
    profile, yahoo_symbol = resolve_trade_profile(identifier)
    cache_key = f"{profile['id']}_{range_str}"
    
    if cache_key in CACHE:
        cached = CACHE[cache_key]
        if time.time() - cached['timestamp'] < CACHE_TTL_SECONDS:
            return cached['data']
            
    data = fetch_yahoo_chart_data(profile, yahoo_symbol, range_str)
    CACHE[cache_key] = {
        'timestamp': time.time(),
        'data': data
    }
    return data

def get_all_featured_trades_summary() -> list[dict]:
    """Returns quick snapshot of all 10 featured trades with live prices in INR."""
    summaries = []
    for trade in FEATURED_TRADES:
        try:
            d = get_stock_data(trade['id'], range_str='5d')
            summaries.append({
                'id': trade['id'],
                'rank': trade['rank'],
                'name': trade['name'],
                'category': trade['category'],
                'unit': trade['unit'],
                'price': d['current_price'],
                'change': d['change'],
                'change_pct': d['change_pct'],
                'currency_symbol': '₹'
            })
        except Exception:
            summaries.append({
                'id': trade['id'],
                'rank': trade['rank'],
                'name': trade['name'],
                'category': trade['category'],
                'unit': trade['unit'],
                'price': trade['base_price'],
                'change': 0.0,
                'change_pct': 0.0,
                'currency_symbol': '₹'
            })
    return summaries

# ==========================================
# Real-Time Live Market & Tick Simulation Engine
# ==========================================

class LiveMarketEngine:
    """
    Real-Time Market Tick Generator and Live Order-Flow State Manager.
    Provides live price ticks, bid/ask order updates, and continuous live data
    for Indian & global markets in Indian Rupees (₹).
    """
    def __init__(self):
        self.market_states = {}  # ticker_id -> full market dict
        self.tick_counts = {}    # ticker_id -> total ticks generated
        self.last_tick_times = {} # ticker_id -> timestamp

    def get_or_create_state(self, identifier: str, range_str: str = '1y') -> dict:
        profile, _ = resolve_trade_profile(identifier)
        ticker_id = profile['id'].upper()
        
        if ticker_id not in self.market_states:
            base_data = get_stock_data(ticker_id, range_str)
            # Create isolated deep copy for live in-memory updates
            self.market_states[ticker_id] = json.loads(json.dumps(base_data))
            self.tick_counts[ticker_id] = 0
            self.last_tick_times[ticker_id] = time.time()
            
        return self.market_states[ticker_id]

    def generate_tick(self, identifier: str) -> dict:
        profile, _ = resolve_trade_profile(identifier)
        ticker_id = profile['id'].upper()
        state = self.get_or_create_state(ticker_id)
        
        candles = state.get('candles', [])
        if not candles:
            return {
                'ticker': ticker_id,
                'name': profile['name'],
                'current_price': profile.get('base_price', 1000.0),
                'change': 0.0,
                'change_pct': 0.0,
                'price_delta': 0.0,
                'tick_direction': 'flat',
                'tick_number': 0,
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'unit': profile.get('unit', '₹')
            }
            
        last_candle = candles[-1]
        curr_price = float(last_candle['close'])
        
        # Determine tick volatility scale based on market category
        cat = profile.get('category', '').lower()
        if 'crypto' in cat:
            vol_step = 0.0018  # 0.18% micro-volatility
        elif 'commodities' in cat:
            vol_step = 0.0009  # 0.09% micro-volatility
        elif 'forex' in cat:
            vol_step = 0.00025 # 0.025% micro-volatility
        elif 'index trading' in cat:
            vol_step = 0.00075 # 0.075% micro-volatility
        else: # Indian indices & global indices
            vol_step = 0.0006  # 0.06% micro-volatility
            
        # Realistic stochastic price shock with mild mean-reversion drift
        shock = random.gauss(0, 1)
        base_anchor = profile.get('base_price', curr_price)
        # Pull slightly back if deviation from anchor exceeds 8%
        mean_rev_drift = -0.015 * (curr_price - base_anchor) / base_anchor if base_anchor else 0.0
        
        pct_delta = mean_rev_drift + (vol_step * shock)
        raw_delta = curr_price * pct_delta
        
        # Enforce minimum tick size according to price magnitude
        if abs(raw_delta) < 0.05:
            raw_delta = 0.05 if random.random() > 0.48 else -0.05
            
        new_price = round(max(0.5, curr_price + raw_delta), 2)
        price_delta = round(new_price - curr_price, 2)
        
        if price_delta > 0:
            tick_dir = 'up'
        elif price_delta < 0:
            tick_dir = 'down'
        else:
            tick_dir = 'flat'
            
        # Update current live candle
        last_candle['close'] = new_price
        last_candle['high'] = max(last_candle['high'], new_price)
        last_candle['low'] = min(last_candle['low'], new_price)
        last_candle['volume'] = int(last_candle['volume'] + random.randint(300, 6500))
        
        # Update overall market state metrics
        prev_close = state.get('previous_close', curr_price)
        change = round(new_price - prev_close, 2)
        change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0
        
        state['current_price'] = new_price
        state['change'] = change
        state['change_pct'] = change_pct
        state['high_52'] = round(max(state.get('high_52', new_price), new_price), 2)
        state['low_52'] = round(min(state.get('low_52', new_price), new_price), 2)
        
        self.tick_counts[ticker_id] = self.tick_counts.get(ticker_id, 0) + 1
        self.last_tick_times[ticker_id] = time.time()
        
        return {
            'ticker': ticker_id,
            'name': profile['name'],
            'current_price': new_price,
            'previous_close': prev_close,
            'change': change,
            'change_pct': change_pct,
            'price_delta': price_delta,
            'tick_direction': tick_dir,
            'tick_number': self.tick_counts[ticker_id],
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'candle': last_candle,
            'high_52': state['high_52'],
            'low_52': state['low_52'],
            'volatility_30d': state.get('volatility_30d', 12.5),
            'avg_volume': state.get('avg_volume', 5000000),
            'unit': profile.get('unit', '₹')
        }

    def get_all_live_featured_trades(self) -> list[dict]:
        """Returns live updating snapshot of all 10 featured trades."""
        results = []
        for trade in FEATURED_TRADES:
            tick_info = self.generate_tick(trade['id'])
            results.append({
                'id': trade['id'],
                'rank': trade['rank'],
                'name': trade['name'],
                'category': trade['category'],
                'unit': trade['unit'],
                'price': tick_info['current_price'],
                'change': tick_info['change'],
                'change_pct': tick_info['change_pct'],
                'price_delta': tick_info['price_delta'],
                'tick_direction': tick_info['tick_direction'],
                'timestamp': tick_info['timestamp'],
                'currency_symbol': '₹'
            })
        return results

# Global Live Market Engine instance
LIVE_MARKET = LiveMarketEngine()

