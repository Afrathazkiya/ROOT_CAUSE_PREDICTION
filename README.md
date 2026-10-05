# Root Cause AI — Network Incident Prediction

A local student-project prototype: React dashboard + Flask API + scikit-learn model + MySQL incident history.

**Dataset note:** The project model is intended for the SmartNet *synthetic* dataset. Its reported accuracy must not be described as real-world performance.

## Requirements
- Python 3.11+ recommended
- Node.js 20+ / npm
- MySQL Server
- Your existing trained model `ml/root_cause_model.pkl`

The model and dataset files are not included in this ZIP. Copy your trained model into `ml/root_cause_model.pkl`. Dataset files (if retraining) belong in `dataset/train.parquet`, `dataset/validation.parquet`, and `dataset/test.parquet`.

## 1. Create the database
Open MySQL Workbench and run `database/schema.sql`.

## 2. Configure and start Flask (project root terminal)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
Copy-Item backend/.env.example backend/.env
```
Edit `backend/.env` with your local MySQL password. Keep `.env` private and do not commit it.

If PowerShell blocks activation:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Start:
```powershell
python backend/app.py
```
Health check: `http://127.0.0.1:5000/`

## 3. Start React (second terminal)
```powershell
cd frontend
npm install
npm run dev
```
Open the URL printed by Vite (usually `http://localhost:5173`).

## Features
- Network incident input form
- Prediction + class probability estimates
- MySQL-backed incident history
- Summary metrics and Recharts category chart
- API connection indicator and error messages

The confidence shown is the model's class probability, not a guarantee. This is a local development prototype, not a production deployment.
