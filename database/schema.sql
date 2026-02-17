CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    steam_id VARCHAR(64) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    avatar_id INTEGER DEFAULT 0,
    region_code CHAR(3) DEFAULT 'UNK'
);

CREATE TABLE IF NOT EXISTS myclub_stats (
    user_id INTEGER PRIMARY KEY,
    gp INTEGER DEFAULT 0,
    coins INTEGER DEFAULT 0,
    rating INTEGER DEFAULT 1000,
    acclaim_level INTEGER DEFAULT 1,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS myclub_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    card_type INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    exp INTEGER DEFAULT 0,
    contracts INTEGER DEFAULT 10,
    is_locked BOOLEAN DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS myclub_squads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    manager_id INTEGER DEFAULT 0,
    formation_data BLOB,
    roster_ids JSON,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
