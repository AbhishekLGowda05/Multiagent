import sqlite3
import os
import pandas as pd
from pydantic import BaseModel
from google.adk.agents import Agent
from sklearn.linear_model import LinearRegression
import numpy as np

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../tallydb.db"))

class SalesForecast(BaseModel):
    historical_months: list
    historical_totals: list
    forecast_month: str
    forecast_total: float

def forecast_sales(query: str) -> SalesForecast:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ✅ Join voucher + accounting to get amounts
    sql = """
    SELECT v.date, a.amount
    FROM trn_voucher v
    JOIN trn_accounting a ON v.guid = a.guid
    WHERE v.voucher_type LIKE '%Sales%';
    """
    rows = cursor.execute(sql).fetchall()
    conn.close()

    if not rows:
        return SalesForecast(
            historical_months=[],
            historical_totals=[],
            forecast_month="",
            forecast_total=0.0
        )

    df = pd.DataFrame(rows, columns=["date", "amount"])
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M")
    monthly_totals = df.groupby("month")["amount"].sum().reset_index()

    # ✅ Prepare regression data
    if len(monthly_totals) < 2:
        # Not enough history for regression
        forecast = monthly_totals["amount"].iloc[-1]
    else:
        X = np.arange(len(monthly_totals)).reshape(-1, 1)
        y = monthly_totals["amount"].values
        model = LinearRegression()
        model.fit(X, y)

        next_month_index = len(monthly_totals)
        forecast = model.predict([[next_month_index]])[0]

    forecast_month = (pd.Timestamp.now().to_period("M") + 1).strftime("%Y-%m")

    return SalesForecast(
        historical_months=[str(m) for m in monthly_totals["month"]],
        historical_totals=[float(v) for v in monthly_totals["amount"]],
        forecast_month=forecast_month,
        forecast_total=round(float(forecast), 2)
    )

predictive_agent = Agent(
    name="predictive_agent",
    model="gemini-2.0-flash",
    description="Predicts future sales based on historical trends in the Tally DB.",
    tools=[forecast_sales],
    instruction="Use this agent when the user asks to forecast future sales or trends."
)
