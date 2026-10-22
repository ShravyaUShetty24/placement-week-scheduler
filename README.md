# Placement Week Scheduler

**Portfolio:** Shravya U Shetty

A Python / Flask / SQLite interview scheduling prototype.

## Features
- Generate placement interview schedules with resource conflict checking
- Manage student, company, room and panel availability
- Detect disruptions and replan interview schedules
- Display schedules and progress in a dashboard

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
On Windows use `.venv\Scripts\activate`. The app creates a local SQLite database. Configure `FLASK_SECRET_KEY` as an environment variable for a persistent deployment.

## Portfolio notes
Code sample only; no production deployment, tested performance figures or production data are claimed. Never upload real student records or secret values.
