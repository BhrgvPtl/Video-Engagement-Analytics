from datetime import datetime
from unittest import TestCase

from src import churn_model
from src.data_contracts import WatchEvent


def make_event(
    user: str, video: str, creator: str, timestamp: str, watched: float, duration: float
) -> WatchEvent:
    return WatchEvent(
        user_id=user,
        video_id=video,
        creator_id=creator,
        event_time=datetime.fromisoformat(timestamp.replace("Z", "+00:00")),
        watched_seconds=watched,
        video_duration=duration,
    )


def sample_events() -> list[WatchEvent]:
    return [
        make_event("u1", "v1", "c1", "2024-03-01T00:00:00Z", 40, 60),
        make_event("u1", "v2", "c2", "2024-03-02T00:10:00Z", 50, 60),
        make_event("u1", "v3", "c3", "2024-03-08T00:05:00Z", 60, 60),
        make_event("u2", "v1", "c1", "2024-03-01T01:00:00Z", 35, 45),
        make_event("u2", "v4", "c3", "2024-03-05T01:20:00Z", 30, 45),
        make_event("u3", "v2", "c2", "2024-03-01T02:00:00Z", 25, 30),
        make_event("u3", "v5", "c4", "2024-03-03T02:10:00Z", 20, 30),
    ]


class ChurnModelTests(TestCase):
    def test_prepare_churn_dataset_aligns_features_and_labels(self) -> None:
        events = sample_events()
        dataset = churn_model.prepare_churn_dataset(events, horizon_days=7)
        self.assertFalse(dataset.is_empty())
        self.assertEqual(dataset.users, dataset.users)
        self.assertEqual(len(dataset.features), len(dataset.target))

    def test_train_and_predict_churn_model_returns_probabilities(self) -> None:
        events = sample_events()
        dataset = churn_model.prepare_churn_dataset(events, horizon_days=7)
        model = churn_model.train_churn_model(dataset, epochs=200)
        scores = churn_model.predict_retention(model, dataset)
        self.assertEqual(len(scores), len(dataset.users))
        for prediction in scores:
            self.assertTrue(0.0 <= prediction.retention_probability <= 1.0)
