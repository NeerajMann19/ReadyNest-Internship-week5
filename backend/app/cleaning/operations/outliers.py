"""
Handling of outliers in Pandas DataFrame.
"""
import pandas as pd
from typing import Tuple

def remove_outliers(df: pd.DataFrame, column: str, strategy: str) -> Tuple[pd.DataFrame, int]:
    """
    Identifies and removes rows containing outliers in the target column. Returns (modified_df, outliers_dropped).
    """
    if column not in df.columns:
        return df, 0
        
    # Outlier detection requires numeric column
    if not pd.api.types.is_numeric_dtype(df[column]):
        return df, 0
        
    initial_rows = len(df)
    non_null_df = df[df[column].notna()]
    if len(non_null_df) == 0:
        return df, 0
        
    if strategy == "iqr":
        q1 = non_null_df[column].quantile(0.25)
        q3 = non_null_df[column].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        df = df[(df[column].isna()) | ((df[column] >= lower_bound) & (df[column] <= upper_bound))]
    elif strategy == "z_score":
        mean = non_null_df[column].mean()
        std = non_null_df[column].std()
        if std > 0:
            z_scores = (df[column] - mean) / std
            df = df[(df[column].isna()) | (z_scores.abs() <= 3)]
            
    removed = initial_rows - len(df)
    return df, removed
