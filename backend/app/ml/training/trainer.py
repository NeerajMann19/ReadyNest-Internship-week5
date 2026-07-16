"""
Machine Learning training coordinator and model search engine.
"""
import time
from typing import List, Dict, Any, Tuple, Optional, Callable
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.metrics import f1_score, r2_score

from app.ml.models.registry import CLASSIFICATION_MODELS, REGRESSION_MODELS
from app.ml.preprocessing.preprocessor import create_preprocessor
from app.ml.evaluation.evaluator import evaluate_model, extract_explainability


def train_champion_model(
    df: pd.DataFrame,
    target_column: str,
    problem_type: str,
    features: Optional[List[str]] = None,
    candidate_algorithms: Optional[List[str]] = None,
    cross_validation: bool = False,
    random_state: int = 42,
    logger_cb: Optional[Callable[[str], None]] = None
) -> Tuple[Pipeline, str, float, Dict[str, Any], Dict[str, float], int, int]:
    """
    Orchestrates the model search process:
    - Preprocesses inputs and validates constraints (size, target classes).
    - Performs train/test split.
    - Trains all candidate algorithms.
    - Ranks candidate models and selects the champion based on evaluation scores.
    - Returns the champion pipeline and performance metrics.
    """
    def log(msg: str):
        if logger_cb:
            logger_cb(msg)

    log("Validating dataset constraints...")
    
    # 1. Validation checks
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' is missing from the dataset.")
        
    # Clean target
    clean_df = df.dropna(subset=[target_column]).copy()
    
    if len(clean_df) < 10:
        raise ValueError("Dataset contains fewer than 10 non-null rows, which is too small for training.")
        
    if problem_type == "classification":
        unique_targets = clean_df[target_column].nunique()
        if unique_targets < 2:
            raise ValueError("Target column must contain at least 2 distinct classes for classification.")

    # 2. Feature Columns resolving
    if features:
        # Verify columns exist
        features = [col for col in features if col in clean_df.columns and col != target_column]
    else:
        # Default: use all columns except target and obvious ID columns
        features = []
        for col in clean_df.columns:
            if col == target_column:
                continue
            col_lower = col.lower()
            if col_lower in ["id", "uuid", "index"] or col_lower.endswith("_id"):
                continue
            features.append(col)
            
    if not features:
        raise ValueError("No valid predictive features selected for training.")

    log(f"Selected {len(features)} feature columns: {features}")

    # Identify datetime/timestamp columns among the features strictly
    datetime_cols = []
    for col in features:
        series = clean_df[col]
        if pd.api.types.is_datetime64_any_dtype(series):
            datetime_cols.append(col)
        elif pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
            # Numeric/boolean columns are never dates
            continue
        else:
            try:
                sample = series.dropna().head(10)
                if not sample.empty:
                    # Ignore values that are purely numbers represented as strings
                    first_val = str(sample.iloc[0]).strip()
                    if first_val.replace('.', '', 1).isdigit():
                        continue
                    pd.to_datetime(sample, errors='raise')
                    datetime_cols.append(col)
            except Exception:
                pass

    # Extract year, month, day_of_week, is_weekend for each datetime column
    for col in datetime_cols:
        log(f"Decomposing datetime column '{col}' into engineered numeric features...")
        try:
            dt_series = pd.to_datetime(clean_df[col], errors='coerce')
            mode_dt = dt_series.mode()
            fallback_dt = mode_dt[0] if not mode_dt.empty else pd.Timestamp("2026-01-01")
            dt_series = dt_series.fillna(fallback_dt)
            
            clean_df[f"{col}_year"] = dt_series.dt.year.astype(int)
            clean_df[f"{col}_month"] = dt_series.dt.month.astype(int)
            clean_df[f"{col}_day_of_week"] = dt_series.dt.dayofweek.astype(int)
            clean_df[f"{col}_is_weekend"] = (dt_series.dt.dayofweek >= 5).astype(int)
            
            # Replace the original column in features list
            features = [f for f in features if f != col]
            features.extend([
                f"{col}_year",
                f"{col}_month",
                f"{col}_day_of_week",
                f"{col}_is_weekend"
            ])
        except Exception as e:
            log(f"Failed to engineer datetime features for '{col}': {str(e)}")

    # Split features and target
    X = clean_df[features]
    y = clean_df[target_column]

    # Resolve Numeric vs Categorical features
    numeric_cols = []
    categorical_cols = []
    for col in features:
        if pd.api.types.is_numeric_dtype(X[col]) and not pd.api.types.is_bool_dtype(X[col]):
            numeric_cols.append(col)
        else:
            categorical_cols.append(col)

    log(f"Categorized features: {len(numeric_cols)} numeric, {len(categorical_cols)} categorical.")

    # Pre-flight guards: high-cardinality categorical columns & total post-encoding width OOM limits
    MAX_UNIQUE_CATEGORIES = 50
    MAX_EXPECTED_WIDTH = 500
    
    high_cardinality_cols = []
    expected_width = len(numeric_cols)
    
    for col in categorical_cols:
        unique_cnt = int(X[col].nunique())
        expected_width += unique_cnt
        if unique_cnt > MAX_UNIQUE_CATEGORIES:
            high_cardinality_cols.append((col, unique_cnt))
            
    if high_cardinality_cols:
        cols_str = ", ".join(f"'{c[0]}' ({c[1]} unique values)" for c in high_cardinality_cols)
        raise ValueError(
            f"High cardinality identifier columns detected: {cols_str}. "
            f"Columns with > {MAX_UNIQUE_CATEGORIES} unique values are not suitable for one-hot encoding. "
            f"Please deselect them to prevent out-of-memory crashes."
        )
        
    if expected_width > MAX_EXPECTED_WIDTH:
        raise ValueError(
            f"The selected combination of categorical features is too wide (estimated post-encoding columns: {expected_width}, limit: {MAX_EXPECTED_WIDTH}). "
            f"Please deselect some categorical features to prevent out-of-memory crashes."
        )

    # 3. Train / Test Split
    test_size = 0.2
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state,
        stratify=y if problem_type == "classification" else None
    )
    
    training_rows = len(X_train)
    testing_rows = len(X_test)
    log(f"Split data into train ({training_rows} rows) and test ({testing_rows} rows) sets.")

    # 4. Resolve Candidate Algorithms
    registry = CLASSIFICATION_MODELS if problem_type == "classification" else REGRESSION_MODELS
    if candidate_algorithms:
        algorithms = [algo for algo in candidate_algorithms if algo in registry]
    else:
        algorithms = list(registry.keys())
        
    if not algorithms:
        raise ValueError(f"No valid algorithms available in registry for {problem_type} problems.")

    # 5. Fit Candidates
    preprocessor = create_preprocessor(numeric_cols, categorical_cols)
    best_pipe = None
    best_algo = ""
    best_score = -float("inf")
    metrics_cache = {}

    for algo in algorithms:
        log(f"Building pipeline for algorithm: {algo}...")
        estimator_cls = registry[algo]
        
        # Instantiate model with default parameters
        model_args = {"random_state": random_state} if hasattr(estimator_cls(), "random_state") else {}
        pipe = Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("model", estimator_cls(**model_args))
        ])

        log(f"Fitting {algo} model on training split...")
        pipe.fit(X_train, y_train)

        # Run cross validation if requested
        if cross_validation:
            log(f"Executing 3-fold cross validation for {algo}...")
            scoring_metric = "f1_weighted" if problem_type == "classification" else "r2"
            cv_scores = cross_val_score(pipe, X_train, y_train, cv=3, scoring=scoring_metric)
            val_score = float(np.mean(cv_scores))
            log(f"{algo} CV mean score: {val_score:.4f}")
        else:
            # Evaluate using test split
            y_pred = pipe.predict(X_test)
            if problem_type == "classification":
                val_score = float(f1_score(y_test, y_pred, average="weighted"))
            else:
                val_score = float(r2_score(y_test, y_pred))
            log(f"{algo} validation test score: {val_score:.4f}")

        # Compute full evaluation stats for this candidate
        metrics = evaluate_model(pipe, X_test, y_test, problem_type)
        metrics_cache[algo] = metrics

        # Compare and update champion
        if val_score > best_score:
            best_score = val_score
            best_pipe = pipe
            best_algo = algo

    log(f"Champion model selected: {best_algo} with score {best_score:.4f}")

    # 6. Fit Champion on full clean dataset for final binary exports
    log("Re-fitting champion model on full cleaned dataset...")
    best_pipe.fit(X, y)

    # 7. Extract Feature Importances and Explainability
    importances = extract_explainability(best_pipe, features, numeric_cols, categorical_cols)

    # Fetch final test metrics matching the champion
    champion_metrics = metrics_cache[best_algo]

    return (
        best_pipe,
        best_algo,
        best_score,
        champion_metrics,
        importances,
        training_rows,
        testing_rows
    )
