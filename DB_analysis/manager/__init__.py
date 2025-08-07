try:
    from .agent import manager_agent as root_agent
except Exception:  # pragma: no cover - optional dependency not available
    root_agent = None

from .utils import get_current_time
from .cross_agent_orchestrator import CrossAgentOrchestrator, DEFAULT_SPECS

__all__ = ["root_agent", "get_current_time", "CrossAgentOrchestrator", "DEFAULT_SPECS"]
