-- Runs on every compose-up via the db-init service.

CREATE TABLE IF NOT EXISTS tickers (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO tickers (symbol, name) VALUES
    ('SPY', 'S&P 500 ETF'),
    ('QQQ', 'Nasdaq 100 ETF'),
    ('IWM', 'Russell 2000 ETF'),
    ('EEM', 'Emerging Markets ETF')
ON CONFLICT (symbol) DO NOTHING;
