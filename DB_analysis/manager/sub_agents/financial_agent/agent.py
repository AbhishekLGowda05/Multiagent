import sqlite3
import os
import pandas as pd
from pydantic import BaseModel
from google.adk.agents import Agent

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../tallydb.db"))

class FinancialSummary(BaseModel):
    total_debit: float
    total_credit: float
    top_income_ledgers: list
    top_expense_ledgers: list

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
        return FinancialSummary(
            total_debit=0.0,
            total_credit=0.0,
            top_income_ledgers=[],
            top_expense_ledgers=[]
        )

    df = pd.DataFrame(rows, columns=["ledger", "amount"])
    income = df[df["amount"] > 0]
    expense = df[df["amount"] < 0]

    total_debit = income["amount"].sum()
    total_credit = abs(expense["amount"].sum())

    top_income_ledgers = (
        income.groupby("ledger")["amount"].sum()
        .sort_values(ascending=False)
        .head(5)
        .to_dict()
    )
    top_expense_ledgers = (
        expense.groupby("ledger")["amount"].sum()
        .abs()
        .sort_values(ascending=False)
        .head(5)
        .to_dict()
    )

    return FinancialSummary(
        total_debit=round(float(total_debit), 2),
        total_credit=round(float(total_credit), 2),
        top_income_ledgers=list(top_income_ledgers.items()),
        top_expense_ledgers=list(top_expense_ledgers.items()),
    )

financial_agent = Agent(
    name="financial_agent",
    model="gemini-2.0-flash",
    description="Handles financial queries and summarizes income, expenses, and top ledgers from the Tally DB.",
    tools=[get_financial_summary],
    instruction="Use this agent for financial or accounting queries.",
)
