from pydantic import BaseModel
import pandas as pd
from .pipeline import query
from .base import BaseAnalytics

class SalesSummary(BaseModel):
    total_invoices: int
    top_customers: list
    voucher_types: list

class SalesDescriptiveAnalytics(BaseAnalytics):
    def get_sales_summary(self, query: str = "") -> SalesSummary:
        sql = """
        SELECT party_name, voucher_type, date
        FROM trn_voucher
        WHERE voucher_type LIKE '%Sales%'
        LIMIT 100;
        """
        df = query(sql)
        if df.empty:
            return SalesSummary(total_invoices=0, top_customers=[], voucher_types=[])

        df = self.clean(df)
        total_invoices = len(df)
        top_customers = df["party_name"].value_counts().head(5).to_dict()
        voucher_types = df["voucher_type"].value_counts().to_dict()

        return SalesSummary(
            total_invoices=total_invoices,
            top_customers=list(top_customers.items()),
            voucher_types=list(voucher_types.items())
        )
