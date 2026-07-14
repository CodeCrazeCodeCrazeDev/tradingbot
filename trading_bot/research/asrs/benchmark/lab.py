import math
from typing import List, Dict, Any

class BenchmarkLaboratory:
    """
    Scientific Benchmark Laboratory (SBL).
    Quantifies and benchmarks latency, calibration accuracy (ECE),
    and RSS memory overhead trends.
    """
    def __init__(self):
        pass

    def calculate_percentiles(self, latencies_ms: List[float]) -> Dict[str, float]:
        """Compute P50, P90, P99, and P99.9 latency metrics."""
        if not latencies_ms:
            return {"P50": 0.0, "P90": 0.0, "P99": 0.0, "P99.9": 0.0}

        sorted_lat = sorted(latencies_ms)
        n = len(sorted_lat)

        def get_pct(pct: float) -> float:
            idx = int(math.ceil((pct / 100.0) * n)) - 1
            return sorted_lat[max(0, min(idx, n - 1))]

        return {
            "P50": get_pct(50),
            "P90": get_pct(90),
            "P99": get_pct(99),
            "P99.9": get_pct(99.9)
        }

    def calculate_ece(self, confidences: List[float], outcomes: List[int], num_bins: int = 5) -> float:
        """
        Calculates Expected Calibration Error (ECE).
        ECE = Sum( (|Bm| / N) * |acc(Bm) - conf(Bm)| )
        """
        if not confidences or len(confidences) != len(outcomes):
            return 1.0

        n = len(confidences)
        ece = 0.0

        for b in range(num_bins):
            # Bin boundaries
            bin_lower = b / num_bins
            bin_upper = (b + 1) / num_bins

            # Extract items in bin
            bin_confs = []
            bin_outs = []
            for conf, out in zip(confidences, outcomes):
                if bin_lower <= conf < bin_upper:
                    bin_confs.append(conf)
                    bin_outs.append(out)

            if bin_confs:
                bin_acc = sum(bin_outs) / len(bin_outs)
                bin_conf = sum(bin_confs) / len(bin_confs)
                ece += (len(bin_confs) / n) * abs(bin_acc - bin_conf)

        return ece

    def verify_memory_slope(self, rss_mb_history: List[float]) -> float:
        """Calculate the memory growth slope (gradient) to detect leaks."""
        if len(rss_mb_history) < 2:
            return 0.0

        # Simple linear regression gradient
        n = len(rss_mb_history)
        x = list(range(n))
        y = rss_mb_history

        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_xx = sum(xi ** 2 for xi in x)

        numerator = n * sum_xy - sum_x * sum_y
        denominator = n * sum_xx - sum_x ** 2

        if denominator == 0:
            return 0.0
        return numerator / denominator
