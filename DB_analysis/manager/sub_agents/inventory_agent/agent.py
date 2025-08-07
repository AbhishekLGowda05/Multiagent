import sqlite3
import os
from statistics import pvariance
from pydantic import BaseModel
from google.adk.agents import Agent

DB_PATH = os.environ.get(
    "TALLY_DB_PATH",
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../../tallydb.db")
    ),

)


class InventorySummary(BaseModel):
    total_unique_items: int
    top_items_quantity: list
    top_items_value: list


class InventoryDemandForecast(BaseModel):
    next_month_quantity: float


class InventoryTurnover(BaseModel):
    turnover_ratio: float


class LowStockItems(BaseModel):
    items: list


def get_inventory_summary(query: str) -> InventorySummary:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        sql = """
        SELECT item, SUM(quantity) AS qty, SUM(amount) AS amount
        FROM trn_inventory
        GROUP BY item;
        """
        rows = cursor.execute(sql).fetchall()

    if not rows:
        return InventorySummary(
            total_unique_items=0, top_items_quantity=[], top_items_value=[]
        )

    qty_totals = {}
    amt_totals = {}
    for item, qty, amount in rows:
        qty_totals[item] = qty_totals.get(item, 0.0) + qty
        amt_totals[item] = amt_totals.get(item, 0.0) + amount

    total_unique_items = len(qty_totals)
    top_items_quantity = sorted(
        qty_totals.items(), key=lambda x: x[1], reverse=True
    )[:5]
    top_items_value = sorted(
        amt_totals.items(), key=lambda x: x[1], reverse=True
    )[:5]

    return InventorySummary(
        total_unique_items=total_unique_items,
        top_items_quantity=[(i, float(q)) for i, q in top_items_quantity],
        top_items_value=[(i, float(v)) for i, v in top_items_value],
    )


def forecast_inventory_demand(query: str) -> InventoryDemandForecast:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        rows = cursor.execute(
            """
    SELECT strftime('%Y-%m', v.date) AS month, SUM(i.quantity) AS qty
    FROM trn_voucher v
    JOIN trn_inventory i ON v.guid = i.guid
    WHERE v.voucher_type LIKE '%Sales%'
    GROUP BY month
    ORDER BY month;
            """
        ).fetchall()

    if not rows or len(rows) < 2:
        return InventoryDemandForecast(next_month_quantity=0.0)

    quantities = [row[1] for row in rows]
    n = len(quantities)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(quantities) / n
    num = sum((x[i] - x_mean) * (quantities[i] - y_mean) for i in range(n))
    den = sum((x[i] - x_mean) ** 2 for i in range(n))
    slope = num / den if den != 0 else 0.0
    intercept = y_mean - slope * x_mean
    next_qty = slope * n + intercept
    return InventoryDemandForecast(next_month_quantity=round(float(next_qty), 2))


def calculate_inventory_turnover(query: str) -> InventoryTurnover:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        sql_sales = (
            "SELECT SUM(i.quantity) FROM trn_inventory i "
            "JOIN trn_voucher v ON i.guid = v.guid "
            "WHERE v.voucher_type LIKE '%Sales%'"
        )
        sql_purchases = (
            "SELECT SUM(i.quantity) FROM trn_inventory i "
            "JOIN trn_voucher v ON i.guid = v.guid "
            "WHERE v.voucher_type LIKE '%Purchase%'"
        )
        sales_qty = cursor.execute(sql_sales).fetchone()[0] or 0.0
        purchase_qty = cursor.execute(sql_purchases).fetchone()[0] or 0.0

    avg_inventory = (purchase_qty - sales_qty) / 2
    if avg_inventory <= 0:
        ratio = 0.0
    else:
        ratio = sales_qty / avg_inventory
    return InventoryTurnover(turnover_ratio=round(float(ratio), 2))


def get_low_stock_items(query: str) -> LowStockItems:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        rows = cursor.execute(
            """
    SELECT item, SUM(quantity) AS qty
    FROM trn_inventory
    GROUP BY item
    HAVING qty < 5
    ORDER BY qty ASC;
            """
        ).fetchall()

    if not rows:
        return LowStockItems(items=[])

    items = [(item, float(qty)) for item, qty in rows]
    return LowStockItems(items=items)


inventory_agent = Agent(
    name="inventory_agent",
    model="gemini-2.0-flash",
    description="Handles inventory-related queries and summarizes stock levels and values from the Tally DB.",
    tools=[
        get_inventory_summary,
        forecast_inventory_demand,
        calculate_inventory_turnover,
        get_low_stock_items,
    ],
    instruction = """
You are the Inventory Agent. You handle all queries related to:
- Product stock levels
- Inventory summaries
- Item-wise availability
- Inventory value over time
- Low stock alerts and trends
anything else if asked for DELEGATE BACK TO ROOT AGENT 
when asked to send email or schedule a calendar event, IMMEDIATELY delegate to the ROOT AGENT saying This request involves sending an email or scheduling an event, which I cannot handle. Delegating to the root agent." or
  - "I'll delegate this email request to the manager agent who has email capabilities."

---

🚨 **CRITICAL MODEL BEHAVIOR (Gemini 2.0 Flash):**
- ALWAYS follow these instructions exactly.
- ALWAYS use the provided tools instead of responding manually.
- NEVER ignore tool triggers or respond with "OK" without using the tool.

---

🚨 **DELEGATION RULES:**
- Inventory queries (product stock, low stock items, availability trends) → `inventory_agent`
- Financial queries (cash flow, expenses, income, ledgers) → `financial_agent`
- Sales queries (summaries, invoices, trends) → `sales_agent`
- Purchase queries (supplier orders, procurement) → `purchase_agent`
- Greetings/user onboarding → `greeting_agent`

✅ Examples:
- "What are the current stock levels?" → Call `inventory_agent`
- "Which items are low on stock?" → Call `inventory_agent`
- "Get profit vs loss details" → Delegate to `financial_agent`
- "Top selling items" → Delegate to `sales_agent`

---

Use ONLY the tools provided to you:
- `get_inventory_summary`
- `get_inventory_stock_levels`
- `get_low_stock_items`
- `get_inventory_value_trend`

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
- "Send current stock summary to my email" → `smart_send_email("Send current stock summary to my email")`
- "Schedule a meeting to discuss inventory" → `smart_schedule_event("Schedule a meeting to discuss inventory")`

---

🚨 **EMAIL FALLBACK LOGIC:**
If ANY sub-agent delegates an email request to you:
→ DO NOT confirm or ask the user.
→ IMMEDIATELY call `smart_send_email(query)` with the last query.

🚨 **CALENDAR FALLBACK LOGIC:**
If ANY sub-agent delegates a calendar request to you:
→ DO NOT confirm or ask the user.
→ IMMEDIATELY call `smart_schedule_event(query)` with the last query.

---

📌 **MANDATORY BEHAVIOR:**
1. ONLY use your tools to answer inventory-related queries.
2. DELEGATE non-inventory queries to the correct agents.
3. DETECT and escalate email/calendar queries to the manager.
4. NEVER respond with "OK" or generic text.
5. NEVER attempt to email or schedule directly.

---

📌 **REMINDER:**
- You do NOT have Gmail or Calendar access.
- If asked to send mail or schedule a meeting:
→ Respond with:
"This request involves sending an email or scheduling an event, which I cannot handle. Delegating to the root agent."
"""
,
)

