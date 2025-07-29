__test__ = False

import sys
import os
import types

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
sys.path.insert(0, os.path.abspath("DB_analysis"))

pydantic_module = types.ModuleType("pydantic")
pydantic_module.BaseModel = type(
    "BaseModel",
    (),
    {"__init__": lambda self, **kw: [setattr(self, k, v) for k, v in kw.items()] and None},
)
sys.modules.setdefault("pydantic", pydantic_module)

from DB_analysis.manager.sub_agents.financial_agent.agent import (
    get_financial_summary,
    analyze_expense_variance,
)
from DB_analysis.manager.utils import parse_finance_query


def run_query(query: str):
    action = parse_finance_query(query)
    if action == "variance":
        result = analyze_expense_variance(query)
    else:
        result = get_financial_summary(query)
    try:
        # pydantic 2.x
        print(result.model_dump_json(indent=2))
    except AttributeError:
        # pydantic 1.x fallback
        print(result.json(indent=2))


if __name__ == "__main__":
    import sys
    user_query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Provide a financial summary"
    run_query(user_query)
