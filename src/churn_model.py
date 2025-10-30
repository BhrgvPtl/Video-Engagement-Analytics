from __future__ import annotations
import pandas as pd
from .utils import path_proc

def prepare_training_data(features_path: str | None = None):
    """
    Load session features and return (X, y) for a simple churn model.
    X = numeric columns from session_features.parquet
    y = placeholder churn label derived from session_duration_seconds (shortest 20% = 1)
    """
    if features_path is None:
        features_path = path_proc("session_features.parquet")

    try:
        df = pd.read_parquet(features_path)
    except Exception:
        df = pd.DataFrame()

    if df.empty:
        # No data yet -> harmless stubs
        X = pd.DataFrame()
        y = pd.Series(dtype=int)
        return X, y

    # Feature matrix: all numeric session features
    X = df.select_dtypes(include="number").fillna(0)

    # Dummy churn label: mark shortest 20% sessions as "churned" (placeholder)
    if "session_duration_seconds" in df.columns and len(df) >= 5:
        thresh = df["session_duration_seconds"].quantile(0.2)
        y = (df["session_duration_seconds"] <= thresh).astype(int)
    else:
        y = pd.Series(0, index=X.index, dtype=int)

    return X, y

def train_churn_model(X: pd.DataFrame, y: pd.Series):
    """
    Train a tiny logistic regression model; return None if not enough data/classes.
    """
    if X is None or X.empty or y is None or len(y) == 0:
        return None

    try:
        from sklearn.linear_model import LogisticRegression
        # Avoid single-class crash
        if getattr(y, "nunique", lambda: 0)() < 2:
            return None
        model = LogisticRegression(max_iter=250)
        model.fit(X, y)
        return model
    except Exception:
        return None

def main():
    X, y = prepare_training_data()
    model = train_churn_model(X, y)
    print("[churn_model] trained:", model is not None, "| X shape:", getattr(X, "shape", None), "| y len:", len(y) if y is not None else None)

if __name__ == "__main__":
    main()
