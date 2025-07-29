import os
import sys
import sqlite3
import importlib
import types

import pytest

# Ensure DB_analysis package is on the path
sys.path.insert(0, os.path.abspath("DB_analysis"))

# Stub google.adk.agents.Agent if the package isn't installed
google_module = types.ModuleType("google")
adk_module = types.ModuleType("google.adk")
agents_module = types.ModuleType("google.adk.agents")

class DummyAgent:
    def __init__(self, *args, **kwargs):
        pass

agents_module.Agent = DummyAgent
adk_module.agents = agents_module
google_module.adk = adk_module

sys.modules.setdefault("google", google_module)
sys.modules.setdefault("google.adk", adk_module)
sys.modules.setdefault("google.adk.agents", agents_module)

# Import agent modules
financial_agent = importlib.import_module("manager.sub_agents.financial_agent.agent")
sales_agent = importlib.import_module("manager.sub_agents.sales_agent.agent")
purchase_agent = importlib.import_module("manager.sub_agents.purchase_agent.agent")
inventory_agent = importlib.import_module("manager.sub_agents.inventory_agent.agent")


@pytest.fixture(scope="session")
def test_db(tmp_path_factory):
    """Create a small sqlite database for testing."""
    db_path = tmp_path_factory.mktemp("data") / "test.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Create tables
    c.execute("CREATE TABLE trn_accounting (ledger TEXT, amount REAL);")
    c.execute(
        "CREATE TABLE trn_voucher (party_name TEXT, voucher_type TEXT, date TEXT, guid TEXT);"
    )
    c.execute(
        "CREATE TABLE trn_inventory (guid TEXT, item TEXT, quantity REAL, amount REAL);"
    )

    # Insert accounting data
    accounting_rows = [
        ("Sales", 100.0),
        ("Other Income", 150.0),
        ("Supplies", -50.0),
        ("Rent", -30.0),
    ]
    c.executemany("INSERT INTO trn_accounting VALUES (?, ?);", accounting_rows)

    # Insert voucher data
    vouchers = [
        ("Customer A", "Sales Invoice", "2024-01-01", "gid1"),
        ("Customer B", "Sales Invoice", "2024-02-01", "gid2"),
        ("Supplier X", "Purchase Invoice", "2024-01-15", "gid3"),
    ]
    c.executemany("INSERT INTO trn_voucher VALUES (?, ?, ?, ?);", vouchers)

    # Insert inventory data
    inventory_rows = [
        ("gid1", "Item1", 5, 50.0),
        ("gid2", "Item1", 3, 30.0),
        ("gid3", "Item2", 10, 100.0),
    ]
    c.executemany("INSERT INTO trn_inventory VALUES (?, ?, ?, ?);", inventory_rows)

    conn.commit()
    conn.close()
    return db_path


def patch_db(monkeypatch, db_path):
    monkeypatch.setattr(financial_agent, "DB_PATH", str(db_path))
    monkeypatch.setattr(sales_agent, "DB_PATH", str(db_path))
    monkeypatch.setattr(purchase_agent, "DB_PATH", str(db_path))
    monkeypatch.setattr(inventory_agent, "DB_PATH", str(db_path))


def test_financial_agent_tools(test_db, monkeypatch):
    patch_db(monkeypatch, test_db)

    summary = financial_agent.get_financial_summary("summary")
    assert isinstance(summary, financial_agent.FinancialSummary)
    assert isinstance(summary.total_debit, float)
    assert isinstance(summary.total_credit, float)
    assert isinstance(summary.top_income_ledgers, list)
    assert isinstance(summary.top_expense_ledgers, list)

    variance = financial_agent.analyze_expense_variance("variance")
    assert isinstance(variance, financial_agent.ExpenseVariance)
    assert isinstance(variance.variance, float)


def test_sales_agent_tools(test_db, monkeypatch):
    patch_db(monkeypatch, test_db)

    summary = sales_agent.get_sales_summary("summary")
    assert isinstance(summary, sales_agent.SalesSummary)
    assert isinstance(summary.total_invoices, int)
    assert isinstance(summary.top_customers, list)
    assert isinstance(summary.voucher_types, list)

    trend = sales_agent.get_sales_trend("trend")
    assert isinstance(trend, sales_agent.SalesTrend)
    assert isinstance(trend.monthly_sales, list)
    assert isinstance(trend.slope, float)


def test_purchase_agent_tools(test_db, monkeypatch):
    patch_db(monkeypatch, test_db)

    summary = purchase_agent.get_purchase_summary("summary")
    assert isinstance(summary, purchase_agent.PurchaseSummary)
    assert isinstance(summary.total_invoices, int)
    assert isinstance(summary.top_suppliers, list)
    assert isinstance(summary.voucher_types, list)


def test_inventory_agent_tools(test_db, monkeypatch):
    patch_db(monkeypatch, test_db)

    summary = inventory_agent.get_inventory_summary("summary")
    assert isinstance(summary, inventory_agent.InventorySummary)
    assert isinstance(summary.total_unique_items, int)
    assert isinstance(summary.top_items_quantity, list)
    assert isinstance(summary.top_items_value, list)

    forecast = inventory_agent.forecast_inventory_demand("forecast")
    assert isinstance(forecast, inventory_agent.InventoryDemandForecast)
    assert isinstance(forecast.next_month_quantity, float)
