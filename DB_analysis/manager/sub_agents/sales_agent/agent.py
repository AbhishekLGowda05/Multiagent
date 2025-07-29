import sqlite3
import os
import pandas as pd
import numpy as np
from pydantic import BaseModel
from google.adk.agents import Agent

DB_PATH = os.environ.get(
    "TALLY_DB_PATH",
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../../tallydb.db")
    ),

)


class SalesSummary(BaseModel):
    total_invoices: int
    top_customers: list
    voucher_types: list


class SalesTrend(BaseModel):
    monthly_sales: list
    slope: float


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
        voucher_types=list(voucher_types.items()),
    )


def get_sales_trend(query: str) -> SalesTrend:
    conn = sqlite3.connect(DB_PATH)
    sql = """
    SELECT strftime('%Y-%m', v.date) AS month, SUM(i.amount) AS total
    FROM trn_voucher v
    JOIN trn_inventory i ON v.guid = i.guid
    WHERE v.voucher_type LIKE '%Sales%'
    GROUP BY month
    ORDER BY month;
    """
    df = pd.read_sql_query(sql, conn)
    conn.close()

    if df.empty:
        return SalesTrend(monthly_sales=[], slope=0.0)

    x = np.arange(len(df))
    y = df["total"].values
    slope = float(np.polyfit(x, y, 1)[0])
    monthly_sales = [(m, float(t)) for m, t in df[["month", "total"]].values.tolist()]
    return SalesTrend(monthly_sales=monthly_sales, slope=round(slope, 2))


sales_agent = Agent(
    name="sales_agent",
    model="gemini-2.0-flash",
    description="Handles all queries about sales, invoices, customers and vouchers.",
    tools=[get_sales_summary, get_sales_trend],
    instruction="Whenever a user asks about sales, invoices or customers, call this agent.",
)
