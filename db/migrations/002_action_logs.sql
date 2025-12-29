CREATE TABLE IF NOT EXISTS action_logs (
    id SERIAL PRIMARY KEY,
    tg_id BIGINT NOT NULL,
    username VARCHAR(255),
    action VARCHAR(64) NOT NULL,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
