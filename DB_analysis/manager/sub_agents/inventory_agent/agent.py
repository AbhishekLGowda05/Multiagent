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


class InventorySummary(BaseModel):
    total_unique_items: int
    top_items_quantity: list
    top_items_value: list


class InventoryDemandForecast(BaseModel):
    next_month_quantity: float


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

    df = pd.DataFrame(rows, columns=["item", "quantity", "amount"])
    total_unique_items = len(df)

    top_items_quantity = (
        df.sort_values("quantity", ascending=False)
        .head(5)[["item", "quantity"]]
        .values.tolist()
    )
    top_items_value = (
        df.sort_values("amount", ascending=False)
        .head(5)[["item", "amount"]]
        .values.tolist()
    )

    return InventorySummary(
        total_unique_items=total_unique_items,
        top_items_quantity=[(i, float(q)) for i, q in top_items_quantity],
        top_items_value=[(i, float(v)) for i, v in top_items_value],
    )


def forecast_inventory_demand(query: str) -> InventoryDemandForecast:
    conn = sqlite3.connect(DB_PATH)
    sql = """
    SELECT strftime('%Y-%m', v.date) AS month, SUM(i.quantity) AS qty
    FROM trn_voucher v
    JOIN trn_inventory i ON v.guid = i.guid
    WHERE v.voucher_type LIKE '%Sales%'
    GROUP BY month
    ORDER BY month;
    """
    df = pd.read_sql_query(sql, conn)
    conn.close()

    if df.empty or len(df) < 2:
        return InventoryDemandForecast(next_month_quantity=0.0)

    x = np.arange(len(df))
    y = df["qty"].values
    slope, intercept = np.polyfit(x, y, 1)
    next_qty = slope * len(df) + intercept
    return InventoryDemandForecast(next_month_quantity=round(float(next_qty), 2))


inventory_agent = Agent(
    name="inventory_agent",
    model="gemini-2.0-flash",
    description="Handles inventory-related queries and summarizes stock levels and values from the Tally DB.",
    tools=[get_inventory_summary, forecast_inventory_demand],
    instruction="Use this agent for questions about inventory levels and stock status.",
)
