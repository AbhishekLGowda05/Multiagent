import sqlite3
import os
import pandas as pd
from pydantic import BaseModel
from google.adk.agents import Agent

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../tallydb.db"))

class FinancialSummary(BaseModel):
    total_income: float
    total_expense: float
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
            total_income=0.0,
            total_expense=0.0,
            top_income_ledgers=[],
            top_expense_ledgers=[],
        )

    df = pd.DataFrame(rows, columns=["ledger", "amount"])
    income = df[df["amount"] > 0]
    expense = df[df["amount"] < 0]
    total_income = income["amount"].sum()
    total_expense = expense["amount"].sum()
    top_income_ledgers = (
        income.groupby("ledger")["amount"].sum()
        .sort_values(ascending=False)
        .head(5)
        .to_dict()
    )
    top_expense_ledgers = (
        expense.groupby("ledger")["amount"].sum()
        .sort_values()
        .head(5)
        .to_dict()
    )

    return FinancialSummary(
        total_income=round(float(total_income), 2),
        total_expense=round(float(total_expense), 2),
        top_income_ledgers=list(top_income_ledgers.items()),
        top_expense_ledgers=list(top_expense_ledgers.items()),
    )


financial_agent = Agent(
    name="financial_agent",
    model="gemini-2.0-flash",
    description="Provides income and expense summaries from the Tally DB.",
    tools=[get_financial_summary],
    instruction="Use this agent for financial queries about income or expenses.",
)
