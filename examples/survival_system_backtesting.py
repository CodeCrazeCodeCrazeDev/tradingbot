#!/usr/bin/env python
"""
Survival System Backtesting Integration

This script demonstrates how to integrate the Survival System with the Advanced
Backtesting Framework to validate its effectiveness under various market conditions.
"""

import asyncio
import logging
import yaml
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

from trading_bot.core.survival_core import SurvivalCore
from trading_bot.backtesting.advanced_backtester import AdvancedBacktester
from trading_bot.backtesting.scenario_generator import MarketScenarioGenerator
from trading_bot.backtesting.monte_carlo import MonteCarloSimulation
from trading_bot.backtesting.performance_analyzer import PerformanceAnalyzer
import numpy
import pandas

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("survival_system_backtesting.log")
    ]
)
logger = logging.getLogger("survival_system_backtesting")


class SurvivalSystemBacktester:
    """Backtester for the Survival System"""
    
    def __init__(self, config_path="config/survival_config.yaml"):
        """Initialize backtester"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load configuration
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        
        # Configure backtesting
        self.backtesting_config = {
            "start_date": datetime.now() - timedelta(days=365),  # 1 year of data
            "end_date": datetime.now(),
            "symbols": self.config.get("symbols", ["EURUSD", "GBPUSD", "USDJPY"]),
            "timeframes": self.config.get("timeframes", ["M5", "M15", "H1"]),
            "initial_balance": 100000.0,
            "commission": 0.0001,  # 1 pip commission
            "slippage": 0.0001,  # 1 pip slippage
            "leverage": 100.0,
            "monte_carlo_runs": 1000,
            "stress_test_scenarios": [
                "normal",
                "high_volatility",
                "market_crash",
                "liquidity_crisis",
                "flash_crash"
            ]
        }
        
        # Initialize components
        self.backtester = AdvancedBacktester(self.backtesting_config)
        self.scenario_generator = MarketScenarioGenerator(self.backtesting_config)
        self.monte_carlo = MonteCarloSimulation(self.backtesting_config)
        self.performance_analyzer = PerformanceAnalyzer()
    
    async def run_standard_backtest(self):
        """Run standard backtest with historical data"""
        self.logger.info("Running standard backtest")
        
        # Create survival system with backtesting mode enabled
        backtest_config = self.config.copy()
        backtest_config["backtesting_mode"] = True
        backtest_config["data_stream"]["simulate_data"] = True
        
        # Create survival system
        system = SurvivalCore(backtest_config)
        
        # Run backtest
        results = await self.backtester.run_backtest(system)
        
        # Analyze results
        analysis = self.performance_analyzer.analyze_backtest(results)
        
        # Log results
        self.logger.info("Backtest Results:")
        self.logger.info(f"Total Trades: {analysis['total_trades']}")
        self.logger.info(f"Win Rate: {analysis['win_rate']:.2%}")
        self.logger.info(f"Profit Factor: {analysis['profit_factor']:.2f}")
        self.logger.info(f"Sharpe Ratio: {analysis['sharpe_ratio']:.2f}")
        self.logger.info(f"Max Drawdown: {analysis['max_drawdown']:.2%}")
        self.logger.info(f"Recovery Factor: {analysis['recovery_factor']:.2f}")
        self.logger.info(f"Expectancy: {analysis['expectancy']:.2f}")
        
        return results, analysis
    
    async def run_monte_carlo_simulation(self, backtest_results):
        """Run Monte Carlo simulation to assess risk and robustness"""
        self.logger.info("Running Monte Carlo simulation")
        
        # Run Monte Carlo simulation
        mc_results = self.monte_carlo.run_simulation(backtest_results)
        
        # Log results
        self.logger.info("Monte Carlo Results:")
        self.logger.info(f"95% VaR: {mc_results['var_95']:.2%}")
        self.logger.info(f"99% VaR: {mc_results['var_99']:.2%}")
        self.logger.info(f"Expected Shortfall: {mc_results['expected_shortfall']:.2%}")
        self.logger.info(f"Probability of 10% Drawdown: {mc_results['prob_10pct_drawdown']:.2%}")
        self.logger.info(f"Probability of 20% Drawdown: {mc_results['prob_20pct_drawdown']:.2%}")
        self.logger.info(f"Probability of 50% Drawdown: {mc_results['prob_50pct_drawdown']:.2%}")
        
        return mc_results
    
    async def run_stress_tests(self):
        """Run stress tests to assess system behavior under extreme conditions"""
        self.logger.info("Running stress tests")
        
        results = {}
        
        for scenario in self.backtesting_config["stress_test_scenarios"]:
            self.logger.info(f"Running {scenario} scenario")
            
            # Generate scenario data
            scenario_data = self.scenario_generator.generate_scenario(scenario)
            
            # Create survival system with backtesting mode enabled
            backtest_config = self.config.copy()
            backtest_config["backtesting_mode"] = True
            backtest_config["data_stream"]["simulate_data"] = True
            backtest_config["data_stream"]["simulated_data"] = scenario_data
            
            # Create survival system
            system = SurvivalCore(backtest_config)
            
            # Run backtest
            scenario_results = await self.backtester.run_backtest(system)
            
            # Analyze results
            analysis = self.performance_analyzer.analyze_backtest(scenario_results)
            
            # Store results
            results[scenario] = {
                "results": scenario_results,
                "analysis": analysis
            }
            
            # Log results
            self.logger.info(f"{scenario.upper()} Results:")
            self.logger.info(f"Total Trades: {analysis['total_trades']}")
            self.logger.info(f"Win Rate: {analysis['win_rate']:.2%}")
            self.logger.info(f"Profit Factor: {analysis['profit_factor']:.2f}")
            self.logger.info(f"Max Drawdown: {analysis['max_drawdown']:.2%}")
        
        return results
    
    async def compare_with_without_survival_system(self):
        """Compare performance with and without survival system"""
        self.logger.info("Comparing performance with and without survival system")
        
        # Run backtest with survival system
        backtest_config_with = self.config.copy()
        backtest_config_with["backtesting_mode"] = True
        backtest_config_with["data_stream"]["simulate_data"] = True
        
        system_with = SurvivalCore(backtest_config_with)
        results_with = await self.backtester.run_backtest(system_with)
        analysis_with = self.performance_analyzer.analyze_backtest(results_with)
        
        # Run backtest without survival system
        backtest_config_without = self.config.copy()
        backtest_config_without["backtesting_mode"] = True
        backtest_config_without["data_stream"]["simulate_data"] = True
        backtest_config_without["disable_survival_features"] = True
        
        system_without = SurvivalCore(backtest_config_without)
        results_without = await self.backtester.run_backtest(system_without)
        analysis_without = self.performance_analyzer.analyze_backtest(results_without)
        
        # Compare results
        comparison = {
            "with_survival": analysis_with,
            "without_survival": analysis_without,
            "difference": {
                "win_rate": analysis_with["win_rate"] - analysis_without["win_rate"],
                "profit_factor": analysis_with["profit_factor"] - analysis_without["profit_factor"],
                "sharpe_ratio": analysis_with["sharpe_ratio"] - analysis_without["sharpe_ratio"],
                "max_drawdown": analysis_with["max_drawdown"] - analysis_without["max_drawdown"],
                "recovery_factor": analysis_with["recovery_factor"] - analysis_without["recovery_factor"],
                "expectancy": analysis_with["expectancy"] - analysis_without["expectancy"]
            }
        }
        
        # Log comparison
        self.logger.info("Comparison Results:")
        self.logger.info(f"Win Rate Difference: {comparison['difference']['win_rate']:.2%}")
        self.logger.info(f"Profit Factor Difference: {comparison['difference']['profit_factor']:.2f}")
        self.logger.info(f"Sharpe Ratio Difference: {comparison['difference']['sharpe_ratio']:.2f}")
        self.logger.info(f"Max Drawdown Difference: {comparison['difference']['max_drawdown']:.2%}")
        self.logger.info(f"Recovery Factor Difference: {comparison['difference']['recovery_factor']:.2f}")
        self.logger.info(f"Expectancy Difference: {comparison['difference']['expectancy']:.2f}")
        
        return comparison
    
    async def generate_report(self):
        """Generate comprehensive backtest report"""
        self.logger.info("Generating backtest report")
        
        # Run all tests
        standard_results, standard_analysis = await self.run_standard_backtest()
        mc_results = await self.run_monte_carlo_simulation(standard_results)
        stress_results = await self.run_stress_tests()
        comparison = await self.compare_with_without_survival_system()
        
        # Generate HTML report
        report_path = "reports/survival_system_backtest_report.html"
        
        # Ensure directory exists
        Path("reports").mkdir(exist_ok=True)
        
        # Generate report
        self.performance_analyzer.generate_html_report(
            report_path,
            {
                "standard": {
                    "results": standard_results,
                    "analysis": standard_analysis
                },
                "monte_carlo": mc_results,
                "stress_tests": stress_results,
                "comparison": comparison
            }
        )
        
        self.logger.info(f"Report generated: {report_path}")
        
        return report_path


async def main():
    """Main function"""
    logger.info("Starting Survival System Backtesting")
    
    try:
        # Create backtester
        backtester = SurvivalSystemBacktester()
        
        # Generate report
        report_path = await backtester.generate_report()
        
        logger.info(f"Backtesting completed. Report available at: {report_path}")
        
    except Exception as e:
        logger.exception(f"Error in backtesting: {e}")
    
    logger.info("Survival System Backtesting completed")


if __name__ == "__main__":
    asyncio.run(main())
