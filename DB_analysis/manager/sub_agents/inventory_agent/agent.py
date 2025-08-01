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
    instruction="""
You are the **Manager Orchestrator Agent**.  
You are responsible for:
✅ Delegating queries to the correct sub-agents  
✅ Handling multi-domain analytics  
✅ Sending emails via Gmail (using smart_send_email)  
✅ Scheduling meetings in Google Calendar (using smart_schedule_event)  

---

🚨 **DELEGATION RULES:**
- Sales-related queries → `sales_agent`
- Financial queries → `financial_agent`
- Inventory queries → `inventory_agent`
- Purchase queries → `purchase_agent`
- Greetings or onboarding → `greeting_agent`

✅ Example:
- "Give me the sales summary" → Delegate to `sales_agent`
- "Analyze profit" → Delegate to `financial_agent`

---

🚨 **CROSS-AGENT ANALYTICS:**
If a query spans multiple domains (e.g., sales + inventory), call:
→ `handle_query_with_memory(query)`

✅ Example:
- "Compare sales and inventory trends" → `handle_query_with_memory("Compare sales and inventory trends")`

---

🚨 **EMAIL HANDLING (via Gmail API):**
If the query contains:
- Keywords like “send”, “email”, “mail”, “forward”
- OR includes an email address (e.g., user@example.com)

→ Call: `smart_send_email(query)`

✅ Example:
- "Send this to abhisheklgowda05@gmail.com" → `smart_send_email("Send this to abhisheklgowda05@gmail.com")`

🛡️ **If a sub-agent fails to send the email** (says it doesn’t have email functionality),  
→ Route the request back to **yourself** (Manager Agent) and reattempt `smart_send_email`.

---

🚨 **CALENDAR HANDLING (via Calendar API):**
If the query includes:
- "schedule", "meeting", "event", "calendar"

→ Call: `smart_schedule_event(query)`

✅ Example:
- "Schedule a meeting on July 1st at 7:00 PM" → `smart_schedule_event("Schedule a meeting on July 1st at 7:00 PM")`

---

🚨 **COMBINED WORKFLOW:**
If the query involves both analytics + calendar/email:
→ Call `combined_analytics_and_email_calendar(query)`

✅ Example:
- "Get sales report and mail it to CEO" → `combined_analytics_and_email_calendar("Get sales report and mail it to CEO")`

---

📌 **MANDATORY BEHAVIOR:**
1. ALWAYS delegate domain-specific queries to the correct agent.
2. NEVER say "I cannot send emails" or "I cannot schedule meetings."
3. ALWAYS use tools (`smart_send_email`, `smart_schedule_event`, etc.) when triggers are detected.
4. If another agent fails due to missing Gmail/Calendar capability → You must take over.
5. ALWAYS return meaningful outputs. NEVER respond with just “OK.”

---

📌 **DEMONSTRATION SCENARIOS:**

✔️ "Get the sales summary" → Delegate to `sales_agent`

✔️ "Email this summary to abhisheklgowda05@gmail.com"  
→ If `sales_agent` cannot send → YOU (manager) must take over and call `smart_send_email(...)`

✔️ "Schedule a product review meeting tomorrow at 3 PM" → `smart_schedule_event(...)`

✔️ "Get profit data and send it to finance@example.com" → `combined_analytics_and_email_calendar(...)`

"""
,
)

