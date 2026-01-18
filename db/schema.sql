CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY,                         -- Telegram user id
    username TEXT NOT NULL,                         -- Telegram username
    name TEXT,                                      -- user-input name
    email TEXT,                                     -- user-input email (may be empty)
    face_photo_path TEXT,                           -- user-input face photo
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS job (
    id INTEGER PRIMARY KEY,
    schedule TEXT DEFAULT 'daily',
    active INTEGER DEFAULT 0,
    last_run TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS job_run (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    status TEXT,
    name TEXT,
    email TEXT,
    face_photo_path TEXT,
    error TEXT,
    run_at TEXT DEFAULT CURRENT_TIMESTAMP
);
