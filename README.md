# MSNCTRL (WIP LAST UPDATED 6/25/26)
MISSION CONTROL: An AI Agent Ecosystem built with:

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![Anthropic](https://img.shields.io/badge/Claude-Anthropic-D97757?style=for-the-badge&logo=anthropic&logoColor=white)
![yfinance](https://img.shields.io/badge/yfinance-Market%20Data-6001D2?style=for-the-badge&logo=yahoo&logoColor=white)

MSNCTRL is a personal AI operating system built around a multi-agent architecture. Currently ships with a market analysis agent that delivers ICT-based premarket briefings for NQ and ES futures every morning.

---

## What it does

Open the dashboard, ask the market agent for a briefing, and get a structured ICT analysis — directional bias, key liquidity levels, Asia/London session recaps, two trade scenarios, and news risk flags. Follow-up questions work too since the agent holds full conversation context.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite |
| Backend | Python + FastAPI |
| Market Data | yfinance (NQ=F, ES=F) |
| AI | Anthropic API (claude-sonnet-4-6) |
| Storage | SQLite (coming soon) |

---

## Getting started

### Backend

```bash
python -m venv venv

# Windows
venv/Scripts/activate

# Mac
source venv/bin/activate

pip install fastapi uvicorn yfinance anthropic apscheduler python-dotenv pandas pytz
```

Create a `.env` file in the root:

```
ANTHROPIC_API_KEY=your_key_here
```

Run the server:

```bash
# Windows
venv/Scripts/uvicorn.exe main:app --reload

# Mac
python -m uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

---

## Roadmap

- [ ] SQLite conversation storage
- [ ] Economic calendar integration
- [ ] Additional agents (Fiverr, Etsy automation)
- [ ] Head orchestrator agent
- [ ] Gamified 3D mission control UI
- [ ] VPS deployment for 24/7 uptime

---

<p align="center">Built by Blake</p>
