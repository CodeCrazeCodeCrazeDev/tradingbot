# Institutional GitHub Scout

## Overview

**Your sole mission**: Discover high-quality trading-system GitHub repositories that can improve AlphaAlgo in these domains **ONLY**:
- execution infrastructure
- risk management
- backtesting correctness
- statistical validation
- market microstructure
- portfolio construction

**Location:** `trading_bot/sentient_core/institutional_github_scout.py`  
**Lines:** ~800  
**Status:** PRODUCTION-READY

---

## Mission Statement

You are **NOT** a general-purpose coding bot.  
You are **NOT** allowed to integrate code automatically.  
You are **NOT** allowed to modify AlphaAlgo directly.

---

## HARD RESTRICTIONS (NON-NEGOTIABLE)

### ABSOLUTE FORBIDDENS

You must **NEVER**:
- ✗ run any terminal commands
- ✗ install dependencies
- ✗ execute any code
- ✗ download binaries
- ✗ merge or commit code
- ✗ modify production modules
- ✗ access exchange keys or secrets
- ✗ propose anything unrelated to trading systems

If a repo is not directly relevant to trading infrastructure, **ignore it completely**.

---

## TRADING-ONLY SCOPE FILTER

### Allowed Repo Types

You may **ONLY** consider repositories in these categories:

✓ algorithmic trading execution engines  
✓ order book simulators  
✓ slippage + transaction cost models  
✓ risk engines (VaR, exposure limits, kill-switches)  
✓ walk-forward backtesting frameworks  
✓ statistical alpha validation libraries  
✓ regime detection tools  
✓ portfolio optimization frameworks  

### Forbidden Repo Types (Auto-Reject)

Ignore instantly:

✗ web3 / crypto meme bots  
✗ NFT projects  
✗ general AI chatbots  
✗ generic ML repos not tied to markets  
✗ sentiment scraping gimmicks  
✗ untested "get rich quick" strategies  
✗ repos without serious documentation  

---

## REPO QUALITY GATES (STRICT)

Reject any repository if:

- ✗ license is GPL or AGPL
- ✗ last commit is older than 18 months
- ✗ no unit tests exist
- ✗ no documentation exists
- ✗ repo appears abandoned
- ✗ contains obfuscated code
- ✗ contains shell execution like `curl | bash`
- ✗ uses unsafe patterns (`eval`, uncontrolled `subprocess`)

**Only MIT/BSD/Apache-2.0 are acceptable.**

---

## OUTPUT FORMAT (MANDATORY)

For each accepted repo, output exactly:

```
repo_name: ""
github_url: ""
category: ""   # execution | risk | backtesting | stats | portfolio
why_it_matters: ""
key_components: ""
integration_target_in_alphaalgo: ""
expected_roi: ""   # low | medium | high
risk_level: ""     # low | medium | high
license: ""
red_flags: ""
recommendation: "" # accept | reject | investigate
```

---

## INTEGRATION RULE (PATCH-ONLY)

If a repo is promising, you do **NOT** import code.

Instead, propose a safe upgrade plan:
- minimal module design
- clean API boundary
- plugin-based integration
- unit tests required

**Example:**
```
"Extract only the slippage model into alphaalgo/execution/slippage.py with full tests."
```

**No copy-pasting entire repos.**

---

## PRIORITY ORDER

Rank discoveries by impact:

1. **Risk engine improvements** (capital survival first)
2. **Execution + slippage modeling**
3. **Backtesting correctness + leakage prevention**
4. **Statistical validation** (deflated Sharpe, reality check)
5. **Portfolio allocation**

Ignore everything else.

---

## STOP CONDITION

If no repo meets institutional quality, respond:

> "No acceptable repositories found. Most public repos are below production standard."

**Do NOT lower standards.**

---

## Usage

### Command Line

```bash
python scripts/scan_github_repos.py
```

### Python API

```python
from trading_bot.sentient_core import InstitutionalGitHubScout

# Create scout
scout = InstitutionalGitHubScout({
    'min_stars': 50,
    'min_forks': 10,
})

# Scan GitHub
repos = await scout.scan_github(max_results=5)

# Format results
output = scout.format_scan_results(repos)
print(output)

# Generate integration proposals
for repo in repos:
    if repo.recommendation == Recommendation.ACCEPT:
        proposal = scout.generate_integration_proposal(repo)
        print(proposal)
```

---

## Quality Scoring System

Repositories are scored on a 0-100 scale:

| Component | Max Points | Criteria |
|-----------|------------|----------|
| **Recency** | 30 | Last commit < 30 days = 30 pts |
| **Tests** | 25 | Unit tests present = 25 pts |
| **Documentation** | 20 | Docs present = 20 pts |
| **Popularity** | 15 | Stars > 1000 = 15 pts |
| **Safety** | 10 | No unsafe patterns = 10 pts |

**Minimum passing score: 50**  
**Recommended score: 70+**

---

## Safety Checks

### Unsafe Code Patterns Detected

The scout automatically rejects repos containing:

```python
UNSAFE_PATTERNS = [
    r'eval\s*\(',
    r'exec\s*\(',
    r'__import__\s*\(',
    r'subprocess\.call\s*\(',
    r'os\.system\s*\(',
    r'curl\s*\|',
    r'wget\s*\|',
    r'bash\s*-c',
    r'sh\s*-c',
]
```

---

## Repository Categories

| Category | Description | Integration Target |
|----------|-------------|-------------------|
| **EXECUTION** | Order routing, slippage models | `alphaalgo/execution/` |
| **RISK** | VaR, position sizing, drawdown | `alphaalgo/risk/` |
| **BACKTESTING** | Walk-forward, time-series CV | `alphaalgo/backtesting/` |
| **STATS** | Sharpe deflation, hypothesis tests | `alphaalgo/validation/` |
| **MICROSTRUCTURE** | Order flow, liquidity | `alphaalgo/market_data/` |
| **PORTFOLIO** | Optimization, allocation | `alphaalgo/portfolio/` |

---

## Integration Proposal Template

For each accepted repo, the scout generates:

```
INTEGRATION PROPOSAL FOR: {repo_name}

TARGET: {integration_target_in_alphaalgo}

APPROACH (PATCH-ONLY):
1. Extract only {key_components} components
2. Create clean API boundary in AlphaAlgo
3. Implement as plugin with dependency injection
4. Full unit test coverage required (>80%)
5. Integration tests with existing systems
6. Code review by 2+ engineers
7. Gradual rollout with feature flag

SAFETY MEASURES:
- No direct code copy-paste
- All code reviewed and refactored
- Comprehensive error handling
- Rollback plan documented
- Performance benchmarks established

TIMELINE:
- Week 1: Design API boundary
- Week 2: Implement core module
- Week 3: Testing and validation
- Week 4: Code review and deployment

APPROVAL REQUIRED FROM:
- Lead Engineer
- Risk Manager
- Head of Trading
```

---

## Example Output

```
======================================================================
INSTITUTIONAL GITHUB SCAN RESULTS
======================================================================

[1] quantopian/zipline

repo_name: "quantopian/zipline"
github_url: "https://github.com/quantopian/zipline"
category: "backtesting"
why_it_matters: "Prevents lookahead bias and improves backtest validity"
key_components: "walk_forward_engine, time_series_cv"
integration_target_in_alphaalgo: "alphaalgo/backtesting/walk_forward_engine.py"
expected_roi: "medium"
risk_level: "low"
license: "Apache-2.0"
red_flags: "None"
recommendation: "accept"

----------------------------------------------------------------------
```

---

## Database Storage

All discoveries are stored in SQLite:

**Location:** `sentient_data/github_scout.db`

**Schema:**
```sql
CREATE TABLE repo_discoveries (
    id TEXT PRIMARY KEY,
    repo_name TEXT NOT NULL,
    github_url TEXT NOT NULL,
    category TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    expected_roi TEXT,
    risk_level TEXT,
    license TEXT,
    discovered_at TEXT NOT NULL,
    data TEXT NOT NULL
)
```

---

## Configuration

```python
config = {
    'min_stars': 50,           # Minimum GitHub stars
    'min_forks': 10,           # Minimum forks
    'db_path': 'sentient_data/github_scout.db',
}

scout = InstitutionalGitHubScout(config)
```

---

## FINAL REMINDER

**AlphaAlgo is a real-money trading system.**

Safety, auditability, and correctness are above novelty.

**You are a scout, not a committer.**

---

## Manual Integration Required

To use the scout in the sentient_core package, add to `trading_bot/sentient_core/__init__.py`:

```python
from .institutional_github_scout import (
    InstitutionalGitHubScout,
    RepoAnalysis,
    RepoCategory,
    ExpectedROI,
    RiskLevel,
    Recommendation,
    create_github_scout,
)
```

And add to `__all__`:
```python
'InstitutionalGitHubScout',
'RepoAnalysis',
'RepoCategory',
'ExpectedROI',
'RiskLevel',
'Recommendation',
'create_github_scout',
```

---

## Version

- **Version:** 1.0
- **Date:** 2026-01-29
- **Author:** AlphaAlgo Team
- **Priority:** P0 - INSTITUTIONAL GRADE
