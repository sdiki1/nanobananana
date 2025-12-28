CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    tg_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    diamonds INTEGER NOT NULL DEFAULT 0,
    bananas INTEGER NOT NULL DEFAULT 0,
    usdt_balance NUMERIC(14, 2) NOT NULL DEFAULT 0,
    earned_usdt NUMERIC(14, 2) NOT NULL DEFAULT 0,
    referral_code TEXT UNIQUE NOT NULL,
    referrer_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    selected_model TEXT NOT NULL DEFAULT 'nano',
    selected_preset TEXT
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    method TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    amount_diamonds INTEGER NOT NULL DEFAULT 0,
    amount_bananas INTEGER NOT NULL DEFAULT 0,
    amount_usdt NUMERIC(14, 2) NOT NULL DEFAULT 0,
    external_id TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS generations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    model TEXT,
    prompt TEXT,
    preset TEXT,
    status TEXT NOT NULL DEFAULT 'processing',
    cost_diamonds INTEGER NOT NULL DEFAULT 0,
    cost_bananas INTEGER NOT NULL DEFAULT 0,
    result_url TEXT,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS referrals (
    id SERIAL PRIMARY KEY,
    referrer_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    referred_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_tg_id ON users(tg_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_generations_user_id ON generations(user_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id);
