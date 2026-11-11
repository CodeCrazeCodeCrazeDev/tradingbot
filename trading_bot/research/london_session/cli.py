"""
CLI Entrypoint for London Session Intelligence Research & Model Training.
Supports:
  python -m trading_bot.research.london_session.cli run --symbol GBPUSD --timeframe 5m --bars 1000
"""

import argparse
import sys
import json
import logging
from typing import Optional

from trading_bot.research.london_session.orchestrator import LondonSessionResearchPipeline
from trading_bot.research.london_session.collector import DataLicenseType

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AlphaAlgo.LondonSessionCLI")


def main() -> None:
    parser = argparse.ArgumentParser(description="AlphaAlgo London Session Research & Model Training CLI")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    run_parser = subparsers.add_parser("run", help="Run end-to-end research, training, and validation pipeline")
    run_parser.add_argument("--symbol", type=str, default="GBPUSD", help="Symbol to research (e.g. GBPUSD, EURUSD)")
    run_parser.add_argument("--timeframe", type=str, default="5m", help="Timeframe (e.g. 1m, 5m, 15m)")
    run_parser.add_argument("--bars", type=int, default=1000, help="Number of intraday bars for synthetic dataset")
    run_parser.add_argument("--local-path", type=str, default=None, help="Optional path to local Parquet/CSV file")
    run_parser.add_argument("--license", type=str, default="SYNTHETIC_RESEARCH", help="License type flag")

    args = parser.parse_args()

    if args.command == "run" or args.command is None:
        symbol = getattr(args, "symbol", "GBPUSD")
        timeframe = getattr(args, "timeframe", "5m")
        bars = getattr(args, "bars", 1000)
        local_path = getattr(args, "local_path", None)
        lic_str = getattr(args, "license", "SYNTHETIC_RESEARCH")

        try:
            license_type = DataLicenseType(lic_str)
        except ValueError:
            license_type = DataLicenseType.SYNTHETIC_RESEARCH

        pipeline = LondonSessionResearchPipeline()
        print(f"Executing London Session Research Pipeline for {symbol} ({timeframe})...")
        results = pipeline.execute_complete_research_run(
            symbol=symbol,
            timeframe=timeframe,
            num_bars=bars,
            local_data_path=local_path,
            license_type=license_type
        )

        print("\n========================================================")
        print(f" RESEARCH RUN COMPLETE — VERDICT: {results['verdict']}")
        print("========================================================")
        print(f"Dataset Rows:           {results['dataset_manifest'].num_rows}")
        print(f"Dataset SHA-256:        {results['dataset_manifest'].sha256_hash[:16]}...")
        print(f"Baseline Accuracy:      {results['validation_metrics']['baseline_accuracy']:.4f}")
        print(f"Meta-Model Accuracy:    {results['validation_metrics']['meta_model_accuracy']:.4f}")
        print(f"Realized Sharpe:        {results['validation_metrics']['realized_sharpe']:.2f}")
        print(f"Deflated Sharpe (DSR):  {results['validation_metrics']['deflated_sharpe']:.2f}")
        print(f"PBO (Overfitting):      {results['validation_metrics']['pbo']:.4f}")
        print(f"Survives Slippage Drag: {results['reality_gap']['edge_survives_drag']}")
        print(f"Model Checkpoint:       {results['model_artifact'].checkpoint_file_path}")
        print(f"Registered Edge ID:     {results['edge'].id}")
        print("========================================================\n")


if __name__ == "__main__":
    main()
