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


class SalesSummary(BaseModel):
    total_invoices: int
    top_customers: list
    voucher_types: list


class SalesTrend(BaseModel):
    monthly_sales: list
    slope: float


class SalesForecast(BaseModel):
    next_month_sales: float


class TopItemsSold(BaseModel):
    top_items: list


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

    total_invoices = len(rows)
    customer_counts = {}
    voucher_counts = {}
    for party, vtype, _ in rows:
        customer_counts[party] = customer_counts.get(party, 0) + 1
        voucher_counts[vtype] = voucher_counts.get(vtype, 0) + 1

    top_customers = sorted(
        customer_counts.items(), key=lambda x: x[1], reverse=True
    )[:5]
    voucher_types = sorted(
        voucher_counts.items(), key=lambda x: x[1], reverse=True
    )

    return SalesSummary(
        total_invoices=total_invoices,
        top_customers=top_customers,
        voucher_types=voucher_types,
    )


def get_sales_trend(query: str) -> SalesTrend:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        rows = cursor.execute(
            """
    SELECT strftime('%Y-%m', v.date) AS month, SUM(i.amount) AS total
    FROM trn_voucher v
    JOIN trn_inventory i ON v.guid = i.guid
    WHERE v.voucher_type LIKE '%Sales%'
    GROUP BY month
    ORDER BY month;
            """
        ).fetchall()

    if not rows:
        return SalesTrend(monthly_sales=[], slope=0.0)

    totals = [row[1] for row in rows]
    n = len(totals)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(totals) / n
    num = sum((x[i] - x_mean) * (totals[i] - y_mean) for i in range(n))
    den = sum((x[i] - x_mean) ** 2 for i in range(n))
    slope = num / den if den != 0 else 0.0
    monthly_sales = [(m, float(t)) for m, t in rows]
    return SalesTrend(monthly_sales=monthly_sales, slope=round(slope, 2))


def forecast_next_month_sales(query: str) -> SalesForecast:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        rows = cursor.execute(
            """
    SELECT strftime('%Y-%m', v.date) AS month, SUM(i.amount) AS total
    FROM trn_voucher v
    JOIN trn_inventory i ON v.guid = i.guid
    WHERE v.voucher_type LIKE '%Sales%'
    GROUP BY month
    ORDER BY month;
            """
        ).fetchall()

    if not rows or len(rows) < 2:
        return SalesForecast(next_month_sales=0.0)

    totals = [row[1] for row in rows]
    n = len(totals)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(totals) / n
    num = sum((x[i] - x_mean) * (totals[i] - y_mean) for i in range(n))
    den = sum((x[i] - x_mean) ** 2 for i in range(n))
    slope = num / den if den != 0 else 0.0
    intercept = y_mean - slope * x_mean
    next_total = slope * n + intercept
    return SalesForecast(next_month_sales=round(float(next_total), 2))


def get_top_items_sold(query: str) -> TopItemsSold:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        rows = cursor.execute(
            """
    SELECT i.item, SUM(i.quantity) AS qty
    FROM trn_inventory i
    JOIN trn_voucher v ON i.guid = v.guid
    WHERE v.voucher_type LIKE '%Sales%'
    GROUP BY i.item
    ORDER BY qty DESC
    LIMIT 5;
            """
        ).fetchall()

    if not rows:
        return TopItemsSold(top_items=[])

    top_items = [(item, float(qty)) for item, qty in rows]
    return TopItemsSold(top_items=top_items)


sales_agent = Agent(
    name="sales_agent",
    model="gemini-2.0-flash",
    description="Handles all queries about sales, invoices, customers and vouchers.",
    tools=[
        get_sales_summary,
        get_sales_trend,
        forecast_next_month_sales,
        get_top_items_sold,
    ],
    instruction="Whenever a user asks about sales, invoices or customers, call this agent.",
)
