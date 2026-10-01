-- ============================================================
-- P_311 Industrial IoT PostgreSQL Initialization Schema
-- ============================================================

-- 1. Machines Profile Table
CREATE TABLE IF NOT EXISTS machines (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(255) NOT NULL,
    rated_voltage DOUBLE PRECISION NOT NULL,
    rated_current DOUBLE PRECISION NOT NULL,
    rated_rpm DOUBLE PRECISION NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'healthy',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2. Telemetry Time-Series Table
CREATE TABLE IF NOT EXISTS telemetry (
    id BIGSERIAL PRIMARY KEY,
    machine_id VARCHAR(64) NOT NULL REFERENCES machines(id),
    timestamp TIMESTAMPTZ NOT NULL,
    temperature DOUBLE PRECISION NOT NULL,
    vibration DOUBLE PRECISION NOT NULL,
    current DOUBLE PRECISION NOT NULL,
    rpm DOUBLE PRECISION NOT NULL,
    voltage DOUBLE PRECISION NOT NULL,
    pressure DOUBLE PRECISION NOT NULL,
    operating_state VARCHAR(32) NOT NULL
);

-- 3. Fault Events Table
CREATE TABLE IF NOT EXISTS fault_events (
    id VARCHAR(64) PRIMARY KEY,
    machine_id VARCHAR(64) NOT NULL REFERENCES machines(id),
    timestamp TIMESTAMPTZ NOT NULL,
    fault_type VARCHAR(64) NOT NULL,
    severity VARCHAR(32) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    sensor_evidence JSONB NOT NULL,
    triggered_rules JSONB NOT NULL,
    resolved_at TIMESTAMPTZ
);

-- 4. Diagnoses Table
CREATE TABLE IF NOT EXISTS diagnoses (
    id VARCHAR(64) PRIMARY KEY,
    fault_event_id VARCHAR(64) NOT NULL REFERENCES fault_events(id),
    machine_id VARCHAR(64) NOT NULL REFERENCES machines(id),
    timestamp TIMESTAMPTZ NOT NULL,
    fault_title VARCHAR(255) NOT NULL,
    severity VARCHAR(32) NOT NULL,
    sensor_evidence JSONB NOT NULL,
    likely_causes JSONB NOT NULL,
    recommended_checks JSONB NOT NULL,
    corrective_actions JSONB NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    uncertainty TEXT NOT NULL,
    knowledge_sources JSONB NOT NULL,
    raw_llm_response TEXT,
    execution_time_ms INTEGER NOT NULL,
    is_fallback BOOLEAN NOT NULL DEFAULT FALSE
);

-- 5. Knowledge Documents Metadata Table
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id VARCHAR(64) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(128) NOT NULL,
    chunk_count INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 6. High-Performance Indexes for Grafana and API Time-Window Queries
CREATE INDEX IF NOT EXISTS idx_telemetry_time ON telemetry(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_machine_time ON telemetry(machine_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_faults_time ON fault_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_faults_machine_time ON fault_events(machine_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_diagnoses_machine_time ON diagnoses(machine_id, timestamp DESC);

-- 7. Seed Default 11 kW Induction Motor Profile
INSERT INTO machines (id, name, type, rated_voltage, rated_current, rated_rpm, status)
VALUES (
    'MOTOR-001',
    'Main Extruder Induction Motor',
    '3-Phase Squirrel Cage Induction Motor (11 kW)',
    400.0,
    9.0,
    1485.0,
    'healthy'
) ON CONFLICT (id) DO NOTHING;
