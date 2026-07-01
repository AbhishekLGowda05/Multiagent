# Multi-Agent Business Analytics (Google ADK)

A multi-agent system built with [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/) that routes business queries to specialized agents for sales, purchases, inventory, and financial analysis over a Tally SQLite database. Includes Gmail and Google Calendar integrations via FastAPI.

## Features

- **Manager agent** with sub-agent delegation for domain-specific queries
- **Cross-agent orchestrator** for queries spanning multiple business areas
- **SQLite analytics** against a Tally export database
- **Gmail & Calendar tools** via Google OAuth (optional mock mode)
- **FastAPI REST API** for email and calendar operations

## Project Structure

```
Multiagent/
├── DB_analysis/           # ADK agent package (run `adk web` from here)
│   ├── manager/           # Root manager agent and sub-agents
│   └── README.md          # Detailed ADK setup and usage
├── google_utils/          # Gmail, Calendar, and auth helpers
├── api_routes.py          # FastAPI application
├── visualization_utils.py # Chart generation utilities
├── cross_agent_example.py # CLI demo for cross-agent queries
├── financial_test.py      # CLI demo for financial queries
└── requirements.txt
```

## Quick Start

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp DB_analysis/.env.example DB_analysis/.env
# Edit DB_analysis/.env and set GOOGLE_API_KEY
```

Place a Tally SQLite database at `tallydb.db` in the project root (or set `TALLY_DB_PATH` in `.env`).

### 3. Run the ADK web UI

```bash
cd DB_analysis
adk web
```

Open http://localhost:8000 and select the **manager** agent.

### 4. Run the FastAPI server (optional)

```bash
uvicorn api_routes:app --reload
```

### Google OAuth (optional)

See [SETUP_GOOGLE_CREDENTIALS.md](SETUP_GOOGLE_CREDENTIALS.md). Copy `google_utils/credentials.json.example` to `google_utils/credentials.json` and complete the OAuth flow.

To test without Google APIs:

```bash
export MOCK_GOOGLE_APIS=true
```

## Example Queries

- "Summarize our latest sales invoices."
- "How many units of each product do we have in stock?"
- "Why did our profit drop if sales are stable?"

## License

Portfolio demonstration project.
