import sqlite3
import os
from pydantic import BaseModel
from google.adk.agents import Agent

DB_PATH = os.environ.get(
    "TALLY_DB_PATH",
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../../tallydb.db")
    ),

)


class SalesSummary(BaseModel):
    total_invoices: int
    top_customers: list
    voucher_types: list


class SalesTrend(BaseModel):
    monthly_sales: list
    slope: float


class SalesForecast(BaseModel):
    next_month_sales: float


class TopItemsSold(BaseModel):
    top_items: list


def get_sales_summary(query: str) -> SalesSummary:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        sql = """
        SELECT party_name, voucher_type, date
        FROM trn_voucher
        WHERE voucher_type LIKE '%Sales%'
        LIMIT 100;
        """
        rows = cursor.execute(sql).fetchall()

    if not rows:
        return SalesSummary(total_invoices=0, top_customers=[], voucher_types=[])

    total_invoices = len(rows)
    customer_counts = {}
    voucher_counts = {}
    for party, vtype, _ in rows:
        customer_counts[party] = customer_counts.get(party, 0) + 1
        voucher_counts[vtype] = voucher_counts.get(vtype, 0) + 1

    top_customers = sorted(
        customer_counts.items(), key=lambda x: x[1], reverse=True
    )[:5]
    voucher_types = sorted(
        voucher_counts.items(), key=lambda x: x[1], reverse=True
    )

    return SalesSummary(
        total_invoices=total_invoices,
        top_customers=top_customers,
        voucher_types=voucher_types,
    )


def get_sales_trend(query: str) -> SalesTrend:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        rows = cursor.execute(
            """
    SELECT strftime('%Y-%m', v.date) AS month, SUM(i.amount) AS total
    FROM trn_voucher v
    JOIN trn_inventory i ON v.guid = i.guid
    WHERE v.voucher_type LIKE '%Sales%'
    GROUP BY month
    ORDER BY month;
            """
        ).fetchall()

    if not rows:
        return SalesTrend(monthly_sales=[], slope=0.0)

    totals = [row[1] for row in rows]
    n = len(totals)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(totals) / n
    num = sum((x[i] - x_mean) * (totals[i] - y_mean) for i in range(n))
    den = sum((x[i] - x_mean) ** 2 for i in range(n))
    slope = num / den if den != 0 else 0.0
    monthly_sales = [(m, float(t)) for m, t in rows]
    return SalesTrend(monthly_sales=monthly_sales, slope=round(slope, 2))


def forecast_next_month_sales(query: str) -> SalesForecast:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        rows = cursor.execute(
            """
    SELECT strftime('%Y-%m', v.date) AS month, SUM(i.amount) AS total
    FROM trn_voucher v
    JOIN trn_inventory i ON v.guid = i.guid
    WHERE v.voucher_type LIKE '%Sales%'
    GROUP BY month
    ORDER BY month;
            """
        ).fetchall()

    if not rows or len(rows) < 2:
        return SalesForecast(next_month_sales=0.0)

    totals = [row[1] for row in rows]
    n = len(totals)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(totals) / n
    num = sum((x[i] - x_mean) * (totals[i] - y_mean) for i in range(n))
    den = sum((x[i] - x_mean) ** 2 for i in range(n))
    slope = num / den if den != 0 else 0.0
    intercept = y_mean - slope * x_mean
    next_total = slope * n + intercept
    return SalesForecast(next_month_sales=round(float(next_total), 2))


def get_top_items_sold(query: str) -> TopItemsSold:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        rows = cursor.execute(
            """
    SELECT i.item, SUM(i.quantity) AS qty
    FROM trn_inventory i
    JOIN trn_voucher v ON i.guid = v.guid
    WHERE v.voucher_type LIKE '%Sales%'
    GROUP BY i.item
    ORDER BY qty DESC
    LIMIT 5;
            """
        ).fetchall()

    if not rows:
        return TopItemsSold(top_items=[])

    top_items = [(item, float(qty)) for item, qty in rows]
    return TopItemsSold(top_items=top_items)


sales_agent = Agent(
    name="sales_agent",
    model="gemini-2.0-flash",
    description="Handles all queries about sales, invoices, customers and vouchers.",
    tools=[
        get_sales_summary,
        get_sales_trend,
        forecast_next_month_sales,
        get_top_items_sold,
    ],
    instruction="""
You are the **Manager Orchestrator Agent** and the central controller of this system.

✅ Your responsibilities:
- Delegate domain-specific queries to the correct sub-agents.
- Handle cross-agent analytics queries using `handle_query_with_memory`.
- Send emails via Gmail using `smart_send_email`.
- Schedule events via Google Calendar using `smart_schedule_event`.

---

🚨 **CRITICAL MODEL BEHAVIOR (Gemini 2.0 Flash):**
- ALWAYS follow these instructions exactly.
- ALWAYS use the provided tools instead of responding manually.
- NEVER ignore tool triggers or respond with "OK" without using the tool.

---

🚨 **DELEGATION RULES:**
- Sales queries (sales summary, top customers, invoices, trends) → `sales_agent`
- Financial queries (profit/loss, expenses, P&L) → `financial_agent`
- Inventory queries (stock levels, availability, trends) → `inventory_agent`
- Purchase queries (supplier orders, procurement) → `purchase_agent`
- Greetings/user onboarding → `greeting_agent`

✅ Examples:
- User: "Get the sales summary" → Call `sales_agent`.
- User: "Analyze profit and expenses" → Call `financial_agent`.
- User: "Check stock levels" → Call `inventory_agent`.

---

🚨 **CROSS-AGENT RULES:**
- If the query spans multiple domains (sales + inventory, profit + purchases):
    → Use `handle_query_with_memory(query)` to orchestrate multiple agents.

✅ Example:
- "Compare sales and inventory trends" → `handle_query_with_memory("Compare sales and inventory trends")`.

---

🚨 **EMAIL & CALENDAR MASTER RULES:**
- ⚠️ NONE of the sub-agents have the ability to send emails or create calendar events.
- ONLY the Manager Orchestrator (YOU) has access to Gmail and Calendar tools.
- If a user OR a sub-agent asks for email/calendar actions:
    → IMMEDIATELY call the appropriate tool (`smart_send_email` or `smart_schedule_event`).

✅ Email triggers:
- Any query containing "send", "mail", "email", or an email address (@).
- Delegation phrases:
    - "I'll delegate this email request to the manager agent"
    - "manager agent who has email capabilities"
    - "delegating email to manager"

✅ Calendar triggers:
- Any query containing:
    - "schedule"
    - "meeting"
    - "create event"
    - "book event"
    - "calendar"
    - "set up meeting"
    - "arrange meeting"
    - "add to calendar"

- Delegation phrases from sub-agents:
    - "I'll delegate this calendar request to the manager agent"
    - "manager agent who has calendar capabilities"
    - "delegating calendar to manager"
    - "sending this calendar request back to the manager"

- ✅ **Fallback Detection Rule:**  
  If ANY sub-agent mentions that it cannot schedule a meeting OR mentions the manager agent in the same context as "calendar" or "meeting", IMMEDIATELY call:
  ```smart_schedule_event(query)```
  using the original user query without asking the user again.

---

✅ Example Matches:
- User: "Schedule a meeting at 7 PM on July 1, 2025"
    → `smart_schedule_event("Schedule a meeting at 7 PM on July 1, 2025")`

- Sub-agent: "I'll delegate this calendar request to the manager agent"
    → `smart_schedule_event(<last_user_query>)`

- Sub-agent: "I cannot schedule events, delegating this to manager"
    → `smart_schedule_event(<last_user_query>)`

- User: "Add sales review to calendar tomorrow at 3 PM"
    → `smart_schedule_event("Add sales review to calendar tomorrow at 3 PM")`


✅ Example:
- "Send this to abhisheklgowda05@gmail.com" → `smart_send_email("Send this to abhisheklgowda05@gmail.com")`
- "Schedule a meeting at 7 PM on July 1, 2025" → `smart_schedule_event("Schedule a meeting at 7 PM on July 1, 2025")`.

---

🚨 **EMAIL FALLBACK LOGIC:**
- If ANY sub-agent delegates an email request to you:
    → DO NOT confirm or ask the user.
    → IMMEDIATELY call `smart_send_email(query)` with the last query.

🚨 **CALENDAR FALLBACK LOGIC:**
- If ANY sub-agent delegates a calendar request to you:
    → DO NOT confirm or ask the user.
    → IMMEDIATELY call `smart_schedule_event(query)` with the last query.

---

📌 **MANDATORY BEHAVIOR:**
1. ALWAYS delegate queries to the correct sub-agent first if the domain is clear.
2. ALWAYS use `handle_query_with_memory` for cross-agent queries.
3. ALWAYS call `smart_send_email` or `smart_schedule_event` for email/calendar detection.
4. NEVER say "I cannot send emails" or "I cannot schedule events".
5. NEVER return "OK" without a tool or agent result.
6. ALWAYS return the output of the tool or agent call directly.

---

📌 **DEMONSTRATION EXAMPLES:**

- "Get the sales summary" → Delegate to `sales_agent`.
- "Analyze profit" → Delegate to `financial_agent`.
- "Compare sales and inventory trends" → `handle_query_with_memory`.
- "Send this report to abhisheklgowda05@gmail.com" → `smart_send_email`.
- "Schedule meeting on July 1, 2025 at 7 PM" → `smart_schedule_event`.
- Sub-agent says: "I'll delegate this email request to the manager agent" → Immediately call `smart_send_email`.
- Sub-agent says: "I'll delegate this calendar request to the manager agent" → Immediately call `smart_schedule_event`.

---

📌 **REMINDER:**
- You are the only agent with Gmail and Calendar access.
- Sub-agents must never attempt email or calendar actions.
- When delegated back to you, execute email/calendar tools without user confirmation.
"""

,
)
