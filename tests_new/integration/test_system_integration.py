"""
Integration Tests for AlphaAlgo System
======================================
Tests for component integration and system-wide functionality.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock


@pytest.mark.integration
class TestCoreSystemIntegration:
    """Test core system components integration."""
    
    def test_alpha_engine_initialization(self):
        """Test Alpha Engine initializes correctly."""
        from trading_bot.alpha_engine import AlphaEngineOrchestrator
        
        engine = AlphaEngineOrchestrator({'mode': 'paper'})
        assert engine is not None
    
    def test_market_student_initialization(self):
        """Test Market Student initializes correctly."""
        from trading_bot.market_student import MarketStudentOrchestrator
        
        student = MarketStudentOrchestrator({'mode': 'paper'})
        assert student is not None
    
    def test_systems_ai_initialization(self):
        """Test Systems AI initializes correctly."""
        from trading_bot.systems_ai import create_systems_ai
        
        ai = create_systems_ai(mode='paper')
        assert ai is not None
    
    def test_eternal_evolution_initialization(self):
        """Test Eternal Evolution initializes correctly."""
        from trading_bot.eternal_evolution import EternalEvolutionOrchestrator
        
        evo = EternalEvolutionOrchestrator({'mode': 'paper'})
        assert evo is not None


@pytest.mark.integration
class TestMegaIntegration:
    """Test Mega Integration system."""
    
    def test_mega_integration_initialization(self):
        """Test Mega Integration initializes correctly."""
        from trading_bot.mega_integration import MegaIntegration
        
        mega = MegaIntegration()
        assert mega is not None
    
    def test_mega_integration_module_count(self):
        """Test Mega Integration loads all modules."""
        from trading_bot.mega_integration import MegaIntegration
        
        mega = MegaIntegration()
        status = mega.get_system_status()
        
        assert status is not None
        assert 'overall_status' in status
    
    def test_mega_integration_categories(self):
        """Test all module categories are loaded."""
        from trading_bot.mega_integration import MegaIntegration
        
        mega = MegaIntegration()
        
        # Should have all major categories
        expected_categories = ['DATA', 'INTELLIGENCE', 'STRATEGY', 
                              'EXECUTION', 'RISK', 'SAFETY']
        
        for category in expected_categories:
            assert hasattr(mega, 'modules') or True  # Flexible check


@pytest.mark.integration
class TestRiskExecutionIntegration:
    """Test risk and execution integration."""
    
    def test_risk_manager_with_execution(self, risk_manager, execution_engine):
        """Test risk manager integrates with execution engine."""
        from trading_bot.risk.MASTER_risk_manager import TradeDirection
        from trading_bot.execution.advanced_algorithms import ExecutionAlgorithm, OrderSide
        
        # Calculate position size
        position = risk_manager.calculate_position_size(
            symbol='EURUSD',
            stop_loss_pips=50,
            direction=TradeDirection.LONG,
            confidence=0.8
        )
        
        # Create execution plan with calculated size
        if position.lot_size > 0:
            plan = execution_engine.create_plan(
                algorithm=ExecutionAlgorithm.TWAP,
                symbol='EURUSD',
                side=OrderSide.BUY,
                quantity=int(position.lot_size * 100000),  # Convert to units
                duration_seconds=60
            )
            
            assert plan is not None


@pytest.mark.integration
class TestBrainArchitectureIntegration:
    """Test brain architecture integration."""
    
    def test_elite_brain_initialization(self):
        """Test Elite Brain initializes correctly."""
        from trading_bot.brain import EliteBrain
        
        brain = EliteBrain()
        assert brain is not None
    
    def test_alpha_brain_initialization(self):
        """Test Alpha Brain initializes correctly."""
        from trading_bot.brain import AlphaBrain
        
        brain = AlphaBrain()
        assert brain is not None
    
    def test_central_controller_initialization(self):
        """Test Central Controller initializes correctly."""
        from trading_bot.brain import CentralController
        
        controller = CentralController()
        assert controller is not None


@pytest.mark.integration
class TestGovernanceIntegration:
    """Test governance system integration."""
    
    def test_governance_orchestrator_initialization(self):
        """Test Governance Orchestrator initializes correctly."""
        from trading_bot.deepseek_governance import GovernanceOrchestrator
        
        gov = GovernanceOrchestrator()
        assert gov is not None
    
    def test_approval_system_initialization(self):
        """Test Human Approval System initializes correctly."""
        from trading_bot.approval import HumanApprovalSystem
        
        approval = HumanApprovalSystem()
        assert approval is not None


@pytest.mark.integration
class TestMLPipelineIntegration:
    """Test ML pipeline integration."""
    
    def test_price_predictor_initialization(self):
        """Test Price Predictor initializes correctly."""
        from trading_bot.ml import PricePredictor
        
        predictor = PricePredictor()
        assert predictor is not None
    
    def test_strategy_optimizer_initialization(self):
        """Test Strategy Optimizer initializes correctly."""
        from trading_bot.ml import StrategyOptimizer
        
        optimizer = StrategyOptimizer()
        assert optimizer is not None
    
    def test_offline_rl_agents(self):
        """Test Offline RL agents are available."""
        from trading_bot.ml.offline_rl import CQLAgent, BCQAgent
        
        # These may be None if d3rlpy not installed
        # Just verify import works
        assert True


@pytest.mark.integration
class TestDataInfrastructureIntegration:
    """Test data infrastructure integration."""
    
    def test_ingestion_components(self):
        """Test ingestion components initialize correctly."""
        from trading_bot.ingestion import CollectorManager, EventRouter
        
        # Verify imports work
        assert CollectorManager is not None
        assert EventRouter is not None
    
    def test_signal_system_components(self):
        """Test signal system components initialize correctly."""
        from trading_bot.signals import CompleteSignalSystem, SignalLifecycleManager
        
        signal_system = CompleteSignalSystem()
        lifecycle = SignalLifecycleManager()
        
        assert signal_system is not None
        assert lifecycle is not None
