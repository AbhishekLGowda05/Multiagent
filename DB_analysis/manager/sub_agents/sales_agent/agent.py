import sqlite3
import os
import pandas as pd
from pydantic import BaseModel
from google.adk.agents import Agent

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../tallydb.db"))

class SalesSummary(BaseModel):
    total_invoices: int
    top_customers: list
    voucher_types: list

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

    df = pd.DataFrame(rows, columns=["party_name", "voucher_type", "date"])
    total_invoices = len(df)
    top_customers = df["party_name"].value_counts().head(5).to_dict()
    voucher_types = df["voucher_type"].value_counts().to_dict()

    

    return SalesSummary(
        total_invoices=total_invoices,
        top_customers=list(top_customers.items()),
        voucher_types=list(voucher_types.items())
    )

sales_agent = Agent(
    
    name="sales_agent",
    model="gemini-2.0-flash",
    description="Handles all queries about sales, invoices, customers and vouchers.",
    tools=[get_sales_summary],
    instruction="Whenever a user asks about sales, invoices or customers, call this agent.",
     
)

