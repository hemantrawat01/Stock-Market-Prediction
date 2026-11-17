import sqlite3
import hashlib
import os
import re
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stock_market.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str, salt: bytes = None) -> tuple[str, str]:
    if salt is None:
        salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return hashed.hex(), salt.hex()

def verify_password(stored_hash: str, salt_hex: str, password_to_check: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    new_hash = hashlib.pbkdf2_hmac('sha256', password_to_check.encode('utf-8'), salt, 100000)
    return new_hash.hex() == stored_hash

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        full_name TEXT NOT NULL,
        avatar TEXT DEFAULT 'user-astronaut',
        theme_pref TEXT DEFAULT 'dark',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # User Watchlists Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS watchlists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ticker TEXT NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE(user_id, ticker)
    )
    ''')
    
    # Predictions History Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ticker TEXT NOT NULL,
        model TEXT NOT NULL,
        horizon INTEGER NOT NULL,
        predicted_price REAL,
        change_pct REAL,
        metrics_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')
    
    conn.commit()
    
    # Create default demo user if not exists: trader@gmail.com / demo12345
    demo_email = 'trader@gmail.com'
    cursor.execute('SELECT id FROM users WHERE email = ?', (demo_email,))
    user = cursor.fetchone()
    if not user:
        p_hash, salt = hash_password('demo12345')
        cursor.execute('''
        INSERT INTO users (email, password_hash, salt, full_name, theme_pref)
        VALUES (?, ?, ?, ?, ?)
        ''', (demo_email, p_hash, salt, 'Alex Trader', 'dark'))
        demo_id = cursor.lastrowid
        
        # Add default watchlist for demo user with 10 trades
        default_tickers = ['NIFTY50', 'BANKNIFTY', 'SENSEX', 'GOLD', 'SILVER', 'CRUDEOIL', 'BTC', 'ETH', 'USDINR', 'NASDAQ100']
        for t in default_tickers:
            cursor.execute('INSERT OR IGNORE INTO watchlists (user_id, ticker) VALUES (?, ?)', (demo_id, t))
        conn.commit()
        
    conn.close()

def is_valid_email(email: str) -> bool:
    # Accept standard email or @gmail.com
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(email_regex, email.strip()))

def register_user(email: str, password: str, full_name: str = '') -> tuple[bool, str, dict]:
    email = email.strip().lower()
    if not is_valid_email(email):
        return False, "Invalid email format. Please provide a valid email (e.g. user@gmail.com).", {}
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long.", {}
        
    if not full_name.strip():
        # Derive name from email username
        full_name = email.split('@')[0].capitalize()
        
    p_hash, salt = hash_password(password)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO users (email, password_hash, salt, full_name, theme_pref)
        VALUES (?, ?, ?, ?, 'dark')
        ''', (email, p_hash, salt, full_name.strip()))
        user_id = cursor.lastrowid
        
        # Default 10 featured trade watchlists
        default_tickers = ['NIFTY50', 'BANKNIFTY', 'SENSEX', 'GOLD', 'SILVER', 'CRUDEOIL', 'BTC', 'ETH', 'USDINR', 'NASDAQ100']
        for t in default_tickers:
            cursor.execute('INSERT OR IGNORE INTO watchlists (user_id, ticker) VALUES (?, ?)', (user_id, t))
            
        conn.commit()
        conn.close()
        return True, "Registration successful!", {
            'id': user_id,
            'email': email,
            'full_name': full_name,
            'theme_pref': 'dark'
        }
    except sqlite3.IntegrityError:
        return False, "A user with this Gmail/email already exists. Please login instead.", {}
    except Exception as e:
        return False, f"Registration failed: {str(e)}", {}

def authenticate_user(email: str, password: str) -> tuple[bool, str, dict]:
    email = email.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return False, "User not found with this email. Please check your email or register.", {}
        
    if not verify_password(user['password_hash'], user['salt'], password):
        return False, "Incorrect password. Please try again.", {}
        
    return True, "Login successful!", {
        'id': user['id'],
        'email': user['email'],
        'full_name': user['full_name'],
        'theme_pref': user['theme_pref'],
        'created_at': user['created_at']
    }

def update_password(user_id: int, current_password: str, new_password: str) -> tuple[bool, str]:
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters long."
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return False, "User not found."
        
    # Verify current password
    if not verify_password(user['password_hash'], user['salt'], current_password):
        conn.close()
        return False, "Current password does not match. Please verify your current password."
        
    # Hash new password
    p_hash, salt = hash_password(new_password)
    now = datetime.now().isoformat()
    cursor.execute('''
    UPDATE users 
    SET password_hash = ?, salt = ?, updated_at = ?
    WHERE id = ?
    ''', (p_hash, salt, now, user_id))
    
    conn.commit()
    conn.close()
    return True, "Password successfully updated!"

def reset_password_direct(email: str, new_password: str) -> tuple[bool, str]:
    email = email.strip().lower()
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters long."
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return False, "No user found with that Gmail address."
        
    p_hash, salt = hash_password(new_password)
    now = datetime.now().isoformat()
    cursor.execute('''
    UPDATE users 
    SET password_hash = ?, salt = ?, updated_at = ?
    WHERE email = ?
    ''', (p_hash, salt, now, email))
    
    conn.commit()
    conn.close()
    return True, f"Password for {email} has been reset successfully!"

def update_user_profile(user_id: int, full_name: str, theme_pref: str) -> tuple[bool, str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE users 
    SET full_name = ?, theme_pref = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    ''', (full_name.strip(), theme_pref, user_id))
    conn.commit()
    conn.close()
    return True, "Profile updated successfully!"

def get_user_watchlist(user_id: int) -> list[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT ticker FROM watchlists WHERE user_id = ? ORDER BY added_at DESC', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [r['ticker'] for r in rows]

def toggle_watchlist_item(user_id: int, ticker: str) -> tuple[bool, bool, str]:
    ticker = ticker.upper().strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM watchlists WHERE user_id = ? AND ticker = ?', (user_id, ticker))
    row = cursor.fetchone()
    
    if row:
        cursor.execute('DELETE FROM watchlists WHERE user_id = ? AND ticker = ?', (user_id, ticker))
        is_favorite = False
        msg = f"Removed {ticker} from watchlist."
    else:
        cursor.execute('INSERT INTO watchlists (user_id, ticker) VALUES (?, ?)', (user_id, ticker))
        is_favorite = True
        msg = f"Added {ticker} to watchlist!"
        
    conn.commit()
    conn.close()
    return True, is_favorite, msg

def save_prediction_record(user_id: int, ticker: str, model: str, horizon: int, predicted_price: float, change_pct: float, metrics_json: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO predictions (user_id, ticker, model, horizon, predicted_price, change_pct, metrics_json)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, ticker.upper(), model, horizon, predicted_price, change_pct, metrics_json))
    conn.commit()
    conn.close()

def get_user_predictions(user_id: int, limit: int = 8):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT * FROM predictions 
    WHERE user_id = ? 
    ORDER BY created_at DESC 
    LIMIT ?
    ''', (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
