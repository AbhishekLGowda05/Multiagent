from agents.base import BaseAgent
from analytics.sales_descriptive import SalesDescriptiveAnalytics
from analytics.sales_diagnostic import SalesDiagnosticAnalytics
from analytics.sales_predictive import SalesPredictiveAnalytics
from analytics.sales_prescriptive import SalesPrescriptiveAnalytics

sales_agent = BaseAgent(
    name="sales_agent",
    model="gemini-2.0-flash",
    description="Handles sales related queries and delegates to analytics tools.",
    tools=[
        SalesDescriptiveAnalytics().get_sales_summary,
        SalesDiagnosticAnalytics().diagnose_sales_change,
        SalesPredictiveAnalytics().forecast_sales,
        SalesPrescriptiveAnalytics().recommend_sales_actions,
    ],
    instruction="""
    You are the sales domain agent. Depending on the requested analysis
    type (descriptive, diagnostic, predictive or prescriptive), call the
    appropriate tool and return its result.
    """,
)
