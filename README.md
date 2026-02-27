# Automated Weather Pipeline

An automated pipeline that retrieves current-day weather data from the Open‑Meteo API, transforms it, stores it in Parquet format, and sends alerts when conditions are met.


**Competencies showcased** : Automatisation, APIs REST, scheduling, data engineering, GitHub Actions

![Python](https://img.shields.io/badge/Python-3.12-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Context 🌤️⛱️🔥

I created this project because I live in Australia, where UV levels are often high and harmful to health, and I wanted to receive notifications to help protect myself from sun damage.


---

## Architecture

```
┌─────────────┐      ┌───────────┐     ┌─────────┐     ┌─────────────┐
│ Open-Meteo  │────> │ Transform │────>│  Load   │────>│    Alert    │
│     API     │      │  (clean)  │     │(Parquet)│     │Notifications│
└─────────────┘      └───────────┘     └─────────┘     │             │
       ▲                                               └─────────────┘
       │                                                   │
       └────────────── GitHub Actions ─────────────────────┘
                      (cron: 7h UTC daily)
```

---

## Quick Start

```bash
# 1. Clone repo and install
cd pipeline-automatise
make setup

# 2. Configure (optionnal)
cp .env.example .env
# Edit .env with your own parameters

# 3. Run the pipeline
make run

# 4. Run mode dry-run (test without alerts)
make run-dry
```

---

## Fonctionnalities

### Data Source
- **[API Open-Meteo](https://open-meteo.com/)**: free, no-authentication required
- Data : temperature, UV index, precipitations of the day

### Transformation
- Clean data (null values, duplicates)
- Enrich data (categories)
- Validation (plausibility of values)

### Stockage
- Format Parquet
- Historical data in `data/archive/`

### Alerts configurables
- Temperature > threshold (hot)
- UV index > threshold (danger)
- Précipitations > seuil (rainy)

### Notifications
- Console (par défaut)
- PushNotification on your phone (using NTFY)
- Gmail Notification
- Slack (webhook)
- Discord (webhook)

---

## Configuration

Environment variables (`.env`) :

| Variable | Description | Default |
|----------|-------------|--------|
| `LATITUDE` | City Latitude | 48.8566 |
| `LONGITUDE` | City Longitude | 2.3522 |
| `LOCATION_NAME` | City Name | Paris |
| `TEMP_MAX_THRESHOLD` | Alert if temp > X | 35.0 |
| `UV_THRESHOLD` | Alert if UV index > X | 8.0 |
| `PRECIPITATION_THRESHOLD` | Alert if precip > X mm | 8.0 |
| `ALERT_ENABLED` | Active alerts | true |
| `PUSH_NOTIFICATION_ENABLED` | Activate Push Notifications | - |
| `PUSH_NOTIFICATION_TOPIC` | NTFY topic for alerts | - |
| `SLACK_WEBHOOK_URL` | Webhook Slack | - |
| `DISCORD_WEBHOOK_URL` | Webhook Discord | - |

---

## Project Structure

```
Weather_Notification
├── src/
│   ├── main.py              # Entry point
│   ├── config/
│   │   └── settings.py      # Configuration (pydantic-settings)
│   ├── extract/
│   │   └── api_client.py    # Client Open-Meteo
│   ├── transform/
│   │   └── processors.py    # Transform data
│   ├── load/
│   │   └── storage.py       # Store in Parquet format
│   ├── alerts/
│   │   ├── conditions.py    # Alert conditions
│   │   └── notifiers.py     # Notifications
│   └── utils/
│       └── logging.py       # Configuration logging
├── tests/
│   ├── test_extract.py
│   ├── test_transform.py
│   └── test_alerts.py
├── data/
│   ├── raw/                 # Raw data brutes
│   ├── processed/           # Transform data
│   └── archive/             # Historical data
├── .github/workflows/
│   ├── run_pipeline.yml     # Run daily - Pipeline
│   └── test.yml             # CI Tests
├── pyproject.toml
├── Makefile
└── README.md
```

---

## Commands

```bash
make setup      # Install dependancies
make run        # Run pipeline
make run-dry    # Run without saving and alerts
make test       # Run tests
make test-cov   # Run tests with coverage
make lint       # Lint code
make lint-fix   # Update code linting issues
make clean      # Remove temporary files
```
---

## GitHub Actions

### 1. Secrets Configuration

In GitHub repo: Settings > Secrets and variables > Actions

Secrets:
- `LATITUDE` / `LONGITUDE` / `LOCATION_NAME`
  
For Push notifications:
`PUSH_NOTIFICATION_ENABLED` need to be true 
- `PUSH_NOTIFICATION_TOPIC` (optionnel)
 
For Other notifications:
- `SLACK_WEBHOOK_URL` (optionnel)
- `DISCORD_WEBHOOK_URL` (optionnel)


### 2. Frequency

Default : runs everyday at 7am UTC 
cron in `.github/workflows/run_pipeline.yml` :

```yaml
on:
  schedule:
    - cron: '0 7 * * *' 
```
---
