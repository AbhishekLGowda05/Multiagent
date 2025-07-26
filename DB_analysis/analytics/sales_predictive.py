from pydantic import BaseModel
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from .pipeline import query
from .base import BaseAnalytics

class SalesForecast(BaseModel):
    historical_months: list
    historical_totals: list
    forecast_month: str
    forecast_total: float

class SalesPredictiveAnalytics(BaseAnalytics):
    def forecast_sales(self, query: str = "") -> SalesForecast:
        sql = """
        SELECT v.date, a.amount
        FROM trn_voucher v
        JOIN trn_accounting a ON v.guid = a.guid
        WHERE v.voucher_type LIKE '%Sales%';
        """
        df = query(sql)
        if df.empty:
            return SalesForecast(
                historical_months=[],
                historical_totals=[],
                forecast_month="",
                forecast_total=0.0
            )
        df = self.clean(df)
        df["date"] = pd.to_datetime(df["date"])
        df["month"] = df["date"].dt.to_period("M")
        monthly_totals = df.groupby("month")["amount"].sum().reset_index()
        if len(monthly_totals) < 2:
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
