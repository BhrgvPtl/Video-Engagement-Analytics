"""Churn modeling helpers for short-form video retention analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


@dataclass
class ChurnModelConfig:
    """Model hyper-parameters and column definitions."""

    numerical_features: Tuple[str, ...] = (
        "session_watch_time_seconds",
        "unique_videos",
        "completion_rate",
        "avg_drop_off_percent",
    )
    categorical_features: Tuple[str, ...] = ("creator_id",)
    test_size: float = 0.2
    random_state: int = 42


def prepare_training_data(path: str) -> pd.DataFrame:
    """Load processed session features with retention labels."""

    df = pd.read_parquet(path)
    required_columns = set(
        ChurnModelConfig().numerical_features
    ).union(ChurnModelConfig().categorical_features)
    required_columns.add("retained_d7")

    missing = required_columns.difference(df.columns)
    if missing:
        raise ValueError(f"Missing columns required for churn model: {missing}")

    return df


def build_preprocessor(config: ChurnModelConfig) -> ColumnTransformer:
    """Create preprocessing pipeline."""

    transformers = []
    if config.numerical_features:
        transformers.append(
            (
                "num",
                StandardScaler(),
                list(config.numerical_features),
            )
        )
    if config.categorical_features:
        transformers.append(
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore"),
                list(config.categorical_features),
            )
        )

    return ColumnTransformer(transformers=transformers)


def train_churn_model(
    df: pd.DataFrame, config: ChurnModelConfig | None = None
) -> Tuple[Pipeline, Dict[str, Dict[str, float]]]:
    """Train a gradient boosting classifier and report metrics."""

    config = config or ChurnModelConfig()
    X = df[list(config.numerical_features) + list(config.categorical_features)]
    y = df["retained_d7"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=config.test_size,
        random_state=config.random_state,
        stratify=y,
    )

    model = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(config)),
            ("classifier", GradientBoostingClassifier(random_state=config.random_state)),
        ]
    )
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    metrics = classification_report(
        y_test,
        predictions,
        output_dict=True,
        zero_division=0,
    )

    return model, metrics
