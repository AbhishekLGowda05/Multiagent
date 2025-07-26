import pandas as pd

class BaseAnalytics:
    """Base class providing common data utilities."""
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.dropna().reset_index(drop=True)
