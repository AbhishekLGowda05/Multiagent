from pydantic import BaseModel
import pandas as pd
from .pipeline import query
from .base import BaseAnalytics

class PrescriptiveActions(BaseModel):
    actions: list

class SalesPrescriptiveAnalytics(BaseAnalytics):
    def recommend_sales_actions(self, query: str = "") -> PrescriptiveActions:
        sql = """
        SELECT party_name, date
        FROM trn_voucher
        WHERE voucher_type LIKE '%Sales%';
        """
        df = query(sql)
        if df.empty:
            return PrescriptiveActions(actions=["No sales data available to prescribe actions."])
        df = self.clean(df)
        df["date"] = pd.to_datetime(df["date"])
        mid_date = df["date"].median()
        p1 = df[df["date"] <= mid_date]
        p2 = df[df["date"] > mid_date]
        p1_counts = p1["party_name"].value_counts()
        p2_counts = p2["party_name"].value_counts()
        diff = (p2_counts - p1_counts).sort_values(ascending=False)
        actions = []
        declining = diff[diff < 0].head(3)
        for cust, change in declining.items():
            actions.append(f"⚠️ Follow up with **{cust}**: Sales dropped by {abs(change)} invoices. Consider special offers or a re-engagement campaign.")
        growing = diff[diff > 0].head(3)
        for cust, change in growing.items():
            actions.append(f"✅ Retain **{cust}**: Sales increased by {change} invoices. Consider providing a loyalty discount to strengthen relationship.")
        inactive = set(p1["party_name"]) - set(p2["party_name"])
        for cust in list(inactive)[:3]:
            actions.append(f"🚨 **{cust}** has gone inactive in the latest period. Reach out to understand reasons and offer incentives.")
        if not actions:
            actions.append("Sales trends are stable. Maintain current customer relationship strategies.")
        return PrescriptiveActions(actions=actions)
