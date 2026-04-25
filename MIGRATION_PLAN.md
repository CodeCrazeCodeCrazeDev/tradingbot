# AlphaAlgo Meta-Intelligence Layer Migration Plan

## Executive Summary

This document provides a comprehensive migration plan to align the existing codebase with the AlphaAlgo Meta-Intelligence Layer specification (Section 1-14).

**Status:** Implementation Phase Complete  
**Target Completion:** Q2 2026  
**Risk Level:** High (requires careful staging)

---

## Current State Assessment

### Existing Components (Pre-Migration)

| Component | Status | Compliance Gap |
|-----------|--------|----------------|
| `capability_registry.py` | ✅ Exists | Missing controlled objects schema |
| `capability_distillation.py` | ✅ Exists | Missing Stage 6 (Distill) integration |
| `meta_learning_loop.py` | ✅ Exists | Missing PROFILE, ATTRIBUTE, PRUNE stages |
| `code_evolution_engine.py` | ✅ Exists | No spec alignment |

### New Components (Implemented)

| Component | Spec Section | Status |
|-----------|-------------|--------|
| `capability_ontology.py` | Section 5 | ✅ Complete |
| `controlled_objects.py` | Section 4 | ✅ Complete |
| `global_objective_function.py` | Section 6 | ✅ Complete |
| `execution_stages.py` | Section 7 | ✅ Complete |
| `memory_systems.py` | Section 9 | ✅ Complete |
| `routing_policy.py` | Section 10 | ✅ Complete |
| `fallback_hierarchy.py` | Section 11 | ✅ Complete |
| `output_modes.py` | Section 13 | ✅ Complete |

---

## Compliance Issues Identified

### Critical Issues (Must Fix)

1. **Capability Ontology Missing**
   - **Location:** `capability_registry.py`, `meta_learning_loop.py`
   - **Issue:** Tasks not mapped to CAP-R-01 through CAP-O-07
   - **Risk:** Cannot evaluate capability fit under constraints
   - **Fix:** Integrate `capability_ontology.py`

2. **Controlled Objects Incomplete**
   - **Location:** `capability_registry.py`
   - **Issue:** Missing: version, owner, risk tier, regime, forbidden uses, rollback target
   - **Risk:** Objects ineligible for promotion per Section 4
   - **Fix:** Migrate to `controlled_objects.py` schema

3. **Global Objective Function Missing**
   - **Location:** All evaluation code
   - **Issue:** No task-conditional utility scoring
   - **Risk:** Optimizing for wrong metrics
   - **Fix:** Use `global_objective_function.py`

4. **Execution Stages Incomplete**
   - **Location:** `meta_learning_loop.py`, `capability_distillation.py`
   - **Issue:** Missing PROFILE, DISTILL, ATTRIBUTE, PRUNE
   - **Risk:** Incomplete validation pipeline
   - **Fix:** Integrate `execution_stages.py`

5. **Memory Systems Fragmented**
   - **Location:** Various files
   - **Issue:** No Behavior Library, Failure Library, Distillation Registry
   - **Risk:** Loss of institutional knowledge
   - **Fix:** Migrate to `memory_systems.py`

### Medium Issues (Should Fix)

6. **Fallback Hierarchy Undefined**
   - **Location:** Routing code
   - **Issue:** No structured fallback chains per Section 11
   - **Fix:** Implement `fallback_hierarchy.py`

7. **Standardized Output Missing**
   - **Location:** Assessment code
   - **Issue:** No Section 13 output format
   - **Fix:** Use `output_modes.py`

### Low Issues (Nice to Have)

8. **Code Evolution Engine Unaligned**
   - **Location:** `code_evolution_engine.py`
   - **Issue:** No connection to Meta-Intelligence Layer
   - **Recommendation:** Deprecate or integrate

---

## Migration Phases

### Phase 1: Foundation (Week 1-2)
**Goal:** Deploy new core components without breaking existing code

**Actions:**
1. ✅ Deploy `capability_ontology.py` - All CAP-* definitions
2. ✅ Deploy `controlled_objects.py` - Full object schema
3. ✅ Deploy `global_objective_function.py` - Utility scoring
4. ✅ Deploy `memory_systems.py` - All memory layers
5. Create compatibility layer between old and new registries

**Validation:**
- All imports resolve
- Unit tests pass
- No runtime errors

---

### Phase 2: Execution Pipeline (Week 3-4)
**Goal:** Implement 11-stage execution loop

**Actions:**
1. ✅ Deploy `execution_stages.py` - PROFILE, DISTILL, ATTRIBUTE, PRUNE
2. ✅ Deploy `routing_policy.py` - Runtime selection
3. ✅ Deploy `fallback_hierarchy.py` - Fallback chains
4. ✅ Deploy `output_modes.py` - Standardized reports
5. Integrate with existing distillation pipeline

**Validation:**
- Stage transitions work
- Fallback chains activate correctly
- Reports generate in Section 13 format

---

### Phase 3: Integration (Week 5-6)
**Goal:** Connect new components to existing infrastructure

**Actions:**
1. Migrate `capability_registry.py` → `controlled_objects.py`
2. Update `meta_learning_loop.py` to use new stages
3. Update `capability_distillation.py` for Stage 6 integration
4. Add capability mapping to all task definitions
5. Connect routing to new policy system

**Validation:**
- End-to-end workflow functional
- Performance metrics tracked
- Rollback mechanisms tested

---

### Phase 4: Validation (Week 7-8)
**Goal:** Full system validation and hardening

**Actions:**
1. Run comprehensive test suite
2. Validate all 11 stages
3. Test fallback scenarios
4. Verify memory persistence
5. Check provenance trails

**Validation:**
- 100% spec compliance on critical paths
- All tests passing
- Performance acceptable

---

### Phase 5: Production Cutover (Week 9-10)
**Goal:** Switch production to new system

**Actions:**
1. Blue-green deployment
2. Canary rollout (5% → 25% → 100%)
3. Monitor for 48 hours per stage
4. Keep rollback capability hot
5. Document lessons learned

**Validation:**
- Production traffic successful
- No P0/P1 incidents
- Metrics improved or stable

---

## Data Migration

### Registry Migration

```sql
-- Migration from old capability_registry to new controlled_objects
-- Run during Phase 3

-- 1. Backup existing data
CREATE TABLE capabilities_backup AS SELECT * FROM capabilities;

-- 2. Create new schema
-- See controlled_objects.py for full schema

-- 3. Migrate data
INSERT INTO controlled_objects (
    object_id, version, owner, object_type,
    task_scope, capability_mapping, risk_tier, regime_applicability,
    cost_profile, latency_profile, known_failure_modes,
    forbidden_uses, promotion_status, rollback_target, provenance_trail
)
SELECT 
    capability_id,
    '1.0.0',  -- Default version
    'migration',  -- Default owner
    'specialist_model',  -- Default type
    json_array(task_category),  -- Convert to array
    json_array(task_category),  -- Map to capability (will need manual review)
    CASE 
        WHEN performance_score > 0.9 THEN 'low'
        WHEN performance_score > 0.7 THEN 'medium'
        ELSE 'high'
    END,
    json_array('normal'),  -- Default regime
    json_object(
        'token_cost_per_1k', 0.0,
        'compute_cost_per_hour', 0.0,
        'api_call_cost', 0.0
    ),
    json_object(
        'p50_ms', latency_ms,
        'p95_ms', latency_ms * 1.5,
        'p99_ms', latency_ms * 2.0,
        'max_ms', latency_ms * 3.0,
        'cold_start_ms', latency_ms * 2.0
    ),
    '[]',  -- Empty failure modes
    '[]',  -- Empty forbidden uses
    status,
    NULL,  -- No rollback target yet
    json_array(json_object(
        'timestamp', created_at,
        'stage', 'migration',
        'action', 'data_migration',
        'actor', 'migration_script'
    ))
FROM capabilities;
```

### Memory System Migration

```python
# Migration script for memory systems
# Run during Phase 3

from memory_systems import MemoryManager
from controlled_objects import ControlledObjectRegistry

def migrate_memory():
    # Initialize new systems
    memory = MemoryManager()
    registry = ControlledObjectRegistry()
    
    # Migrate routing history
    old_decisions = load_old_routing_history()
    for decision in old_decisions:
        # Convert to new format
        memory.route_memory.record_performance(
            convert_to_new_format(decision)
        )
    
    # Migrate capability records to behavior library
    for cap in registry.get_all_capabilities():
        behavior = convert_capability_to_behavior(cap)
        memory.behavior_library.store_behavior(behavior)
```

---

## Rollback Plan

### Rollback Triggers

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Error rate spike | >5% for 5 min | Immediate rollback |
| Latency degradation | >50% p95 | Gradual rollback |
| Capability failures | >10% | Pause and assess |
| Data corruption | Any | Immediate rollback |

### Rollback Procedures

1. **Immediate Rollback (< 5 min)**
   ```bash
   # Switch traffic to old system
   ./scripts/emergency_rollback.sh
   ```

2. **Gradual Rollback (5-30 min)**
   ```bash
   # Reduce new system traffic gradually
   ./scripts/gradual_rollback.sh --percentage 50
   ```

3. **Data Rollback (if needed)**
   ```sql
   -- Restore from backup
   DROP TABLE capabilities;
   ALTER TABLE capabilities_backup RENAME TO capabilities;
   ```

---

## Testing Strategy

### Unit Tests

| Component | Coverage Target | Priority |
|-----------|-----------------|----------|
| capability_ontology.py | 100% | P0 |
| controlled_objects.py | 100% | P0 |
| global_objective_function.py | 95% | P0 |
| execution_stages.py | 90% | P1 |
| memory_systems.py | 90% | P1 |
| routing_policy.py | 90% | P1 |
| fallback_hierarchy.py | 95% | P0 |
| output_modes.py | 90% | P1 |

### Integration Tests

1. **End-to-end capability lifecycle**
   - OBSERVE → PROFILE → BENCHMARK → VALIDATE → DEPLOY

2. **Fallback chain activation**
   - Test all failure triggers

3. **Memory system persistence**
   - Verify all memory layers

4. **Attribution accuracy**
   - Confirm causal estimates

### Load Tests

- 10x normal traffic for 1 hour
- Measure latency percentiles
- Check memory usage
- Verify no degradation

---

## Success Criteria

### Phase Completion Criteria

| Phase | Criteria |
|-------|----------|
| 1 | All new components deploy without errors |
| 2 | Stage pipeline executes correctly |
| 3 | Integration tests pass >95% |
| 4 | Full test suite passes |
| 5 | Production metrics stable for 48h |

### Final Success Metrics

| Metric | Target |
|--------|--------|
| Spec compliance | 100% on critical paths |
| Test coverage | >90% |
| Error rate | <0.1% |
| P95 latency | <2000ms |
| Capability promotion rate | >80% pass rate |
| Rollback time | <5 minutes |

---

## Post-Migration

### Monitoring

1. **Real-time dashboards**
   - Stage progression
   - Capability scores
   - Routing decisions
   - Fallback activations

2. **Alerting**
   - Promotion failures
   - Rollback triggers
   - Performance degradation

3. **Reporting**
   - Weekly attribution reports
   - Monthly pruning reviews
   - Quarterly capability audits

### Maintenance

1. **Weekly**
   - Review expired behaviors
   - Check distillation drift
   - Validate fallback chains

2. **Monthly**
   - Pruning cycle
   - Capability revalidation
   - Memory optimization

3. **Quarterly**
   - Full system audit
   - Spec compliance review
   - Architecture evolution planning

---

## Appendix: File Mapping

### New Files (Implemented)

```
trading_bot/neuros_evolution/
├── capability_ontology.py      # Section 5: All CAP-* IDs
├── controlled_objects.py       # Section 4: Full object schema
├── global_objective_function.py # Section 6: Utility scoring
├── execution_stages.py         # Section 7: PROFILE, DISTILL, ATTRIBUTE, PRUNE
├── memory_systems.py           # Section 9: All memory layers
├── routing_policy.py          # Section 10: Runtime selection
├── fallback_hierarchy.py      # Section 11: Fallback chains
└── output_modes.py            # Section 13: Standardized reports
```

### Files Requiring Updates

```
trading_bot/neuros_evolution/
├── capability_registry.py      # Migrate to controlled_objects.py
├── capability_distillation.py  # Add Stage 6 integration
└── meta_learning_loop.py      # Add missing stages
```

---

**End of Migration Plan**
