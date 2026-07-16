"""
Handling of missing values in Pandas DataFrame.
"""
import pandas as pd
from typing import Tuple, Any

def fill_missing(df: pd.DataFrame, column: str, strategy: str, fill_value: Any = None) -> Tuple[pd.DataFrame, int]:
    """
    Fills null cells in column based on strategy. Returns (modified_df, affected_count).
    """
    if column not in df.columns:
        return df, 0
        
    affected = int(df[column].isna().sum())
    if affected == 0:
        return df, 0
        
    if strategy == "mean":
        val = df[column].mean()
        df[column] = df[column].fillna(val)
    elif strategy == "median":
        val = df[column].median()
        df[column] = df[column].fillna(val)
    elif strategy == "mode":
        modes = df[column].mode()
        val = modes[0] if not modes.empty else ""
        df[column] = df[column].fillna(val)
    elif strategy == "constant":
        df[column] = df[column].fillna(fill_value if fill_value is not None else "")
    elif strategy == "ffill":
        df[column] = df[column].ffill()
    elif strategy == "bfill":
        df[column] = df[column].bfill()
        
    return df, affected
