import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from clarity_metrics import canonical_path, compact_raw_snapshot


class CanonicalPathTests(unittest.TestCase):
    def test_strips_all_query_parameters_and_fragment(self):
        self.assertEqual(
            canonical_path(
                "https://www.haywoodgolf.com/products/mid-mallet-golf-putter/"
                "?gclid=abc&utm_source=google&_su_rec=xyz#details"
            ),
            "/products/mid-mallet-golf-putter",
        )

    def test_normalizes_root_and_duplicate_slashes(self):
        self.assertEqual(canonical_path("https://www.haywoodgolf.com/?fbclid=abc"), "/")
        self.assertEqual(canonical_path("/collections//golf-irons//?srsltid=abc"), "/collections/golf-irons")


class CompactionTests(unittest.TestCase):
    def test_combines_url_variants_with_weighted_rates(self):
        rows = [
            {
                "Device": "Mobile",
                "Url": "https://www.haywoodgolf.com/products/test?gclid=a",
                "totalSessionCount": 10,
                "totalBotSessionCount": 0,
                "pagesPerSessionPercentage": 2,
            },
            {
                "Device": "Mobile",
                "Url": "https://www.haywoodgolf.com/products/test?fbclid=b",
                "totalSessionCount": 30,
                "totalBotSessionCount": 0,
                "pagesPerSessionPercentage": 4,
            },
        ]
        behavior_rows = [
            {**rows[0], "sessionsCount": 10, "sessionsWithMetricPercentage": 10, "subTotal": 1},
            {**rows[1], "sessionsCount": 30, "sessionsWithMetricPercentage": 20, "subTotal": 7},
        ]
        raw = {
            "collected_at": "2026-09-01T00:00:00+00:00",
            "window_days": 3,
            "segments": {
                "device": {"data": []},
                "url_device": {
                    "data": [
                        {"metricName": "Traffic", "information": rows},
                        {"metricName": "QuickbackClick", "information": behavior_rows},
                    ]
                },
            },
            "validation": {"traffic_sessions": 40},
        }

        compact = compact_raw_snapshot(raw)
        self.assertEqual(len(compact["page_device"]), 1)
        page = compact["page_device"][0]
        self.assertEqual(page["path"], "/products/test")
        self.assertEqual(page["sessions"], 40)
        self.assertEqual(page["pages_per_session"], 3.5)
        self.assertEqual(page["behaviors"]["quick_back"]["affected_sessions_est"], 7)
        self.assertEqual(page["behaviors"]["quick_back"]["rate_pct"], 17.5)


if __name__ == "__main__":
    unittest.main()
