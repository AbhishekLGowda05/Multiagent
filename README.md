# Multiagent Financial Analysis Demo

This repository demonstrates a multi‑agent analytics system built with Google's Agent Development Kit (ADK). The project defines a **manager** agent that delegates work to several specialised sub‑agents and exposes tools for email and calendar integration.

## Directory overview

- `DB_analysis/` – main package containing the manager agent, sub‑agents and orchestration utilities.
  - `manager/agent.py` defines the `root_agent` used by ADK. It registers sub‑agents and tools.
  - `manager/cross_agent_orchestrator.py` implements `CrossAgentOrchestrator`, allowing multiple agents to run for a single query.
  - `manager/sub_agents/` holds domain‑specific agents for sales, purchases, inventory, finance and simple greetings.
- `google_utils/` – helper module for Gmail and Calendar API access.
- `tallydb.db` – SQLite database with example accounting data.
- `financial_test.py` and `cross_agent_example.py` – runnable scripts showing standalone usage of the analytics tools and orchestrator.
- `tests/` – pytest suite exercising agents and orchestration logic.

See `DB_analysis/README.md` for a deep dive into ADK multi‑agent setups.

## How it works

1. **Manager agent**
   - Configured in `DB_analysis/manager/agent.py`.
   - Uses ADK's `Agent` class and provides tools:
     - `handle_query_with_memory` – routes analytics requests to the orchestrator and stores the result.
     - `smart_send_email` and `smart_schedule_event` – wrappers around Gmail and Calendar utilities.
     - `combined_analytics_and_email_calendar` – combines analytics with email/calendar actions when the user asks for both.
   - Registers sub‑agents so the manager can delegate queries about sales, purchases, inventory or finance.

2. **Sub‑agents**
   - Located in `manager/sub_agents/*/agent.py`.
   - Each defines a small ADK agent with tools that query `tallydb.db`. For example, `sales_agent` summarises invoices and trends while `financial_agent` computes ledgers or profit‑and‑loss information.

3. **Cross‑agent orchestration**
   - `CrossAgentOrchestrator` (in `manager/cross_agent_orchestrator.py`) analyses the user query, determines which agents are relevant and runs only the necessary tools. It aggregates results and can generate insights spanning multiple business domains.

4. **Google Workspace integration**
   - The Gmail and Calendar helpers under `google_utils/` rely on OAuth credentials. When the credentials are configured, tools can send emails or create events on behalf of the user.

5. **Running the demo**
   - Ensure dependencies from `requirements.txt` are installed.
   - Start the ADK web UI from the repository root:
     ```bash
     adk web
     ```
   - Choose the `manager` agent in the UI and begin chatting. The manager decides which sub‑agent or tool should handle each request.
   - The scripts `financial_test.py` and `cross_agent_example.py` show how to call the tools from the command line.

6. **Testing**
   - Run `pytest` to execute the unit tests. They use temporary SQLite databases and stubbed ADK classes so no network access is required.

## Notes

The repository includes a sample OAuth `credentials.json` file for development. In a production project you should store credentials securely and exclude them from version control.

