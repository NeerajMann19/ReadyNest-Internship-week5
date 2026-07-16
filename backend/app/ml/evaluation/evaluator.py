"""
Machine Learning model evaluation engine and explainability extractor.
"""
from typing import Dict, Any, List
import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score,
    mean_squared_error, mean_absolute_error, mean_absolute_percentage_error, r2_score
)


def evaluate_model(pipeline: Pipeline, X_test: pd.DataFrame, y_test: pd.Series, problem_type: str) -> Dict[str, Any]:
    """
    Computes validation performance statistics for classification or regression estimators.
    """
    y_pred = pipeline.predict(X_test)
    metrics = {}

    if problem_type == "classification":
        metrics["accuracy"] = float(accuracy_score(y_test, y_pred))
        metrics["precision"] = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
        metrics["recall"] = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
        metrics["f1"] = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
        
        # Classification report
        rep = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        metrics["classification_report"] = rep
        
        # Confusion matrix
        matrix = confusion_matrix(y_test, y_pred)
        metrics["confusion_matrix"] = matrix.tolist()

        # Class distribution count
        class_counts = pd.Series(y_pred).value_counts().to_dict()
        metrics["class_distribution"] = {str(k): int(v) for k, v in class_counts.items()}

        # ROC AUC
        metrics["roc_auc"] = None
        if hasattr(pipeline.named_steps["model"], "predict_proba"):
            try:
                y_prob = pipeline.predict_proba(X_test)
                unique_classes = np.unique(y_test)
                if len(unique_classes) == 2:
                    # Binary classification
                    metrics["roc_auc"] = float(roc_auc_score(y_test, y_prob[:, 1]))
                elif len(unique_classes) > 2:
                    # Multiclass
                    metrics["roc_auc"] = float(roc_auc_score(y_test, y_prob, multi_class="ovr", average="weighted"))
            except Exception:
                pass

    else:
        # Regression
        mse = float(mean_squared_error(y_test, y_pred))
        metrics["mse"] = mse
        metrics["rmse"] = float(np.sqrt(mse))
        metrics["mae"] = float(mean_absolute_error(y_test, y_pred))
        metrics["r2"] = float(r2_score(y_test, y_pred))
        
        try:
            metrics["mape"] = float(mean_absolute_percentage_error(y_test, y_pred))
        except Exception:
            metrics["mape"] = None

    return metrics


def extract_explainability(
    pipeline: Pipeline,
    features: List[str],
    numeric_cols: List[str],
    categorical_cols: List[str]
) -> Dict[str, float]:
    """
    Extracts, normalizes, and ranks feature importances or coefficients.
    Saves only the top 20 features to prevent excessive payload sizes.
    """
    model = pipeline.named_steps["model"]
    preprocessor = pipeline.named_steps["preprocessor"]

    # 1. Resolve feature names after one-hot encoding
    feature_names = []
    if numeric_cols:
        feature_names.extend(numeric_cols)
        
    if categorical_cols:
        try:
            # Resolve OneHotEncoder transformer column names
            onehot = preprocessor.named_transformers_["cat"].named_steps["onehot"]
            onehot_cols = onehot.get_feature_names_out(categorical_cols).tolist()
            feature_names.extend(onehot_cols)
        except Exception:
            feature_names.extend(categorical_cols)

    # 2. Retrieve coefficients or feature importances
    importances_arr = None
    if hasattr(model, "feature_importances_"):
        importances_arr = model.feature_importances_
    elif hasattr(model, "coef_"):
        coefs = model.coef_
        # If multi-class logistic regression, coef_ is 2D
        if len(coefs.shape) > 1:
            importances_arr = np.mean(np.abs(coefs), axis=0)
        else:
            importances_arr = np.abs(coefs)

    if importances_arr is None or len(importances_arr) != len(feature_names):
        # Fallback: equal importances
        importances_arr = np.ones(len(feature_names)) / len(feature_names)

    # 3. Normalize importances (sum to 1.0)
    total_val = np.sum(importances_arr)
    if total_val > 0:
        importances_arr = importances_arr / total_val

    # 4. Map, sort, and slice top 20
    mapped = {name: float(imp) for name, imp in zip(feature_names, importances_arr)}
    sorted_features = sorted(mapped.items(), key=lambda x: x[1], reverse=True)
    top_20 = dict(sorted_features[:20])

    return top_20
