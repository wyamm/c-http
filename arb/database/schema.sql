CREATE TABLE IF NOT EXISTS bookies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    balance NUMERIC(12, 2) DEFAULT 0,
    pnl NUMERIC(12, 2) DEFAULT 0,
    bonus NUMERIC(12, 2) DEFAULT 0,
    bonus_reset TIMESTAMP(0),
    loss_back NUMERIC(4, 2) DEFAULT 0,
    can_use_loss_back BOOLEAN DEFAULT TRUE,
    loss_back_reset TIMESTAMP(0),
    traded BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP(0) DEFAULT NOW(),
    updated_at TIMESTAMP(0) DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS odds (
    bookie_id INTEGER NOT NULL,
    game_name VARCHAR(100) NOT NULL,
    market VARCHAR(100) NOT NULL,
    outcome VARCHAR(100) NOT NULL,
    price NUMERIC(5, 2) NOT NULL,
    captured_at TIMESTAMP(0) NOT NULL DEFAULT NOW(),
    game_date DATE,
    FOREIGN KEY (bookie_id) REFERENCES bookies(id)
);

CREATE TABLE IF NOT EXISTS margin (
    game_name VARCHAR(100) NOT NULL,
    margin NUMERIC(12, 2) NOT NULL,
    selected_odds VARCHAR(100) NOT NULL,
    selected_bookies VARCHAR(100) NOT NULL,
    date DATE,
    captured_at TIMESTAMP(0) NOT NULL DEFAULT NOW()
);