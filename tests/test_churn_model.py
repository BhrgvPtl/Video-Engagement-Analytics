import pandas as pd

from src import churn_model


def sample_events() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "user_id": ["u1", "u1", "u1", "u2", "u2", "u3", "u3"],
            "video_id": ["v1", "v2", "v3", "v1", "v4", "v2", "v5"],
            "creator_id": ["c1", "c2", "c1", "c1", "c3", "c2", "c4"],
            "event_time": pd.to_datetime(
                [
                    "2024-03-01T00:00:00Z",
                    "2024-03-02T00:10:00Z",
                    "2024-03-08T00:05:00Z",
                    "2024-03-01T01:00:00Z",
                    "2024-03-01T01:20:00Z",
                    "2024-03-01T02:00:00Z",
                    "2024-03-03T02:10:00Z",
                ]
            ),
            "watched_seconds": [40, 50, 60, 35, 30, 25, 20],
            "video_duration": [60, 60, 60, 45, 45, 30, 30],
        }
    )


def test_prepare_churn_dataset_aligns_features_and_labels():
    events = sample_events()
    dataset = churn_model.prepare_churn_dataset(events, horizon_days=7)
    assert not dataset.features.empty
    assert list(dataset.features.index) == list(dataset.target.index)


def test_train_and_predict_churn_model_returns_probabilities():
    events = sample_events()
    dataset = churn_model.prepare_churn_dataset(events, horizon_days=7)
    model = churn_model.train_churn_model(dataset)
    scores = churn_model.predict_retention(model, dataset.features)
    assert {"user_id", "retention_probability"}.issubset(scores.columns)
    assert len(scores) == len(dataset.features)
