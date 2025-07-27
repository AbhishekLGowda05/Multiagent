import sqlite3
import os
import pandas as pd
from pydantic import BaseModel
from google.adk.agents import Agent

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../tallydb.db"))

class FinancialSummary(BaseModel):
    total_debit: float
    total_credit: float
    top_ledgers: list

def get_financial_summary(query: str) -> FinancialSummary:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    sql = """
    SELECT ledger, amount
    FROM trn_accounting;
    """
    rows = cursor.execute(sql).fetchall()
    conn.close()

    if not rows:
        return FinancialSummary(total_debit=0.0, total_credit=0.0, top_ledgers=[])

    df = pd.DataFrame(rows, columns=["ledger", "amount"])
    total_debit = df[df["amount"] > 0]["amount"].sum()
    total_credit = df[df["amount"] < 0]["amount"].abs().sum()
    ledger_totals = (
        df.groupby("ledger")["amount"].sum().abs().sort_values(ascending=False).head(5).to_dict()
    )

    return FinancialSummary(
        total_debit=round(float(total_debit), 2),
        total_credit=round(float(total_credit), 2),
        top_ledgers=list(ledger_totals.items()),
    )

financial_agent = Agent(
    name="financial_agent",
    model="gemini-2.0-flash",
    description="Summarizes ledger balances and financial totals.",
    tools=[get_financial_summary],
    instruction="Use this agent for finance or accounting queries.",
)
