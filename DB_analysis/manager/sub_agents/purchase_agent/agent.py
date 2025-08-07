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

class PurchaseSummary(BaseModel):
    total_invoices: int
    top_suppliers: list
    voucher_types: list


class PurchaseTrend(BaseModel):
    monthly_purchases: list
    slope: float


class TopPurchasedItems(BaseModel):
    top_items: list

def get_purchase_summary(query: str) -> PurchaseSummary:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        sql = """
        SELECT party_name, voucher_type, date
        FROM trn_voucher
        WHERE voucher_type LIKE '%Purchase%'
        LIMIT 100;
        """
        rows = cursor.execute(sql).fetchall()

    if not rows:
        return PurchaseSummary(total_invoices=0, top_suppliers=[], voucher_types=[])

    total_invoices = len(rows)
    supplier_counts = {}
    voucher_counts = {}
    for party, vtype, _ in rows:
        supplier_counts[party] = supplier_counts.get(party, 0) + 1
        voucher_counts[vtype] = voucher_counts.get(vtype, 0) + 1

    top_suppliers = sorted(
        supplier_counts.items(), key=lambda x: x[1], reverse=True
    )[:5]
    voucher_types = sorted(
        voucher_counts.items(), key=lambda x: x[1], reverse=True
    )

    return PurchaseSummary(
        total_invoices=total_invoices,
        top_suppliers=top_suppliers,
        voucher_types=voucher_types,
    )


def get_purchase_trend(query: str) -> PurchaseTrend:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        rows = cursor.execute(
            """
    SELECT strftime('%Y-%m', v.date) AS month, SUM(i.amount) AS total
    FROM trn_voucher v
    JOIN trn_inventory i ON v.guid = i.guid
    WHERE v.voucher_type LIKE '%Purchase%'
    GROUP BY month
    ORDER BY month;
            """
        ).fetchall()

    if not rows:
        return PurchaseTrend(monthly_purchases=[], slope=0.0)

    totals = [row[1] for row in rows]
    n = len(totals)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(totals) / n
    num = sum((x[i] - x_mean) * (totals[i] - y_mean) for i in range(n))
    den = sum((x[i] - x_mean) ** 2 for i in range(n))
    slope = num / den if den != 0 else 0.0
    monthly_purchases = [(m, float(t)) for m, t in rows]
    return PurchaseTrend(monthly_purchases=monthly_purchases, slope=round(slope, 2))


def get_top_items_purchased(query: str) -> TopPurchasedItems:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        rows = cursor.execute(
            """
    SELECT i.item, SUM(i.quantity) AS qty
    FROM trn_inventory i
    JOIN trn_voucher v ON i.guid = v.guid
    WHERE v.voucher_type LIKE '%Purchase%'
    GROUP BY i.item
    ORDER BY qty DESC
    LIMIT 5;
            """
        ).fetchall()

    if not rows:
        return TopPurchasedItems(top_items=[])

    top_items = [(item, float(qty)) for item, qty in rows]
    return TopPurchasedItems(top_items=top_items)

purchase_agent = Agent(
    name="purchase_agent",
    model="gemini-2.0-flash",
    description="Handles purchase-related queries and summarizes purchase invoices and suppliers from the Tally DB.",
    tools=[
        get_purchase_summary,
        get_purchase_trend,
        get_top_items_purchased,
    ],
   instruction = """
You are the Purchase Agent. You handle all queries related to:
- Supplier purchases and orders
- Procurement data
- Top suppliers
- Purchase summaries and trends
- Incoming inventory due to purchasing
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
- Purchase queries (supplier data, procurement summaries, top vendors) → `purchase_agent`
- Inventory queries (stock, low items, inventory value) → `inventory_agent`
- Financial queries (P&L, income/expenses) → `financial_agent`
- Sales queries (sales trend, top customers, invoices) → `sales_agent`
- Greetings/user onboarding → `greeting_agent`

✅ Examples:
- "Show me purchase summary for last month" → Call `purchase_agent`
- "Which suppliers contributed to the largest orders?" → Call `purchase_agent`
- "Get stock availability" → Delegate to `inventory_agent`
- "Analyze profit" → Delegate to `financial_agent`

---

Use ONLY the tools provided to you:
- `get_purchase_summary`
- `get_top_suppliers`
- `get_procurement_trend`

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
- "Send purchase summary to abhisheklgowda05@gmail.com" → `smart_send_email("Send purchase summary to abhisheklgowda05@gmail.com")`
- "Schedule a call with the top supplier for next Friday" → `smart_schedule_event("Schedule a call with the top supplier for next Friday")`

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
1. ONLY use your tools to answer purchase-related queries.
2. DELEGATE non-purchase queries to the correct agents.
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
