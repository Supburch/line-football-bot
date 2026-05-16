# Football LINE Bot

Enterprise-grade LINE Bot for English Premier League match tracking, real-time score alerts, and standings via football-data.org APIv4.

## Features
- **Real-time Goal Alerts**: Pushes updates to registered groups using Jitter and Rate-Limiting.
- **Circuit Breaker**: Robust API querying using `cachetools` and automatic retries.
- **Smart Scheduler**: Only polls frequently when matches are currently LIVE.
- **Modular Architecture**: Clean, enterprise-ready separation of jobs, handlers, and services.

## Deployment
Easy deployment to Render via the provided `render.yaml`.
Uses Gunicorn with 1 worker and 8 threads to prevent duplicate background scheduler tasks.
