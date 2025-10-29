from datetime import datetime
from unittest import TestCase

from src import features, metrics
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
        make_event("u1", "v1", "c1", "2024-03-01T00:00:00Z", 30, 60),
        make_event("u1", "v2", "c2", "2024-03-01T00:10:00Z", 45, 60),
        make_event("u2", "v3", "c1", "2024-03-02T00:05:00Z", 40, 50),
        make_event("u3", "v4", "c3", "2024-03-03T01:00:00Z", 20, 40),
    ]


class MetricsTests(TestCase):
    def test_completion_rate_between_zero_and_one(self) -> None:
        events = sample_events()
        rate = metrics.completion_rate(events)
        self.assertTrue(0.0 <= rate <= 1.0)

    def test_drop_off_positions_keys_match_thresholds(self) -> None:
        events = sample_events()
        drops = metrics.drop_off_positions(events, thresholds=(0.5, 0.9))
        self.assertEqual({"below_50", "below_90"}, set(drops.keys()))

    def test_dau_wau_ratio_never_exceeds_one(self) -> None:
        events = sample_events()
        ratio_info = metrics.dau_wau_ratio(events)
        self.assertTrue(0.0 <= ratio_info["ratio"] <= 1.0)

    def test_creator_contribution_limits_results(self) -> None:
        events = sample_events()
        top_creators = metrics.creator_contribution(events, top_n=2)
        self.assertEqual(2, len(top_creators))
