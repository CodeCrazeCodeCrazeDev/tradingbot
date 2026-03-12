"""
Knowledge Consolidation System

IF I WERE THIS BOT, I WOULD CONSOLIDATE AND MASTER WHAT I LEARN:
- Turn scattered insights into structured knowledge
- Build a hierarchy of skills from basic to advanced
- Track mastery level for each skill
- Reinforce knowledge through spaced repetition
- Connect related concepts into a knowledge graph
- Verify mastery through practical application
- Never forget critical lessons

This is my knowledge mastery engine - it turns learning into permanent capability.
"""

import json
import logging
import sqlite3
import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class KnowledgeLevel(Enum):
    """Levels of knowledge mastery"""
    UNKNOWN = 0          # Never encountered
    AWARE = 1            # Heard of it
    FAMILIAR = 2         # Basic understanding
    COMPETENT = 3        # Can apply in simple cases
    PROFICIENT = 4       # Can apply in complex cases
    EXPERT = 5           # Deep understanding, can teach
    MASTER = 6           # Intuitive mastery, can innovate


class SkillCategory(Enum):
    """Categories of trading skills"""
    MARKET_ANALYSIS = auto()
    TECHNICAL_ANALYSIS = auto()
    RISK_MANAGEMENT = auto()
    POSITION_SIZING = auto()
    ENTRY_TIMING = auto()
    EXIT_TIMING = auto()
    REGIME_DETECTION = auto()
    PSYCHOLOGY = auto()
    EXECUTION = auto()
    PORTFOLIO_MANAGEMENT = auto()


@dataclass
class MasteredSkill:
    """A skill that I have mastered (or am mastering)"""
    skill_id: str
    name: str
    category: SkillCategory
    description: str
    
    # Mastery tracking
    level: KnowledgeLevel
    mastery_score: float  # 0.0 to 1.0
    
    # Evidence of mastery
    successful_applications: int
    failed_applications: int
    last_applied: Optional[datetime]
    
    # Learning history
    times_studied: int
    times_tested: int
    test_pass_rate: float
    
    # Spaced repetition
    next_review: Optional[datetime]
    review_interval_days: int
    ease_factor: float  # SM-2 algorithm
    
    # Connections
    prerequisites: List[str] = field(default_factory=list)
    related_skills: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'skill_id': self.skill_id,
            'name': self.name,
            'category': self.category.name,
            'description': self.description,
            'level': self.level.name,
            'mastery_score': self.mastery_score,
            'successful_applications': self.successful_applications,
            'failed_applications': self.failed_applications,
            'last_applied': self.last_applied.isoformat() if self.last_applied else None,
            'times_studied': self.times_studied,
            'times_tested': self.times_tested,
            'test_pass_rate': self.test_pass_rate,
            'next_review': self.next_review.isoformat() if self.next_review else None,
            'review_interval_days': self.review_interval_days,
            'ease_factor': self.ease_factor,
            'prerequisites': self.prerequisites,
            'related_skills': self.related_skills,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    @property
    def application_success_rate(self) -> float:
        try:
            total = self.successful_applications + self.failed_applications
            return self.successful_applications / total if total > 0 else 0.0
        except Exception as e:
            logger.error(f"Error in application_success_rate: {e}")
            raise
    
    @property
    def needs_review(self) -> bool:
        try:
            if self.next_review is None:
                return True
            return datetime.now() >= self.next_review
        except Exception as e:
            logger.error(f"Error in needs_review: {e}")
            raise


@dataclass
class ConsolidationResult:
    """Result of a knowledge consolidation session"""
    session_id: str
    timestamp: datetime
    
    # What was consolidated
    insights_processed: int
    skills_updated: int
    skills_created: int
    connections_made: int
    
    # Mastery changes
    level_ups: List[Tuple[str, KnowledgeLevel, KnowledgeLevel]]
    level_downs: List[Tuple[str, KnowledgeLevel, KnowledgeLevel]]
    
    # Reviews scheduled
    reviews_scheduled: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat(),
            'insights_processed': self.insights_processed,
            'skills_updated': self.skills_updated,
            'skills_created': self.skills_created,
            'connections_made': self.connections_made,
            'level_ups': [(s, f.name, t.name) for s, f, t in self.level_ups],
            'level_downs': [(s, f.name, t.name) for s, f, t in self.level_downs],
            'reviews_scheduled': self.reviews_scheduled,
        }


class KnowledgeConsolidator:
    """
    My knowledge mastery engine.
    
    IF I WERE THIS BOT, I WOULD:
    1. Convert insights into structured skills
    2. Track mastery level for each skill
    3. Use spaced repetition to reinforce learning
    4. Build connections between related skills
    5. Verify mastery through application
    6. Identify and fill knowledge gaps
    7. Never let critical knowledge decay
    """
    
    # Core trading skills that I should master
    CORE_SKILLS = {
        'trend_identification': {
            'name': 'Trend Identification',
            'category': SkillCategory.TECHNICAL_ANALYSIS,
            'description': 'Ability to identify market trends accurately',
            'prerequisites': [],
        },
        'support_resistance': {
            'name': 'Support/Resistance Levels',
            'category': SkillCategory.TECHNICAL_ANALYSIS,
            'description': 'Identifying key price levels',
            'prerequisites': ['trend_identification'],
        },
        'risk_per_trade': {
            'name': 'Risk Per Trade Management',
            'category': SkillCategory.RISK_MANAGEMENT,
            'description': 'Proper position sizing based on risk',
            'prerequisites': [],
        },
        'stop_loss_placement': {
            'name': 'Stop Loss Placement',
            'category': SkillCategory.RISK_MANAGEMENT,
            'description': 'Optimal stop loss positioning',
            'prerequisites': ['support_resistance', 'risk_per_trade'],
        },
        'entry_timing': {
            'name': 'Entry Timing',
            'category': SkillCategory.ENTRY_TIMING,
            'description': 'Timing entries for optimal risk/reward',
            'prerequisites': ['trend_identification', 'support_resistance'],
        },
        'exit_timing': {
            'name': 'Exit Timing',
            'category': SkillCategory.EXIT_TIMING,
            'description': 'Knowing when to take profits or cut losses',
            'prerequisites': ['entry_timing'],
        },
        'regime_detection': {
            'name': 'Market Regime Detection',
            'category': SkillCategory.REGIME_DETECTION,
            'description': 'Identifying market conditions (trending, ranging, volatile)',
            'prerequisites': ['trend_identification'],
        },
        'volatility_assessment': {
            'name': 'Volatility Assessment',
            'category': SkillCategory.MARKET_ANALYSIS,
            'description': 'Understanding and measuring market volatility',
            'prerequisites': [],
        },
        'position_sizing': {
            'name': 'Dynamic Position Sizing',
            'category': SkillCategory.POSITION_SIZING,
            'description': 'Adjusting position size based on conditions',
            'prerequisites': ['risk_per_trade', 'volatility_assessment'],
        },
        'drawdown_management': {
            'name': 'Drawdown Management',
            'category': SkillCategory.RISK_MANAGEMENT,
            'description': 'Managing and recovering from drawdowns',
            'prerequisites': ['risk_per_trade'],
        },
        'emotional_control': {
            'name': 'Emotional Control',
            'category': SkillCategory.PSYCHOLOGY,
            'description': 'Maintaining discipline during losses and wins',
            'prerequisites': [],
        },
        'patience': {
            'name': 'Trading Patience',
            'category': SkillCategory.PSYCHOLOGY,
            'description': 'Waiting for high-quality setups',
            'prerequisites': ['emotional_control'],
        },
    }
    
    def __init__(self, data_dir: str = "self_mastery_data"):
        try:
            self.data_dir = Path(data_dir)
            self.data_dir.mkdir(parents=True, exist_ok=True)
        
            self.db_path = self.data_dir / "knowledge_consolidation.db"
            self._init_database()
        
            # In-memory skill cache
            self.skills: Dict[str, MasteredSkill] = {}
            self._load_skills()
        
            # Initialize core skills if not present
            self._initialize_core_skills()
        
            logger.info(f"KnowledgeConsolidator initialized with {len(self.skills)} skills")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _init_database(self):
        """Initialize SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS skills (
                    skill_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    level INTEGER DEFAULT 0,
                    mastery_score REAL DEFAULT 0.0,
                    successful_applications INTEGER DEFAULT 0,
                    failed_applications INTEGER DEFAULT 0,
                    last_applied TEXT,
                    times_studied INTEGER DEFAULT 0,
                    times_tested INTEGER DEFAULT 0,
                    test_pass_rate REAL DEFAULT 0.0,
                    next_review TEXT,
                    review_interval_days INTEGER DEFAULT 1,
                    ease_factor REAL DEFAULT 2.5,
                    prerequisites TEXT,
                    related_skills TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
        
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS skill_applications (
                    application_id TEXT PRIMARY KEY,
                    skill_id TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    context TEXT,
                    outcome TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
                )
            ''')
        
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_connections (
                    connection_id TEXT PRIMARY KEY,
                    skill_a TEXT NOT NULL,
                    skill_b TEXT NOT NULL,
                    connection_type TEXT NOT NULL,
                    strength REAL DEFAULT 0.5,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (skill_a) REFERENCES skills(skill_id),
                    FOREIGN KEY (skill_b) REFERENCES skills(skill_id)
                )
            ''')
        
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error in _init_database: {e}")
            raise
    
    def _load_skills(self):
        """Load skills from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        
            cursor.execute('SELECT * FROM skills')
            rows = cursor.fetchall()
            conn.close()
        
            for row in rows:
                skill = MasteredSkill(
                    skill_id=row[0],
                    name=row[1],
                    category=SkillCategory[row[2]],
                    description=row[3] or '',
                    level=KnowledgeLevel(row[4]),
                    mastery_score=row[5],
                    successful_applications=row[6],
                    failed_applications=row[7],
                    last_applied=datetime.fromisoformat(row[8]) if row[8] else None,
                    times_studied=row[9],
                    times_tested=row[10],
                    test_pass_rate=row[11],
                    next_review=datetime.fromisoformat(row[12]) if row[12] else None,
                    review_interval_days=row[13],
                    ease_factor=row[14],
                    prerequisites=json.loads(row[15]) if row[15] else [],
                    related_skills=json.loads(row[16]) if row[16] else [],
                    created_at=datetime.fromisoformat(row[17]),
                    updated_at=datetime.fromisoformat(row[18]),
                )
                self.skills[skill.skill_id] = skill
        except Exception as e:
            logger.error(f"Error in _load_skills: {e}")
            raise
    
    def _initialize_core_skills(self):
        """Initialize core trading skills"""
        try:
            for skill_id, skill_data in self.CORE_SKILLS.items():
                if skill_id not in self.skills:
                    skill = MasteredSkill(
                        skill_id=skill_id,
                        name=skill_data['name'],
                        category=skill_data['category'],
                        description=skill_data['description'],
                        level=KnowledgeLevel.UNKNOWN,
                        mastery_score=0.0,
                        successful_applications=0,
                        failed_applications=0,
                        last_applied=None,
                        times_studied=0,
                        times_tested=0,
                        test_pass_rate=0.0,
                        next_review=datetime.now(),
                        review_interval_days=1,
                        ease_factor=2.5,
                        prerequisites=skill_data.get('prerequisites', []),
                    )
                    self._save_skill(skill)
                    self.skills[skill_id] = skill
        except Exception as e:
            logger.error(f"Error in _initialize_core_skills: {e}")
            raise
    
    def _save_skill(self, skill: MasteredSkill):
        """Save skill to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        
            cursor.execute('''
                INSERT OR REPLACE INTO skills 
                (skill_id, name, category, description, level, mastery_score,
                 successful_applications, failed_applications, last_applied,
                 times_studied, times_tested, test_pass_rate, next_review,
                 review_interval_days, ease_factor, prerequisites, related_skills,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                skill.skill_id,
                skill.name,
                skill.category.name,
                skill.description,
                skill.level.value,
                skill.mastery_score,
                skill.successful_applications,
                skill.failed_applications,
                skill.last_applied.isoformat() if skill.last_applied else None,
                skill.times_studied,
                skill.times_tested,
                skill.test_pass_rate,
                skill.next_review.isoformat() if skill.next_review else None,
                skill.review_interval_days,
                skill.ease_factor,
                json.dumps(skill.prerequisites),
                json.dumps(skill.related_skills),
                skill.created_at.isoformat(),
                skill.updated_at.isoformat(),
            ))
        
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error in _save_skill: {e}")
            raise
    
    def consolidate_from_insights(
        self,
        insights: List[Dict[str, Any]]
    ) -> ConsolidationResult:
        """
        Consolidate insights into structured knowledge.
        This is how I turn learning into permanent skills.
        """
        try:
            session_id = hashlib.md5(
                f"consolidate_{datetime.now().isoformat()}".encode()
            ).hexdigest()[:12]
        
            skills_updated = 0
            skills_created = 0
            connections_made = 0
            level_ups = []
            level_downs = []
        
            for insight in insights:
                # Map insight to relevant skills
                relevant_skills = self._map_insight_to_skills(insight)
            
                for skill_id in relevant_skills:
                    if skill_id in self.skills:
                        # Update existing skill
                        old_level = self.skills[skill_id].level
                        self._update_skill_from_insight(skill_id, insight)
                        new_level = self.skills[skill_id].level
                    
                        if new_level.value > old_level.value:
                            level_ups.append((skill_id, old_level, new_level))
                        elif new_level.value < old_level.value:
                            level_downs.append((skill_id, old_level, new_level))
                    
                        skills_updated += 1
                    else:
                        # Create new skill from insight
                        new_skill = self._create_skill_from_insight(skill_id, insight)
                        if new_skill:
                            self.skills[skill_id] = new_skill
                            self._save_skill(new_skill)
                            skills_created += 1
            
                # Find and create connections
                if len(relevant_skills) > 1:
                    for i, skill_a in enumerate(relevant_skills):
                        for skill_b in relevant_skills[i+1:]:
                            self._create_connection(skill_a, skill_b, 'co_occurrence')
                            connections_made += 1
        
            # Schedule reviews
            reviews_scheduled = self._schedule_reviews()
        
            result = ConsolidationResult(
                session_id=session_id,
                timestamp=datetime.now(),
                insights_processed=len(insights),
                skills_updated=skills_updated,
                skills_created=skills_created,
                connections_made=connections_made,
                level_ups=level_ups,
                level_downs=level_downs,
                reviews_scheduled=reviews_scheduled,
            )
        
            logger.info(f"Consolidation complete: {skills_updated} updated, {skills_created} created")
        
            return result
        except Exception as e:
            logger.error(f"Error in consolidate_from_insights: {e}")
            raise
    
    def _map_insight_to_skills(self, insight: Dict[str, Any]) -> List[str]:
        """Map an insight to relevant skills"""
        try:
            relevant = []
            description = insight.get('description', '').lower()
            recommendation = insight.get('action_recommendation', '').lower()
        
            # Keyword mapping
            keyword_skill_map = {
                'trend': 'trend_identification',
                'support': 'support_resistance',
                'resistance': 'support_resistance',
                'risk': 'risk_per_trade',
                'stop': 'stop_loss_placement',
                'entry': 'entry_timing',
                'exit': 'exit_timing',
                'regime': 'regime_detection',
                'volatility': 'volatility_assessment',
                'position size': 'position_sizing',
                'drawdown': 'drawdown_management',
                'emotion': 'emotional_control',
                'patience': 'patience',
                'overtrad': 'patience',
            }
        
            text = f"{description} {recommendation}"
        
            for keyword, skill_id in keyword_skill_map.items():
                if keyword in text:
                    if skill_id not in relevant:
                        relevant.append(skill_id)
        
            return relevant
        except Exception as e:
            logger.error(f"Error in _map_insight_to_skills: {e}")
            raise
    
    def _update_skill_from_insight(self, skill_id: str, insight: Dict[str, Any]):
        """Update a skill based on an insight"""
        try:
            skill = self.skills[skill_id]
        
            # Update study count
            skill.times_studied += 1
        
            # Update mastery based on insight type
            insight_type = insight.get('insight_type', '')
            confidence = insight.get('confidence', 0.5)
        
            if 'SUCCESS' in insight_type:
                # Positive reinforcement
                skill.mastery_score = min(1.0, skill.mastery_score + 0.05 * confidence)
            elif 'MISTAKE' in insight_type or 'WEAKNESS' in insight_type:
                # Negative feedback - need more practice
                skill.mastery_score = max(0.0, skill.mastery_score - 0.02)
            else:
                # Neutral - slight increase from exposure
                skill.mastery_score = min(1.0, skill.mastery_score + 0.01)
        
            # Update level based on mastery score
            skill.level = self._calculate_level(skill.mastery_score)
        
            skill.updated_at = datetime.now()
            self._save_skill(skill)
        except Exception as e:
            logger.error(f"Error in _update_skill_from_insight: {e}")
            raise
    
    def _create_skill_from_insight(
        self,
        skill_id: str,
        insight: Dict[str, Any]
    ) -> Optional[MasteredSkill]:
        """Create a new skill from an insight"""
        # Determine category from insight
        try:
            description = insight.get('description', '')
        
            category = SkillCategory.MARKET_ANALYSIS  # Default
            if 'risk' in description.lower():
                category = SkillCategory.RISK_MANAGEMENT
            elif 'entry' in description.lower():
                category = SkillCategory.ENTRY_TIMING
            elif 'exit' in description.lower():
                category = SkillCategory.EXIT_TIMING
        
            skill = MasteredSkill(
                skill_id=skill_id,
                name=skill_id.replace('_', ' ').title(),
                category=category,
                description=description[:200],
                level=KnowledgeLevel.AWARE,
                mastery_score=0.1,
                successful_applications=0,
                failed_applications=0,
                last_applied=None,
                times_studied=1,
                times_tested=0,
                test_pass_rate=0.0,
                next_review=datetime.now() + timedelta(days=1),
                review_interval_days=1,
                ease_factor=2.5,
            )
        
            return skill
        except Exception as e:
            logger.error(f"Error in _create_skill_from_insight: {e}")
            raise
    
    def _calculate_level(self, mastery_score: float) -> KnowledgeLevel:
        """Calculate knowledge level from mastery score"""
        try:
            if mastery_score < 0.1:
                return KnowledgeLevel.UNKNOWN
            elif mastery_score < 0.25:
                return KnowledgeLevel.AWARE
            elif mastery_score < 0.4:
                return KnowledgeLevel.FAMILIAR
            elif mastery_score < 0.6:
                return KnowledgeLevel.COMPETENT
            elif mastery_score < 0.8:
                return KnowledgeLevel.PROFICIENT
            elif mastery_score < 0.95:
                return KnowledgeLevel.EXPERT
            else:
                return KnowledgeLevel.MASTER
        except Exception as e:
            logger.error(f"Error in _calculate_level: {e}")
            raise
    
    def _create_connection(self, skill_a: str, skill_b: str, connection_type: str):
        """Create a connection between two skills"""
        try:
            connection_id = hashlib.md5(
                f"{skill_a}_{skill_b}_{connection_type}".encode()
            ).hexdigest()[:12]
        
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        
            cursor.execute('''
                INSERT OR IGNORE INTO knowledge_connections
                (connection_id, skill_a, skill_b, connection_type, strength, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                connection_id,
                skill_a,
                skill_b,
                connection_type,
                0.5,
                datetime.now().isoformat(),
            ))
        
            conn.commit()
            conn.close()
        
            # Update related skills
            if skill_a in self.skills and skill_b not in self.skills[skill_a].related_skills:
                self.skills[skill_a].related_skills.append(skill_b)
                self._save_skill(self.skills[skill_a])
        
            if skill_b in self.skills and skill_a not in self.skills[skill_b].related_skills:
                self.skills[skill_b].related_skills.append(skill_a)
                self._save_skill(self.skills[skill_b])
        except Exception as e:
            logger.error(f"Error in _create_connection: {e}")
            raise
    
    def _schedule_reviews(self) -> int:
        """Schedule reviews using spaced repetition (SM-2 algorithm)"""
        try:
            reviews_scheduled = 0
        
            for skill in self.skills.values():
                if skill.needs_review:
                    # Calculate next review using SM-2
                    if skill.mastery_score >= 0.6:
                        # Good recall - increase interval
                        skill.review_interval_days = int(
                            skill.review_interval_days * skill.ease_factor
                        )
                        skill.ease_factor = min(2.5, skill.ease_factor + 0.1)
                    else:
                        # Poor recall - reset interval
                        skill.review_interval_days = 1
                        skill.ease_factor = max(1.3, skill.ease_factor - 0.2)
                
                    skill.next_review = datetime.now() + timedelta(days=skill.review_interval_days)
                    self._save_skill(skill)
                    reviews_scheduled += 1
        
            return reviews_scheduled
        except Exception as e:
            logger.error(f"Error in _schedule_reviews: {e}")
            raise
    
    def record_application(
        self,
        skill_id: str,
        success: bool,
        context: Dict[str, Any],
        outcome: str
    ):
        """Record when a skill is applied in practice"""
        try:
            if skill_id not in self.skills:
                return
        
            skill = self.skills[skill_id]
        
            # Update application counts
            if success:
                skill.successful_applications += 1
                skill.mastery_score = min(1.0, skill.mastery_score + 0.03)
            else:
                skill.failed_applications += 1
                skill.mastery_score = max(0.0, skill.mastery_score - 0.01)
        
            skill.last_applied = datetime.now()
            skill.level = self._calculate_level(skill.mastery_score)
            skill.updated_at = datetime.now()
        
            self._save_skill(skill)
        
            # Record application
            app_id = hashlib.md5(
                f"{skill_id}_{datetime.now().isoformat()}".encode()
            ).hexdigest()[:12]
        
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        
            cursor.execute('''
                INSERT INTO skill_applications
                (application_id, skill_id, success, context, outcome, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                app_id,
                skill_id,
                1 if success else 0,
                json.dumps(context),
                outcome,
                datetime.now().isoformat(),
            ))
        
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error in record_application: {e}")
            raise
    
    def get_skills_due_for_review(self) -> List[MasteredSkill]:
        """Get skills that need review"""
        return [s for s in self.skills.values() if s.needs_review]
    
    def get_weakest_skills(self, n: int = 5) -> List[MasteredSkill]:
        """Get the N weakest skills that need improvement"""
        try:
            sorted_skills = sorted(
                self.skills.values(),
                key=lambda s: s.mastery_score
            )
            return sorted_skills[:n]
        except Exception as e:
            logger.error(f"Error in get_weakest_skills: {e}")
            raise
    
    def get_strongest_skills(self, n: int = 5) -> List[MasteredSkill]:
        """Get the N strongest skills"""
        try:
            sorted_skills = sorted(
                self.skills.values(),
                key=lambda s: s.mastery_score,
                reverse=True
            )
            return sorted_skills[:n]
        except Exception as e:
            logger.error(f"Error in get_strongest_skills: {e}")
            raise
    
    def get_skill_gaps(self) -> List[str]:
        """Identify skill gaps - prerequisites not met"""
        try:
            gaps = []
        
            for skill in self.skills.values():
                for prereq_id in skill.prerequisites:
                    if prereq_id in self.skills:
                        prereq = self.skills[prereq_id]
                        if prereq.level.value < KnowledgeLevel.COMPETENT.value:
                            gaps.append(prereq_id)
        
            return list(set(gaps))
        except Exception as e:
            logger.error(f"Error in get_skill_gaps: {e}")
            raise
    
    def get_mastery_summary(self) -> Dict[str, Any]:
        """Get summary of knowledge mastery"""
        try:
            total_skills = len(self.skills)
        
            level_counts = defaultdict(int)
            category_scores = defaultdict(list)
        
            for skill in self.skills.values():
                level_counts[skill.level.name] += 1
                category_scores[skill.category.name].append(skill.mastery_score)
        
            category_averages = {
                cat: np.mean(scores) if scores else 0
                for cat, scores in category_scores.items()
            }
        
            overall_mastery = np.mean([s.mastery_score for s in self.skills.values()])
        
            return {
                'total_skills': total_skills,
                'overall_mastery': overall_mastery,
                'level_distribution': dict(level_counts),
                'category_mastery': category_averages,
                'skills_due_review': len(self.get_skills_due_for_review()),
                'skill_gaps': self.get_skill_gaps(),
                'weakest_skills': [s.name for s in self.get_weakest_skills(3)],
                'strongest_skills': [s.name for s in self.get_strongest_skills(3)],
            }
        except Exception as e:
            logger.error(f"Error in get_mastery_summary: {e}")
            raise
    
    def verify_mastery(self, skill_id: str) -> Dict[str, Any]:
        """Verify mastery of a skill through testing"""
        try:
            if skill_id not in self.skills:
                return {'verified': False, 'reason': 'Skill not found'}
        
            skill = self.skills[skill_id]
        
            # Check prerequisites
            for prereq_id in skill.prerequisites:
                if prereq_id in self.skills:
                    prereq = self.skills[prereq_id]
                    if prereq.level.value < KnowledgeLevel.COMPETENT.value:
                        return {
                            'verified': False,
                            'reason': f'Prerequisite {prereq.name} not mastered',
                            'prerequisite_level': prereq.level.name,
                        }
        
            # Check application success rate
            if skill.application_success_rate < 0.6:
                return {
                    'verified': False,
                    'reason': 'Application success rate too low',
                    'success_rate': skill.application_success_rate,
                }
        
            # Check mastery score
            if skill.mastery_score < 0.6:
                return {
                    'verified': False,
                    'reason': 'Mastery score too low',
                    'mastery_score': skill.mastery_score,
                }
        
            return {
                'verified': True,
                'level': skill.level.name,
                'mastery_score': skill.mastery_score,
                'success_rate': skill.application_success_rate,
            }
        except Exception as e:
            logger.error(f"Error in verify_mastery: {e}")
            raise
