"""Pure technical-analysis calculations over OHLCV bars."""

from typing import Any, Dict, List, Sequence

from tradingview_service.errors import ValidationError
from tradingview_service.models import Bar


def average_true_range(bars: Sequence[Bar], period: int = 14) -> float:
    """Return the simple average true range for the latest ``period`` bars."""
    if period <= 0:
        raise ValidationError("period must be > 0")
    required = period + 1
    if len(bars) < required:
        raise ValidationError(f"average true range requires at least {required} bars")

    true_ranges = []
    for index in range(len(bars) - period, len(bars)):
        bar = bars[index]
        previous_close = bars[index - 1].close
        true_ranges.append(
            max(
                bar.high - bar.low,
                abs(bar.high - previous_close),
                abs(bar.low - previous_close),
            )
        )
    return sum(true_ranges) / period


def detect_swing_points(bars: Sequence[Bar], window: int = 2) -> Dict[str, List[Dict[str, Any]]]:
    """Find confirmed local extrema with ``window`` bars on both sides.

    Tied highs or lows are intentionally excluded because they do not identify a
    unique pivot.
    """
    if window <= 0:
        raise ValidationError("window must be > 0")

    highs: List[Dict[str, Any]] = []
    lows: List[Dict[str, Any]] = []
    for index in range(window, len(bars) - window):
        bar = bars[index]
        neighbors = bars[index - window : index] + bars[index + 1 : index + window + 1]
        if all(bar.high > neighbor.high for neighbor in neighbors):
            highs.append({"index": index, "time": bar.time, "price": bar.high})
        if all(bar.low < neighbor.low for neighbor in neighbors):
            lows.append({"index": index, "time": bar.time, "price": bar.low})
    return {"highs": highs, "lows": lows}


def cluster_price_levels(
    prices: Sequence[float], tolerance_percent: float = 0.5
) -> List[Dict[str, Any]]:
    """Cluster nearby positive prices and return centroid/touch evidence."""
    if tolerance_percent <= 0:
        raise ValidationError("tolerance_percent must be > 0")
    if any(price <= 0 for price in prices):
        raise ValidationError("prices must contain only positive values")

    clusters: List[List[float]] = []
    for price in sorted(prices):
        if not clusters:
            clusters.append([price])
            continue
        centroid = sum(clusters[-1]) / len(clusters[-1])
        distance_percent = abs(price - centroid) / max(price, centroid) * 100
        if distance_percent <= tolerance_percent:
            clusters[-1].append(price)
        else:
            clusters.append([price])

    return [
        {
            "price": sum(cluster) / len(cluster),
            "touches": len(cluster),
            "min_price": min(cluster),
            "max_price": max(cluster),
        }
        for cluster in clusters
    ]


def summarize_trend(
    bars: Sequence[Bar], short_period: int = 20, long_period: int = 50
) -> Dict[str, Any]:
    """Summarize close-price direction using SMAs and regression slope."""
    if short_period <= 0 or long_period <= 0:
        raise ValidationError("periods must be > 0")
    if short_period >= long_period:
        raise ValidationError("short_period must be less than long_period")
    if len(bars) < long_period:
        raise ValidationError(f"trend summary requires at least {long_period} bars")

    closes = [bar.close for bar in bars[-long_period:]]
    short_sma = sum(closes[-short_period:]) / short_period
    long_sma = sum(closes) / long_period
    slope = _linear_regression_slope(closes)
    first_close = closes[0]
    change_percent = None if first_close == 0 else (closes[-1] - first_close) / first_close * 100

    scale = max(abs(long_sma), 1.0)
    epsilon = scale * 1e-12
    if short_sma > long_sma + epsilon and slope > epsilon:
        direction = "bullish"
    elif short_sma < long_sma - epsilon and slope < -epsilon:
        direction = "bearish"
    else:
        direction = "flat"

    return {
        "direction": direction,
        "short_period": short_period,
        "long_period": long_period,
        "short_sma": short_sma,
        "long_sma": long_sma,
        "slope_per_bar": slope,
        "change_percent": change_percent,
    }


def _linear_regression_slope(values: Sequence[float]) -> float:
    count = len(values)
    mean_x = (count - 1) / 2
    mean_y = sum(values) / count
    numerator = sum((index - mean_x) * (value - mean_y) for index, value in enumerate(values))
    denominator = sum((index - mean_x) ** 2 for index in range(count))
    return 0.0 if denominator == 0 else numerator / denominator
