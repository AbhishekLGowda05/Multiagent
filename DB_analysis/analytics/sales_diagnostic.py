from pydantic import BaseModel
import pandas as pd
from .pipeline import query
from .base import BaseAnalytics

class DiagnosticSummary(BaseModel):
    period_1_revenue: float
    period_2_revenue: float
    change_percent: float
    top_increase_customers: list
    top_decrease_customers: list

class SalesDiagnosticAnalytics(BaseAnalytics):
    def diagnose_sales_change(self, query: str = "") -> DiagnosticSummary:
        sql = """
        SELECT v.party_name, v.date, a.amount
        FROM trn_voucher v
        JOIN trn_accounting a ON v.guid = a.guid
        WHERE v.voucher_type LIKE '%Sales%';
        """
        df = query(sql)
        if df.empty:
            return DiagnosticSummary(
                period_1_revenue=0,
                period_2_revenue=0,
                change_percent=0,
                top_increase_customers=[],
                top_decrease_customers=[]
            )
        df = self.clean(df)
        df["date"] = pd.to_datetime(df["date"])
        mid_date = df["date"].median()
        p1 = df[df["date"] <= mid_date]
        p2 = df[df["date"] > mid_date]
        p1_revenue = p1["amount"].sum()
        p2_revenue = p2["amount"].sum()
        change_percent = ((p2_revenue - p1_revenue) / max(p1_revenue, 1)) * 100
        p1_cust = p1.groupby("party_name")["amount"].sum()
        p2_cust = p2.groupby("party_name")["amount"].sum()
        diff = (p2_cust - p1_cust).sort_values(ascending=False)
        top_increase = diff[diff > 0].head(3).to_dict()
        top_decrease = diff[diff < 0].head(3).to_dict()
        return DiagnosticSummary(
            period_1_revenue=round(float(p1_revenue), 2),
            period_2_revenue=round(float(p2_revenue), 2),
            change_percent=round(float(change_percent), 2),
            top_increase_customers=list(top_increase.items()),
            top_decrease_customers=list(top_decrease.items())
        )
