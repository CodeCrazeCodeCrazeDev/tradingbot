"""
Core interfaces and base abstractions for the Scientific Quantitative Research Operating System (Research OS).
These interfaces decouple high-level research business logic from specific library implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np


# =============================================================================
# 1. LITERATURE & OPPORTUNITY DISCOVERY
# =============================================================================

@dataclass
class ResearchPaper:
    """Standardized representation of a discovered scientific paper."""
    paper_id: str
    title: str
    authors: List[str]
    publish_date: Optional[datetime]
    abstract: str
    url: Optional[str] = None
    source_provider: str = "unknown"
    summary: str = ""
    category: str = "general"
    scoring: Dict[str, float] = field(default_factory=dict)  # e.g., expected alpha, complexity, risk
    embeddings: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class EmbeddingProvider(ABC):
    """Abstract interface for text embedding models."""

    @abstractmethod
    def embed(self, text: str) -> np.ndarray:
        """Generate vector embedding for a given text."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate vector embeddings for a list of texts."""
        pass


class DuplicateDetectionProvider(ABC):
    """Abstract interface for duplicate/redundant research detection."""

    @abstractmethod
    def find_duplicates(self, new_paper: ResearchPaper, existing_papers: List[ResearchPaper]) -> List[Tuple[ResearchPaper, float]]:
        """Identify potential duplicates along with similarity scores."""
        pass


class LiteratureDiscoveryProvider(ABC):
    """Abstract interface for literature opportunity search providers (e.g., arXiv, Semantic Scholar)."""

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[ResearchPaper]:
        """Query the search provider for recent quantitative research papers."""
        pass


# =============================================================================
# 2. HYPOTHESIS & STATE REPRESENTATION
# =============================================================================

@dataclass
class HypothesisObject:
    """Scientific representation of a testable quant research hypothesis."""
    hypothesis_id: str
    description: str
    assumptions: List[str]
    market: str
    timeframe: str
    expected_mechanism: str
    measurable_prediction: str
    failure_conditions: List[str]
    lineage_paper_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "draft"  # e.g., draft, testing, validated, rejected
    timestamp: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# 3. DATA PROVIDER & VALIDATION
# =============================================================================

@dataclass
class StandardizedDataset:
    """Standardized dataset containing financial data and associated validation/provenance metadata."""
    dataset_id: str
    asset_class: str  # e.g., Forex, Equity, Crypto
    symbols: List[str]
    timeframe: str
    start_time: datetime
    end_time: datetime
    data: Dict[str, np.ndarray]  # Map of column names (e.g., 'open', 'high', 'close', 'volume') to numpy arrays
    timestamps: np.ndarray  # Array of np.datetime64/int timestamps
    metadata: Dict[str, Any] = field(default_factory=dict)
    provenance: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Dict[str, Any] = field(default_factory=dict)


class DataProvider(ABC):
    """Abstract interface for ingesting financial market datasets."""

    @abstractmethod
    def load_dataset(
        self,
        symbols: List[str],
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        **kwargs
    ) -> StandardizedDataset:
        """Incorporate real or local historical data into a standardized dataset."""
        pass


class DatasetValidator(ABC):
    """Abstract interface for validating quantitative datasets (quality, gaps, look-ahead bias)."""

    @abstractmethod
    def validate(self, dataset: StandardizedDataset) -> Tuple[bool, Dict[str, Any]]:
        """Validate data quality, returning true if acceptable and details of any anomalies."""
        pass


# =============================================================================
# 4. FEATURES & SCORING
# =============================================================================

@dataclass
class EngineeredFeature:
    """Representation of an engineered quantitative feature."""
    feature_id: str
    name: str
    values: np.ndarray
    timestamps: np.ndarray
    dependencies: List[str] = field(default_factory=list)  # features/raw variables needed
    pipeline_code: Optional[str] = None  # Code snippet for reproduction
    metadata: Dict[str, Any] = field(default_factory=dict)


class FeatureScorer(ABC):
    """Abstract interface for feature importance and predictive scoring."""

    @abstractmethod
    def score_features(self, features: List[EngineeredFeature], target: np.ndarray) -> Dict[str, float]:
        """Compute relative importance scores (e.g., Mutual Information, SHAP) for candidates."""
        pass


# =============================================================================
# 5. STATISTICAL VALIDATION
# =============================================================================

class StatisticalTest(ABC):
    """Abstract interface representing a rigorous statistical hypothesis test."""

    @property
    @abstractmethod
    def test_name(self) -> str:
        """Return identifier of the test."""
        pass

    @abstractmethod
    def run_test(self, data: np.ndarray, **kwargs) -> Dict[str, Any]:
        """Run the statistical test, returning a dictionary of metrics, p-value, and decision."""
        pass


# =============================================================================
# 6. ALPHA SIGNAL GENERATION
# =============================================================================

@dataclass
class AlphaSignal:
    """Scientific quant alpha signal representation."""
    alpha_id: str
    hypothesis_id: str
    values: np.ndarray
    timestamps: np.ndarray
    metrics: Dict[str, Any] = field(default_factory=dict)  # IC, turnover, capacity, decay
    lineage_feature_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlphaGenerator(ABC):
    """Abstract interface for generating candidate alpha signals."""

    @abstractmethod
    def generate_alpha(self, dataset: StandardizedDataset, features: List[EngineeredFeature]) -> List[AlphaSignal]:
        """Synthesize features to produce candidate alpha signals."""
        pass


# =============================================================================
# 7. STRATEGY SYNTHESIS & EXECUTION
# =============================================================================

class ResearchStrategy(ABC):
    """Abstract class representing an executable research strategy candidate."""

    @property
    @abstractmethod
    def strategy_id(self) -> str:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def generate_signals(self, dataset: StandardizedDataset) -> np.ndarray:
        """Run strategy logic on a dataset, returning signal arrays (-1 for sell, 1 for buy, 0 for cash)."""
        pass

    @abstractmethod
    def get_lineage(self) -> Dict[str, Any]:
        """Return lineage including hypothesis, papers, features, and model versions."""
        pass


# =============================================================================
# 8. REGISTRIES (SYSTEMS OF RECORD)
# =============================================================================

class ExperimentRegistry(ABC):
    """Registry tracking quantitative experiments for reproducibility."""

    @abstractmethod
    def register_experiment(self, experiment_id: str, experiment_data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        pass


class DatasetRegistry(ABC):
    """Registry tracking datasets, versions, and quality metrics."""

    @abstractmethod
    def register_dataset(self, dataset: StandardizedDataset) -> None:
        pass

    @abstractmethod
    def get_dataset(self, dataset_id: str) -> Optional[StandardizedDataset]:
        pass


class FeatureRegistry(ABC):
    """Registry managing engineered features, genealogies, and retirement history."""

    @abstractmethod
    def register_feature(self, feature: EngineeredFeature) -> None:
        pass

    @abstractmethod
    def get_feature(self, feature_id: str) -> Optional[EngineeredFeature]:
        pass


class ModelRegistry(ABC):
    """Registry for ML/DL models with hyperparameters, metrics, and lineage tracking."""

    @abstractmethod
    def register_model(self, model_id: str, model_data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        pass


class StrategyRegistry(ABC):
    """Registry capturing deployed research strategies, lineage, approvals, and performance."""

    @abstractmethod
    def register_strategy(self, strategy: ResearchStrategy, metadata: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def get_strategy(self, strategy_id: str) -> Optional[Tuple[ResearchStrategy, Dict[str, Any]]]:
        pass


class KnowledgeRegistry(ABC):
    """Registry archiving discoveries, failed hypothesis post-mortems, and general findings."""

    @abstractmethod
    def archive_knowledge(self, key: str, knowledge: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def query_knowledge(self, query: str) -> List[Dict[str, Any]]:
        pass


# =============================================================================
# 9. COGNITIVE REASONING MEMORY (RESEARCH GRAPH)
# =============================================================================

class GraphStore(ABC):
    """Abstract interface representing the cognitive Graph store."""

    @abstractmethod
    def add_node(self, node_id: str, node_type: str, properties: Dict[str, Any]) -> None:
        """Add a research artifact node to the Graph."""
        pass

    @abstractmethod
    def add_edge(self, source_id: str, target_id: str, relationship_type: str, properties: Optional[Dict[str, Any]] = None) -> None:
        """Link two nodes via a scientific relationship."""
        pass

    @abstractmethod
    def query_semantic(self, query_type: str, *args, **kwargs) -> Any:
        """Execute semantic queries such as lineage tracing or contradiction lookup."""
        pass

    @abstractmethod
    def export_graph(self, format_type: str = "json") -> str:
        """Export state to GraphML or JSON representation."""
        pass


# =============================================================================
# 10. ORCHESTRATION & EVENT MANAGEMENT
# =============================================================================

@dataclass
class ResearchEvent:
    """Core operating system event for the Research OS."""
    event_id: str
    event_type: str  # e.g., 'paper_discovered', 'hypothesis_generated', 'backtest_failed'
    source_component: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ResearchOrchestrator(ABC):
    """The central scientific workflow manager and scheduler kernel."""

    @abstractmethod
    def submit_task(self, task_type: str, payload: Dict[str, Any]) -> str:
        """Submit an on-demand task for immediate or async execution."""
        pass

    @abstractmethod
    def start_continuous_mode(self) -> None:
        """Initiate background loops for literature discovery and live strategy drift tracking."""
        pass

    @abstractmethod
    def start_scheduled_mode(self, schedule_type: str) -> None:
        """Execute scheduled periodic quant research loops."""
        pass


# =============================================================================
# PHASE 2 EXTENSIONS: THE RESEARCH INTELLIGENCE LAYER
# =============================================================================

# -----------------------------------------------------------------------------
# P2-1: Experiment OS & Prioritization Abstractions
# -----------------------------------------------------------------------------

@dataclass
class ResearchProposal:
    """Quant research hypothesis proposal with economic and resource estimations."""
    proposal_id: str
    hypothesis_id: str
    estimated_compute_hours: float
    estimated_data_cost: float
    expected_alpha: float
    expected_sharpe_improvement: float
    expected_uncertainty_reduction: float  # Shannon entropy reduction proxy
    confidence: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class SchedulingPolicy(ABC):
    """Pluggable prioritization scheduling policy algorithm interface."""

    @abstractmethod
    def prioritize_queue(self, queue: List[ResearchProposal], available_resources: Dict[str, Any]) -> List[ResearchProposal]:
        """Rank and return prioritised list of Proposals."""
        pass


class ResearchPrioritizationPolicy(ABC):
    """Bayesian Expected Value of Information (EVI) or Knowledge Gradient policy."""

    @abstractmethod
    def score_proposal(self, proposal: ResearchProposal) -> float:
        """Compute relative economic prior score to optimize knowledge gain."""
        pass


class ExperimentScheduler(ABC):
    """Abstract scientific experiment workflow queue, scheduler, and resource allocator."""

    @abstractmethod
    def queue_proposal(self, proposal: ResearchProposal) -> None:
        pass

    @abstractmethod
    def select_next_experiment(self, available_resources: Dict[str, Any]) -> Optional[ResearchProposal]:
        pass

    @abstractmethod
    def get_reproducibility_score(self, experiment_id: str) -> float:
        """Calculates reproducibility score based on seeds, commits, hashes consistency."""
        pass


# -----------------------------------------------------------------------------
# P2-2: Research Marketplace & Multi-Agent Debate
# -----------------------------------------------------------------------------

@dataclass
class ReviewerOpinion:
    """Structured critique output from a quantitative reviewer agent."""
    reviewer_name: str
    persona: str  # e.g., PM, Statistician, Econometrician, Skeptic
    is_approved: bool
    confidence: float  # 0.0 to 1.0
    rationale: str
    objections: List[str]
    evidence_considered: Dict[str, Any]


class ReviewAgent(ABC):
    """Interface representing a specialized quantitative reviewer agent persona."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def persona(self) -> str:
        pass

    @abstractmethod
    def critique(self, hypothesis: HypothesisObject, backtest_results: Dict[str, Any]) -> ReviewerOpinion:
        """Critique the proposal independently based on specialized expertise."""
        pass


# -----------------------------------------------------------------------------
# P2-3: Causal Discovery
# -----------------------------------------------------------------------------

class CausalDiscoveryEngine(ABC):
    """Abstract interface representing a Structural Causal Model (SCM) or causal graph builder."""

    @abstractmethod
    def discover_causal_graph(self, dataset: StandardizedDataset, features: List[EngineeredFeature]) -> Dict[str, Any]:
        """Discover causal pathways across the variable space, returning the causal SCM structure."""
        pass

    @abstractmethod
    def evaluate_counterfactual(self, causal_model: Any, query_variable: str, intervention: Dict[str, float]) -> Dict[str, Any]:
        """Evaluate a 'What if?' counterfactual mathematical scenario."""
        pass


# -----------------------------------------------------------------------------
# P2-4: Active Learning
# -----------------------------------------------------------------------------

class ActiveLearningPolicy(ABC):
    """Abstract active learning policy algorithm to optimize quantitative data acquisition."""

    @abstractmethod
    def select_regime_gaps(self, registered_datasets: List[StandardizedDataset]) -> List[Dict[str, Any]]:
        """Identify zones of high volatility/variance but sparse data coverage (uncertainty zone)."""
        pass


# -----------------------------------------------------------------------------
# P2-5: World Model & Digital Twin Simulator
# -----------------------------------------------------------------------------

class WorldModel(ABC):
    """AlphaAlgo's internal learned latent market structure representation."""

    @abstractmethod
    def predict_latent_states(self, dataset: StandardizedDataset) -> Dict[str, np.ndarray]:
        """Identify current hidden regimes, volatility clustering, and transition matrices."""
        pass


class DigitalTwin(ABC):
    """Execution sandbox that instantiates adversarial scenarios using the World Model."""

    @abstractmethod
    def instantiate_scenario(self, scenario_type: str, baseline_dataset: StandardizedDataset) -> StandardizedDataset:
        """Generate flash crashes, news shocks, spread expansion, or liquidity failures."""
        pass


# -----------------------------------------------------------------------------
# P2-6: Meta-Research Engine & Scientific Decision Intelligence
# -----------------------------------------------------------------------------

@dataclass
class DecisionRecord:
    """Signed, cryptographically structured record capturing a critical system/scientific decision."""
    decision_id: str
    decision_type: str  # e.g., 'accept_hypothesis', 'promote_strategy'
    evidence: Dict[str, Any]
    assumptions: List[str]
    confidence: float
    alternatives_considered: List[str]
    rationale: str
    author: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    signature: str = "signed_v5_superior"
    validation_outcome: Optional[str] = None


class MetaResearchEngine(ABC):
    """Evaluates R&D workflows, reviewer calibration, and optimizes gate thresholds over time."""

    @abstractmethod
    def analyze_reviewer_calibration(self, reviews: List[ReviewerOpinion], strategy_outcomes: Dict[str, float]) -> Dict[str, float]:
        """Compute the calibration scores of reviewers based on live strategy performance."""
        pass

    @abstractmethod
    def optimize_gate_thresholds(self, historical_promotions: List[DecisionRecord], returns: Dict[str, float]) -> Dict[str, float]:
        """Learns and adjusts statistical, alpha, and drawdowns gate thresholds to optimize live Sharpe."""
        pass
