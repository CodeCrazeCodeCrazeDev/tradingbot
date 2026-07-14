# Engineering Decomposition: SAGE (arXiv:2605.12061)

## Core Hypothesis
RAG is static and flat. Dynamic evidence chains require a self-evolving graph memory substrate where relationships are strengthened by use and pruned by failure.

## Mathematical Formulation
- **Graph Evolution**: $G_{t+1} = G_t \cup \text{Extract}(H) \setminus \text{Prune}(F)$.
- **Retrieval**: Multi-hop path search over $G$ using Graph-FM embeddings.
- **Edge Weight**: $W(e) = \sum \text{Successes} - \lambda \sum \text{Vetoes}$.

## Training Methodology
- **Contrastive Graph Alignment**: Training the Memory Reader to align natural language queries with multi-hop graph sub-structures.
- **GFM-SFT**: Fine-tuning a Graph Foundation Model on evidence recovery tasks.

## Learning Algorithm
- **Graph-Native Reasoning**: Agents traverse the graph to find non-obvious causal links (e.g., "Sector A $\to$ Input B $\to$ Commodity C").
- **Incremental Construction**: The Memory Writer adds nodes/edges in real-time as the agent learns.

## Memory Architecture
Self-evolving Agentic Graph-Memory (the "Substrate").

## Planning Architecture
Structure-aware planning. The agent uses the graph to bound its search space to "causally relevant" market factors.

## Agent Architecture
Graph-integrated agent. Knowledge is state, not just a retrieval target.

## World Model Contribution
Serves as the persistent structural grounding for the world model's causal DAG.

## Self-improvement Contribution
The graph becomes more accurate and efficient the more it is used for trading.

## Failure Modes
- **Semantic Drift**: Nodes being merged incorrectly.
- **Graph Explosion**: Exponential growth of nodes in volatile regimes.

## Scalability Limits
Graph traversal latency for very large networks.

## Computational Complexity
$\mathcal{O}(|V| + |E| \cdot \log |V|)$ for multi-hop retrieval.

## Engineering Tradeoffs
Retrieval precision (graph) vs. simplicity (vector DB).

## Financial Applicability
Mapping the global causal relationship between macro indicators, central bank policy, and asset prices.

## Production Readiness
Medium. Requires high-performance graph database (e.g., RedisGraph, Neo4j) and custom GFM.
