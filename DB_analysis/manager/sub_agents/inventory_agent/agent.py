import sqlite3
import os
import pandas as pd
from pydantic import BaseModel
from google.adk.agents import Agent

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../tallydb.db"))

class InventorySummary(BaseModel):
    total_items: int
    top_items: list

def get_inventory_overview(query: str) -> InventorySummary:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    sql = """
    SELECT item, SUM(quantity) as qty
    FROM trn_inventory
    GROUP BY item;
    """
    rows = cursor.execute(sql).fetchall()
    conn.close()

    if not rows:
        return InventorySummary(total_items=0, top_items=[])

    df = pd.DataFrame(rows, columns=["item", "quantity"])
    total_items = df.shape[0]
    top_items = (
        df.sort_values("quantity", ascending=False)
        .head(5)
        .set_index("item")["quantity"]
        .to_dict()
    )

    return InventorySummary(
        total_items=int(total_items),
        top_items=list(top_items.items()),
    )

inventory_agent = Agent(
    name="inventory_agent",
    model="gemini-2.0-flash",
    description="Provides stock levels and inventory summaries.",
    tools=[get_inventory_overview],
    instruction="Use this agent for questions about stock levels or inventory status.",
)
