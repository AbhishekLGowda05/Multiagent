from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any


@dataclass
class AgentSpec:
    """Enhanced configuration for a single agent with intelligent tool selection."""

    agent: Any
    keywords: List[str]
    tools: Dict[str, Callable[[str], Any]] = field(default_factory=dict)
    tool_keywords: Dict[str, List[str]] = field(default_factory=dict)  # NEW: Keywords for specific tools
    priority_keywords: List[str] = field(default_factory=list)  # NEW: High-priority keywords

    def is_relevant(self, query: str) -> bool:
        q = query.lower()
        return any(k in q for k in self.keywords)
    
    def get_relevant_tools(self, query: str) -> List[str]:
        """NEW: Intelligently select which tools to execute based on query content."""
        q = query.lower()
        relevant_tools = []
        
        # Check tool-specific keywords
        for tool_name, tool_keywords in self.tool_keywords.items():
            if any(keyword in q for keyword in tool_keywords):
                relevant_tools.append(tool_name)
        
        # If no specific tools found, use all available tools
        if not relevant_tools:
            relevant_tools = list(self.tools.keys())
        
        # Prioritize tools based on priority keywords
        if self.priority_keywords:
            priority_tools = []
            for tool_name in relevant_tools:
                if tool_name in self.tool_keywords:
                    tool_keywords = self.tool_keywords[tool_name]
                    if any(pk in q for pk in self.priority_keywords):
                        priority_tools.append(tool_name)
            
            if priority_tools:
                return priority_tools
        
        return relevant_tools


class CrossAgentOrchestrator:
    """Enhanced orchestrator with intelligent tool selection and better error handling."""

    def __init__(self, specs: Dict[str, AgentSpec] | None = None) -> None:
        self.specs: Dict[str, AgentSpec] = specs or {}
        self.execution_log: List[str] = []  # NEW: Track execution for debugging

    def register_agent(self, name: str, spec: AgentSpec) -> None:
        self.specs[name] = spec

    def handle_query(self, query: str) -> Dict[str, Dict[str, Any]]:
        """Enhanced query handling with intelligent tool selection and dependency resolution."""
        self.execution_log.clear()
        self.execution_log.append(f"🔍 Processing query: '{query}'")
        
        responses: Dict[str, Dict[str, Any]] = {}
        relevant_agents = []
        
        # Step 1: Find all relevant agents
        for name, spec in self.specs.items():
            if spec.is_relevant(query):
                relevant_agents.append(name)
        
        self.execution_log.append(f"📊 Relevant agents: {relevant_agents}")
        
        if not relevant_agents:
            self.execution_log.append("⚠️  No relevant agents found")
            return {
                "message": "No relevant agents found for this query",
                "execution_log": self.execution_log
            }
        
        # Step 2: Execute tools for each relevant agent with intelligent selection
        for name, spec in self.specs.items():
            if spec.is_relevant(query):
                agent_result: Dict[str, Any] = {}
                relevant_tools = spec.get_relevant_tools(query)
                
                self.execution_log.append(f"🔧 {name} executing tools: {relevant_tools}")
                
                for tool_name in relevant_tools:
                    if tool_name in spec.tools:
                        try:
                            tool_fn = spec.tools[tool_name]
                            result = tool_fn(query)
                            
                            # Enhanced result processing
                            data = self._process_tool_result(result, tool_name)
                            agent_result[tool_name] = data
                            
                            self.execution_log.append(f"   ✅ {tool_name}: Success")
                            
                        except Exception as e:
                            error_msg = f"Error in {tool_name}: {str(e)}"
                            agent_result[tool_name] = {"error": error_msg}
                            self.execution_log.append(f"   ❌ {tool_name}: {error_msg}")
                
                responses[name] = agent_result
        
        # Step 3: Add execution metadata
        responses["_metadata"] = {
            "query": query,
            "agents_triggered": relevant_agents,
            "execution_log": self.execution_log,
            "cross_agent_analysis": self._generate_cross_agent_insights(responses, query)
        }
        
        return responses
    
    def _process_tool_result(self, result: Any, tool_name: str) -> Dict[str, Any]:
        """Enhanced result processing with better data extraction."""
        try:
            if hasattr(result, "model_dump"):
                return result.model_dump()
            elif hasattr(result, "dict"):
                return result.dict()
            elif isinstance(result, dict):
                return result
            elif hasattr(result, "__dict__"):
                return result.__dict__
            else:
                return {"value": str(result), "type": type(result).__name__}
        except Exception as e:
            return {"error": f"Failed to process result: {str(e)}", "raw_result": str(result)}
    
    def _generate_cross_agent_insights(self, responses: Dict[str, Dict[str, Any]], query: str) -> Dict[str, Any]:
        """NEW: Generate cross-domain insights by analyzing results from multiple agents."""
        insights = {
            "summary": "",
            "key_findings": [],
            "recommendations": [],
            "data_relationships": []
        }
        
        agent_count = len([k for k in responses.keys() if not k.startswith("_")])
        
        if agent_count > 1:
            insights["summary"] = f"Cross-domain analysis across {agent_count} business areas"
            
            # Extract key metrics from each agent
            for agent_name, agent_data in responses.items():
                if not agent_name.startswith("_"):
                    for tool_name, tool_data in agent_data.items():
                        if isinstance(tool_data, dict) and "error" not in tool_data:
                            insights["key_findings"].append(f"{agent_name}.{tool_name}: {self._extract_key_metric(tool_data)}")
            
            # Generate recommendations based on query type
            insights["recommendations"] = self._generate_recommendations(query, responses)
        
        return insights
    
    def _extract_key_metric(self, data: Dict[str, Any]) -> str:
        """Extract the most important metric from tool data."""
        if "total_sales" in data:
            return f"Sales: ${data['total_sales']:,.2f}"
        elif "total_purchases" in data:
            return f"Purchases: ${data['total_purchases']:,.2f}"
        elif "profit" in data:
            return f"Profit: ${data['profit']:,.2f}"
        elif "slope" in data:
            return f"Trend: {data['slope']:+.2f}"
        elif "turnover_ratio" in data:
            return f"Turnover: {data['turnover_ratio']:.2f}x"
        else:
            return "Data available"
    
    def _generate_recommendations(self, query: str, responses: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate business recommendations based on cross-agent results."""
        recommendations = []
        q = query.lower()
        
        if "compare" in q or "vs" in q:
            recommendations.append("Consider the relationship between these metrics for strategic decision-making")
        
        if "profit" in q and "sales" in q:
            recommendations.append("Analyze profit margins to identify opportunities for revenue optimization")
        
        if "efficiency" in q or "performance" in q:
            recommendations.append("Focus on operational improvements based on cross-departmental insights")
        
        if len(responses) > 2:
            recommendations.append("Leverage comprehensive view across multiple business domains for holistic strategy")
        
        return recommendations if recommendations else ["Continue monitoring these key business metrics"]


# Enhanced default configuration with intelligent tool selection
try:
    from .sub_agents.financial_agent.agent import (
        financial_agent,
        get_profit_loss,
        get_financial_summary,
        get_cash_flow,
        get_account_balance,
        analyze_expense_variance,
        get_ledger_summary,
        get_payment_receipts,
    )
    from .sub_agents.sales_agent.agent import (
        sales_agent, 
        get_sales_trend,
        get_sales_summary,
        forecast_next_month_sales,
        get_top_items_sold,
    )
    from .sub_agents.purchase_agent.agent import (
        purchase_agent, 
        get_purchase_trend,
        get_purchase_summary,
        get_top_items_purchased,
    )
    from .sub_agents.inventory_agent.agent import (
        inventory_agent, 
        get_inventory_summary,
        forecast_inventory_demand,
        calculate_inventory_turnover,
        get_low_stock_items,
    )
except Exception:  # pragma: no cover - when modules missing in tests
    # Fallback definitions
    financial_agent = sales_agent = purchase_agent = inventory_agent = None
    get_profit_loss = get_financial_summary = get_cash_flow = get_account_balance = lambda q: {"status": "unavailable"}
    analyze_expense_variance = get_ledger_summary = get_payment_receipts = lambda q: {"status": "unavailable"}
    get_sales_trend = get_sales_summary = forecast_next_month_sales = get_top_items_sold = lambda q: {"status": "unavailable"}
    get_purchase_trend = get_purchase_summary = get_top_items_purchased = lambda q: {"status": "unavailable"}
    get_inventory_summary = forecast_inventory_demand = calculate_inventory_turnover = get_low_stock_items = lambda q: {"status": "unavailable"}


DEFAULT_SPECS: Dict[str, AgentSpec] = {
    "financial_agent": AgentSpec(
        agent=financial_agent,
        keywords=["profit", "finance", "cash", "balance", "expense", "loss", "accounting", "financial", "ledger", "payment", "receipt"],
        tools={
            "profit_loss": get_profit_loss,
            "financial_summary": get_financial_summary,
            "cash_flow": get_cash_flow,
            "account_balance": get_account_balance,
            "expense_variance": analyze_expense_variance,
            "ledger_summary": get_ledger_summary,
            "payment_receipts": get_payment_receipts,
        },
        tool_keywords={
            "profit_loss": ["profit", "loss", "margin", "profitability"],
            "financial_summary": ["summary", "overview", "financial", "total"],
            "cash_flow": ["cash", "flow", "liquidity", "inflow", "outflow"],
            "account_balance": ["balance", "account", "debit", "credit"],
            "expense_variance": ["variance", "volatility", "expense", "variation"],
            "ledger_summary": ["ledger", "accounts", "top"],
            "payment_receipts": ["payment", "receipt", "transaction", "processing"],
        },
        priority_keywords=["profit", "cash", "balance"],
    ),
    "sales_agent": AgentSpec(
        agent=sales_agent,
        keywords=["sales", "customer", "revenue", "selling", "invoices", "income"],
        tools={
            "sales_trend": get_sales_trend,
            "sales_summary": get_sales_summary,
            "sales_forecast": forecast_next_month_sales,
            "top_items_sold": get_top_items_sold,
        },
        tool_keywords={
            "sales_trend": ["trend", "slope", "growth", "pattern"],
            "sales_summary": ["summary", "total", "overview"],
            "sales_forecast": ["forecast", "predict", "future", "next"],
            "top_items_sold": ["top", "best", "popular", "items"],
        },
        priority_keywords=["sales", "revenue"],
    ),
    "purchase_agent": AgentSpec(
        agent=purchase_agent,
        keywords=["purchase", "supplier", "vendor", "procurement", "buying", "expense"],
        tools={
            "purchase_trend": get_purchase_trend,
            "purchase_summary": get_purchase_summary,
            "top_items_purchased": get_top_items_purchased,
        },
        tool_keywords={
            "purchase_trend": ["trend", "cost", "supplier", "expense"],
            "purchase_summary": ["summary", "total", "procurement"],
            "top_items_purchased": ["top", "most", "items", "products"],
        },
        priority_keywords=["purchase", "supplier", "cost"],
    ),
    "inventory_agent": AgentSpec(
        agent=inventory_agent,
        keywords=["inventory", "stock", "item", "products", "demand", "forecast"],
        tools={
            "inventory_summary": get_inventory_summary,
            "inventory_forecast": forecast_inventory_demand,
            "inventory_turnover": calculate_inventory_turnover,
            "low_stock_items": get_low_stock_items,
        },
        tool_keywords={
            "inventory_summary": ["summary", "stock", "levels", "total"],
            "inventory_forecast": ["forecast", "demand", "prediction", "future"],
            "inventory_turnover": ["turnover", "efficiency", "rotation"],
            "low_stock_items": ["low", "stock", "restock", "alert"],
        },
        priority_keywords=["inventory", "stock", "demand"],
    ),
}