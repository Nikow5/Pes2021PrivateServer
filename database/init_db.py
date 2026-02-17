import sqlite3
import os

DB_PATH = 'pes2021.db'
SCHEMA_PATH = 'database/schema.sql'

def init_db():
    print(f"[*] Initializing database at {DB_PATH}...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(SCHEMA_PATH, 'r') as f:
        schema = f.read()
        cursor.executescript(schema)

    print("[*] Schema applied.")

    # Insert Mock Data
    try:
        cursor.execute("INSERT INTO users (steam_id, username, region_code) VALUES (?, ?, ?)",
                       ('76561198000000000', 'TestUser', 'FRA'))
        user_id = cursor.lastrowid

        cursor.execute("INSERT INTO myclub_stats (user_id, gp, coins) VALUES (?, ?, ?)",
                       (user_id, 10000, 500))

        # Add some inventory (Player IDs are hypothetical)
        cursor.execute("INSERT INTO myclub_inventory (user_id, player_id, card_type) VALUES (?, ?, ?)",
                       (user_id, 10001, 1)) # Featured Player 1

        conn.commit()
        print(f"[*] Mock user 'TestUser' (ID: {user_id}) created.")

    except sqlite3.IntegrityError:
        print("[*] Mock data already exists.")

    conn.close()

if __name__ == "__main__":
    init_db()
