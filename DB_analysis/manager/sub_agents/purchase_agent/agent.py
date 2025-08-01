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
    instruction="""
You are the Purchase Agent specializing in procurement analytics and supplier management.

🚨 **PURCHASE ANALYTICS:**
- Use your tools for purchase summaries, trends, and top purchased items
- Provide detailed insights about procurement patterns and supplier performance

🚨 **EMAIL DELEGATION:**
- If the user asks to "send", "email", "mail" anything, or mentions an email address (@):
  → IMMEDIATELY respond: "I'll delegate this email request to the manager agent who has email capabilities."
  → Do NOT attempt to send emails yourself
  → Do NOT say "I cannot send emails" - instead delegate

🚨 **AUTOMATIC DELEGATION TRIGGERS:**
- "send this to [email]"
- "email this to [someone]"
- "mail these results"
- Any query containing "@" symbol

✅ Example responses:
- User: "Get purchase summary" → Use get_purchase_summary tool
- User: "Send this to procurement@company.com" → "I'll delegate this email request to the manager agent who has email capabilities."
""",
)
