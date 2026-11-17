from flask import Flask, render_template, request, jsonify, session
import os
import json
from database import (
    init_db, register_user, authenticate_user, update_password,
    reset_password_direct, update_user_profile, get_user_watchlist,
    toggle_watchlist_item, save_prediction_record, get_user_predictions
)
from stock_service import get_stock_data, FEATURED_TRADES, get_all_featured_trades_summary, LIVE_MARKET
from time_series_engine import calculate_indicators_pack, run_time_series_prediction

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'stock-market-pred-ultra-secret-2026')
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Initialize SQLite database on startup
init_db()

@app.route('/')
def index():
    return render_template('index.html')

# ==========================================
# Authentication Endpoints
# ==========================================

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    email = data.get('email', '')
    password = data.get('password', '')
    full_name = data.get('full_name', '')
    
    success, message, user = register_user(email, password, full_name)
    if success:
        session['user_id'] = user['id']
        session['email'] = user['email']
        session['full_name'] = user['full_name']
        session['theme_pref'] = user.get('theme_pref', 'dark')
        return jsonify({'success': True, 'message': message, 'user': user})
    return jsonify({'success': False, 'message': message}), 400

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email', '')
    password = data.get('password', '')
    
    success, message, user = authenticate_user(email, password)
    if success:
        session['user_id'] = user['id']
        session['email'] = user['email']
        session['full_name'] = user['full_name']
        session['theme_pref'] = user.get('theme_pref', 'dark')
        return jsonify({'success': True, 'message': message, 'user': user})
    return jsonify({'success': False, 'message': message}), 401

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully.'})

@app.route('/api/auth/me', methods=['GET'])
def api_me():
    user_id = session.get('user_id')
    if user_id:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': user_id,
                'email': session.get('email'),
                'full_name': session.get('full_name'),
                'theme_pref': session.get('theme_pref', 'dark')
            }
        })
    return jsonify({'authenticated': False, 'user': None})

@app.route('/api/auth/update-password', methods=['POST'])
def api_update_password():
    """Allows user to edit their password with confirmation of current password."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first to update password.'}), 401
        
    data = request.get_json() or {}
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    success, message = update_password(user_id, current_password, new_password)
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'message': message}), 400

@app.route('/api/auth/reset-password', methods=['POST'])
def api_reset_password():
    """Allows direct password reset by Gmail address."""
    data = request.get_json() or {}
    email = data.get('email', '')
    new_password = data.get('new_password', '')
    
    success, message = reset_password_direct(email, new_password)
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'message': message}), 400

@app.route('/api/auth/update-profile', methods=['POST'])
def api_update_profile():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not authenticated.'}), 401
        
    data = request.get_json() or {}
    full_name = data.get('full_name', session.get('full_name', ''))
    theme_pref = data.get('theme_pref', session.get('theme_pref', 'dark'))
    
    success, message = update_user_profile(user_id, full_name, theme_pref)
    if success:
        session['full_name'] = full_name
        session['theme_pref'] = theme_pref
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'message': message}), 400

# ==========================================
# Stock & Time Series Analysis Endpoints
# ==========================================

@app.route('/api/stock/<ticker>', methods=['GET'])
def api_stock_data(ticker):
    range_str = request.args.get('range', '1y')
    stock_info = get_stock_data(ticker, range_str)
    return jsonify(stock_info)

@app.route('/api/stock/<ticker>/indicators', methods=['GET'])
def api_stock_indicators(ticker):
    range_str = request.args.get('range', '1y')
    stock_info = get_stock_data(ticker, range_str)
    candles = stock_info.get('candles', [])
    if not candles:
        return jsonify({'error': 'No candle data available'}), 404
        
    indicators = calculate_indicators_pack(candles)
    return jsonify(indicators)

@app.route('/api/stock/<ticker>/predict', methods=['POST'])
def api_stock_predict(ticker):
    data = request.get_json() or {}
    model_name = data.get('model', 'ensemble')
    horizon = int(data.get('horizon', 14))
    range_str = data.get('range', '1y')
    
    # Cap horizon within sensible limits [3, 90]
    horizon = max(3, min(90, horizon))
    
    stock_info = get_stock_data(ticker, range_str)
    candles = stock_info.get('candles', [])
    if not candles:
        return jsonify({'error': 'No candle data found for prediction'}), 404
        
    prediction_result = run_time_series_prediction(candles, model_name, horizon)
    
    # If user is authenticated, log this prediction in their history
    user_id = session.get('user_id')
    if user_id:
        metrics_json = json.dumps(prediction_result['metrics'])
        save_prediction_record(
            user_id=user_id,
            ticker=ticker,
            model=prediction_result['model_display'],
            horizon=horizon,
            predicted_price=prediction_result['target_price'],
            change_pct=prediction_result['expected_change_pct'],
            metrics_json=metrics_json
        )
        
    return jsonify(prediction_result)

@app.route('/api/trades/featured', methods=['GET'])
def api_featured_trades():
    trades = get_all_featured_trades_summary()
    return jsonify(trades)

@app.route('/api/trades/live-featured', methods=['GET'])
def api_live_featured_trades():
    """Generates continuous live ticks for all 10 featured trades."""
    trades = LIVE_MARKET.get_all_live_featured_trades()
    return jsonify(trades)

@app.route('/api/stock/<ticker>/live-tick', methods=['GET', 'POST'])
def api_stock_live_tick(ticker):
    """
    Triggers an instant live tick for the requested asset, updates its real-time daily candle,
    and optionally executes instantaneous live technical analysis and time series re-prediction.
    """
    predict_flag = request.args.get('predict', 'false').lower() in ['1', 'true', 'yes']
    model_name = request.args.get('model', 'ensemble')
    horizon = int(request.args.get('horizon', 14))
    range_str = request.args.get('range', '1y')
    
    # Generate live order-flow tick
    tick_result = LIVE_MARKET.generate_tick(ticker)
    
    if predict_flag:
        state = LIVE_MARKET.get_or_create_state(ticker, range_str)
        candles = state.get('candles', [])
        if candles:
            indicators = calculate_indicators_pack(candles)
            prediction = run_time_series_prediction(candles, model_name, horizon)
            tick_result['indicators'] = indicators
            tick_result['prediction'] = prediction
            
    return jsonify(tick_result)

@app.route('/api/stock/popular', methods=['GET'])
def api_popular_stocks():
    return jsonify(FEATURED_TRADES)

# ==========================================
# Watchlist & Prediction History Endpoints
# ==========================================

@app.route('/api/watchlist', methods=['GET'])
def api_get_watchlist():
    user_id = session.get('user_id')
    if not user_id:
        # Default fallback list for guests with 10 trades
        return jsonify({'watchlist': [t['id'] for t in FEATURED_TRADES]})
        
    watchlist = get_user_watchlist(user_id)
    if not watchlist:
        watchlist = [t['id'] for t in FEATURED_TRADES]
    return jsonify({'watchlist': watchlist})

@app.route('/api/watchlist/toggle', methods=['POST'])
def api_toggle_watchlist():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login to save to your watchlist.'}), 401
        
    data = request.get_json() or {}
    ticker = data.get('ticker', '')
    if not ticker:
        return jsonify({'success': False, 'message': 'Ticker required.'}), 400
        
    success, is_favorite, message = toggle_watchlist_item(user_id, ticker)
    return jsonify({'success': success, 'is_favorite': is_favorite, 'message': message})

@app.route('/api/predictions/history', methods=['GET'])
def api_prediction_history():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'history': []})
        
    history = get_user_predictions(user_id, limit=10)
    return jsonify({'history': history})

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else int(os.environ.get('PORT', 8080))
    print(f"Starting Stock Market Prediction App on http://localhost:{port} (http://127.0.0.1:{port})")
    app.run(host='0.0.0.0', port=port, debug=False)
