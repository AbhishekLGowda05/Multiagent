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
pydantic_module = types.ModuleType("pydantic")

class DummyAgent:
    def __init__(self, *args, **kwargs):
        pass

agents_module.Agent = DummyAgent
adk_module.agents = agents_module
google_module.adk = adk_module
pydantic_module.BaseModel = type(
    "BaseModel",
    (),
    {"__init__": lambda self, **kw: [setattr(self, k, v) for k, v in kw.items()] and None},
)

sys.modules.setdefault("google", google_module)
sys.modules.setdefault("google.adk", adk_module)
sys.modules.setdefault("google.adk.agents", agents_module)
sys.modules.setdefault("pydantic", pydantic_module)

# Import modules
financial_agent = importlib.import_module("manager.sub_agents.financial_agent.agent")
sales_agent = importlib.import_module("manager.sub_agents.sales_agent.agent")
purchase_agent = importlib.import_module("manager.sub_agents.purchase_agent.agent")

cross_module = importlib.import_module("manager.cross_agent_orchestrator")


@pytest.fixture(scope="session")
def test_db(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("data") / "test.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("CREATE TABLE trn_accounting (ledger TEXT, amount REAL);")
    c.execute(
        "CREATE TABLE trn_voucher (party_name TEXT, voucher_type TEXT, date TEXT, guid TEXT);"
    )
    c.execute(
        "CREATE TABLE trn_inventory (guid TEXT, item TEXT, quantity REAL, amount REAL);"
    )
    accounting_rows = [
        ("Sales", 200.0),
        ("Supplies", -60.0),
    ]
    c.executemany("INSERT INTO trn_accounting VALUES (?, ?);", accounting_rows)
    vouchers = [
        ("Customer A", "Sales Invoice", "2024-01-01", "gid1"),
        ("Supplier X", "Purchase Invoice", "2024-01-15", "gid2"),
    ]
    c.executemany("INSERT INTO trn_voucher VALUES (?, ?, ?, ?);", vouchers)
    inventory_rows = [
        ("gid1", "Item1", 5, 50.0),
        ("gid2", "Item2", 10, 100.0),
    ]
    c.executemany("INSERT INTO trn_inventory VALUES (?, ?, ?, ?);", inventory_rows)
    conn.commit()
    conn.close()
    return db_path


def patch_db(monkeypatch, db_path):
    monkeypatch.setattr(financial_agent, "DB_PATH", str(db_path))
    monkeypatch.setattr(sales_agent, "DB_PATH", str(db_path))
    monkeypatch.setattr(purchase_agent, "DB_PATH", str(db_path))


def test_cross_agent_query(test_db, monkeypatch):
    patch_db(monkeypatch, test_db)
    orchestrator = cross_module.CrossAgentOrchestrator(cross_module.DEFAULT_SPECS)
    query = "Why did our profit drop if sales are stable?"
    results = orchestrator.handle_query(query)
    assert "financial_agent" in results
    assert "sales_agent" in results
    assert "purchase_agent" in results
    assert "profit_loss" in results["financial_agent"]
    assert "sales_trend" in results["sales_agent"]
    assert "purchase_trend" in results["purchase_agent"]

