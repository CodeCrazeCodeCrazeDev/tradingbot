"""
Integration Layer - Connects Existing Approval Systems

Integrates the 4 existing approval systems into the unified hub:
1. trading_bot/approval/human_in_loop.py
2. trading_bot/human_layer/approval.py
3. trading_bot/alphaalgo_core/central_controller.py
4. trading_bot/autonomous_pipeline/approval_system.py
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from .approval_hub import get_approval_hub
from .approval_types import ApprovalCategory, ApprovalPriority, RiskLevel

logger = logging.getLogger(__name__)


class ApprovalSystemIntegrator:
    """
    Integrates all existing approval systems into the unified hub
    """
    
    def __init__(self):
        self.hub = get_approval_hub()
        self.integrated_systems = []
        
    async def integrate_all(self):
        """Integrate all existing approval systems"""
        logger.info("Starting integration of existing approval systems...")
        
        # Integrate each system
        await self._integrate_human_in_loop()
        await self._integrate_human_layer()
        await self._integrate_central_controller()
        await self._integrate_autonomous_pipeline()
        
        logger.info(f"Integration complete. Integrated {len(self.integrated_systems)} systems")
    
    async def _integrate_human_in_loop(self):
        """Integrate trading_bot/approval/human_in_loop.py"""
        try:
            from trading_bot.approval.human_in_loop import HumanApprovalSystem, ApprovalType
            
            # Create wrapper that forwards to unified hub
            original_system = HumanApprovalSystem()
            
            # Monkey-patch request_approval method
            original_request = original_system.request_approval
            
            async def unified_request_approval(approval_type, details, requester="system", priority=2, value=None):
                # Map to unified categories
                category_map = {
                    ApprovalType.LARGE_ORDER: ApprovalCategory.TRADE_EXECUTION,
                    ApprovalType.POSITION_INCREASE: ApprovalCategory.POSITION_MANAGEMENT,
                    ApprovalType.NEW_SYMBOL: ApprovalCategory.STRATEGY_CHANGE,
                    ApprovalType.STRATEGY_CHANGE: ApprovalCategory.STRATEGY_CHANGE,
                    ApprovalType.RISK_OVERRIDE: ApprovalCategory.RISK_OVERRIDE,
                    ApprovalType.EMERGENCY_ACTION: ApprovalCategory.EMERGENCY_ACTION,
                    ApprovalType.WITHDRAWAL: ApprovalCategory.POSITION_MANAGEMENT,
                    ApprovalType.CONFIG_CHANGE: ApprovalCategory.CONFIG_CHANGE,
                    ApprovalType.SYSTEM_RESTART: ApprovalCategory.SYSTEM_RESTART,
                }
                
                category = category_map.get(approval_type, ApprovalCategory.CONFIG_CHANGE)
                
                return await self.hub.request_approval(
                    category=category,
                    title=f"{approval_type.value.replace('_', ' ').title()}",
                    description=str(details),
                    details=details,
                    requester=requester,
                    source_system="human_in_loop",
                    value=value,
                )
            
            original_system.request_approval = unified_request_approval
            self.integrated_systems.append("human_in_loop")
            logger.info("✓ Integrated: human_in_loop.py")
            
        except ImportError as e:
            logger.warning(f"Could not integrate human_in_loop: {e}")
    
    async def _integrate_human_layer(self):
        """Integrate trading_bot/human_layer/approval.py"""
        try:
            from trading_bot.human_layer.approval import get_approval_gate
            
            gate = get_approval_gate()
            
            # Monkey-patch request_approval method
            original_request = gate.request_approval
            
            async def unified_request_approval(action, description, details=None, risk_assessment="UNKNOWN", timeout_seconds=None):
                # Determine category from action
                action_lower = action.lower()
                if 'trade' in action_lower or 'order' in action_lower:
                    category = ApprovalCategory.TRADE_EXECUTION
                elif 'position' in action_lower:
                    category = ApprovalCategory.POSITION_MANAGEMENT
                elif 'risk' in action_lower:
                    category = ApprovalCategory.RISK_PARAMETERS
                elif 'strategy' in action_lower:
                    category = ApprovalCategory.STRATEGY_CHANGE
                elif 'code' in action_lower or 'deploy' in action_lower:
                    category = ApprovalCategory.CODE_DEPLOYMENT
                else:
                    category = ApprovalCategory.CONFIG_CHANGE
                
                request = await self.hub.request_approval(
                    category=category,
                    title=action,
                    description=description,
                    details=details or {},
                    requester="system",
                    source_system="human_layer",
                )
                
                # Return True if approved
                return request.status.value in ['approved', 'conditional']
            
            gate.request_approval = unified_request_approval
            self.integrated_systems.append("human_layer")
            logger.info("✓ Integrated: human_layer/approval.py")
            
        except ImportError as e:
            logger.warning(f"Could not integrate human_layer: {e}")
    
    async def _integrate_central_controller(self):
        """Integrate trading_bot/alphaalgo_core/central_controller.py"""
        try:
            from trading_bot.alphaalgo_core.central_controller import G0_HumanAuthority, ActionType
            
            authority = G0_HumanAuthority()
            
            # Monkey-patch request_approval method
            original_request = authority.request_approval
            
            def unified_request_approval(action_type, description, details, requested_by="G1_Controller", 
                                       expires_hours=24, reversible=True, rollback_plan=None):
                # Map ActionType to ApprovalCategory
                action_map = {
                    ActionType.DEPLOY_CODE: ApprovalCategory.CODE_DEPLOYMENT,
                    ActionType.MODIFY_RISK_PARAMS: ApprovalCategory.RISK_PARAMETERS,
                    ActionType.CHANGE_POSITION_SIZING: ApprovalCategory.POSITION_MANAGEMENT,
                    ActionType.MODIFY_ORDER_EXECUTION: ApprovalCategory.TRADE_EXECUTION,
                    ActionType.CONNECT_LIVE_BROKER: ApprovalCategory.BROKER_CONNECTION,
                    ActionType.ENABLE_LIVE_TRADING: ApprovalCategory.LIVE_TRADING,
                    ActionType.CHANGE_GOVERNANCE_RULES: ApprovalCategory.GOVERNANCE_CHANGE,
                    ActionType.DELETE_DATA: ApprovalCategory.DATA_DELETION,
                    ActionType.EXTERNAL_COMMUNICATION: ApprovalCategory.EXTERNAL_API,
                }
                
                category = action_map.get(action_type, ApprovalCategory.CONFIG_CHANGE)
                
                # Create request synchronously (will be handled async internally)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                request = loop.run_until_complete(
                    self.hub.request_approval(
                        category=category,
                        title=description,
                        description=description,
                        details=details,
                        requester=requested_by,
                        source_system="central_controller",
                        reversible=reversible,
                        rollback_plan=rollback_plan,
                    )
                )
                loop.close()
                
                # Return original format for compatibility
                return request
            
            authority.request_approval = unified_request_approval
            self.integrated_systems.append("central_controller")
            logger.info("✓ Integrated: alphaalgo_core/central_controller.py")
            
        except ImportError as e:
            logger.warning(f"Could not integrate central_controller: {e}")
    
    async def _integrate_autonomous_pipeline(self):
        """Integrate trading_bot/autonomous_pipeline/approval_system.py"""
        try:
            from trading_bot.autonomous_pipeline.approval_system import HumanApprovalSystem
            
            system = HumanApprovalSystem()
            
            # Monkey-patch create_request method
            original_create = system.create_request
            
            def unified_create_request(item_name, item_type, test_results, discovered_item=None):
                # Determine category from item type
                type_map = {
                    'stock_data': ApprovalCategory.DATA_SOURCE,
                    'forex_data': ApprovalCategory.DATA_SOURCE,
                    'crypto_data': ApprovalCategory.DATA_SOURCE,
                    'sentiment_data': ApprovalCategory.DATA_SOURCE,
                    'satellite_data': ApprovalCategory.DATA_SOURCE,
                    'ml_model': ApprovalCategory.MODEL_DEPLOYMENT,
                    'strategy': ApprovalCategory.STRATEGY_DEPLOYMENT,
                    'indicator': ApprovalCategory.INDICATOR_ADDITION,
                }
                
                category = type_map.get(item_type, ApprovalCategory.DATA_SOURCE)
                
                # Create unified request
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                request = loop.run_until_complete(
                    self.hub.request_approval(
                        category=category,
                        title=f"Deploy {item_type}: {item_name}",
                        description=discovered_item.get('description', f"New {item_type}") if discovered_item else f"New {item_type}",
                        details={
                            'item_name': item_name,
                            'item_type': item_type,
                            'test_results': test_results,
                            'discovered_item': discovered_item,
                        },
                        requester="autonomous_pipeline",
                        source_system="autonomous_pipeline",
                        test_score=test_results.get('overall_score', 0.0),
                    )
                )
                loop.close()
                
                return request
            
            system.create_request = unified_create_request
            self.integrated_systems.append("autonomous_pipeline")
            logger.info("✓ Integrated: autonomous_pipeline/approval_system.py")
            
        except ImportError as e:
            logger.warning(f"Could not integrate autonomous_pipeline: {e}")
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get integration status"""
        return {
            'integrated_systems': self.integrated_systems,
            'total_integrated': len(self.integrated_systems),
            'target_systems': 4,
            'integration_complete': len(self.integrated_systems) >= 4,
        }


async def integrate_approval_systems():
    """Convenience function to integrate all systems"""
    integrator = ApprovalSystemIntegrator()
    await integrator.integrate_all()
    return integrator.get_integration_status()


if __name__ == "__main__":
    # Test integration
    async def test():
        integrator = ApprovalSystemIntegrator()
        await integrator.integrate_all()
        status = integrator.get_integration_status()
        print(f"\nIntegration Status:")
        print(f"  Integrated: {status['total_integrated']}/{status['target_systems']}")
        print(f"  Systems: {', '.join(status['integrated_systems'])}")
        print(f"  Complete: {status['integration_complete']}")
    
    asyncio.run(test())
