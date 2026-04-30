"""
Phase 2: Multi-Agent Coordinator
Coordinates decisions from multiple specialized agents.
"""

import logging
from typing import Dict, List, Optional

import numpy as np

from ..a2a import A2AMessageBus
from ..world2agent import World2AgentBridge
from .base_agent import AgentCommunication, AgentProposal, BaseAgent

# Set up logger
logger = logging.getLogger(__name__)


class MultiAgentCoordinator:
    """
    Coordinates multiple trading agents and aggregates their decisions.
    Uses voting, weighting, consensus, and shared A2A/world2agent plumbing.
    """

    def __init__(
        self,
        agents: Dict[str, BaseAgent],
        a2a_bus: Optional[A2AMessageBus] = None,
        world_bridge: Optional[World2AgentBridge] = None,
    ):
        try:
            self.agents = agents
            self.decision_history = []
            self.a2a_bus = a2a_bus or A2AMessageBus()
            self.world_bridge = world_bridge or World2AgentBridge(self.a2a_bus)
            self.communication = AgentCommunication(
                a2a_bus=self.a2a_bus,
                world_bridge=self.world_bridge,
            )
            self.coordinator_id = "agents2.coordinator"

            self.a2a_bus.register_agent(
                self.coordinator_id,
                capabilities=["coordination", "consensus", "decision_aggregation"],
            )
            for agent_id, agent in agents.items():
                self.communication.register_agent(
                    agent_id,
                    capabilities=[agent.agent_type.value, agent.get_strategy_name()],
                )

            logger.info(
                "Multi-Agent Coordinator initialized with %d agents",
                len(agents),
            )
            for agent_id, agent in agents.items():
                logger.info("   - %s: %s", agent_id, agent.get_strategy_name())
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    def get_proposals(self, market_data: Dict) -> List[AgentProposal]:
        """Get proposals from all agents."""
        try:
            proposals = []
            self.communication.publish_world_state(
                sender_id=self.coordinator_id,
                world_state=market_data,
                audience=list(self.agents.keys()),
                context_type="market",
            )

            for agent_id, agent in self.agents.items():
                if agent.should_trade(market_data):
                    proposal = agent.analyze_market(market_data)
                    proposals.append(proposal)
                    self.communication.broadcast(
                        sender_id=agent_id,
                        message_type="proposal",
                        data=proposal.to_dict(),
                    )
                    logger.debug(
                        "%s: %s (confidence=%.2f)",
                        agent_id,
                        proposal.action,
                        proposal.confidence,
                    )

            return proposals
        except Exception as e:
            logger.error(f"Error in get_proposals: {e}")
            raise

    def aggregate_decisions(
        self,
        proposals: List[AgentProposal],
        method: str = "weighted_vote",
    ) -> Dict:
        """
        Aggregate proposals from multiple agents.

        Args:
            proposals: List of agent proposals
            method: 'weighted_vote', 'consensus', 'best_agent', 'ensemble'

        Returns:
            Aggregated decision
        """
        try:
            if not proposals:
                result = {
                    "action": "HOLD",
                    "confidence": 0.0,
                    "reasoning": "No agent proposals",
                    "method": method,
                }
            elif method == "weighted_vote":
                result = self._weighted_vote(proposals)
            elif method == "consensus":
                result = self._consensus_decision(proposals)
            elif method == "best_agent":
                result = self._best_agent_decision(proposals)
            elif method == "ensemble":
                result = self._ensemble_decision(proposals)
            else:
                result = self._weighted_vote(proposals)

            self.decision_history.append(result)
            self.a2a_bus.broadcast(
                sender=self.coordinator_id,
                intent="collective_decision",
                payload=self.world_bridge.build_agent_context(
                    self.coordinator_id,
                    {
                        "decision": result,
                        "num_agents": len(proposals),
                    },
                ),
                recipients=list(self.agents.keys()),
                channel="agents2",
                metadata={"method": method},
            )
            return result
        except Exception as e:
            logger.error(f"Error in aggregate_decisions: {e}")
            raise

    def _weighted_vote(self, proposals: List[AgentProposal]) -> Dict:
        """Weighted voting based on confidence and priority."""
        try:
            votes = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}
            total_weight = 0.0

            for proposal in proposals:
                weight = proposal.confidence * proposal.priority
                votes[proposal.action] += weight
                total_weight += weight

            if total_weight > 0:
                for action in votes:
                    votes[action] /= total_weight

            final_action = max(votes, key=votes.get)
            final_confidence = votes[final_action]
            supporting_proposals = [p for p in proposals if p.action == final_action]
            reasoning = f"Weighted vote: {final_action} ({len(supporting_proposals)} agents)"

            return {
                "action": final_action,
                "confidence": final_confidence,
                "reasoning": reasoning,
                "votes": votes,
                "method": "weighted_vote",
                "num_agents": len(proposals),
            }
        except Exception as e:
            logger.error(f"Error in _weighted_vote: {e}")
            raise

    def _consensus_decision(self, proposals: List[AgentProposal]) -> Dict:
        """Require consensus (majority agreement)."""
        try:
            action_counts = {"BUY": 0, "SELL": 0, "HOLD": 0}
            for proposal in proposals:
                action_counts[proposal.action] += 1

            total_agents = len(proposals)
            majority_threshold = total_agents / 2

            for action, count in action_counts.items():
                if count > majority_threshold:
                    supporting = [p for p in proposals if p.action == action]
                    avg_confidence = np.mean([p.confidence for p in supporting])
                    return {
                        "action": action,
                        "confidence": avg_confidence,
                        "reasoning": f"Consensus: {count}/{total_agents} agents agree on {action}",
                        "method": "consensus",
                        "num_agents": total_agents,
                    }

            return {
                "action": "HOLD",
                "confidence": 0.0,
                "reasoning": (
                    f"No consensus reached (BUY:{action_counts['BUY']}, "
                    f"SELL:{action_counts['SELL']}, HOLD:{action_counts['HOLD']})"
                ),
                "method": "consensus",
                "num_agents": total_agents,
            }
        except Exception as e:
            logger.error(f"Error in _consensus_decision: {e}")
            raise

    def _best_agent_decision(self, proposals: List[AgentProposal]) -> Dict:
        """Use decision from best performing agent."""
        try:
            best_proposal = max(proposals, key=lambda p: p.confidence)
            return {
                "action": best_proposal.action,
                "confidence": best_proposal.confidence,
                "reasoning": f"Best agent ({best_proposal.agent_id}): {best_proposal.reasoning}",
                "method": "best_agent",
                "num_agents": len(proposals),
            }
        except Exception as e:
            logger.error(f"Error in _best_agent_decision: {e}")
            raise

    def _ensemble_decision(self, proposals: List[AgentProposal]) -> Dict:
        """Ensemble method combining multiple approaches."""
        try:
            weighted = self._weighted_vote(proposals)
            consensus = self._consensus_decision(proposals)
            best = self._best_agent_decision(proposals)

            if weighted["action"] == consensus["action"] == best["action"]:
                return {
                    "action": weighted["action"],
                    "confidence": 0.9,
                    "reasoning": f"Strong ensemble agreement: {weighted['action']}",
                    "method": "ensemble",
                    "num_agents": len(proposals),
                }

            actions = [weighted["action"], consensus["action"], best["action"]]
            if actions.count(weighted["action"]) >= 2:
                return {
                    "action": weighted["action"],
                    "confidence": 0.7,
                    "reasoning": f"Moderate ensemble agreement: {weighted['action']}",
                    "method": "ensemble",
                    "num_agents": len(proposals),
                }

            return {
                "action": "HOLD",
                "confidence": 0.3,
                "reasoning": "Ensemble disagreement, holding",
                "method": "ensemble",
                "num_agents": len(proposals),
            }
        except Exception as e:
            logger.error(f"Error in _ensemble_decision: {e}")
            raise

    def update_agent_performance(self, agent_id: str, trade_result: Dict):
        """Update performance of specific agent."""
        try:
            if agent_id in self.agents:
                self.agents[agent_id].update_performance(trade_result)
        except Exception as e:
            logger.error(f"Error in update_agent_performance: {e}")
            raise

    def get_agent_rankings(self) -> List[Dict]:
        """Get agents ranked by performance."""
        try:
            rankings = []

            for agent_id, agent in self.agents.items():
                metrics = agent.get_performance_metrics()
                rankings.append(
                    {
                        "agent_id": agent_id,
                        "agent_type": agent.agent_type.value,
                        "win_rate": metrics["win_rate"],
                        "total_trades": metrics["total_trades"],
                        "avg_return": metrics["avg_return"],
                        "sharpe_ratio": metrics["sharpe_ratio"],
                    }
                )

            rankings.sort(key=lambda x: x["win_rate"], reverse=True)
            return rankings
        except Exception as e:
            logger.error(f"Error in get_agent_rankings: {e}")
            raise

    def display_agent_performance(self):
        """Display performance of all agents."""
        try:
            logger.info("\n" + "=" * 80)
            logger.info("AGENT PERFORMANCE")
            logger.info("=" * 80)

            rankings = self.get_agent_rankings()

            for i, agent_stats in enumerate(rankings, 1):
                logger.info("%d. %s (%s)", i, agent_stats["agent_id"], agent_stats["agent_type"])
                logger.info("   Win Rate: %.1f%%", agent_stats["win_rate"] * 100)
                logger.info("   Trades: %s", agent_stats["total_trades"])
                logger.info("   Avg Return: $%.2f", agent_stats["avg_return"])
                logger.info("   Sharpe: %.2f", agent_stats["sharpe_ratio"])

            logger.info("=" * 80)
        except Exception as e:
            logger.error(f"Error in display_agent_performance: {e}")
            raise

    def adaptive_weighting(self) -> Dict[str, float]:
        """
        Calculate adaptive weights for agents based on recent performance.
        Better performing agents get higher weights.
        """
        try:
            weights = {}

            for agent_id, agent in self.agents.items():
                metrics = agent.get_performance_metrics()
                if metrics["total_trades"] > 10:
                    weight = 0.5 * metrics["win_rate"] + 0.5 * max(metrics["sharpe_ratio"], 0)
                else:
                    weight = 0.5
                weights[agent_id] = weight

            total_weight = sum(weights.values())
            if total_weight > 0:
                weights = {k: v / total_weight for k, v in weights.items()}

            return weights
        except Exception as e:
            logger.error(f"Error in adaptive_weighting: {e}")
            raise

    def get_interoperability_status(self) -> Dict[str, object]:
        """Expose A2A and world2agent state for diagnostics."""
        latest_snapshot = self.world_bridge.get_latest_snapshot()
        return {
            "registered_agents": self.a2a_bus.list_agents(),
            "message_count": self.a2a_bus.message_count(),
            "decision_count": len(self.decision_history),
            "latest_world_context_id": latest_snapshot.context_id if latest_snapshot else None,
        }
