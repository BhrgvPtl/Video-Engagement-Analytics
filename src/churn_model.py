"""Churn modeling utilities for retention forecasting."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from . import features


@dataclass
class ChurnDataset:
    features: pd.DataFrame
    target: pd.Series


def create_user_features(events: pd.DataFrame, session_gap_minutes: int = 30) -> pd.DataFrame:
    """Aggregate user-level engagement features for churn modeling."""

    sessionized = features.sessionize_events(events, session_gap_minutes=session_gap_minutes)
    sessions = features.aggregate_sessions(sessionized)
    if sessions.empty:
        return pd.DataFrame(columns=["sessions", "avg_session_minutes", "total_watch_seconds", "mean_completion_ratio"])

    session_features = (
        sessions.groupby("user_id")
        .agg(
            sessions=("session_id", "nunique"),
            avg_session_minutes=("session_duration_minutes", "mean"),
            total_watch_seconds=("session_watch_seconds", "sum"),
            mean_completion_ratio=("mean_completion_ratio", "mean"),
        )
        .fillna(0.0)
    )
    return session_features


def label_retention(events: pd.DataFrame, horizon_days: int = 7) -> pd.Series:
    """Label whether users return on or after the retention horizon."""

    if events.empty:
        return pd.Series(dtype=int)

    df = features.sessionize_events(events)
    first_watch = df.groupby("user_id")["watch_day"].min()
    last_watch = df.groupby("user_id")["watch_day"].max()
    retained = last_watch >= (first_watch + pd.Timedelta(days=horizon_days))
    return retained.astype(int).rename("retained")


def prepare_churn_dataset(events: pd.DataFrame, horizon_days: int = 7, session_gap_minutes: int = 30) -> ChurnDataset:
    """Generate aligned features and labels for churn modeling."""

    user_features = create_user_features(events, session_gap_minutes=session_gap_minutes)
    labels = label_retention(events, horizon_days=horizon_days)
    aligned = user_features.join(labels, how="inner")
    target = aligned.pop("retained")
    return ChurnDataset(features=aligned, target=target)


def train_churn_model(dataset: ChurnDataset) -> Pipeline:
    """Fit a logistic regression churn model."""

    if dataset.features.empty:
        raise ValueError("Cannot train churn model with no features")

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000)),
    ])
    model.fit(dataset.features, dataset.target)
    return model


def predict_retention(model: Pipeline, features_df: pd.DataFrame) -> pd.DataFrame:
    """Return retention probabilities for each user."""

    if features_df.empty:
        return pd.DataFrame(columns=["user_id", "retention_probability"])

    probabilities = model.predict_proba(features_df)[:, 1]
    return pd.DataFrame({"user_id": features_df.index, "retention_probability": probabilities})
