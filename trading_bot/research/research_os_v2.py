"""
Research Operating System V2 (Research OS V2)
==============================================
An institutional-grade, highly rigorous quantitative research and execution operating system.
Supports SQL persistence, DAG-based lineage tracking, advanced statistical validation
(Deflated Sharpe Ratio, FDR Benjamini-Hochberg, look-ahead and duplicate filters),
immutable cryptographic peer-review governance logs, and closed-loop evolutionary tournaments.
"""

import os
import json
import sqlite3
import hashlib
import logging
import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from uuid import uuid4

from ..core.unified_registry import registry as unified_registry

logger = logging.getLogger("AlphaAlgo.ResearchOS_V2")

class ResearchWorkspaceV2:
    """
    Authoritative Central Orchestrator for the Quantitative Research Platform (QRP).
    Evolves the existing Research OS into a modular, SQL-persistent, scientifically rigorous OS.
    Registered in the Unified Component Registry under component type 'research_operating_system'.
    """

    def __init__(self, db_path: str = "research.db", target_sharpe: float = 2.0, max_drawdown: float = 8.0) -> None:
        self.db_path = db_path
        self.target_sharpe = target_sharpe
        self.max_drawdown = max_drawdown
        self._init_db()
        self._register_with_unified_registry()
        logger.info(f"ResearchOS-V2: Initialized with database at {self.db_path}")

    # ===========================================================================
    # 1. SQL-Backed Database Initialization & CRUD
    # ===========================================================================

    def _init_db(self) -> None:
        """Initializes all required database tables for institutional storage and governance."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Enable WAL mode for high concurrency
            cursor.execute("PRAGMA journal_mode=WAL;")

            # 1. Projects Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    objective TEXT,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL
                );
            """)

            # 2. Questions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id TEXT PRIMARY KEY,
                    project_id TEXT,
                    question_text TEXT NOT NULL,
                    economic_foundation TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                );
            """)

            # 3. Hypotheses Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hypotheses (
                    id TEXT PRIMARY KEY,
                    question_id TEXT,
                    name TEXT NOT NULL,
                    description TEXT,
                    rationale TEXT,
                    counterparty TEXT,
                    falsifications TEXT, -- JSON list
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (question_id) REFERENCES questions(id)
                );
            """)

            # 4. Datasets Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS datasets (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    path TEXT,
                    hash_value TEXT NOT NULL,
                    num_records INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                );
            """)

            # 5. Features Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS features (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    dataset_id TEXT,
                    formula TEXT,
                    importance_score REAL DEFAULT 0.0,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (dataset_id) REFERENCES datasets(id)
                );
            """)

            # 6. Experiments Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    id TEXT PRIMARY KEY,
                    hypothesis_id TEXT,
                    dataset_id TEXT,
                    parameters TEXT, -- JSON dictionary
                    is_sharpe REAL DEFAULT 0.0,
                    oos_sharpe REAL DEFAULT 0.0,
                    num_bars INTEGER DEFAULT 0,
                    status TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id),
                    FOREIGN KEY (dataset_id) REFERENCES datasets(id)
                );
            """)

            # 7. Validation Reports Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS validation_reports (
                    id TEXT PRIMARY KEY,
                    experiment_id TEXT,
                    deflated_sharpe REAL DEFAULT 0.0,
                    p_value REAL DEFAULT 1.0,
                    is_statistically_significant INTEGER DEFAULT 0,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
                );
            """)

            # 8. Peer Reviews Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS peer_reviews (
                    id TEXT PRIMARY KEY,
                    experiment_id TEXT,
                    checklist_passed INTEGER DEFAULT 0,
                    challenges_json TEXT, -- JSON list
                    verdict TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
                );
            """)

            # 9. Deployments Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deployments (
                    id TEXT PRIMARY KEY,
                    experiment_id TEXT,
                    mode TEXT NOT NULL, -- shadow, paper, live
                    risk_limit_pips REAL DEFAULT 0.0,
                    max_capital_usd REAL DEFAULT 0.0,
                    deployed_at TEXT NOT NULL,
                    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
                );
            """)

            # 10. Performance Reports Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_reports (
                    id TEXT PRIMARY KEY,
                    deployment_id TEXT,
                    total_return_usd REAL DEFAULT 0.0,
                    live_drawdown_pct REAL DEFAULT 0.0,
                    realized_sharpe REAL DEFAULT 0.0,
                    slippage_drag_pips REAL DEFAULT 0.0,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (deployment_id) REFERENCES deployments(id)
                );
            """)

            # 11. Knowledge Entries Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_entries (
                    id TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL, -- hypothesis, experiment, deployment
                    source_id TEXT NOT NULL,
                    lessons_learned TEXT,
                    recommendation TEXT,
                    timestamp TEXT NOT NULL
                );
            """)

            # 12. Immutable Cryptographic Governance Log (Blockchain-style block ledger)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS governance_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL, -- JSON string
                    prev_hash TEXT NOT NULL,
                    block_hash TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
            """)
            conn.commit()

    def _register_with_unified_registry(self) -> None:
        """Self-registers with the Unified Component Registry as the primary research OS."""
        try:
            unified_registry.register(
                name="research_operating_system_v2",
                component=self,
                component_type="research_operating_system",
                metadata={"version": "2.0.0", "persistent": True}
            )
        except Exception as e:
            logger.warning(f"Failed to register ResearchOS-V2 with Unified Registry: {e}")

    # ===========================================================================
    # 2. CRUD APIs for Research Entities
    # ===========================================================================

    def create_project(self, title: str, objective: str) -> Dict[str, Any]:
        proj_id = str(uuid4())
        created_at = datetime.utcnow().isoformat()
        status = "Active"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO projects (id, title, objective, created_at, status) VALUES (?, ?, ?, ?, ?)",
                (proj_id, title, objective, created_at, status)
            )
        return {"id": proj_id, "title": title, "objective": objective, "created_at": created_at, "status": status}

    def formulate_question(self, project_id: str, question: str, foundation: str) -> Dict[str, Any]:
        q_id = str(uuid4())
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO questions (id, project_id, question_text, economic_foundation, timestamp) VALUES (?, ?, ?, ?, ?)",
                (q_id, project_id, question, foundation, timestamp)
            )
        return {"id": q_id, "project_id": project_id, "question_text": question, "economic_foundation": foundation, "timestamp": timestamp}

    def record_hypothesis(self, question_id: str, name: str, description: str, rationale: str, counterparty: str, falsifications: List[str]) -> Dict[str, Any]:
        hyp_id = str(uuid4())
        created_at = datetime.utcnow().isoformat()
        status = "Proposed"
        falsifications_json = json.dumps(falsifications)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO hypotheses (id, question_id, name, description, rationale, counterparty, falsifications, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (hyp_id, question_id, name, description, rationale, counterparty, falsifications_json, status, created_at)
            )
        return {
            "id": hyp_id, "question_id": question_id, "name": name, "description": description,
            "economic_rationale": rationale, "counterparty_profile": counterparty,
            "falsification_conditions": falsifications, "status": status, "created_at": created_at
        }

    def register_dataset(self, name: str, path: str, df: pd.DataFrame) -> Dict[str, Any]:
        dataset_id = str(uuid4())
        created_at = datetime.utcnow().isoformat()
        df_json = json.dumps(df.to_dict(orient="split"), default=str)
        hash_val = hashlib.sha256(df_json.encode("utf-8")).hexdigest()
        num_records = len(df)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO datasets (id, name, path, hash_value, num_records, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (dataset_id, name, path, hash_val, num_records, created_at)
            )
        return {"id": dataset_id, "name": name, "path": path, "hash_value": hash_val, "num_records": num_records, "created_at": created_at}

    def create_feature(self, name: str, dataset_id: str, formula: str, importance_score: float = 0.0) -> Dict[str, Any]:
        feature_id = str(uuid4())
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO features (id, name, dataset_id, formula, importance_score, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (feature_id, name, dataset_id, formula, importance_score, timestamp)
            )
        return {"id": feature_id, "name": name, "dataset_id": dataset_id, "formula": formula, "importance_score": importance_score, "timestamp": timestamp}

    def register_experiment(self, hypothesis_id: str, dataset_id: str, parameters: Dict[str, Any], is_sharpe: float, oos_sharpe: float, num_bars: int) -> Dict[str, Any]:
        exp_id = str(uuid4())
        timestamp = datetime.utcnow().isoformat()
        params_json = json.dumps(parameters)
        status = "Completed"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO experiments (id, hypothesis_id, dataset_id, parameters, is_sharpe, oos_sharpe, num_bars, status, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (exp_id, hypothesis_id, dataset_id, params_json, is_sharpe, oos_sharpe, num_bars, status, timestamp)
            )
        return {
            "id": exp_id, "hypothesis_id": hypothesis_id, "dataset_id": dataset_id, "parameters": parameters,
            "is_sharpe": is_sharpe, "oos_sharpe": oos_sharpe, "num_bars": num_bars, "status": status, "timestamp": timestamp
        }

    # ===========================================================================
    # 3. Deterministic Lineage Tracking (DAG Representation)
    # ===========================================================================

    def get_lineage_graph(self) -> nx.DiGraph:
        """
        Builds a NetworkX Directed Acyclic Graph representing the entire research lineage.
        Nodes map out the pipeline trace from datasets to deployments.
        """
        dag = nx.DiGraph()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Datasets
            cursor.execute("SELECT id, name, hash_value FROM datasets")
            for r in cursor.fetchall():
                dag.add_node(r[0], type="Dataset", name=r[1], hash=r[2])

            # Features
            cursor.execute("SELECT id, name, dataset_id FROM features")
            for r in cursor.fetchall():
                dag.add_node(r[0], type="Feature", name=r[1])
                if r[2]: # Dataset edge
                    dag.add_edge(r[2], r[0], relation="EXTRACTED_FROM")

            # Hypotheses
            cursor.execute("SELECT id, name FROM hypotheses")
            for r in cursor.fetchall():
                dag.add_node(r[0], type="Hypothesis", name=r[1])

            # Experiments
            cursor.execute("SELECT id, hypothesis_id, dataset_id FROM experiments")
            for r in cursor.fetchall():
                dag.add_node(r[0], type="Experiment")
                if r[1]:
                    dag.add_edge(r[1], r[0], relation="TESTED_BY")
                if r[2]:
                    dag.add_edge(r[2], r[0], relation="RUN_ON")

            # Validation Reports
            cursor.execute("SELECT id, experiment_id, deflated_sharpe FROM validation_reports")
            for r in cursor.fetchall():
                dag.add_node(r[0], type="ValidationReport", deflated_sharpe=r[2])
                if r[1]:
                    dag.add_edge(r[1], r[0], relation="VALIDATES")

            # Peer Reviews
            cursor.execute("SELECT id, experiment_id, verdict FROM peer_reviews")
            for r in cursor.fetchall():
                dag.add_node(r[0], type="PeerReview", verdict=r[2])
                if r[1]:
                    dag.add_edge(r[1], r[0], relation="REVIEWS")

            # Deployments
            cursor.execute("SELECT id, experiment_id, mode FROM deployments")
            for r in cursor.fetchall():
                dag.add_node(r[0], type="Deployment", mode=r[2])
                if r[1]:
                    dag.add_edge(r[1], r[0], relation="DEPLOYED_FROM")

            # Performance Reports
            cursor.execute("SELECT id, deployment_id, total_return_usd FROM performance_reports")
            for r in cursor.fetchall():
                dag.add_node(r[0], type="PerformanceReport", total_return=r[2])
                if r[1]:
                    dag.add_edge(r[1], r[0], relation="TRACKS")

        return dag

    def verify_reproducibility_hash(self, dataset_id: str, df: pd.DataFrame) -> bool:
        """Verifies if the current dataset is mathematically identical to the registered version's hash."""
        df_json = json.dumps(df.to_dict(orient="split"), default=str)
        current_hash = hashlib.sha256(df_json.encode("utf-8")).hexdigest()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT hash_value FROM datasets WHERE id = ?", (dataset_id,))
            res = cursor.fetchone()
            if res:
                return res[0] == current_hash
        return False

    # ===========================================================================
    # 4. Advanced Scientific Validation & Anti-Bias Filters
    # ===========================================================================

    def calculate_dsr(self, observed_sr: float, num_trials: int, variance_of_srs: float,
                      skewness: float, kurtosis: float, num_bars: int) -> float:
        """
        Calculates Bailey and Lopez de Prado's Deflated Sharpe Ratio (DSR) to correct for multiple testing.
        Returns the probability (0.0 to 1.0) that the true Sharpe is greater than 0.
        """
        if num_trials <= 1:
            expected_max_sr = 0.0
        else:
            # Euler-Mascheroni approximation for expected max of standard normal variables
            euler_gamma = 0.5772156649
            z = np.sqrt(2 * np.log(num_trials)) - (np.log(np.log(num_trials)) + np.log(4 * np.pi)) / (2 * np.sqrt(2 * np.log(num_trials)))
            expected_max_sr = float(z * np.sqrt(variance_of_srs))

        # Standard deviation of Sharpe Ratio under non-normality
        bars_safe = max(num_bars, 2)
        sr_variance = (1.0 + (1.0 + skewness * observed_sr) * (observed_sr**2 / 4.0) -
                       skewness * (observed_sr**3 / 2.0) + (kurtosis - 1.0) * (observed_sr**4 / 4.0)) / (bars_safe - 1.0)
        sr_std = np.sqrt(max(sr_variance, 1e-8))

        z_stat = (observed_sr - expected_max_sr) / sr_std
        dsr = 0.5 * (1.0 + np.tanh(z_stat / np.sqrt(2.0)))
        return float(dsr)

    def log_validation_report(self, experiment_id: str, observed_sr: float, num_trials: int,
                              variance_of_srs: float, skewness: float, kurtosis: float, num_bars: int) -> Dict[str, Any]:
        """Runs the DSR check and logs the validation report in the persistent store."""
        dsr = self.calculate_dsr(observed_sr, num_trials, variance_of_srs, skewness, kurtosis, num_bars)
        is_sig = dsr >= 0.95 and observed_sr >= self.target_sharpe

        report_id = str(uuid4())
        timestamp = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO validation_reports (id, experiment_id, deflated_sharpe, p_value, is_statistically_significant, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (report_id, experiment_id, dsr, 1.0 - dsr, 1 if is_sig else 0, timestamp)
            )

        return {
            "id": report_id,
            "experiment_id": experiment_id,
            "deflated_sharpe": dsr,
            "p_value": 1.0 - dsr,
            "is_statistically_significant": is_sig,
            "timestamp": timestamp
        }

    @staticmethod
    def validate_temporal_leakage(train_df: pd.DataFrame, test_df: pd.DataFrame, time_col: str = "timestamp") -> bool:
        """
        Checks that no training observation has a timestamp greater than or equal to any test observation's.
        Returns True if clean, False if look-ahead leakage exists.
        """
        if train_df.empty or test_df.empty:
            return True

        # Convert to datetime series
        train_times = pd.to_datetime(train_df[time_col])
        test_times = pd.to_datetime(test_df[time_col])

        # Strict non-overlapping interval: Max train time must be strictly less than Min test time
        return train_times.max() < test_times.min()

    @staticmethod
    def filter_duplicate_samples(train_df: pd.DataFrame, test_df: pd.DataFrame) -> bool:
        """
        Verifies there are no identical overlapping samples across training and test sets.
        Returns True if clean, False if duplicates are present.
        """
        if train_df.empty or test_df.empty:
            return True

        # Drop timezone/unhashable structures for comparison
        train_clean = train_df.drop(columns=["timestamp"], errors="ignore")
        test_clean = test_df.drop(columns=["timestamp"], errors="ignore")

        # Convert to sets of tuples
        train_tuples = set(tuple(x) for x in train_clean.values)
        test_tuples = set(tuple(x) for x in test_clean.values)

        intersection = train_tuples.intersection(test_tuples)
        return len(intersection) == 0

    # ===========================================================================
    # 5. Model Governance (FDR Controls & Append-Only Ledger)
    # ===========================================================================

    @staticmethod
    def apply_benjamini_hochberg(p_values: List[float], q: float = 0.05) -> List[bool]:
        """
        Applies Benjamini-Hochberg False Discovery Rate (FDR) control over a list of p-values.
        Returns a list of booleans indicating significance.
        """
        m = len(p_values)
        if m == 0:
            return []

        # Sort with index tracking
        indexed_p = sorted(enumerate(p_values), key=lambda x: x[1])
        significant_indices = set()

        max_k = -1
        for k, (orig_idx, p_val) in enumerate(indexed_p):
            # BH threshold: (k + 1) / m * q
            threshold = ((k + 1) / m) * q
            if p_val <= threshold:
                max_k = k

        if max_k != -1:
            # Reject null hypotheses for all trials up to max_k
            for k in range(max_k + 1):
                significant_indices.add(indexed_p[k][0])

        return [i in significant_indices for i in range(m)]

    def submit_for_peer_review(self, experiment_id: str, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Runs the checklist challenging look-ahead bias and Sharpe overfitting."""
        challenges = []
        checklist_passed = True

        # Challenge overfitted Sharpe
        if metrics.get("sharpe_ratio", 0.0) > 4.5:
            challenges.append("WARNING: Sharpe > 4.5. High probability of look-ahead leak or cost modeling errors.")
            checklist_passed = False

        # Challenge sample size
        if metrics.get("num_bars", 0) < 100:
            challenges.append("WARNING: Sample size too small (<100 bars) for statistical validation.")
            checklist_passed = False

        # Challenge OOS degradation
        is_sharpe = metrics.get("is_sharpe", 0.0)
        oos_sharpe = metrics.get("oos_sharpe", 0.0)
        if oos_sharpe < is_sharpe * 0.40:
            challenges.append("WARNING: OOS Sharpe degrades by more than 60% compared to In-Sample Sharpe.")
            checklist_passed = False

        verdict = "APPROVED" if checklist_passed else "CONDITIONAL_REVISION"
        if len(challenges) >= 3:
            verdict = "REJECTED"

        review_id = str(uuid4())
        timestamp = datetime.utcnow().isoformat()
        challenges_json = json.dumps(challenges)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO peer_reviews (id, experiment_id, checklist_passed, challenges_json, verdict, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (review_id, experiment_id, 1 if checklist_passed else 0, challenges_json, verdict, timestamp)
            )

        # Log to the immutable tamper-proof cryptographic ledger
        self.append_to_governance_ledger(
            event_type="PEER_REVIEW_DECISION",
            payload={
                "review_id": review_id,
                "experiment_id": experiment_id,
                "verdict": verdict,
                "checklist_passed": checklist_passed,
                "challenges": challenges
            }
        )

        return {
            "id": review_id,
            "experiment_id": experiment_id,
            "checklist_passed": checklist_passed,
            "challenges_documented": challenges,
            "verdict": verdict,
            "timestamp": timestamp
        }

    def append_to_governance_ledger(self, event_type: str, payload: Dict[str, Any]) -> str:
        """
        Appends a record to the append-only cryptographic governance log.
        Creates a linked SHA-256 block hash to prevent tampering.
        """
        event_id = str(uuid4())
        timestamp = datetime.utcnow().isoformat()
        payload_str = json.dumps(payload, sort_keys=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Retrieve the latest block's hash
            cursor.execute("SELECT block_hash FROM governance_log ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            prev_hash = row[0] if row else "GENESIS"

            # Compute current block hash
            hasher = hashlib.sha256()
            hasher.update(event_id.encode("utf-8"))
            hasher.update(event_type.encode("utf-8"))
            hasher.update(payload_str.encode("utf-8"))
            hasher.update(prev_hash.encode("utf-8"))
            hasher.update(timestamp.encode("utf-8"))
            block_hash = hasher.hexdigest()

            cursor.execute(
                "INSERT INTO governance_log (event_id, event_type, payload, prev_hash, block_hash, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (event_id, event_type, payload_str, prev_hash, block_hash, timestamp)
            )
            conn.commit()

        return block_hash

    def verify_governance_ledger(self) -> bool:
        """
        Verifies the absolute cryptographic integrity of the governance ledger.
        Ensures none of the logs have been altered, added, or deleted.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT event_id, event_type, payload, prev_hash, block_hash, timestamp FROM governance_log ORDER BY id ASC")
            rows = cursor.fetchall()

            expected_prev_hash = "GENESIS"
            for row in rows:
                event_id, event_type, payload, prev_hash, block_hash, timestamp = row

                # 1. Verify prev_hash matches expectation
                if prev_hash != expected_prev_hash:
                    logger.error(f"Ledger altered! Expected prev_hash {expected_prev_hash}, got {prev_hash} for event {event_id}")
                    return False

                # 2. Recompute hash
                hasher = hashlib.sha256()
                hasher.update(event_id.encode("utf-8"))
                hasher.update(event_type.encode("utf-8"))
                hasher.update(payload.encode("utf-8"))
                hasher.update(prev_hash.encode("utf-8"))
                hasher.update(timestamp.encode("utf-8"))
                computed_hash = hasher.hexdigest()

                if computed_hash != block_hash:
                    logger.error(f"Ledger tamper detected! Block hash mismatch for event {event_id}")
                    return False

                expected_prev_hash = block_hash

        return True

    # ===========================================================================
    # 6. Bidirectional Production Feedback & Evolution Tournament
    # ===========================================================================

    def trigger_anomaly_alert(self, strategy_id: str, anomaly_type: str, observed: float, limit: float) -> Dict[str, Any]:
        """Detects live degradation and spawns a prioritized remedial research post-mortem idea."""
        proj = self.create_project(
            title=f"Post-Mortem: {strategy_id} {anomaly_type}",
            objective=f"Analyze and remedy performance degradation for {strategy_id}"
        )
        q = self.formulate_question(
            project_id=proj["id"],
            question=f"Why did strategy {strategy_id} trigger {anomaly_type} at observed={observed:.2f} vs limit={limit:.2f}?",
            foundation="Microstructure drift or market regime transition"
        )
        return {
            "project": proj,
            "question": q,
            "observed_value": observed,
            "limit_value": limit,
            "timestamp": proj["created_at"]
        }

    @staticmethod
    def mutate_and_crossover_alpha_weights(parent_a: np.ndarray, parent_b: np.ndarray, mutation_rate: float = 0.1) -> np.ndarray:
        """Applies uniform crossover and Gaussian mutation to combine weight vectors."""
        size = min(len(parent_a), len(parent_b))
        child = np.zeros(size)

        # Crossover
        for i in range(size):
            child[i] = parent_a[i] if np.random.rand() > 0.5 else parent_b[i]

        # Mutate
        for i in range(size):
            if np.random.rand() < mutation_rate:
                child[i] += np.random.normal(0, 0.1)

        return child

    def run_regime_tournament(self, champion_returns: pd.Series, challenger_returns: List[pd.Series],
                              min_oos_bars: int = 100) -> Dict[str, Any]:
        """
        Runs a Sandbox Regime Tournament over out-of-sample data.
        Determines if any challengers statistically outperform the current champion.
        """
        if len(champion_returns) < min_oos_bars:
            return {"status": "FAILED", "reason": f"OOS data size {len(champion_returns)} too small (<{min_oos_bars})"}

        # Compute champion performance
        champ_mean = champion_returns.mean()
        champ_std = champion_returns.std()
        champ_sharpe = (champ_mean / (champ_std + 1e-8)) * np.sqrt(252)

        results = []
        for i, challenger in enumerate(challenger_returns):
            if len(challenger) != len(champion_returns):
                continue
            chal_mean = challenger.mean()
            chal_std = challenger.std()
            chal_sharpe = (chal_mean / (chal_std + 1e-8)) * np.sqrt(252)

            results.append({
                "challenger_idx": i,
                "sharpe": chal_sharpe,
                "outperformed_champion": chal_sharpe > champ_sharpe
            })

        # Sort by Sharpe descending
        results.sort(key=lambda x: x["sharpe"], reverse=True)

        return {
            "status": "COMPLETED",
            "champion_sharpe": champ_sharpe,
            "challengers": results,
            "best_challenger": results[0] if results else None
        }
