from DB_analysis.manager.cross_agent_orchestrator import (
    CrossAgentOrchestrator,
    DEFAULT_SPECS,
)

if __name__ == "__main__":
    import json
    import sys

    query = " ".join(sys.argv[1:]) or "Why did our profit drop if sales are stable?"

    orchestrator = CrossAgentOrchestrator(DEFAULT_SPECS)
    results = orchestrator.handle_query(query)
    print(json.dumps(results, indent=2))
