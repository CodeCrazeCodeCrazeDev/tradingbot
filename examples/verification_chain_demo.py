"""
Decision Verification Chain Demo

Demonstrates the comprehensive verification system that fact-checks
the bot's decisions and prevents hallucinations.

This demo shows:
1. Decision Verification Chain (8 stages)
2. Cross-Source Validation
3. Confidence Calibration
4. Adversarial Self-Questioning
5. Unified Verification Orchestrator

Author: AlphaAlgo Team
Date: 2026-01-28
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.verification import (
    # Decision Verification Chain
    DecisionVerificationChain,
    VerificationStatus,
    HallucinationType,
    # Cross Validator
    CrossValidator,
    SourceOpinion,
    SourceType,
    # Confidence Calibrator
    ConfidenceCalibrator,
    CalibrationStatus,
    # Adversarial Checker
    AdversarialChecker,
    ChallengeLevel,
    CognitiveBias,
    # Orchestrator
    VerificationOrchestrator,
    FinalVerdict,
)


def print_header(title: str):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subheader(title: str):
    """Print a subsection header"""
    print(f"\n--- {title} ---")


async def demo_verification_chain():
    """Demonstrate the Decision Verification Chain"""
    print_header("DECISION VERIFICATION CHAIN DEMO")
    
    # Create verification chain
    chain = DecisionVerificationChain()
    
    # Example decision with some issues
    decision = {
        'id': 'TRADE_001',
        'symbol': 'BTCUSDT',
        'direction': 'BUY',
        'confidence': 0.95,  # Very high - might be overconfident
        'current_price': 45000.0,
        'stop_loss': 44000.0,
        'take_profit': 48000.0,
        'rsi': 75,  # Overbought
        'reasoning': 'Price is going up so we should buy.',  # Weak reasoning
        'risk_reward': 3.0,
    }
    
    # Market data for grounding
    market_data = {
        'price': 45050.0,  # Slightly different from claimed
        'volume': 1000000,
        'timestamp': '2026-01-28T12:00:00Z',
    }
    
    print("\nOriginal Decision:")
    print(f"  Symbol: {decision['symbol']}")
    print(f"  Direction: {decision['direction']}")
    print(f"  Confidence: {decision['confidence']:.1%}")
    print(f"  Price: ${decision['current_price']:,.2f}")
    print(f"  Stop Loss: ${decision['stop_loss']:,.2f}")
    print(f"  Take Profit: ${decision['take_profit']:,.2f}")
    
    # Run verification
    print("\nRunning 8-stage verification chain...")
    result = await chain.verify_decision(decision, market_data)
    
    print_subheader("Verification Results")
    print(f"  Overall Status: {result.overall_status.value.upper()}")
    print(f"  Overall Confidence: {result.overall_confidence:.1%}")
    print(f"  Recommended Action: {result.recommended_action.value}")
    print(f"  Hallucinations Detected: {len(result.hallucinations_detected)}")
    print(f"  Verification Hash: {result.verification_hash[:16]}...")
    print(f"  Duration: {result.total_duration_ms:.2f}ms")
    
    # Show stage results
    print_subheader("Stage Results")
    for stage_result in result.stage_results:
        status = "[PASS]" if stage_result.passed else "[FAIL]"
        print(f"  {status} {stage_result.stage.name}: confidence={stage_result.confidence:.2f}")
        for finding in stage_result.findings[:2]:
            print(f"       - {finding}")
    
    # Show hallucinations if any
    if result.hallucinations_detected:
        print_subheader("Hallucinations Detected")
        for h in result.hallucinations_detected:
            print(f"  [{h.hallucination_type.value}] Severity: {h.severity:.2f}")
            print(f"    Claim: {h.claim}")
            if h.suggested_correction:
                print(f"    Fix: {h.suggested_correction}")
    
    return result


async def demo_cross_validator():
    """Demonstrate Cross-Source Validation"""
    print_header("CROSS-SOURCE VALIDATION DEMO")
    
    validator = CrossValidator()
    
    # Decision to validate
    decision = {
        'direction': 'BUY',
        'confidence': 0.8,
        'rsi': 45,
        'trend': 'UP',
        'volume_ratio': 1.5,
        'sentiment': 0.3,
    }
    
    # Additional source opinions
    sources = [
        SourceOpinion(
            source_name='Technical_MA',
            source_type=SourceType.TECHNICAL,
            direction='BUY',
            confidence=0.75,
            reasoning='Price above 50 MA',
            weight=0.9
        ),
        SourceOpinion(
            source_name='Sentiment_Social',
            source_type=SourceType.SENTIMENT,
            direction='BUY',
            confidence=0.6,
            reasoning='Positive social sentiment',
            weight=0.7
        ),
        SourceOpinion(
            source_name='Pattern_Recognition',
            source_type=SourceType.TECHNICAL,
            direction='SELL',  # Disagrees!
            confidence=0.65,
            reasoning='Bearish divergence detected',
            weight=0.8
        ),
    ]
    
    print("\nValidating decision against multiple sources...")
    result = await validator.validate(decision, sources)
    
    print_subheader("Cross-Validation Results")
    print(f"  Validated: {result.validated}")
    print(f"  Agreement Level: {result.source_agreement.agreement_level.value}")
    print(f"  Agreement Ratio: {result.source_agreement.agreement_ratio:.1%}")
    print(f"  Sources Agreeing: {result.source_agreement.agreeing_sources}/{result.source_agreement.total_sources}")
    print(f"  Adjusted Confidence: {result.adjusted_confidence:.1%}")
    
    if result.warnings:
        print_subheader("Warnings")
        for w in result.warnings:
            print(f"  - {w}")
    
    if result.recommendations:
        print_subheader("Recommendations")
        for r in result.recommendations:
            print(f"  - {r}")
    
    return result


def demo_confidence_calibrator():
    """Demonstrate Confidence Calibration"""
    print_header("CONFIDENCE CALIBRATION DEMO")
    
    calibrator = ConfidenceCalibrator()
    
    # Simulate historical predictions
    print("\nSimulating 50 historical predictions...")
    import random
    random.seed(42)
    
    for _ in range(50):
        # Simulate overconfident predictions
        confidence = random.uniform(0.6, 0.95)
        # Actual accuracy is lower than confidence
        was_correct = random.random() < (confidence * 0.7)
        calibrator.record_outcome(confidence, was_correct, "trade")
    
    # Now calibrate a new prediction
    original_confidence = 0.85
    result = calibrator.calibrate(original_confidence)
    
    print_subheader("Calibration Results")
    print(f"  Original Confidence: {result.original_confidence:.1%}")
    print(f"  Calibrated Confidence: {result.calibrated_confidence:.1%}")
    print(f"  Calibration Status: {result.calibration_status.value}")
    print(f"  Calibration Error: {result.calibration_error:.2f}")
    print(f"  Adjustment Factor: {result.adjustment_factor:.2f}")
    print(f"  Uncertainty Bounds: [{result.uncertainty_bounds[0]:.2f}, {result.uncertainty_bounds[1]:.2f}]")
    
    if result.recommendations:
        print_subheader("Recommendations")
        for r in result.recommendations:
            print(f"  - {r}")
    
    # Show calibration stats
    stats = calibrator.get_calibration_stats()
    print_subheader("Calibration Statistics")
    print(f"  Samples: {stats.get('samples', 0)}")
    print(f"  Overall Accuracy: {stats.get('overall_accuracy', 0):.1%}")
    print(f"  Avg Confidence: {stats.get('avg_confidence', 0):.1%}")
    print(f"  Expected Calibration Error: {stats.get('expected_calibration_error', 0):.3f}")
    
    return result


def demo_adversarial_checker():
    """Demonstrate Adversarial Self-Questioning"""
    print_header("ADVERSARIAL SELF-QUESTIONING DEMO")
    
    checker = AdversarialChecker()
    
    # Decision with potential issues
    decision = {
        'direction': 'BUY',
        'confidence': 0.92,  # Very high
        'leverage': 10,  # High leverage
        'position_size_pct': 25,  # Large position
        'reasoning': 'Everyone is buying and the price is definitely going up. This is a sure thing.',
        'sentiment': 0.9,  # Extreme sentiment
    }
    
    print("\nAnalyzing decision with adversarial techniques...")
    result = checker.analyze(decision)
    
    print_subheader("Adversarial Analysis Results")
    print(f"  Overall Robustness: {result.overall_robustness:.1%}")
    print(f"  Should Proceed: {result.should_proceed}")
    print(f"  Confidence Adjustment: {result.confidence_adjustment:.2f}")
    print(f"  Total Challenges: {len(result.challenges)}")
    print(f"  Biases Detected: {len(result.biases_detected)}")
    
    # Show challenges by level
    print_subheader("Challenges by Severity")
    for level in [ChallengeLevel.CRITICAL, ChallengeLevel.SIGNIFICANT, ChallengeLevel.MODERATE]:
        challenges = [c for c in result.challenges if c.level == level]
        if challenges:
            print(f"\n  {level.value.upper()} ({len(challenges)}):")
            for c in challenges[:2]:
                print(f"    - {c.concern}")
                if c.mitigation:
                    print(f"      Fix: {c.mitigation}")
    
    # Show biases
    if result.biases_detected:
        print_subheader("Cognitive Biases Detected")
        for b in result.biases_detected:
            print(f"  [{b.bias_type.value}] Severity: {b.severity:.2f}")
            print(f"    Evidence: {b.evidence}")
            print(f"    Recommendation: {b.recommendation}")
    
    # Show critical weaknesses
    if result.critical_weaknesses:
        print_subheader("Critical Weaknesses")
        for w in result.critical_weaknesses:
            print(f"  [!] {w}")
    
    return result


async def demo_verification_orchestrator():
    """Demonstrate the Unified Verification Orchestrator"""
    print_header("UNIFIED VERIFICATION ORCHESTRATOR DEMO")
    
    orchestrator = VerificationOrchestrator()
    
    # Complete decision to verify
    decision = {
        'id': 'TRADE_002',
        'symbol': 'EURUSD',
        'direction': 'SELL',
        'confidence': 0.78,
        'current_price': 1.0850,
        'stop_loss': 1.0900,
        'take_profit': 1.0750,
        'rsi': 68,
        'trend': 'DOWN',
        'volume_ratio': 1.2,
        'sentiment': -0.2,
        'reasoning': 'EUR showing weakness against USD. RSI approaching overbought. However, there are risks from upcoming ECB meeting.',
    }
    
    market_data = {
        'price': 1.0852,
        'volume': 500000,
        'spread': 0.0002,
        'timestamp': '2026-01-28T14:00:00Z',
    }
    
    print("\nRunning complete verification pipeline...")
    print("(This runs all 4 verification components)")
    
    result = await orchestrator.verify(decision, market_data)
    
    print_subheader("Final Verdict")
    print(f"  Verdict: {result.final_verdict.value.upper()}")
    print(f"  Final Confidence: {result.final_confidence:.1%}")
    print(f"  Total Hallucinations: {result.total_hallucinations}")
    print(f"  Total Challenges: {result.total_challenges}")
    print(f"  Verification Hash: {result.verification_hash[:16]}...")
    print(f"  Duration: {result.total_duration_ms:.2f}ms")
    
    # Show executive summary
    print_subheader("Executive Summary")
    print(f"  {result.get_executive_summary()}")
    
    # Show component results
    print_subheader("Component Results")
    if result.chain_result:
        print(f"  Chain: {result.chain_result.overall_status.value}")
    if result.cross_validation_result:
        print(f"  Cross-Validation: validated={result.cross_validation_result.validated}")
    if result.calibration_result:
        print(f"  Calibration: {result.calibration_result.calibration_status.value}")
    if result.adversarial_result:
        print(f"  Adversarial: proceed={result.adversarial_result.should_proceed}")
    
    # Show critical issues
    if result.critical_issues:
        print_subheader("Critical Issues")
        for issue in result.critical_issues:
            print(f"  [!] {issue}")
    
    # Show warnings
    if result.warnings:
        print_subheader("Warnings")
        for w in result.warnings[:5]:
            print(f"  - {w}")
    
    # Show recommendations
    if result.recommendations:
        print_subheader("Recommendations")
        for r in result.recommendations[:5]:
            print(f"  - {r}")
    
    # Show modified decision if applicable
    if result.modified_decision:
        print_subheader("Modified Decision")
        print(f"  Original Confidence: {decision['confidence']:.1%}")
        print(f"  Modified Confidence: {result.modified_decision.get('confidence', 0):.1%}")
    
    return result


async def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("  ALPHAALGO DECISION VERIFICATION SYSTEM DEMO")
    print("  Fact-Checking and Hallucination Prevention")
    print("=" * 70)
    
    # Demo 1: Verification Chain
    await demo_verification_chain()
    
    # Demo 2: Cross-Source Validation
    await demo_cross_validator()
    
    # Demo 3: Confidence Calibration
    demo_confidence_calibrator()
    
    # Demo 4: Adversarial Checker
    demo_adversarial_checker()
    
    # Demo 5: Unified Orchestrator
    await demo_verification_orchestrator()
    
    # Final summary
    print_header("DEMO COMPLETE")
    print("""
The Decision Verification System provides:

1. 8-STAGE VERIFICATION CHAIN
   - Data Grounding (verify against market data)
   - Logical Consistency (detect contradictions)
   - Cross-Source Validation (multiple sources)
   - Historical Accuracy (compare with past)
   - Adversarial Questioning (challenge conclusions)
   - Confidence Calibration (match historical accuracy)
   - Reality Anchor (physically possible values)
   - Audit Trail (immutable records)

2. HALLUCINATION TYPES DETECTED
   - Fabricated data points
   - Invented patterns
   - False correlations
   - Overconfident predictions
   - Logical contradictions
   - Temporal impossibilities
   - Magnitude errors

3. COGNITIVE BIAS DETECTION
   - Confirmation bias
   - Recency bias
   - Anchoring
   - Overconfidence
   - Loss aversion
   - Gambler's fallacy
   - Herding

4. ADVERSARIAL TECHNIQUES
   - Devil's Advocate
   - Pre-Mortem Analysis
   - Red Team Thinking
   - Assumption Challenging
   - Contrarian Analysis
   - Black Swan Hunting

USAGE:
    from trading_bot.verification import VerificationOrchestrator
    
    orchestrator = VerificationOrchestrator()
    result = await orchestrator.verify(decision, market_data)
    
    if result.final_verdict == FinalVerdict.APPROVED:
        execute_trade(decision)
    elif result.final_verdict == FinalVerdict.REJECTED:
        log_rejection(result.critical_issues)
    """)


if __name__ == "__main__":
    asyncio.run(main())
