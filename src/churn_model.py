"""Churn modeling utilities for retention forecasting."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from math import exp
from typing import Dict, Iterable, List, Sequence

from .data_contracts import WatchEvent
from . import features


@dataclass(frozen=True)
class UserFeatures:
    """Aggregated engagement features for a user."""

    sessions: int
    avg_session_minutes: float
    total_watch_seconds: float
    mean_completion_ratio: float

    def as_vector(self) -> List[float]:
        return [
            float(self.sessions),
            float(self.avg_session_minutes),
            float(self.total_watch_seconds),
            float(self.mean_completion_ratio),
        ]


@dataclass(frozen=True)
class ChurnDataset:
    """Feature matrix and retention labels aligned by user."""

    users: List[str]
    features: List[List[float]]
    feature_names: List[str]
    target: List[int]

    def is_empty(self) -> bool:
        return not self.features or not self.target


@dataclass(frozen=True)
class RetentionPrediction:
    """Retention probability for a user."""

    user_id: str
    retention_probability: float


@dataclass(frozen=True)
class LogisticRegressionModel:
    """Minimal logistic regression model trained via gradient descent."""

    weights: List[float]
    bias: float
    means: List[float]
    scales: List[float]

    def _scale(self, vector: Sequence[float]) -> List[float]:
        scaled: List[float] = []
        for value, mean, scale in zip(vector, self.means, self.scales):
            if scale == 0:
                scaled.append(0.0)
            else:
                scaled.append((value - mean) / scale)
        return scaled

    def predict_probability(self, vector: Sequence[float]) -> float:
        scaled = self._scale(vector)
        score = sum(weight * value for weight, value in zip(self.weights, scaled)) + self.bias
        return 1.0 / (1.0 + exp(-score))

    def predict_proba(self, vectors: Sequence[Sequence[float]]) -> List[float]:
        return [self.predict_probability(vector) for vector in vectors]


def create_user_features(
    events: Sequence[WatchEvent], session_gap_minutes: int = 30
) -> Dict[str, UserFeatures]:
    """Aggregate user-level engagement features for churn modeling."""

    sessionized = features.sessionize_events(events, session_gap_minutes=session_gap_minutes)
    sessions = features.aggregate_sessions(sessionized)
    if not sessions:
        return {}

    totals: Dict[str, Dict[str, float]] = {}
    for summary in sessions:
        stats = totals.setdefault(
            summary.user_id,
            {
                "sessions": 0.0,
                "total_watch_seconds": 0.0,
                "total_session_minutes": 0.0,
                "total_completion": 0.0,
            },
        )
        stats["sessions"] += 1.0
        stats["total_watch_seconds"] += summary.session_watch_seconds
        stats["total_session_minutes"] += summary.session_duration_minutes
        stats["total_completion"] += summary.mean_completion_ratio

    features_by_user: Dict[str, UserFeatures] = {}
    for user_id, stats in totals.items():
        sessions_count = int(stats["sessions"])
        avg_session_minutes = (
            stats["total_session_minutes"] / sessions_count if sessions_count else 0.0
        )
        mean_completion_ratio = (
            stats["total_completion"] / sessions_count if sessions_count else 0.0
        )
        features_by_user[user_id] = UserFeatures(
            sessions=sessions_count,
            avg_session_minutes=avg_session_minutes,
            total_watch_seconds=stats["total_watch_seconds"],
            mean_completion_ratio=mean_completion_ratio,
        )
    return features_by_user


def label_retention(events: Sequence[WatchEvent], horizon_days: int = 7) -> Dict[str, int]:
    """Label whether users return on or after the retention horizon."""

    if not events:
        return {}

    watch_days: Dict[str, List[date]] = {}
    for event in events:
        watch_days.setdefault(event.user_id, []).append(event.event_time.date())

    labels: Dict[str, int] = {}
    horizon = timedelta(days=horizon_days)
    for user_id, days in watch_days.items():
        first_day = min(days)
        last_day = max(days)
        labels[user_id] = int(last_day - first_day >= horizon)
    return labels


def prepare_churn_dataset(
    events: Sequence[WatchEvent],
    horizon_days: int = 7,
    session_gap_minutes: int = 30,
) -> ChurnDataset:
    """Generate aligned features and labels for churn modeling."""

    user_features = create_user_features(events, session_gap_minutes=session_gap_minutes)
    labels = label_retention(events, horizon_days=horizon_days)
    users = sorted(set(user_features) & set(labels))

    feature_names = [
        "sessions",
        "avg_session_minutes",
        "total_watch_seconds",
        "mean_completion_ratio",
    ]

    features_matrix = [user_features[user].as_vector() for user in users]
    targets = [labels[user] for user in users]
    return ChurnDataset(users=users, features=features_matrix, feature_names=feature_names, target=targets)


def _column_means(matrix: Sequence[Sequence[float]]) -> List[float]:
    columns = len(matrix[0])
    means: List[float] = []
    for column in range(columns):
        total = sum(row[column] for row in matrix)
        means.append(total / len(matrix))
    return means


def _column_scales(matrix: Sequence[Sequence[float]], means: Sequence[float]) -> List[float]:
    columns = len(matrix[0])
    scales: List[float] = []
    for column in range(columns):
        variance = sum((row[column] - means[column]) ** 2 for row in matrix) / len(matrix)
        scales.append(variance ** 0.5 if variance > 0 else 1.0)
    return scales


def _scale_matrix(matrix: Sequence[Sequence[float]], means: Sequence[float], scales: Sequence[float]) -> List[List[float]]:
    scaled: List[List[float]] = []
    for row in matrix:
        scaled_row: List[float] = []
        for value, mean, scale in zip(row, means, scales):
            scaled_row.append((value - mean) / scale if scale else 0.0)
        scaled.append(scaled_row)
    return scaled


def train_churn_model(dataset: ChurnDataset, learning_rate: float = 0.1, epochs: int = 300) -> LogisticRegressionModel:
    """Fit a logistic regression churn model using gradient descent."""

    if dataset.is_empty():
        raise ValueError("Cannot train churn model with no features")

    means = _column_means(dataset.features)
    scales = _column_scales(dataset.features, means)
    scaled_features = _scale_matrix(dataset.features, means, scales)

    weights = [0.0 for _ in dataset.feature_names]
    bias = 0.0

    for _ in range(epochs):
        gradient_weights = [0.0 for _ in weights]
        gradient_bias = 0.0
        for features_row, target in zip(scaled_features, dataset.target):
            score = sum(weight * value for weight, value in zip(weights, features_row)) + bias
            prediction = 1.0 / (1.0 + exp(-score))
            error = prediction - target
            for index, value in enumerate(features_row):
                gradient_weights[index] += error * value
            gradient_bias += error
        n = len(scaled_features)
        for index in range(len(weights)):
            weights[index] -= learning_rate * gradient_weights[index] / n
        bias -= learning_rate * gradient_bias / n

    return LogisticRegressionModel(weights=weights, bias=bias, means=means, scales=scales)


def predict_retention(model: LogisticRegressionModel, dataset: ChurnDataset) -> List[RetentionPrediction]:
    """Return retention probabilities for each user."""

    if dataset.is_empty():
        return []

    probabilities = model.predict_proba(dataset.features)
    return [
        RetentionPrediction(user_id=user, retention_probability=probability)
        for user, probability in zip(dataset.users, probabilities)
    ]
