CREATE DATABASE IF NOT EXISTS root_cause_system;
USE root_cause_system;

CREATE TABLE IF NOT EXISTS incidents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_type VARCHAR(50) NOT NULL,
    rssi_dbm INT NOT NULL,
    channel_utilization_pct INT NOT NULL,
    latency_ms INT NOT NULL,
    packet_loss_pct FLOAT NOT NULL,
    dhcp_failures INT NOT NULL,
    dns_risk_score FLOAT NOT NULL,
    predicted_root_cause VARCHAR(50) NOT NULL,
    prediction_confidence FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
