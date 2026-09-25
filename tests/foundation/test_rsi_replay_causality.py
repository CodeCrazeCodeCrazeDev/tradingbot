import pandas as pd

from trading_bot.evaluation.walk_forward import WalkForwardEvaluator


class RecordingBrain:
    def __init__(self):
        self.cycles = 0
        self.outcomes = []

    def process_cycle(self, **kwargs):
        self.cycles += 1
        return {"authorized_action": "BUY", "raw_win_probability": 0.6,
                "calibrated_probability": 0.6, "market_state": {"trend": "BULLISH"}}

    def record_outcome(self, probability, correct):
        self.outcomes.append((self.cycles, probability, correct))


def test_calibration_does_not_use_unrealized_future_or_test_labels():
    df = pd.DataFrame([{"open": 1.0, "high": 1.002, "low": 0.998,
                        "close": 1.0 + 0.0001 * i, "volume": 100} for i in range(12)])
    brain = RecordingBrain()
    evaluator = WalkForwardEvaluator(brain=brain, horizon_bars=3, signal="BUY")
    evaluator._run_split(df, "EURUSD", "train", feed_calibration=True)
    assert brain.outcomes
    assert all(cycle >= 3 for cycle, _, _ in brain.outcomes)
    assert len(brain.outcomes) == 9
    evaluator._run_split(df, "EURUSD", "test", feed_calibration=False)
    assert len(brain.outcomes) == 9


def test_parameter_replay_is_paired_costed_and_diagnostic_only():
    from trading_bot.evaluation.runner import BoundedMeanReversionReplay

    prices = [1.0 + 0.01 * ((i % 9) - 4) for i in range(65)]
    df = pd.DataFrame([{"open": p, "close": p + 0.001, "high": p + 0.002,
                        "low": p - 0.002, "volume": 1000, "timestamp": i}
                       for i, p in enumerate(prices)])
    result = BoundedMeanReversionReplay(cost_bps=5).run(df, symbol="EURUSD",
                                                    baseline_lookback=20, candidate_lookback=4)
    assert result["promotion_eligible"] is False
    assert result["evidence_source"] == "unsealed_diagnostic_replay"
    assert len(result["bars"]) == 64
    assert any(row["baseline_gross"] != row["candidate_gross"] for row in result["bars"])
    assert all(row["candidate_net"] <= row["candidate_gross"] for row in result["bars"])
