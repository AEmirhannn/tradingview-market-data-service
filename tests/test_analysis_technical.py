import unittest

from tradingview_service.analysis.technical import (
    average_true_range,
    cluster_price_levels,
    detect_swing_points,
    summarize_trend,
)
from tradingview_service.errors import ValidationError
from tradingview_service.models import Bar


def make_bar(index, *, high, low, close, open_=None):
    return Bar(
        time=1_700_000_000 + index * 60,
        open=close if open_ is None else open_,
        high=high,
        low=low,
        close=close,
        volume=100.0,
    )


class AverageTrueRangeTests(unittest.TestCase):
    def test_uses_previous_close_for_gaps(self):
        bars = [
            make_bar(0, high=10, low=8, close=9),
            make_bar(1, high=13, low=11, close=12),
            make_bar(2, high=12.5, low=10.5, close=11),
        ]

        self.assertAlmostEqual(average_true_range(bars, period=2), 3.0)

    def test_rejects_insufficient_bars(self):
        with self.assertRaisesRegex(ValidationError, "at least 4 bars"):
            average_true_range([make_bar(0, high=2, low=1, close=1.5)], period=3)


class SwingPointTests(unittest.TestCase):
    def test_detects_confirmed_highs_and_lows(self):
        bars = [
            make_bar(0, high=2, low=1, close=1.5),
            make_bar(1, high=3, low=2, close=2.5),
            make_bar(2, high=6, low=3, close=5),
            make_bar(3, high=4, low=2, close=3),
            make_bar(4, high=3, low=0.5, close=1),
            make_bar(5, high=4, low=2, close=3),
            make_bar(6, high=3, low=1.5, close=2),
        ]

        swings = detect_swing_points(bars, window=2)

        self.assertEqual(swings["highs"], [{"index": 2, "time": bars[2].time, "price": 6}])
        self.assertEqual(swings["lows"], [{"index": 4, "time": bars[4].time, "price": 0.5}])

    def test_ties_are_not_reported_as_swings(self):
        bars = [
            make_bar(0, high=2, low=1, close=1.5),
            make_bar(1, high=5, low=2, close=4),
            make_bar(2, high=5, low=2, close=4),
            make_bar(3, high=3, low=1, close=2),
        ]

        self.assertEqual(detect_swing_points(bars, window=1), {"highs": [], "lows": []})


class PriceLevelClusteringTests(unittest.TestCase):
    def test_clusters_nearby_levels_with_touch_counts(self):
        levels = [100.0, 100.4, 99.8, 105.0, 105.3]

        clusters = cluster_price_levels(levels, tolerance_percent=0.5)

        self.assertEqual([cluster["touches"] for cluster in clusters], [3, 2])
        self.assertAlmostEqual(clusters[0]["price"], 100.0666666667)
        self.assertAlmostEqual(clusters[1]["price"], 105.15)

    def test_rejects_non_positive_prices(self):
        with self.assertRaisesRegex(ValidationError, "positive"):
            cluster_price_levels([100.0, 0.0], tolerance_percent=1)


class TrendSummaryTests(unittest.TestCase):
    def test_reports_bullish_trend_with_evidence(self):
        bars = [make_bar(i, high=i + 2, low=i, close=i + 1) for i in range(6)]

        summary = summarize_trend(bars, short_period=2, long_period=4)

        self.assertEqual(summary["direction"], "bullish")
        self.assertAlmostEqual(summary["short_sma"], 5.5)
        self.assertAlmostEqual(summary["long_sma"], 4.5)
        self.assertGreater(summary["slope_per_bar"], 0)
        self.assertGreater(summary["change_percent"], 0)

    def test_reports_flat_for_constant_market(self):
        bars = [make_bar(i, high=11, low=9, close=10) for i in range(5)]

        summary = summarize_trend(bars, short_period=2, long_period=4)

        self.assertEqual(summary["direction"], "flat")
        self.assertEqual(summary["slope_per_bar"], 0)
        self.assertEqual(summary["change_percent"], 0)

    def test_reports_bearish_trend(self):
        bars = [make_bar(i, high=8 - i, low=6 - i, close=7 - i) for i in range(6)]

        summary = summarize_trend(bars, short_period=2, long_period=4)

        self.assertEqual(summary["direction"], "bearish")
        self.assertLess(summary["slope_per_bar"], 0)
        self.assertLess(summary["change_percent"], 0)

    def test_rejects_invalid_periods(self):
        bars = [make_bar(i, high=11, low=9, close=10) for i in range(5)]

        with self.assertRaisesRegex(ValidationError, "short_period"):
            summarize_trend(bars, short_period=4, long_period=2)


if __name__ == "__main__":
    unittest.main()
