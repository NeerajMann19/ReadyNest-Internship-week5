"""
Handling of datatype casting in Pandas DataFrame.
"""
import pandas as pd
from typing import Tuple

def cast_datatype(df: pd.DataFrame, column: str, target_type: str) -> Tuple[pd.DataFrame, int]:
    """
    Casts column to different types. Returns (modified_df, affected_count).
    """
    if column not in df.columns:
        return df, 0
        
    initial_series = df[column].copy()
    
    if target_type == "string":
        df[column] = df[column].astype(str)
    elif target_type == "numeric":
        df[column] = pd.to_numeric(df[column], errors='coerce')
    elif target_type == "datetime":
        df[column] = pd.to_datetime(df[column], errors='coerce')
    elif target_type == "boolean":
        def parse_bool(val):
            if pd.isna(val):
                return False
            val_str = str(val).strip().lower()
            if val_str in ["true", "1", "yes", "t", "y"]:
                return True
            return False
            
        df[column] = df[column].apply(parse_bool)
        
    # Determine counts of changed values or errors
    affected = int((initial_series.isna() != df[column].isna()).sum() + (initial_series.dropna() != df[column].dropna()).sum())
    return df, affected
