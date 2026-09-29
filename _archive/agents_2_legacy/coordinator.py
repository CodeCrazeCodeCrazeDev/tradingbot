"""
Phase 2: Multi-Agent Coordinator
Coordinates decisions from multiple specialized agents
"""

import logging
from typing import Dict, List
import numpy as np
from .base_agent import BaseAgent, AgentProposal

# Set up logger
logger = logging.getLogger(__name__)


class MultiAgentCoordinator:
    """
    Coordinates multiple trading agents and aggregates their decisions.
    Uses voting, weighting, and consensus mechanisms.
    """
    
    def __init__(self, agents: Dict[str, BaseAgent]):
        self.agents = agents
        self.decision_history = []
        
        logger.info(f"🤝 Multi-Agent Coordinator initialized with {len(agents)} agents")
        for agent_id, agent in agents.items():
            logger.info(f"   - {agent_id}: {agent.get_strategy_name()}")
    
    def get_proposals(self, market_data: Dict) -> List[AgentProposal]:
        """Get proposals from all agents."""
        proposals = []
        
        for agent_id, agent in self.agents.items():
            if agent.should_trade(market_data):
                proposal = agent.analyze_market(market_data)
                proposals.append(proposal)
                
                logger.debug(f"📋 {agent_id}: {proposal.action} "
                           f"(confidence={proposal.confidence:.2f})")
        
        return proposals
    
    def aggregate_decisions(
        self,
        proposals: List[AgentProposal],
        method: str = 'weighted_vote'
    ) -> Dict:
        """
        Aggregate proposals from multiple agents.
        
        Args:
            proposals: List of agent proposals
            method: 'weighted_vote', 'consensus', 'best_agent', 'ensemble'
        
        Returns:
            Aggregated decision
        """
        if not proposals:
            return {
                'action': 'HOLD',
                'confidence': 0.0,
                'reasoning': 'No agent proposals',
                'method': method
            }
        
        if method == 'weighted_vote':
            return self._weighted_vote(proposals)
        elif method == 'consensus':
            return self._consensus_decision(proposals)
        elif method == 'best_agent':
            return self._best_agent_decision(proposals)
        elif method == 'ensemble':
            return self._ensemble_decision(proposals)
        else:
            return self._weighted_vote(proposals)
    
    def _weighted_vote(self, proposals: List[AgentProposal]) -> Dict:
        """Weighted voting based on confidence and priority."""
        
        # Count votes for each action
        votes = {'BUY': 0.0, 'SELL': 0.0, 'HOLD': 0.0}
        total_weight = 0.0
        
        for proposal in proposals:
            # Weight = confidence * priority
            weight = proposal.confidence * proposal.priority
            votes[proposal.action] += weight
            total_weight += weight
        
        # Normalize votes
        if total_weight > 0:
            for action in votes:
                votes[action] /= total_weight
        
        # Select action with most votes
        final_action = max(votes, key=votes.get)
        final_confidence = votes[final_action]
        
        # Aggregate reasoning
        supporting_proposals = [p for p in proposals if p.action == final_action]
        reasoning = f"Weighted vote: {final_action} ({len(supporting_proposals)} agents)"
        
        return {
            'action': final_action,
            'confidence': final_confidence,
            'reasoning': reasoning,
            'votes': votes,
            'method': 'weighted_vote',
            'num_agents': len(proposals)
        }
    
    def _consensus_decision(self, proposals: List[AgentProposal]) -> Dict:
        """Require consensus (majority agreement)."""
        
        # Count actions
        action_counts = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        for proposal in proposals:
            action_counts[proposal.action] += 1
        
        total_agents = len(proposals)
        majority_threshold = total_agents / 2
        
        # Check for majority
        for action, count in action_counts.items():
            if count > majority_threshold:
                # Calculate average confidence of supporting agents
                supporting = [p for p in proposals if p.action == action]
                avg_confidence = np.mean([p.confidence for p in supporting])
                
                return {
                    'action': action,
                    'confidence': avg_confidence,
                    'reasoning': f"Consensus: {count}/{total_agents} agents agree on {action}",
                    'method': 'consensus',
                    'num_agents': total_agents
                }
        
        # No consensus
        return {
            'action': 'HOLD',
            'confidence': 0.0,
            'reasoning': f"No consensus reached (BUY:{action_counts['BUY']}, "
                        f"SELL:{action_counts['SELL']}, HOLD:{action_counts['HOLD']})",
            'method': 'consensus',
            'num_agents': total_agents
        }
    
    def _best_agent_decision(self, proposals: List[AgentProposal]) -> Dict:
        """Use decision from best performing agent."""
        
        # Find agent with highest confidence
        best_proposal = max(proposals, key=lambda p: p.confidence)
        
        return {
            'action': best_proposal.action,
            'confidence': best_proposal.confidence,
            'reasoning': f"Best agent ({best_proposal.agent_id}): {best_proposal.reasoning}",
            'method': 'best_agent',
            'num_agents': len(proposals)
        }
    
    def _ensemble_decision(self, proposals: List[AgentProposal]) -> Dict:
        """Ensemble method combining multiple approaches."""
        
        # Get decisions from different methods
        weighted = self._weighted_vote(proposals)
        consensus = self._consensus_decision(proposals)
        best = self._best_agent_decision(proposals)
        
        # If all agree, high confidence
        if weighted['action'] == consensus['action'] == best['action']:
            return {
                'action': weighted['action'],
                'confidence': 0.9,
                'reasoning': f"Strong ensemble agreement: {weighted['action']}",
                'method': 'ensemble',
                'num_agents': len(proposals)
            }
        
        # If two agree
        actions = [weighted['action'], consensus['action'], best['action']]
        if actions.count(weighted['action']) >= 2:
            return {
                'action': weighted['action'],
                'confidence': 0.7,
                'reasoning': f"Moderate ensemble agreement: {weighted['action']}",
                'method': 'ensemble',
                'num_agents': len(proposals)
            }
        
        # No agreement - be cautious
        return {
            'action': 'HOLD',
            'confidence': 0.3,
            'reasoning': "Ensemble disagreement, holding",
            'method': 'ensemble',
            'num_agents': len(proposals)
        }
    
    def update_agent_performance(self, agent_id: str, trade_result: Dict):
        """Update performance of specific agent."""
        if agent_id in self.agents:
            self.agents[agent_id].update_performance(trade_result)
    
    def get_agent_rankings(self) -> List[Dict]:
        """Get agents ranked by performance."""
        rankings = []
        
        for agent_id, agent in self.agents.items():
            metrics = agent.get_performance_metrics()
            rankings.append({
                'agent_id': agent_id,
                'agent_type': agent.agent_type.value,
                'win_rate': metrics['win_rate'],
                'total_trades': metrics['total_trades'],
                'avg_return': metrics['avg_return'],
                'sharpe_ratio': metrics['sharpe_ratio']
            })
        
        # Sort by win rate
        rankings.sort(key=lambda x: x['win_rate'], reverse=True)
        return rankings
    
    def display_agent_performance(self):
        """Display performance of all agents."""
        logger.info("\n" + "="*80)
        logger.info("🤖 AGENT PERFORMANCE")
        logger.info("="*80)
        
        rankings = self.get_agent_rankings()
        
        for i, agent_stats in enumerate(rankings, 1):
            logger.info(f"{i}. {agent_stats['agent_id']} ({agent_stats['agent_type']})")
            logger.info(f"   Win Rate: {agent_stats['win_rate']:.1%}")
            logger.info(f"   Trades: {agent_stats['total_trades']}")
            logger.info(f"   Avg Return: ${agent_stats['avg_return']:.2f}")
            logger.info(f"   Sharpe: {agent_stats['sharpe_ratio']:.2f}")
        
        logger.info("="*80)
    
    def adaptive_weighting(self) -> Dict[str, float]:
        """
        Calculate adaptive weights for agents based on recent performance.
        Better performing agents get higher weights.
        """
        weights = {}
        
        for agent_id, agent in self.agents.items():
            metrics = agent.get_performance_metrics()
            
            # Base weight on win rate and sharpe ratio
            if metrics['total_trades'] > 10:
                weight = 0.5 * metrics['win_rate'] + 0.5 * max(metrics['sharpe_ratio'], 0)
            else:
                weight = 0.5  # Default weight for new agents
            
            weights[agent_id] = weight
        
        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v/total_weight for k, v in weights.items()}
        
        return weights
