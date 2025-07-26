import os
import sqlite3
import pandas as pd

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tallydb.db'))

def query(sql: str) -> pd.DataFrame:
    """Run a SQL query against the Tally database and return a DataFrame."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df
