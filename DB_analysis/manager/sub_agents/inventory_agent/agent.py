import sqlite3
import os
import pandas as pd
from pydantic import BaseModel
from google.adk.agents import Agent

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../tallydb.db"))

class InventorySummary(BaseModel):
    total_unique_items: int
    top_items_quantity: list
    top_items_value: list


def get_inventory_summary(query: str) -> InventorySummary:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    sql = """
    SELECT item, SUM(quantity) AS qty, SUM(amount) AS amount
    FROM trn_inventory
    GROUP BY item;
    """
    rows = cursor.execute(sql).fetchall()
    conn.close()

    if not rows:
        return InventorySummary(
            total_unique_items=0,
            top_items_quantity=[],
            top_items_value=[],
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


inventory_agent = Agent(
    name="inventory_agent",
    model="gemini-2.0-flash",
    description="Summarizes inventory levels and stock values from the Tally DB.",
    tools=[get_inventory_summary],
    instruction="Use this agent for inventory level and stock value questions.",
)
