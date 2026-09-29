import sqlite3
from datetime import datetime, timedelta
import random

def seed():
    conn = sqlite3.connect('market_data.db')
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute("CREATE TABLE IF NOT EXISTS market_data (id INTEGER PRIMARY KEY, timestamp DATETIME, symbol TEXT, timeframe TEXT, open REAL, high REAL, low REAL, close REAL, volume REAL)")

    symbol = 'EURUSD'
    timeframe = 'M15'
    start_time = datetime.now() - timedelta(days=30)

    price = 1.0850
    for i in range(1000):
        timestamp = start_time + timedelta(minutes=15 * i)
        change = (random.random() - 0.5) * 0.001
        open_p = price
        close_p = price + change
        high_p = max(open_p, close_p) + random.random() * 0.0002
        low_p = min(open_p, close_p) - random.random() * 0.0002
        volume = random.random() * 1000

        cursor.execute("INSERT INTO market_data (timestamp, symbol, timeframe, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (timestamp.isoformat(), symbol, timeframe, open_p, high_p, low_p, close_p, volume))
        price = close_p

    conn.commit()
    conn.close()
    print("Seeded 1000 bars of grounded data.")

if __name__ == "__main__":
    seed()
