-- MindWall — Database Schema DDL
-- Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

CREATE TABLE IF NOT EXISTS employees (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT NOT NULL UNIQUE,
    display_name    TEXT,
    department      TEXT,
    risk_score      REAL DEFAULT 0.0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sender_baselines (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_email     TEXT NOT NULL,
    sender_email        TEXT NOT NULL,
    avg_word_count      REAL,
    avg_sentence_length REAL,
    typical_hours       TEXT,
    formality_score     REAL,
    typical_requests    TEXT,
    sample_count        INTEGER DEFAULT 0,
    last_updated        DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(recipient_email, sender_email)
);

CREATE TABLE IF NOT EXISTS analyses (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    message_uid             TEXT NOT NULL,
    recipient_email         TEXT NOT NULL,
    sender_email            TEXT NOT NULL,
    sender_display_name     TEXT,
    subject                 TEXT,
    received_at             DATETIME,
    analyzed_at             DATETIME DEFAULT CURRENT_TIMESTAMP,
    channel                 TEXT NOT NULL,
    prefilter_triggered     BOOLEAN DEFAULT FALSE,
    prefilter_signals       TEXT,
    manipulation_score      REAL,
    dimension_scores        TEXT,
    explanation             TEXT,
    recommended_action      TEXT,
    llm_raw_response        TEXT,
    processing_time_ms      INTEGER,
    UNIQUE(message_uid, recipient_email)
);

CREATE TABLE IF NOT EXISTS alerts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id     INTEGER NOT NULL REFERENCES analyses(id),
    severity        TEXT NOT NULL,
    acknowledged    BOOLEAN DEFAULT FALSE,
    acknowledged_by TEXT,
    acknowledged_at DATETIME,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_analyses_recipient ON analyses(recipient_email, analyzed_at DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_score ON analyses(manipulation_score DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity, acknowledged, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_baselines_lookup ON sender_baselines(recipient_email, sender_email);
