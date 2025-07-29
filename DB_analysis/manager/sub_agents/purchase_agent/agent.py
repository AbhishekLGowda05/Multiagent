import sqlite3
import os
import pandas as pd
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

    df = pd.DataFrame(rows, columns=["party_name", "voucher_type", "date"])
    total_invoices = len(df)
    top_suppliers = df["party_name"].value_counts().head(5).to_dict()
    voucher_types = df["voucher_type"].value_counts().to_dict()

    return PurchaseSummary(
        total_invoices=total_invoices,
        top_suppliers=list(top_suppliers.items()),
        voucher_types=list(voucher_types.items()),
    )

purchase_agent = Agent(
    name="purchase_agent",
    model="gemini-2.0-flash",
    description="Handles purchase-related queries and summarizes purchase invoices and suppliers from the Tally DB.",
    tools=[get_purchase_summary],
    instruction="Use this agent for questions about purchases, suppliers, or vendor invoices.",
)
