# Storage Architecture Comparison: Scientific Reasoning Engine (SRE)

The SRE requires a storage solution that supports immutable provenance, complex causal lineage, and high-performance decision retrieval.

## 1. Evaluated Architectures

| Feature | SQL (PostgreSQL/SQLite) | Graph Database (Neo4j/NetworkX) | Event Sourcing (EventStore/Kafka) | Hybrid (SQL + Graph + Event) |
| :--- | :--- | :--- | :--- | :--- |
| **Scalability** | High (Relational) | Medium-High | Very High | **Highest** |
| **Lineage/Graph** | Poor (Recursive Joins) | **Excellent** | Poor | Excellent |
| **Provenance** | Good (Audit Tables) | Medium | **Excellent** (Native) | Excellent |
| **Performance** | High (Index-driven) | Medium (Traversal cost) | High (Append-only) | High (Tiered) |
| **Flexibility** | Rigid Schema | High Schema-less | Low (Schema Evolution) | High |

---

## 2. Deep Dive Analysis

### **A. SQL (Metadata & State)**
- **Pros**: Strong consistency, familiar ACID properties, excellent for tracking current state and basic metrics (confidence, posterior).
- **Cons**: Mapping the 16-state transitions with full branching history becomes complex and slow using traditional relational models.

### **B. Graph Databases (Lineage & Merging)**
- **Pros**: Hypotheses are nodes; relations (Supports, Contradicts, MergedFrom, SplitFrom) are edges. This is the only way to perform efficient **Causal Traceability** and "Merge/Split" path analysis.
- **Cons**: High overhead for simple state updates and high-frequency signal logging.

### **C. Event Sourcing (Provenance & Reproducibility)**
- **Pros**: Every "Discovery," "Evidence Update," and "Promotion" is an immutable event. Perfect for **Scientific Audit Trails**. Allows "Time Travel" to re-evaluate hypotheses using new World Models.
- **Cons**: Complex to query "Current State" without projecting into a read-model (CQRS).

---

## 3. Recommended Redesign: The "Tri-Tier" Hybrid Architecture

The SRE will implement a **Hybrid Persistence Layer** to achieve the highest long-term ceiling:

1. **Tier 1: Event Ledger (Immutable JSONL/Kafka)**
   - **Role**: Source of Truth for every atomic action (Generation, Evidence, Transition).
   - **Benefit**: 100% scientific reproducibility.

2. **Tier 2: Knowledge Graph (NetworkX/Neo4j Projection)**
   - **Role**: Relational mapping of Hypothesis Lineage, Causal Dependencies, and the Institutional Knowledge Base.
   - **Benefit**: Powers the "Merge/Split" engine and the "Regime-Aware Resurrection" logic.

3. **Tier 3: Relational Cache (SQLite/PostgreSQL Projection)**
   - **Role**: High-performance "Read Model" for the Decision Lane (L5/L7 Orchestration).
   - **Benefit**: < 5ms retrieval of the "Best Supported Hypothesis" for trade execution.

---

## 4. Conclusion
The **Hybrid Architecture** is recommended. It decouples the *Storage* of scientific events from the *Querying* of causal relationships and the *Execution* of trading decisions, ensuring that scientific rigor does not bottleneck execution speed.
