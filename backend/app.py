from pathlib import Path
import os
import sys

import joblib
import mysql.connector
import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from mysql.connector import Error

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "backend" / ".env")
app = Flask(__name__)
CORS(app)

FEATURES = ["device_type", "rssi_dbm", "channel_utilization_pct", "latency_ms",
            "packet_loss_pct", "dhcp_failures", "dns_risk_score"]
MODEL_PATH = ROOT / os.getenv("MODEL_PATH", "ml/root_cause_model.pkl")
try:
    model = joblib.load(MODEL_PATH)
except Exception as exc:
    model = None
    print(f"WARNING: could not load model at {MODEL_PATH}: {exc}", file=sys.stderr)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "root_cause_system"),
        connection_timeout=5,
    )

def validate_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")
    missing = [k for k in FEATURES if k not in payload or payload[k] in (None, "")]
    if missing:
        raise ValueError("Missing required fields: " + ", ".join(missing))
    try:
        row = {
            "device_type": str(payload["device_type"]).strip(),
            "rssi_dbm": int(payload["rssi_dbm"]),
            "channel_utilization_pct": float(payload["channel_utilization_pct"]),
            "latency_ms": float(payload["latency_ms"]),
            "packet_loss_pct": float(payload["packet_loss_pct"]),
            "dhcp_failures": int(payload["dhcp_failures"]),
            "dns_risk_score": float(payload["dns_risk_score"]),
        }
    except (TypeError, ValueError):
        raise ValueError("Numeric fields must contain valid numbers.")
    if not row["device_type"]:
        raise ValueError("Device type cannot be empty.")
    if not 0 <= row["channel_utilization_pct"] <= 100:
        raise ValueError("Channel utilization must be between 0 and 100.")
    if row["latency_ms"] < 0 or row["packet_loss_pct"] < 0 or row["dhcp_failures"] < 0:
        raise ValueError("Latency, packet loss, and DHCP failures cannot be negative.")
    if not 0 <= row["dns_risk_score"] <= 1:
        raise ValueError("DNS risk score must be between 0 and 1.")
    return row

@app.get("/")
def health():
    return jsonify({"message": "Root Cause AI API is running", "model_loaded": model is not None})

@app.get("/incidents")
def get_incidents():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""SELECT id, device_type, rssi_dbm, channel_utilization_pct,
            latency_ms, packet_loss_pct, dhcp_failures, dns_risk_score,
            predicted_root_cause, prediction_confidence, created_at
            FROM incidents ORDER BY created_at DESC, id DESC LIMIT 200""")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        for row in rows:
            if row.get("created_at"):
                row["created_at"] = row["created_at"].isoformat(sep=" ", timespec="seconds")
        return jsonify(rows)
    except Error as exc:
        return jsonify({"error": f"Database error: {exc}"}), 503

@app.get("/stats")
def stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS total FROM incidents")
        total = cursor.fetchone()["total"]
        cursor.execute("""SELECT predicted_root_cause, COUNT(*) AS count
            FROM incidents GROUP BY predicted_root_cause ORDER BY count DESC""")
        by_cause = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"total_incidents": total, "by_cause": by_cause})
    except Error as exc:
        return jsonify({"error": f"Database error: {exc}"}), 503

@app.post("/predict")
def predict():
    if model is None:
        return jsonify({"error": "Model file missing. Copy ml/root_cause_model.pkl into the ml folder or train it."}), 503
    try:
        row = validate_payload(request.get_json(silent=True))
        frame = pd.DataFrame([row], columns=FEATURES)
        predicted = str(model.predict(frame)[0])
        probs = model.predict_proba(frame)[0]
        probability_data = {str(label): float(p) for label, p in zip(model.classes_, probs)}
        confidence = probability_data[predicted]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO incidents (
            device_type, rssi_dbm, channel_utilization_pct, latency_ms,
            packet_loss_pct, dhcp_failures, dns_risk_score,
            predicted_root_cause, prediction_confidence
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (row["device_type"], row["rssi_dbm"], row["channel_utilization_pct"],
             row["latency_ms"], row["packet_loss_pct"], row["dhcp_failures"],
             row["dns_risk_score"], predicted, confidence))
        conn.commit()
        incident_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({"incident_id": incident_id, "predicted_root_cause": predicted,
                        "prediction_confidence": confidence, "probabilities": probability_data,
                        "message": "Incident predicted and saved successfully"})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Error as exc:
        return jsonify({"error": f"Database error: {exc}"}), 503
    except Exception as exc:
        app.logger.exception("Prediction failed")
        return jsonify({"error": f"Prediction failed: {exc}"}), 500

if __name__ == "__main__":
    app.run(host=os.getenv("FLASK_HOST", "127.0.0.1"),
            port=int(os.getenv("FLASK_PORT", "5000")), debug=True)
