# AGENT IDENTITY, CAPABILITY SECURITY & MULTI-AGENT ISOLATION
**AlphaAlgo Agent Security Model (UCA-2026)**
**Status:** FACT & EVIDENCE AUDIT
**Date:** 2026-03-30

---

## 1. MULTI-AGENT RESOURCE & STATE SHARING AUDIT

[FACT] Inspection of `trading_bot/agents/multi_agent_debate.py`, `trading_bot/foundation_agents/`, and `trading_bot/core/csc/` reveals shared infrastructure resources across agent routines:
- **Shared Files/Directories:** `temp_hms/`, SQLite databases (`alpha_brain_memory.db`, `perplexity_trading_memory.db`).
- **Shared Memory:** Python heap memory in multi-agent debate threads; shared `private_memory` dict access without cryptographic process boundaries.
- **Shared Queues:** `UnifiedDecisionBus` event priority queues.
- **Shared Credentials:** Direct access to `os.getenv()` in execution/research layers.

[EVIDENCE] Answers to inter-agent capability questions:
1. **Can agents modify each other's state?** Prior to explicit isolation barriers, agents shared in-process references and could modify shared message lists.
2. **Can agents kill each other's processes?** No direct process kill API exists inside agents, but unhandled exceptions could terminate the shared orchestrator loop.
3. **Can agents overwrite files?** Unrestricted disk I/O could allow file overwrites if sandbox gates were bypassed.
4. **Can agents forge identities or messages?** Without payload signing, string-based `sender_name` fields could be spoofed.
5. **Can agents spawn unauthorized instances?** Without allowlisted manifests, agents could instantiate `TradingAgent` objects dynamically.

---

## 2. SIGNED INTER-AGENT MESSAGE PROTOCOL

[PROPOSED DESIGN] All inter-agent communication passed through `UnifiedDecisionBus` or multi-agent debate protocols MUST encapsulate `SignedInterAgentMessage` containing:
1. `sender_id` (str, authenticated agent identity)
2. `sender_version` (str, code/model version)
3. `task_id` (str, active workflow task UUID)
4. `message_id` (str, unique message UUID)
5. `timestamp` (float, UTC timestamp)
6. `causal_parent` (Optional[str], parent message ID)
7. `provenance` (Dict[str, Any], evidence references & observation lineage)
8. `payload_hash` (str, SHA-256 over message body)
9. `capabilities` (List[str], declared agent capabilities)
10. `expiration` (float, UTC expiration timestamp)
11. `signature` (str, HMAC-SHA256 signature using agent session key)

---

## 3. CAPABILITY SECURITY DOMAINS & LEAST PRIVILEGE

[PROPOSED DESIGN] AlphaAlgo strictly segregates capabilities into 6 non-overlapping domains enforcing least privilege:
1. **INTELLIGENCE:** Market observation, signal extraction, reasoning hypothesis generation.
2. **RESEARCH:** Out-of-sample backtesting, strategy candidate formulation, literature synthesis.
3. **GOVERNANCE:** Evolution validation, policy enforcement, promotion gate verification.
4. **RISK:** Risk assessment, exposure monitoring, position size calculation, kill switch triggers.
5. **EXECUTION:** Order building, broker interaction, trade reconciliation.
6. **DEPLOYMENT:** Release candidate packaging, production deployment checks.

*Invariant:* No general-purpose agent shall simultaneously possess memory write access, arbitrary code execution, network egress, credential access, agent spawning, self-modification, deployment, and live trading capabilities.
