"""
Research Roadmap Demo Runner

Demonstrates all implemented research components:
- Week 5-6: TFT Forecasting
- Week 7-8: AgentFlow & Almgren-Chriss
- Week 9-10: MAML Meta-Learning
- Week 11-12: Contrastive Learning
- Week 13-14: Graph Neural Networks
"""

import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_tft_forecasting():
    """Demo TFT forecasting system"""
    print("\n" + "="*80)
    print("WEEK 5-6: TFT FORECASTING DEMO")
    print("="*80)
    
    try:
        from trading_bot.ml.forecasting import TFTForecaster, TFTConfig, create_sample_data
        
        # Create sample data
        print("Creating sample data...")
        data = create_sample_data(n_samples=2000)
        
        # Initialize forecaster
        config = TFTConfig(
            max_encoder_length=168,
            max_prediction_length=24,
            hidden_size=32,
            max_epochs=5
        )
        
        forecaster = TFTForecaster(config)
        
        # Prepare dataset
        print("Preparing dataset...")
        forecaster.prepare_dataset(data)
        
        # Train
        print("Training TFT model...")
        forecaster.train(gpus=0)
        
        # Evaluate
        print("Evaluating model...")
        metrics = forecaster.evaluate(data)
        
        print(f"\n✅ TFT Demo Complete!")
        print(f"   MAPE: {metrics['mape']:.2f}%")
        print(f"   RMSE: {metrics['rmse']:.6f}")
        print(f"   Coverage: {metrics['coverage_80']:.2%}")
        
        return True
        
    except Exception as e:
        logger.error(f"TFT demo failed: {e}")
        return False


def demo_agentflow():
    """Demo AgentFlow system"""
    print("\n" + "="*80)
    print("WEEK 7-8: AGENTFLOW & OPTIMAL EXECUTION DEMO")
    print("="*80)
    
    try:
        from trading_bot.agents.planner_agent import PlannerAgent
        from trading_bot.agents.verifier_agent import VerifierAgent
        from trading_bot.execution.almgren_chriss import AlmgrenChrissOptimizer
        
        # Create agents
        planner = PlannerAgent(min_confidence=0.6)
        verifier = VerifierAgent(max_position_size=0.50)
        
        # Sample market data
        market_data = {
            'price': 1.0850,
            'rsi': 45,
            'macd': 0.0003,
            'macd_signal': 0.0001,
            'ma_20': 1.0840,
            'ma_50': 1.0820,
            'atr': 0.0008,
            'volatility': 0.012,
            'news_sentiment': 0.65,
            'forecast': {
                'median_prediction': 0.0015,
                'confidence': 0.80
            }
        }
        
        # Planner proposes trade
        print("Planner analyzing market...")
        proposal = planner.propose_trade('EURUSD', market_data)
        
        if proposal:
            print(f"✅ Trade proposed: {proposal.action.upper()} {proposal.lots:.2f} lots")
            print(f"   Confidence: {proposal.confidence:.2%}")
            print(f"   Expected Value: ${proposal.expected_value:.2f}")
            
            # Verifier checks trade
            print("\nVerifier checking proposal...")
            result = verifier.verify_proposal(proposal, [], 10000.0)
            
            if result.approved:
                print(f"✅ Trade APPROVED by verifier")
            else:
                print(f"❌ Trade REJECTED: {result.reason}")
        
        # Demo Almgren-Chriss
        print("\nOptimal Execution Demo...")
        optimizer = AlmgrenChrissOptimizer(risk_aversion=0.5)
        schedule = optimizer.compute_optimal_trajectory(1.0, 10)
        
        print(f"✅ Optimal schedule: {schedule.total_quantity:.2f} lots over {schedule.time_horizon} min")
        print(f"   Expected cost: ${schedule.expected_cost:.4f}")
        
        return True
        
    except Exception as e:
        logger.error(f"AgentFlow demo failed: {e}")
        return False


def demo_maml():
    """Demo MAML meta-learning"""
    print("\n" + "="*80)
    print("WEEK 9-10: MAML META-LEARNING DEMO")
    print("="*80)
    
    try:
        from trading_bot.ml.meta_learning.maml import MAML, TradingPolicy, create_sample_tasks
        import torch
        
        # Create model
        model = TradingPolicy(input_dim=50, hidden_dim=64, output_dim=3)
        
        # Create MAML
        maml = MAML(model, inner_lr=0.01, outer_lr=0.001, inner_steps=5)
        
        # Create tasks
        print("Creating meta-learning tasks...")
        train_tasks = create_sample_tasks(n_tasks=20, n_samples_per_task=50)
        
        # Meta-train
        print("Meta-training...")
        history = maml.meta_train(tasks=train_tasks, epochs=20)
        
        # Test fast adaptation
        print("Testing fast adaptation...")
        new_task = (torch.randn(50, 50), torch.randint(0, 3, (50,)))
        adapted_model = maml.fast_adapt(new_task, steps=5)
        
        print(f"\n✅ MAML Demo Complete!")
        print(f"   Final meta-loss: {history['train_loss'][-1]:.4f}")
        print(f"   Fast adaptation: 5 steps")
        
        return True
        
    except Exception as e:
        logger.error(f"MAML demo failed: {e}")
        return False


def demo_contrastive_learning():
    """Demo contrastive learning"""
    print("\n" + "="*80)
    print("WEEK 11-12: CONTRASTIVE LEARNING DEMO")
    print("="*80)
    
    try:
        from trading_bot.ml.representation.contrastive_pretrain import (
            TimeSeriesEncoder, ContrastivePretrainer, FineTuner
        )
        import torch
        from torch.utils.data import TensorDataset, DataLoader
        
        # Create encoder
        encoder = TimeSeriesEncoder(input_channels=1, hidden_dim=64, output_dim=64)
        
        # Create unlabeled data
        print("Creating unlabeled data...")
        unlabeled_data = torch.randn(500, 1, 168)
        dataset = TensorDataset(unlabeled_data)
        data_loader = DataLoader(dataset, batch_size=32, shuffle=True)
        
        # Pretrain
        print("Pretraining encoder...")
        pretrainer = ContrastivePretrainer(encoder, temperature=0.5)
        history = pretrainer.pretrain(data_loader, epochs=20)
        
        # Fine-tune
        print("Fine-tuning on labeled data...")
        labeled_features = torch.randn(200, 1, 168)
        labeled_targets = torch.randint(0, 3, (200,))
        
        train_dataset = TensorDataset(labeled_features[:150], labeled_targets[:150])
        val_dataset = TensorDataset(labeled_features[150:], labeled_targets[150:])
        
        train_loader = DataLoader(train_dataset, batch_size=16)
        val_loader = DataLoader(val_dataset, batch_size=16)
        
        finetuner = FineTuner(encoder, num_classes=3, freeze_encoder=True)
        ft_history = finetuner.finetune(train_loader, val_loader, epochs=15)
        
        print(f"\n✅ Contrastive Learning Demo Complete!")
        print(f"   Pretraining loss: {history['loss'][-1]:.4f}")
        print(f"   Fine-tuning accuracy: {ft_history['val_acc'][-1]:.2%}")
        
        return True
        
    except Exception as e:
        logger.error(f"Contrastive learning demo failed: {e}")
        return False


def demo_gnn():
    """Demo Graph Neural Networks"""
    print("\n" + "="*80)
    print("WEEK 13-14: GRAPH NEURAL NETWORKS DEMO")
    print("="*80)
    
    try:
        from trading_bot.ml.graph.gnn_model import AssetGNN, AssetGraph, SpilloverPredictor
        import numpy as np
        
        # Define assets
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
        
        # Create graph
        asset_graph = AssetGraph(symbols)
        
        # Create sample data
        print("Creating cross-asset data...")
        price_data = {
            symbol: np.random.randn(100).cumsum() + 100
            for symbol in symbols
        }
        
        market_data = {
            symbol: {
                'price': price_data[symbol][-1],
                'volume': 1000,
                'rsi': 50 + np.random.randn() * 10,
                'macd': np.random.randn() * 0.001,
                'atr': 0.001,
                'bb_upper': price_data[symbol][-1] * 1.01,
                'bb_lower': price_data[symbol][-1] * 0.99,
                'volume_ratio': 1.0,
                'spread': 0.0001,
                'volatility': 0.01
            }
            for symbol in symbols
        }
        
        # Build graph
        adj = asset_graph.build_correlation_graph(price_data)
        features = asset_graph.build_feature_matrix(market_data)
        
        print(f"Graph: {len(symbols)} nodes, {adj.sum().item():.0f} edges")
        
        # Create model
        model = AssetGNN(in_features=10, hidden_features=32)
        
        # Test spillover prediction
        print("Testing spillover prediction...")
        predictor = SpilloverPredictor(model, asset_graph)
        
        spillover = predictor.predict_spillover(
            'EURUSD', 0.01, market_data, price_data
        )
        
        # Test hedge suggestion
        hedge_symbol, hedge_size = predictor.suggest_hedge(
            'EURUSD', 1.0, market_data, price_data
        )
        
        print(f"\n✅ GNN Demo Complete!")
        print(f"   Spillover effects calculated for {len(spillover)} assets")
        if hedge_symbol:
            print(f"   Hedge suggestion: {hedge_size:.2f} lots {hedge_symbol}")
        
        return True
        
    except Exception as e:
        logger.error(f"GNN demo failed: {e}")
        return False


def main():
    """Run all demos"""
    print("\n" + "="*80)
    print("RESEARCH ROADMAP COMPREHENSIVE DEMO")
    print("="*80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    results = {}
    
    # Run all demos
    results['TFT Forecasting'] = demo_tft_forecasting()
    results['AgentFlow'] = demo_agentflow()
    results['MAML Meta-Learning'] = demo_maml()
    results['Contrastive Learning'] = demo_contrastive_learning()
    results['Graph Neural Networks'] = demo_gnn()
    
    # Summary
    print("\n" + "="*80)
    print("DEMO SUMMARY")
    print("="*80)
    
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(results.values())
    
    print("="*80)
    print(f"Results: {passed}/{total} demos passed ({passed/total*100:.0f}%)")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
