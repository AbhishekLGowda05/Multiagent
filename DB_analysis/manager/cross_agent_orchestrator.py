from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any


@dataclass
class AgentSpec:
    """Configuration for a single agent."""

    agent: Any
    keywords: List[str]
    tools: Dict[str, Callable[[str], Any]] = field(default_factory=dict)

    def is_relevant(self, query: str) -> bool:
        q = query.lower()
        return any(k in q for k in self.keywords)


class CrossAgentOrchestrator:
    """Simple orchestrator that can call multiple agents for a single query."""

    def __init__(self, specs: Dict[str, AgentSpec] | None = None) -> None:
        self.specs: Dict[str, AgentSpec] = specs or {}

    def register_agent(self, name: str, spec: AgentSpec) -> None:
        self.specs[name] = spec

    def handle_query(self, query: str) -> Dict[str, Dict[str, Any]]:
        """Execute tools from all relevant agents and return combined results."""
        responses: Dict[str, Dict[str, Any]] = {}
        for name, spec in self.specs.items():
            if spec.is_relevant(query):
                agent_result: Dict[str, Any] = {}
                for tool_name, tool_fn in spec.tools.items():
                    result = tool_fn(query)
                    if hasattr(result, "model_dump"):
                        data = result.model_dump()
                    elif hasattr(result, "dict"):
                        data = result.dict()
                    elif isinstance(result, dict):
                        data = result
                    else:
                        data = result.__dict__
                    agent_result[tool_name] = data
                responses[name] = agent_result
        return responses


# Default configuration using existing agents
try:
    from .sub_agents.financial_agent.agent import (
        financial_agent,
        get_profit_loss,
    )
    from .sub_agents.sales_agent.agent import sales_agent, get_sales_trend
    from .sub_agents.purchase_agent.agent import purchase_agent, get_purchase_trend
    from .sub_agents.inventory_agent.agent import inventory_agent, get_inventory_summary
except Exception:  # pragma: no cover - when modules missing in tests
    financial_agent = None
    sales_agent = None
    purchase_agent = None
    inventory_agent = None
    get_profit_loss = lambda q: {}
    get_sales_trend = lambda q: {}
    get_purchase_trend = lambda q: {}
    get_inventory_summary = lambda q: {}

DEFAULT_SPECS: Dict[str, AgentSpec] = {
    "financial_agent": AgentSpec(
        agent=financial_agent,
        keywords=["profit", "finance", "cash", "balance", "expense", "loss"],
        tools={"profit_loss": get_profit_loss},
    ),
    "sales_agent": AgentSpec(
        agent=sales_agent,
        keywords=["sales", "customer", "revenue"],
        tools={"sales_trend": get_sales_trend},
    ),
    "purchase_agent": AgentSpec(
        agent=purchase_agent,
        keywords=["purchase", "supplier", "vendor", "expense", "profit"],
        tools={"purchase_trend": get_purchase_trend},
    ),
    "inventory_agent": AgentSpec(
        agent=inventory_agent,
        keywords=["inventory", "stock", "item"],
        tools={"inventory_summary": get_inventory_summary},
    ),
}
