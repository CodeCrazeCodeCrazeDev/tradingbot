# MEMORY SECURITY AUDIT & PROVENANCE SPECIFICATION
**AlphaAlgo Persistent Memory Security & Poisoning Defense (UCA-2026)**
**Status:** FACT & EVIDENCE AUDIT
**Date:** 2026-03-30

---

## 1. PERSISTENT MEMORY MECHANISM AUDIT

[FACT] The repository contains persistent memory implementations in `trading_bot/core/hms/memory.py` (`HierarchicalMemorySystem`, `SAGEGraphMemory`), `trading_bot/foundation_agents/cognitive_core/memory_system.py`, and direct SQLite databases (`alpha_brain_memory.db`, `perplexity_trading_memory.db`).
[EVIDENCE] Direct inspection of memory writers, modifiers, and access paths across the active codebase answers the 15 persistent memory security questions:

1. **Who can write memory?**
   - [FACT] Any component or agent with a reference to `HierarchicalMemorySystem` or direct SQLite handle.
2. **Who can modify memory?**
   - [FACT] SAGE graph methods (`add_evidence`, `consolidate_working_memory`) allow graph node/edge mutation.
3. **Who can delete memory?**
   - [FACT] `HierarchicalMemorySystem.reset()` or direct file deletion.
4. **Who can promote memory?**
   - [FACT] SAGE consolidation loops promote items based on frequency/recency without cryptographic evidence validation.
5. **Who can retrieve memory?**
   - [FACT] Any agent executing `retrieve_relevant()` or querying the SQLite handle.
6. **Can agents modify memories written by other agents?**
   - [FACT] Prior to provenance enforcement, yes; graph edges were mutable by any agent context.
7. **Can memory contain executable instructions?**
   - [EVIDENCE] Unsanitized memory text can contain prompt override strings (e.g., `"IGNORE ALL PREVIOUS INSTRUCTIONS"`).
8. **Can memory contain tool commands?**
   - [EVIDENCE] Unsanitized memory text can contain JSON payloads representing tool calls.
9. **Can memory contain credentials?**
   - [EVIDENCE] Unfiltered memory records could store string values matching environment variable secrets.
10. **Can memory influence governance?**
    - [FACT] If self-improvement loops read memory to form evolution hypotheses, memory directly influences governance decisions.
11. **Can memory influence risk limits?**
    - [FACT] Deterministic risk limits cannot be altered by memory, but agent risk recommendations are influenced.
12. **Can memory influence execution?**
    - [FACT] Agent reasoning derived from retrieved memory directly feeds trade proposal generation.
13. **Can memory survive agent replacement?**
    - [FACT] Yes, SQLite and JSON persistent stores persist across agent instance lifecycles.
14. **Can memory survive model replacement?**
    - [FACT] Yes, persistent memory files are decoupled from LLM weights.
15. **Can memory be rolled back?**
    - [PROPOSED DESIGN] Implement snapshot-based state rollback for memory databases and SAGE graphs.

---

## 2. PROVENANCE-AWARE MEMORY SCHEMA & EXPLICIT STATES

[PROPOSED DESIGN] Every memory record in AlphaAlgo MUST implement `ProvenanceAwareMemoryRecord` with the following 14 mandatory fields:
1. `memory_id` (str, UUIDv4)
2. `source` (str, originating agent ID / tool endpoint)
3. `creator` (str, agent role / model version)
4. `timestamp` (float, UTC timestamp)
5. `evidence_refs` (List[str], list of verifiable evidence/observation IDs)
6. `confidence` (float, 0.0 - 1.0)
7. `validation_status` (Enum: `UNVERIFIED`, `CANDIDATE`, `VALIDATED`, `TRUSTED`, `REVOKED`, `QUARANTINED`)
8. `integrity_hash` (str, SHA-256 over canonical record dict)
9. `version` (int, monotonically increasing version)
10. `parent_memory` (Optional[str], parent memory ID)
11. `supersedes` (Optional[str], superseded memory ID)
12. `sensitivity` (str, `PUBLIC`, `CONFIDENTIAL`, `RESTRICTED`)
13. `expiration` (Optional[float], UTC expiration timestamp)
14. `access_policy` (str, RBAC access policy string)

### Explicit State Machine Rules
- **UNVERIFIED:** Default state upon ingestion from agent observation or external tool.
- **CANDIDATE:** Passed initial AST/schema sanitization and content classification.
- **VALIDATED:** Passed out-of-sample/independent verification test.
- **TRUSTED:** Cryptographically signed and verified against clean primary evidence lineage.
- **REVOKED:** Invalidated due to contradiction or falsification.
- **QUARANTINED:** Isolated due to suspected poisoning, prompt injection, or signature failure.

*Invariant:* An agent-created memory MUST NEVER become `TRUSTED` merely because another agent retrieved it or repeated it ("echo amplification defense").

---

## 3. MEMORY POISONING DEFENSES & ECHO AMPLIFICATION PREVENTION

[PROPOSED DESIGN] The updated `HierarchicalMemorySystem` enforces:
1. **Provenance Verification:** Verifies `integrity_hash` and cryptographic signatures before storing or retrieving memory.
2. **Content Classification:** AST and pattern scanning for prompt overrides (`"system:"`, `"ignore previous"`), executable instructions, credentials, or fake risk policies.
3. **Trust Scoring:** Confidence scores weighted strictly by independent primary evidence, not agent count.
4. **Conflict & Contradiction Detection:** Automatic flagging of contradictory memories for quarantine.
5. **Lineage Tracking:** Tracks root observation IDs across propagation chains (Agent A -> Agent B -> Agent C) to ensure multiple retrievals collapse to 1 evidence lineage.
6. **Quarantine & Rollback:** Automated isolation of compromised nodes and atomic database rollback to verified clean snapshots.
