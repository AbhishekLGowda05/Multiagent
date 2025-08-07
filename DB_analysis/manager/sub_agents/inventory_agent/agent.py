import sqlite3
import os
from statistics import pvariance
from pydantic import BaseModel
from google.adk.agents import Agent

DB_PATH = os.environ.get(
    "TALLY_DB_PATH",
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../../tallydb.db")
    ),

)


class InventorySummary(BaseModel):
    total_unique_items: int
    top_items_quantity: list
    top_items_value: list


class InventoryDemandForecast(BaseModel):
    next_month_quantity: float


class InventoryTurnover(BaseModel):
    turnover_ratio: float


class LowStockItems(BaseModel):
    items: list


def get_inventory_summary(query: str) -> InventorySummary:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        sql = """
        SELECT item, SUM(quantity) AS qty, SUM(amount) AS amount
        FROM trn_inventory
        GROUP BY item;
        """
        rows = cursor.execute(sql).fetchall()

    if not rows:
        return InventorySummary(
            total_unique_items=0, top_items_quantity=[], top_items_value=[]
        )

    qty_totals = {}
    amt_totals = {}
    for item, qty, amount in rows:
        qty_totals[item] = qty_totals.get(item, 0.0) + qty
        amt_totals[item] = amt_totals.get(item, 0.0) + amount

    total_unique_items = len(qty_totals)
    top_items_quantity = sorted(
        qty_totals.items(), key=lambda x: x[1], reverse=True
    )[:5]
    top_items_value = sorted(
        amt_totals.items(), key=lambda x: x[1], reverse=True
    )[:5]

    return InventorySummary(
        total_unique_items=total_unique_items,
        top_items_quantity=[(i, float(q)) for i, q in top_items_quantity],
        top_items_value=[(i, float(v)) for i, v in top_items_value],
    )


def forecast_inventory_demand(query: str) -> InventoryDemandForecast:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        rows = cursor.execute(
            """
    SELECT strftime('%Y-%m', v.date) AS month, SUM(i.quantity) AS qty
    FROM trn_voucher v
    JOIN trn_inventory i ON v.guid = i.guid
    WHERE v.voucher_type LIKE '%Sales%'
    GROUP BY month
    ORDER BY month;
            """
        ).fetchall()

    if not rows or len(rows) < 2:
        return InventoryDemandForecast(next_month_quantity=0.0)

    quantities = [row[1] for row in rows]
    n = len(quantities)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(quantities) / n
    num = sum((x[i] - x_mean) * (quantities[i] - y_mean) for i in range(n))
    den = sum((x[i] - x_mean) ** 2 for i in range(n))
    slope = num / den if den != 0 else 0.0
    intercept = y_mean - slope * x_mean
    next_qty = slope * n + intercept
    return InventoryDemandForecast(next_month_quantity=round(float(next_qty), 2))


def calculate_inventory_turnover(query: str) -> InventoryTurnover:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        sql_sales = (
            "SELECT SUM(i.quantity) FROM trn_inventory i "
            "JOIN trn_voucher v ON i.guid = v.guid "
            "WHERE v.voucher_type LIKE '%Sales%'"
        )
        sql_purchases = (
            "SELECT SUM(i.quantity) FROM trn_inventory i "
            "JOIN trn_voucher v ON i.guid = v.guid "
            "WHERE v.voucher_type LIKE '%Purchase%'"
        )
        sales_qty = cursor.execute(sql_sales).fetchone()[0] or 0.0
        purchase_qty = cursor.execute(sql_purchases).fetchone()[0] or 0.0

    avg_inventory = (purchase_qty - sales_qty) / 2
    if avg_inventory <= 0:
        ratio = 0.0
    else:
        ratio = sales_qty / avg_inventory
    return InventoryTurnover(turnover_ratio=round(float(ratio), 2))


def get_low_stock_items(query: str) -> LowStockItems:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        rows = cursor.execute(
            """
    SELECT item, SUM(quantity) AS qty
    FROM trn_inventory
    GROUP BY item
    HAVING qty < 5
    ORDER BY qty ASC;
            """
        ).fetchall()

    if not rows:
        return LowStockItems(items=[])

    items = [(item, float(qty)) for item, qty in rows]
    return LowStockItems(items=items)


inventory_agent = Agent(
    name="inventory_agent",
    model="gemini-2.0-flash",
    description="Handles inventory-related queries and summarizes stock levels and values from the Tally DB.",
    tools=[
        get_inventory_summary,
        forecast_inventory_demand,
        calculate_inventory_turnover,
        get_low_stock_items,
    ],
    instruction="""You are the Inventory Agent. Handle product stock levels, inventory summaries, item-wise availability, inventory value over time, and low stock alerts and trends.

Delegate email requests to the manager agent. Meeting or calendar requests are ignored because scheduling is unsupported.

If a query is outside your inventory scope, delegate it back to the root agent.""",
)

