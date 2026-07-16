"""
Handling of whitespace trimming and text transformations in Pandas DataFrame.
"""
import pandas as pd
from typing import Tuple

def clean_text(df: pd.DataFrame, column: str, strategy: str) -> Tuple[pd.DataFrame, int]:
    """
    Transforms text casing or trims spacing in target column. Returns (modified_df, affected_count).
    """
    if column not in df.columns:
        return df, 0
        
    col_series = df[column].astype(str)
    affected = 0
    
    if strategy == "trim":
        trimmed = col_series.str.strip()
        affected = int((col_series != trimmed).sum())
        df[column] = trimmed
    elif strategy == "lower":
        lowered = col_series.str.lower()
        affected = int((col_series != lowered).sum())
        df[column] = lowered
    elif strategy == "upper":
        uppered = col_series.str.upper()
        affected = int((col_series != uppered).sum())
        df[column] = uppered
    elif strategy == "title":
        titled = col_series.str.title()
        affected = int((col_series != titled).sum())
        df[column] = titled
        
    return df, affected
