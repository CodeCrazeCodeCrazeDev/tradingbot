"""
Command Line Interface (CLI) for commanding the Research OS.
Exposes deep querying, opportunity discovery, full pipeline runs, and graph inspections.
"""

import sys
import argparse
import json
from datetime import datetime
from trading_bot.research.orchestration.kernel import SovereignResearchOrchestrator


def run_cli():
    parser = argparse.ArgumentParser(description="AlphaAlgo Research OS Command Center")
    subparsers = parser.add_subparsers(dest="command", help="Research OS commands")

    # 1. run-pipeline command
    pipeline_parser = subparsers.add_parser("run-pipeline", help="Execute the 14-stage quantitative research loop")
    pipeline_parser.add_argument("--symbol", type=str, default="EURUSD", help="Forex ticker symbol")
    pipeline_parser.add_argument("--query", type=str, default="microstructure", help="Scientific literature search topic")

    # 2. evaluate-paper command
    paper_parser = subparsers.add_parser("evaluate-paper", help="Ingest and score a scientific quantitative paper")
    paper_parser.add_argument("--title", type=str, required=True, help="Title of the paper")
    paper_parser.add_argument("--abstract", type=str, required=True, help="Abstract text describing the paper's core claims")

    # 3. export-graph command
    graph_parser = subparsers.add_parser("export-graph", help="Export the Cognitive Research Graph")
    graph_parser.add_argument("--format", type=str, choices=["json", "graphml"], default="json", help="Graph export format")

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    orchestrator = SovereignResearchOrchestrator()

    if args.command == "run-pipeline":
        print(f"[*] Initializing Sovereign Quantitative research run for {args.symbol} (Domain: {args.query})...")
        res = orchestrator._execute_full_pipeline({"symbol": args.symbol, "query": args.query}, "cli_interactive")
        print("\n================== PIPELINE RUN RESULTS ==================")
        print(f"Status:             {res.get('status').upper()}")
        print(f"Promoted to Live:   {res.get('promoted')}")
        print(f"Strategy ID:        {res.get('strategy_id')}")
        print(f"Decision Post-Mortem:\n  -> {res.get('decision')}")

        backtest = res.get("backtest", {})
        if backtest:
            print("\n------------------ BACKTEST METRICS ------------------")
            print(f"Total Return:       {backtest.get('total_return'):.2%}")
            print(f"CAGR:               {backtest.get('cagr'):.2%}")
            print(f"Sharpe Ratio:       {backtest.get('sharpe'):.2f}")
            print(f"Max Drawdown:       {backtest.get('max_drawdown'):.2%}")
            print(f"Sortino Ratio:      {backtest.get('sortino'):.2f}")
            print(f"Conditional VaR:    {backtest.get('cvar_95_tail_risk'):.4%}")
            print(f"Profit Factor:      {backtest.get('profit_factor'):.2f}")
            print(f"Trades Executed:    {backtest.get('trades_count')}")

    elif args.command == "evaluate-paper":
        print(f"[*] Submitting paper for cognitive evaluation and embed-mapping...")
        res = orchestrator._execute_evaluate_paper({
            "title": args.title,
            "abstract": args.abstract,
            "authors": ["CLI Automated Ingestion"]
        }, "cli_interactive")
        print("\n================== INGESTION RESULTS ==================")
        print(f"Status:   {res.get('status').upper()}")
        if res.get("status") == "success":
            print(f"Paper ID: {res.get('paper_id')}")
        else:
            print(f"Reason:   {res.get('reason')}")
            print(f"Duplicate of ID: {res.get('duplicate_of')}")

    elif args.command == "export-graph":
        print(f"[*] Exporting current scientific memory state in '{args.format}' format...")
        # Populate with a quick baseline sequence if graph is currently empty to show full nodes structure
        if len(orchestrator.graph_store._graph.nodes) == 0:
            orchestrator._execute_full_pipeline({"symbol": "EURUSD", "query": "microstructure"}, "cli_export_prep")

        graph_data = orchestrator.graph_store.export_graph(format_type=args.format)
        print("\n================== GRAPH EXPORT STATE ==================")
        if args.format == "json":
            # Pretty-print JSON
            parsed = json.loads(graph_data)
            print(json.dumps(parsed, indent=2))
        else:
            print(graph_data)


if __name__ == "__main__":
    run_cli()
