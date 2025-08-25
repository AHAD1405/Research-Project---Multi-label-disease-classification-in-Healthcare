import pandas as pd

def to_year(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce").dt.year