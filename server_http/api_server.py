from flask import Flask, jsonify, request
import sqlite3
import os

app = Flask(__name__)
DB_PATH = 'pes2021.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/system/maintenance', methods=['GET'])
def maintenance_check():
    """
    Check if the game servers are online.
    Returns: JSON { "status": "online", "message": "" }
    """
    return jsonify({
        "status": "online",
        "maintenance": False,
        "message": "Servers are operational."
    })

@app.route('/api/myclub/userdata', methods=['GET'])
def get_userdata():
    """
    Returns user stats (GP, Coins, Rating).
    Requires 'steam_id' or 'token' in headers (mocked).
    """
    # Mock Auth: Assume User ID 1 for now
    user_id = 1

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    stats = conn.execute('SELECT * FROM myclub_stats WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()

    if not user or not stats:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "username": user['username'],
        "region": user['region_code'],
        "gp": stats['gp'],
        "coins": stats['coins'],
        "rating": stats['rating'],
        "acclaim": stats['acclaim_level']
    })

@app.route('/api/myclub/squad', methods=['GET'])
def get_squad():
    """
    Returns the current active squad formation.
    """
    # Mock Auth: Assume User ID 1
    user_id = 1

    conn = get_db_connection()
    squad = conn.execute('SELECT * FROM myclub_squads WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()

    if not squad:
        # Return default empty squad structure
        return jsonify({
            "manager_id": 0,
            "formation": [],
            "roster": []
        })

    return jsonify({
        "manager_id": squad['manager_id'],
        "formation": squad['formation_data'], # Should be parsed if BLOB
        "roster": squad['roster_ids'] # Should be parsed if JSON
    })

if __name__ == '__main__':
    # Run on port 80 (requires sudo) or 5000 for dev
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
