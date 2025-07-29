from datetime import datetime, timezone


def get_current_time() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def parse_finance_query(query: str) -> str:
    """Return 'variance' if the query asks about expense variance, else 'summary'."""
    q = query.lower()
    variance_keywords = ["variance", "fluctuation", "volatility", "change"]
    if any(k in q for k in variance_keywords):
        return "variance"
    return "summary"
