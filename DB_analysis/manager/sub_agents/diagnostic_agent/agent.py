import sqlite3
import os
import pandas as pd
from pydantic import BaseModel
from google.adk.agents import Agent

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../tallydb.db"))

class DiagnosticSummary(BaseModel):
    period_1_revenue: float
    period_2_revenue: float
    change_percent: float
    top_increase_customers: list
    top_decrease_customers: list

def diagnose_sales_change(query: str) -> DiagnosticSummary:
    """
    Compares sales revenue between two time windows and identifies customers driving change.
    """

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    sql = """
    SELECT v.party_name, v.date, a.amount
    FROM trn_voucher v
    JOIN trn_accounting a ON v.guid = a.guid
    WHERE v.voucher_type LIKE '%Sales%';
    """
    rows = cursor.execute(sql).fetchall()
    conn.close()

    if not rows:
        return DiagnosticSummary(
            period_1_revenue=0,
            period_2_revenue=0,
            change_percent=0,
            top_increase_customers=[],
            top_decrease_customers=[]
        )

    df = pd.DataFrame(rows, columns=["party_name", "date", "amount"])
    df["date"] = pd.to_datetime(df["date"])

    # ✅ Split into two halves of available data
    mid_date = df["date"].median()
    p1 = df[df["date"] <= mid_date]
    p2 = df[df["date"] > mid_date]

    p1_revenue = p1["amount"].sum()
    p2_revenue = p2["amount"].sum()
    change_percent = ((p2_revenue - p1_revenue) / max(p1_revenue, 1)) * 100

    # ✅ Customer contribution changes
    p1_cust = p1.groupby("party_name")["amount"].sum()
    p2_cust = p2.groupby("party_name")["amount"].sum()
    diff = (p2_cust - p1_cust).sort_values(ascending=False)

    top_increase = diff[diff > 0].head(3).to_dict()
    top_decrease = diff[diff < 0].head(3).to_dict()

    return DiagnosticSummary(
        period_1_revenue=round(float(p1_revenue), 2),
        period_2_revenue=round(float(p2_revenue), 2),
        change_percent=round(float(change_percent), 2),
        top_increase_customers=list(top_increase.items()),
        top_decrease_customers=list(top_decrease.items())
    )

diagnostic_agent = Agent(
    name="diagnostic_agent",
    model="gemini-2.0-flash",
    description="Analyzes revenue changes between periods and identifies customer impact.",
    tools=[diagnose_sales_change],
    instruction="Use this agent when the user asks why sales or revenue changed over time."
)
