-- Financial Risk Data ETL Pipeline — target schema
-- Matches docs/data_mapping_doc.xlsx

CREATE TABLE IF NOT EXISTS raw_prices (
    trade_date   DATE           NOT NULL,
    ticker       VARCHAR(10)    NOT NULL,
    open_price   NUMERIC(12,4),
    high_price   NUMERIC(12,4),
    low_price    NUMERIC(12,4),
    close_price  NUMERIC(12,4),
    volume       BIGINT,
    PRIMARY KEY (trade_date, ticker)
);

CREATE TABLE IF NOT EXISTS daily_returns (
    trade_date   DATE           NOT NULL,
    ticker       VARCHAR(10)    NOT NULL,
    pct_return   NUMERIC(12,8),
    PRIMARY KEY (trade_date, ticker)
);

CREATE TABLE IF NOT EXISTS risk_metrics (
    trade_date     DATE         NOT NULL,
    ticker         VARCHAR(10)  NOT NULL,
    ma_short       NUMERIC(12,4),
    ma_long        NUMERIC(12,4),
    volatility_30d NUMERIC(12,8),
    var_95         NUMERIC(12,8),
    PRIMARY KEY (trade_date, ticker)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id              SERIAL PRIMARY KEY,
    run_timestamp   TIMESTAMP    NOT NULL DEFAULT NOW(),
    stage           VARCHAR(50)  NOT NULL,
    table_name      VARCHAR(50),
    rows_processed  INTEGER,
    rows_failed     INTEGER,
    status          VARCHAR(20),
    notes           TEXT
);

ALTER TABLE raw_prices ADD CONSTRAINT uq_trade_date_ticker UNIQUE (trade_date, ticker);

CREATE TABLE pipeline_runs (
    run_id SERIAL PRIMARY KEY,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration_seconds DOUBLE PRECISION NOT NULL,
    status VARCHAR(20) NOT NULL,
    extracted_rows INTEGER NOT NULL DEFAULT 0,
    loaded_rows INTEGER NOT NULL DEFAULT 0,
    validation_errors INTEGER NOT NULL DEFAULT 0,
    reconciliation_status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);