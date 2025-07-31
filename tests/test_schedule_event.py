import os
import sys
import importlib
import types
from datetime import datetime, timedelta

import pytest

# Ensure DB_analysis package is on the path
sys.path.insert(0, os.path.abspath("DB_analysis"))

# Stub google.adk.agents.Agent if the package isn't installed
google_module = types.ModuleType("google")
adk_module = types.ModuleType("google.adk")
agents_module = types.ModuleType("google.adk.agents")
tools_module = types.ModuleType("google.adk.tools")
function_tool_module = types.ModuleType("google.adk.tools.function_tool")

class DummyAgent:
    def __init__(self, *args, **kwargs):
        pass

agents_module.Agent = DummyAgent
function_tool_module.FunctionTool = lambda fn: fn
tools_module.function_tool = function_tool_module
adk_module.agents = agents_module
adk_module.tools = tools_module
google_module.adk = adk_module

sys.modules.setdefault("google", google_module)
sys.modules.setdefault("google.adk", adk_module)
sys.modules.setdefault("google.adk.agents", agents_module)
sys.modules.setdefault("google.adk.tools", tools_module)
sys.modules.setdefault("google.adk.tools.function_tool", function_tool_module)

# Import the agent module now that stubs are in place
agent_module = importlib.import_module("manager.agent")


def patch_calendar(monkeypatch):
    def fake_create_event(title: str, start_time: str, end_time: str):
        return {"title": title, "start_time": start_time, "end_time": end_time}

    monkeypatch.setattr(agent_module, "create_event", fake_create_event)


@pytest.mark.parametrize("query", [
    "schedule meeting on 31st of July at 7 PM",
    "schedule meeting at 7 PM on 31st of July",
])
def test_smart_schedule_event_date_and_time_order(query, monkeypatch):
    patch_calendar(monkeypatch)

    result = agent_module.smart_schedule_event(query)
    assert result["title"] in {"Business Meeting", "Sales Review Meeting"}

    # compute expected start time
    now = datetime.now()
    target_year = now.year
    target_date = datetime(target_year, 7, 31)
    if target_date < now:
        target_date = datetime(target_year + 1, 7, 31)

    expected_start = target_date.replace(hour=19, minute=0, second=0, microsecond=0).isoformat() + "Z"
    assert result["start_time"] == expected_start
    expected_end = (target_date.replace(hour=19, minute=0, second=0, microsecond=0) + timedelta(hours=1)).isoformat() + "Z"
    assert result["end_time"] == expected_end
