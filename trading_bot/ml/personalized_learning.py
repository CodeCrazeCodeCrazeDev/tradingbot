import logging
logger = logging.getLogger(__name__)
"""Personalized Adaptive Learning Module

This module implements personalized learning systems that adapt to individual
trading preferences, risk tolerance, and performance patterns.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
import json
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from loguru import logger
import numpy
import pandas


class LearningMode(Enum):
    """Learning modes for personalization."""
    CONSERVATIVE = auto()
    BALANCED = auto()
    AGGRESSIVE = auto()
    ADAPTIVE = auto()


class PreferenceType(Enum):
    """Types of user preferences."""
    RISK_TOLERANCE = auto()
    TRADING_STYLE = auto()
    TIME_HORIZON = auto()
    ASSET_PREFERENCE = auto()
    STRATEGY_PREFERENCE = auto()


@dataclass
class UserProfile:
    """User profile for personalized learning."""
    user_id: str
    risk_tolerance: float  # 0.0 to 1.0
    trading_style: str  # 'scalping', 'day_trading', 'swing', 'position'
    time_horizon: str  # 'short', 'medium', 'long'
    preferred_assets: List[str]
    learning_mode: LearningMode
    performance_history: List[Dict[str, Any]] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class LearningSession:
    """Individual learning session data."""
    session_id: str
    user_id: str
    timestamp: datetime
    actions_taken: List[Dict[str, Any]]
    outcomes: List[Dict[str, Any]]
    feedback_score: float
    learning_points: List[str]


@dataclass
class AdaptationRecommendation:
    """Recommendation for strategy adaptation."""
    user_id: str
    recommendation_type: str
    description: str
    confidence: float
    expected_improvement: float
    parameters: Dict[str, Any]
    rationale: str


class PersonalizedLearningSystem:
    """System for personalized adaptive learning."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the personalized learning system.
        
        Args:
            config: Configuration dictionary
        """
        try:
            self.config = config or {}
            self._init_default_config()
        
            # User data
            self.user_profiles: Dict[str, UserProfile] = {}
            self.learning_sessions: Dict[str, List[LearningSession]] = {}
            self.user_clusters: Dict[str, int] = {}
        
            # Learning models
            self.preference_models: Dict[str, Any] = {}
            self.performance_predictors: Dict[str, Any] = {}
        
            # Similarity matrix for collaborative filtering
            self.user_similarity_matrix: Optional[np.ndarray] = None
        
            logger.info("PersonalizedLearningSystem initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _init_default_config(self):
        """Initialize default configuration."""
        try:
            defaults = {
                "min_sessions_for_adaptation": 10,
                "similarity_threshold": 0.7,
                "learning_rate": 0.1,
                "adaptation_frequency_days": 7,
                "max_recommendations": 5,
                "confidence_threshold": 0.6,
                "performance_window_days": 30,
                "clustering_features": [
                    'risk_tolerance', 'avg_trade_duration', 'win_rate', 
                    'profit_factor', 'max_drawdown'
                ]
            }
        
            for key, value in defaults.items():
                if key not in self.config:
                    self.config[key] = value
        except Exception as e:
            logger.error(f"Error in _init_default_config: {e}")
            raise
    
    def create_user_profile(self,
                          user_id: str,
                          risk_tolerance: float,
                          trading_style: str,
                          time_horizon: str,
                          preferred_assets: List[str],
                          initial_preferences: Dict[str, Any] = None) -> UserProfile:
        """Create a new user profile.
        
        Args:
            user_id: User identifier
            risk_tolerance: Risk tolerance (0.0 to 1.0)
            trading_style: Trading style preference
            time_horizon: Investment time horizon
            preferred_assets: List of preferred assets
            initial_preferences: Initial preference settings
            
        Returns:
            Created user profile
        """
        # Determine initial learning mode based on risk tolerance
        try:
            if risk_tolerance <= 0.3:
                learning_mode = LearningMode.CONSERVATIVE
            elif risk_tolerance <= 0.7:
                learning_mode = LearningMode.BALANCED
            else:
                learning_mode = LearningMode.AGGRESSIVE
        
            profile = UserProfile(
                user_id=user_id,
                risk_tolerance=risk_tolerance,
                trading_style=trading_style,
                time_horizon=time_horizon,
                preferred_assets=preferred_assets,
                learning_mode=learning_mode,
                preferences=initial_preferences or {}
            )
        
            self.user_profiles[user_id] = profile
            self.learning_sessions[user_id] = []
        
            logger.info(f"Created user profile for {user_id}")
            return profile
        except Exception as e:
            logger.error(f"Error in create_user_profile: {e}")
            raise
    
    def record_learning_session(self,
                              user_id: str,
                              actions: List[Dict[str, Any]],
                              outcomes: List[Dict[str, Any]],
                              feedback_score: float) -> str:
        """Record a learning session.
        
        Args:
            user_id: User identifier
            actions: Actions taken during session
            outcomes: Outcomes of the actions
            feedback_score: User feedback score (0.0 to 1.0)
            
        Returns:
            Session ID
        """
        try:
            if user_id not in self.user_profiles:
                logger.error(f"User profile not found: {user_id}")
                return ""
        
            session_id = f"{user_id}_{int(datetime.now().timestamp())}"
        
            # Extract learning points from session
            learning_points = self._extract_learning_points(actions, outcomes, feedback_score)
        
            session = LearningSession(
                session_id=session_id,
                user_id=user_id,
                timestamp=datetime.now(),
                actions_taken=actions,
                outcomes=outcomes,
                feedback_score=feedback_score,
                learning_points=learning_points
            )
        
            self.learning_sessions[user_id].append(session)
        
            # Update user profile based on session
            self._update_user_profile(user_id, session)
        
            logger.info(f"Recorded learning session {session_id} for user {user_id}")
            return session_id
        except Exception as e:
            logger.error(f"Error in record_learning_session: {e}")
            raise
    
    def _extract_learning_points(self,
                                actions: List[Dict[str, Any]],
                                outcomes: List[Dict[str, Any]],
                                feedback_score: float) -> List[str]:
        """Extract learning points from a session."""
        try:
            learning_points = []
        
            # Analyze action-outcome pairs
            for action, outcome in zip(actions, outcomes):
                if outcome.get('success', False):
                    if feedback_score > 0.7:
                        learning_points.append(f"Successful {action.get('type', 'action')} with positive feedback")
                    else:
                        learning_points.append(f"Successful {action.get('type', 'action')} but mixed feedback")
                else:
                    learning_points.append(f"Failed {action.get('type', 'action')} - need improvement")
        
            # Overall session assessment
            if feedback_score > 0.8:
                learning_points.append("High satisfaction - continue current approach")
            elif feedback_score < 0.4:
                learning_points.append("Low satisfaction - significant changes needed")
        
            return learning_points
        except Exception as e:
            logger.error(f"Error in _extract_learning_points: {e}")
            raise
    
    def _update_user_profile(self, user_id: str, session: LearningSession):
        """Update user profile based on learning session."""
        try:
            profile = self.user_profiles[user_id]
        
            # Update performance history
            session_performance = {
                'timestamp': session.timestamp.isoformat(),
                'feedback_score': session.feedback_score,
                'actions_count': len(session.actions_taken),
                'success_rate': sum(1 for outcome in session.outcomes 
                                  if outcome.get('success', False)) / len(session.outcomes)
                if session.outcomes else 0.0
            }
        
            profile.performance_history.append(session_performance)
        
            # Keep only recent history
            cutoff_date = datetime.now() - timedelta(days=self.config["performance_window_days"])
            profile.performance_history = [
                perf for perf in profile.performance_history
                if datetime.fromisoformat(perf['timestamp']) >= cutoff_date
            ]
        
            # Adapt learning mode based on recent performance
            if len(profile.performance_history) >= 5:
                recent_scores = [perf['feedback_score'] for perf in profile.performance_history[-5:]]
                avg_score = np.mean(recent_scores)
            
                if avg_score > 0.8 and profile.learning_mode != LearningMode.AGGRESSIVE:
                    # User is doing well, can be more aggressive
                    profile.learning_mode = LearningMode.AGGRESSIVE
                    logger.info(f"Updated {user_id} to aggressive learning mode")
                elif avg_score < 0.4 and profile.learning_mode != LearningMode.CONSERVATIVE:
                    # User struggling, be more conservative
                    profile.learning_mode = LearningMode.CONSERVATIVE
                    logger.info(f"Updated {user_id} to conservative learning mode")
        
            profile.last_updated = datetime.now()
        except Exception as e:
            logger.error(f"Error in _update_user_profile: {e}")
            raise
    
    def generate_personalized_recommendations(self, user_id: str) -> List[AdaptationRecommendation]:
        """Generate personalized recommendations for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of adaptation recommendations
        """
        try:
            if user_id not in self.user_profiles:
                logger.error(f"User profile not found: {user_id}")
                return []
        
            profile = self.user_profiles[user_id]
            sessions = self.learning_sessions.get(user_id, [])
        
            if len(sessions) < self.config["min_sessions_for_adaptation"]:
                return self._generate_initial_recommendations(profile)
        
            recommendations = []
        
            # Performance-based recommendations
            recommendations.extend(self._generate_performance_recommendations(profile, sessions))
        
            # Collaborative filtering recommendations
            recommendations.extend(self._generate_collaborative_recommendations(profile))
        
            # Preference-based recommendations
            recommendations.extend(self._generate_preference_recommendations(profile, sessions))
        
            # Sort by confidence and expected improvement
            recommendations.sort(key=lambda r: (r.confidence * r.expected_improvement), reverse=True)
        
            return recommendations[:self.config["max_recommendations"]]
        except Exception as e:
            logger.error(f"Error in generate_personalized_recommendations: {e}")
            raise
    
    def _generate_initial_recommendations(self, profile: UserProfile) -> List[AdaptationRecommendation]:
        """Generate initial recommendations for new users."""
        try:
            recommendations = []
        
            # Risk-based recommendations
            if profile.risk_tolerance < 0.3:
                recommendations.append(AdaptationRecommendation(
                    user_id=profile.user_id,
                    recommendation_type="risk_management",
                    description="Start with conservative position sizing (1-2% per trade)",
                    confidence=0.8,
                    expected_improvement=0.3,
                    parameters={"position_size_pct": 0.02, "max_risk_per_trade": 0.01},
                    rationale="Low risk tolerance suggests conservative approach"
                ))
        
            # Style-based recommendations
            if profile.trading_style == "scalping":
                recommendations.append(AdaptationRecommendation(
                    user_id=profile.user_id,
                    recommendation_type="strategy_selection",
                    description="Focus on high-frequency, low-risk strategies",
                    confidence=0.7,
                    expected_improvement=0.25,
                    parameters={"strategy_types": ["momentum_scalping", "mean_reversion"]},
                    rationale="Scalping style requires quick execution strategies"
                ))
        
            return recommendations
        except Exception as e:
            logger.error(f"Error in _generate_initial_recommendations: {e}")
            raise
    
    def _generate_performance_recommendations(self,
                                           profile: UserProfile,
                                           sessions: List[LearningSession]) -> List[AdaptationRecommendation]:
        """Generate recommendations based on performance analysis."""
        try:
            recommendations = []
        
            if not profile.performance_history:
                return recommendations
        
            # Analyze recent performance trends
            recent_scores = [perf['feedback_score'] for perf in profile.performance_history[-10:]]
        
            if len(recent_scores) >= 5:
                trend = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]
            
                if trend < -0.1:  # Declining performance
                    recommendations.append(AdaptationRecommendation(
                        user_id=profile.user_id,
                        recommendation_type="strategy_adjustment",
                        description="Reduce trading frequency to improve decision quality",
                        confidence=0.7,
                        expected_improvement=0.4,
                        parameters={"frequency_multiplier": 0.7},
                        rationale="Declining performance suggests overtrading"
                    ))
            
                elif trend > 0.1:  # Improving performance
                    recommendations.append(AdaptationRecommendation(
                        user_id=profile.user_id,
                        recommendation_type="position_sizing",
                        description="Gradually increase position sizes",
                        confidence=0.6,
                        expected_improvement=0.3,
                        parameters={"size_multiplier": 1.2},
                        rationale="Improving performance allows for increased risk"
                    ))
        
            return recommendations
        except Exception as e:
            logger.error(f"Error in _generate_performance_recommendations: {e}")
            raise
    
    def _generate_collaborative_recommendations(self, profile: UserProfile) -> List[AdaptationRecommendation]:
        """Generate recommendations using collaborative filtering."""
        try:
            recommendations = []
        
            # Find similar users
            similar_users = self._find_similar_users(profile.user_id)
        
            if not similar_users:
                return recommendations
        
            # Analyze successful strategies from similar users
            successful_strategies = self._analyze_similar_user_strategies(similar_users)
        
            for strategy, success_rate in successful_strategies.items():
                if success_rate > 0.7:  # High success rate
                    recommendations.append(AdaptationRecommendation(
                        user_id=profile.user_id,
                        recommendation_type="strategy_adoption",
                        description=f"Try {strategy} strategy used successfully by similar traders",
                        confidence=min(0.8, success_rate),
                        expected_improvement=0.2,
                        parameters={"strategy_name": strategy},
                        rationale=f"Similar users achieved {success_rate:.1%} success rate"
                    ))
        
            return recommendations
        except Exception as e:
            logger.error(f"Error in _generate_collaborative_recommendations: {e}")
            raise
    
    def _generate_preference_recommendations(self,
                                          profile: UserProfile,
                                          sessions: List[LearningSession]) -> List[AdaptationRecommendation]:
        """Generate recommendations based on user preferences."""
        try:
            recommendations = []
        
            # Analyze action patterns from sessions
            action_types = {}
            for session in sessions[-20:]:  # Recent sessions
                for action in session.actions_taken:
                    action_type = action.get('type', 'unknown')
                    if action_type not in action_types:
                        action_types[action_type] = {'count': 0, 'total_feedback': 0}
                    action_types[action_type]['count'] += 1
                    action_types[action_type]['total_feedback'] += session.feedback_score
        
            # Recommend more of what works
            for action_type, data in action_types.items():
                if data['count'] >= 3:  # Sufficient data
                    avg_feedback = data['total_feedback'] / data['count']
                    if avg_feedback > 0.7:
                        recommendations.append(AdaptationRecommendation(
                            user_id=profile.user_id,
                            recommendation_type="action_emphasis",
                            description=f"Increase use of {action_type} actions",
                            confidence=min(0.8, avg_feedback),
                            expected_improvement=0.15,
                            parameters={"action_type": action_type, "emphasis_factor": 1.5},
                            rationale=f"High satisfaction ({avg_feedback:.1%}) with this action type"
                        ))
        
            return recommendations
        except Exception as e:
            logger.error(f"Error in _generate_preference_recommendations: {e}")
            raise
    
    def _find_similar_users(self, user_id: str, top_k: int = 5) -> List[str]:
        """Find users similar to the given user."""
        try:
            if user_id not in self.user_profiles:
                return []
        
            target_profile = self.user_profiles[user_id]
            similarities = []
        
            for other_id, other_profile in self.user_profiles.items():
                if other_id == user_id:
                    continue
            
                # Calculate similarity based on profile features
                similarity = self._calculate_user_similarity(target_profile, other_profile)
            
                if similarity >= self.config["similarity_threshold"]:
                    similarities.append((other_id, similarity))
        
            # Sort by similarity and return top k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return [user_id for user_id, _ in similarities[:top_k]]
        except Exception as e:
            logger.error(f"Error in _find_similar_users: {e}")
            raise
    
    def _calculate_user_similarity(self, profile1: UserProfile, profile2: UserProfile) -> float:
        """Calculate similarity between two user profiles."""
        # Feature vector for comparison
        try:
            features1 = [
                profile1.risk_tolerance,
                self._encode_trading_style(profile1.trading_style),
                self._encode_time_horizon(profile1.time_horizon),
                len(profile1.preferred_assets)
            ]
        
            features2 = [
                profile2.risk_tolerance,
                self._encode_trading_style(profile2.trading_style),
                self._encode_time_horizon(profile2.time_horizon),
                len(profile2.preferred_assets)
            ]
        
            # Add performance features if available
            if profile1.performance_history and profile2.performance_history:
                avg_feedback1 = np.mean([p['feedback_score'] for p in profile1.performance_history])
                avg_feedback2 = np.mean([p['feedback_score'] for p in profile2.performance_history])
                features1.append(avg_feedback1)
                features2.append(avg_feedback2)
        
            # Calculate cosine similarity
            features1 = np.array(features1).reshape(1, -1)
            features2 = np.array(features2).reshape(1, -1)
        
            return cosine_similarity(features1, features2)[0][0]
        except Exception as e:
            logger.error(f"Error in _calculate_user_similarity: {e}")
            raise
    
    def _encode_trading_style(self, style: str) -> float:
        """Encode trading style as numeric value."""
        try:
            style_map = {
                'scalping': 0.0,
                'day_trading': 0.33,
                'swing': 0.67,
                'position': 1.0
            }
            return style_map.get(style, 0.5)
        except Exception as e:
            logger.error(f"Error in _encode_trading_style: {e}")
            raise
    
    def _encode_time_horizon(self, horizon: str) -> float:
        """Encode time horizon as numeric value."""
        try:
            horizon_map = {
                'short': 0.0,
                'medium': 0.5,
                'long': 1.0
            }
            return horizon_map.get(horizon, 0.5)
        except Exception as e:
            logger.error(f"Error in _encode_time_horizon: {e}")
            raise
    
    def _analyze_similar_user_strategies(self, similar_users: List[str]) -> Dict[str, float]:
        """Analyze successful strategies from similar users."""
        try:
            strategy_performance = {}
        
            for user_id in similar_users:
                sessions = self.learning_sessions.get(user_id, [])
            
                for session in sessions:
                    for action in session.actions_taken:
                        strategy = action.get('strategy', 'unknown')
                    
                        if strategy not in strategy_performance:
                            strategy_performance[strategy] = {'successes': 0, 'total': 0}
                    
                        strategy_performance[strategy]['total'] += 1
                        if session.feedback_score > 0.6:
                            strategy_performance[strategy]['successes'] += 1
        
            # Calculate success rates
            success_rates = {}
            for strategy, data in strategy_performance.items():
                if data['total'] >= 3:  # Minimum sample size
                    success_rates[strategy] = data['successes'] / data['total']
        
            return success_rates
        except Exception as e:
            logger.error(f"Error in _analyze_similar_user_strategies: {e}")
            raise
    
    def update_user_preferences(self,
                              user_id: str,
                              preference_updates: Dict[str, Any]) -> bool:
        """Update user preferences.
        
        Args:
            user_id: User identifier
            preference_updates: Dictionary of preference updates
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if user_id not in self.user_profiles:
                return False
        
            profile = self.user_profiles[user_id]
        
            # Update profile attributes
            for key, value in preference_updates.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
                else:
                    profile.preferences[key] = value
        
            profile.last_updated = datetime.now()
        
            logger.info(f"Updated preferences for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error in update_user_preferences: {e}")
            raise
    
    def get_learning_insights(self, user_id: str) -> Dict[str, Any]:
        """Get learning insights for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary of learning insights
        """
        try:
            if user_id not in self.user_profiles:
                return {"error": "User not found"}
        
            profile = self.user_profiles[user_id]
            sessions = self.learning_sessions.get(user_id, [])
        
            # Calculate insights
            insights = {
                "user_id": user_id,
                "learning_mode": profile.learning_mode.name,
                "total_sessions": len(sessions),
                "profile_last_updated": profile.last_updated.isoformat()
            }
        
            if profile.performance_history:
                recent_scores = [p['feedback_score'] for p in profile.performance_history[-10:]]
                insights.update({
                    "average_satisfaction": np.mean(recent_scores),
                    "satisfaction_trend": "improving" if len(recent_scores) > 1 and 
                                        recent_scores[-1] > recent_scores[0] else "stable",
                    "performance_consistency": 1.0 - np.std(recent_scores) if len(recent_scores) > 1 else 1.0
                })
        
            if sessions:
                recent_sessions = sessions[-5:]
                all_learning_points = []
                for session in recent_sessions:
                    all_learning_points.extend(session.learning_points)
            
                insights["recent_learning_points"] = all_learning_points[-10:]  # Last 10 points
                insights["learning_velocity"] = len(all_learning_points) / len(recent_sessions)
        
            return insights
        except Exception as e:
            logger.error(f"Error in get_learning_insights: {e}")
            raise
    
    def cluster_users(self) -> Dict[str, List[str]]:
        """Cluster users based on their profiles and performance.
        
        Returns:
            Dictionary mapping cluster IDs to user lists
        """
        try:
            if len(self.user_profiles) < 3:
                return {"cluster_0": list(self.user_profiles.keys())}
        
            # Prepare feature matrix
            features = []
            user_ids = []
        
            for user_id, profile in self.user_profiles.items():
                feature_vector = [
                    profile.risk_tolerance,
                    self._encode_trading_style(profile.trading_style),
                    self._encode_time_horizon(profile.time_horizon),
                    len(profile.preferred_assets)
                ]
            
                # Add performance features if available
                if profile.performance_history:
                    avg_feedback = np.mean([p['feedback_score'] for p in profile.performance_history])
                    feature_vector.append(avg_feedback)
                else:
                    feature_vector.append(0.5)  # Default value
            
                features.append(feature_vector)
                user_ids.append(user_id)
        
            # Standardize features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
        
            # Perform clustering
            n_clusters = min(5, len(self.user_profiles) // 2)  # Reasonable number of clusters
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(features_scaled)
        
            # Group users by cluster
            clusters = {}
            for user_id, cluster_id in zip(user_ids, cluster_labels):
                cluster_key = f"cluster_{cluster_id}"
                if cluster_key not in clusters:
                    clusters[cluster_key] = []
                clusters[cluster_key].append(user_id)
                self.user_clusters[user_id] = cluster_id
        
            logger.info(f"Clustered {len(user_ids)} users into {len(clusters)} clusters")
            return clusters
        except Exception as e:
            logger.error(f"Error in cluster_users: {e}")
            raise
