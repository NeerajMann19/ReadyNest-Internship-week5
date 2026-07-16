"""
Handling of duplicate rows in Pandas DataFrame.
"""
import pandas as pd
from typing import Tuple

def drop_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Drops exact duplicate rows. Returns (modified_df, duplicates_count).
    """
    initial_rows = len(df)
    df = df.drop_duplicates()
    duplicates_removed = initial_rows - len(df)
    return df, duplicates_removed
