import sqlite3
import os
import pandas as pd
from pydantic import BaseModel
from google.adk.agents import Agent

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../tallydb.db"))

class PrescriptiveActions(BaseModel):
    actions: list

def recommend_sales_actions(query: str) -> PrescriptiveActions:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    sql = """
    SELECT party_name, date 
    FROM trn_voucher
    WHERE voucher_type LIKE '%Sales%';
    """
    rows = cursor.execute(sql).fetchall()
    conn.close()

    if not rows:
        return PrescriptiveActions(actions=["No sales data available to prescribe actions."])

    df = pd.DataFrame(rows, columns=["party_name", "date"])
    df["date"] = pd.to_datetime(df["date"])

    # ✅ Split into two periods to see trends
    mid_date = df["date"].median()
    p1 = df[df["date"] <= mid_date]
    p2 = df[df["date"] > mid_date]

    p1_counts = p1["party_name"].value_counts()
    p2_counts = p2["party_name"].value_counts()
    diff = (p2_counts - p1_counts).sort_values(ascending=False)

    actions = []

    # ✅ Customers with declining sales → follow-up
    declining = diff[diff < 0].head(3)
    for cust, change in declining.items():
        actions.append(f"⚠️ Follow up with **{cust}**: Sales dropped by {abs(change)} invoices. Consider special offers or a re-engagement campaign.")

    # ✅ Customers with increasing sales → loyalty discounts
    growing = diff[diff > 0].head(3)
    for cust, change in growing.items():
        actions.append(f"✅ Retain **{cust}**: Sales increased by {change} invoices. Consider providing a loyalty discount to strengthen relationship.")

    # ✅ Customers with no activity in second period → churn prevention
    inactive = set(p1["party_name"]) - set(p2["party_name"])
    for cust in list(inactive)[:3]:
        actions.append(f"🚨 **{cust}** has gone inactive in the latest period. Reach out to understand reasons and offer incentives.")

    if not actions:
        actions.append("Sales trends are stable. Maintain current customer relationship strategies.")

    return PrescriptiveActions(actions=actions)

prescriptive_agent = Agent(
    name="prescriptive_agent",
    model="gemini-2.0-flash",
    description="Analyzes sales patterns and prescribes business actions to improve performance.",
    tools=[recommend_sales_actions],
    instruction="Use this agent when the user asks what actions should be taken to boost sales or retain customers."
)
