from pathlib import Path
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dataset"
TARGET = "label"
FEATURES = ["device_type", "rssi_dbm", "channel_utilization_pct", "latency_ms",
            "packet_loss_pct", "dhcp_failures", "dns_risk_score"]

def main():
    train = pd.read_parquet(DATA / "train.parquet")
    validation = pd.read_parquet(DATA / "validation.parquet")
    test = pd.read_parquet(DATA / "test.parquet")
    preprocessor = ColumnTransformer([
        ("categorical", OneHotEncoder(handle_unknown="ignore"), ["device_type"]),
        ("numeric", StandardScaler(), FEATURES[1:]),
    ])
    model = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)),
    ])
    model.fit(train[FEATURES], train[TARGET])
    for name, frame in [("Validation", validation), ("Test", test)]:
        prediction = model.predict(frame[FEATURES])
        print(f"{name} accuracy: {accuracy_score(frame[TARGET], prediction):.4%}")
        if name == "Test":
            print(classification_report(frame[TARGET], prediction, zero_division=0))
    output = ROOT / "ml" / "root_cause_model.pkl"
    joblib.dump(model, output)
    print(f"Saved model: {output}")

if __name__ == "__main__":
    main()
