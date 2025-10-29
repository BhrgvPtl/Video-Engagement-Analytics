from datetime import datetime
from unittest import TestCase

from src import features
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
        make_event("u1", "v2", "c2", "2024-03-01T00:10:00Z", 50, 60),
        make_event("u2", "v3", "c1", "2024-03-01T01:00:00Z", 30, 45),
        make_event("u2", "v3", "c1", "2024-03-02T01:05:00Z", 45, 45),
    ]


class FeatureEngineeringTests(TestCase):
    def test_sessionize_events_assigns_unique_sessions(self) -> None:
        events = sample_events()
        sessionized = features.sessionize_events(events, session_gap_minutes=15)
        session_ids = {event.session_id for event in sessionized}
        self.assertEqual(3, len(session_ids))
        u1_sessions = {event.session_id for event in sessionized if event.user_id == "u1"}
        self.assertEqual({"u1-1"}, u1_sessions)

    def test_retention_curve_returns_expected_days(self) -> None:
        events = sample_events()
        curve = features.retention_curve(events, days=(1, 7))
        self.assertEqual([1, 7], [point.day for point in curve])
        for point in curve:
            self.assertTrue(0.0 <= point.retention_rate <= 1.0)

    def test_creator_watch_share_normalizes_totals(self) -> None:
        events = sample_events()
        share = features.creator_watch_share(events)
        total_share = sum(item.watch_share for item in share)
        self.assertAlmostEqual(1.0, total_share, places=6)
