# 1,000 CRITICAL QUESTIONS - PART 4

## SECTION 8: LATENCY, INFRASTRUCTURE & EXECUTION PATHS (Questions 471-530)

### Network Infrastructure

471. What is your network topology, and where are the single points of failure?
472. How do you handle network partitions between components?
473. What happens when network latency spikes unexpectedly?
474. What is your strategy for network redundancy?
475. How do you detect network degradation before it causes problems?
476. What happens when DNS resolution fails?
477. How do you handle network security without adding latency?
478. What is your strategy for handling network congestion?
479. How do you detect when network infrastructure is being attacked?
480. What happens when network failover doesn't work as expected?

### Compute Infrastructure

481. What happens when compute resources are exhausted?
482. How do you handle compute failures during critical operations?
483. What is your strategy for compute redundancy?
484. How do you detect when compute performance is degrading?
485. What happens when compute scaling doesn't happen fast enough?
486. How do you handle compute that is shared with other processes?
487. What is your strategy for handling compute during peak load?
488. How do you detect when compute infrastructure is misconfigured?
489. What happens when compute costs exceed budget?
490. How do you handle compute failures that corrupt state?

### Storage Infrastructure

491. What happens when storage becomes unavailable?
492. How do you handle storage failures during write operations?
493. What is your strategy for storage redundancy?
494. How do you detect when storage performance is degrading?
495. What happens when storage capacity is exhausted?
496. How do you handle storage that is shared with other systems?
497. What is your strategy for handling storage during peak load?
498. How do you detect when storage infrastructure is corrupted?
499. What happens when storage costs exceed budget?
500. How do you handle storage failures that cause data loss?

### Execution Path Optimization

501. What is the critical path for order execution, and how is it optimized?
502. How do you detect when execution path latency increases?
503. What happens when execution path optimization causes bugs?
504. What is your strategy for handling execution path failures?
505. How do you handle execution paths that have variable latency?
506. What happens when execution path components are upgraded?
507. How do you test execution path performance under load?
508. What is your strategy for execution path redundancy?
509. How do you detect when execution path is being throttled?
510. What happens when execution path optimization conflicts with reliability?

### Monitoring Infrastructure

511. What happens when monitoring infrastructure fails?
512. How do you detect when monitoring is missing events?
513. What is your strategy for monitoring the monitors?
514. How do you handle monitoring that creates too much data?
515. What happens when monitoring latency is too high?
516. How do you handle monitoring across distributed components?
517. What is your strategy for monitoring cost management?
518. How do you detect when monitoring is producing false positives?
519. What happens when monitoring alerts are ignored?
520. How do you handle monitoring during system failures?

### Disaster Recovery

521. What is your disaster recovery plan, and when was it last tested?
522. How long does it take to recover from a complete system failure?
523. What happens when disaster recovery procedures fail?
524. What is your strategy for data recovery after a disaster?
525. How do you handle disasters that affect multiple components?
526. What happens when disaster recovery takes longer than market hours?
527. How do you test disaster recovery without causing disruption?
528. What is your strategy for communicating during a disaster?
529. How do you handle disasters that affect your disaster recovery infrastructure?
530. What happens when disaster recovery causes additional problems?

---

## SECTION 9: BACKTESTING FLAWS & SIMULATION LEAKAGE (Questions 531-590)

### Data Leakage

531. How do you ensure no future information leaks into historical simulations?
532. What happens when data leakage is subtle and hard to detect?
533. How do you detect data leakage in feature engineering?
534. What is your strategy for preventing data leakage in cross-validation?
535. How do you handle data leakage from data preprocessing?
536. What happens when data leakage is introduced by third-party libraries?
537. How do you detect data leakage in ensemble methods?
538. What is your strategy for auditing for data leakage?
539. How do you handle data leakage that is discovered after deployment?
540. What happens when data leakage makes strategies look better than they are?

### Survivorship Bias

541. How do you account for delisted securities in backtests?
542. What happens when survivorship bias inflates backtest returns?
543. How do you detect survivorship bias in your data?
544. What is your strategy for obtaining survivorship-bias-free data?
545. How do you handle survivorship bias in alternative data?
546. What happens when survivorship bias affects strategy selection?
547. How do you detect survivorship bias in benchmark comparisons?
548. What is your strategy for adjusting for survivorship bias?
549. How do you handle survivorship bias in factor research?
550. What happens when survivorship bias is impossible to eliminate?

### Transaction Cost Modeling

551. How do you model transaction costs in backtests?
552. What happens when transaction cost models are inaccurate?
553. How do you handle transaction costs that vary over time?
554. What is your strategy for modeling market impact in backtests?
555. How do you detect when transaction cost models are too optimistic?
556. What happens when transaction costs make strategies unprofitable?
557. How do you handle transaction costs for illiquid instruments?
558. What is your strategy for modeling transaction costs across venues?
559. How do you detect when transaction cost assumptions are violated?
560. What happens when transaction costs change after strategy deployment?

### Execution Simulation

561. How do you simulate order execution in backtests?
562. What happens when execution simulation is unrealistic?
563. How do you handle partial fills in backtests?
564. What is your strategy for simulating execution latency?
565. How do you detect when execution simulation is too optimistic?
566. What happens when execution simulation doesn't match live execution?
567. How do you handle execution simulation for different order types?
568. What is your strategy for simulating execution during market stress?
569. How do you detect when execution simulation assumptions are violated?
570. What happens when execution simulation hides strategy weaknesses?

### Market Regime Changes

571. How do you handle market regime changes in backtests?
572. What happens when backtests don't include relevant market regimes?
573. How do you detect when strategies are regime-dependent?
574. What is your strategy for testing across multiple market regimes?
575. How do you handle regime changes that occur during backtests?
576. What happens when future regimes are different from historical regimes?
577. How do you detect when regime assumptions are violated?
578. What is your strategy for regime-adaptive backtesting?
579. How do you handle regimes that have never occurred in your data?
580. What happens when regime detection is unreliable?

### Statistical Validity

581. How do you ensure backtest results are statistically significant?
582. What happens when backtest results are due to chance?
583. How do you handle multiple hypothesis testing in strategy research?
584. What is your strategy for avoiding p-hacking in backtests?
585. How do you detect when backtest results are overfitted?
586. What happens when statistical tests give conflicting results?
587. How do you handle backtests with limited data?
588. What is your strategy for out-of-sample validation?
589. How do you detect when statistical assumptions are violated?
590. What happens when backtest confidence intervals are too wide?

---

## SECTION 10: LIVE TRADING VS RESEARCH DIVERGENCE (Questions 591-650)

### Implementation Differences

591. How do you ensure research code matches production code?
592. What happens when research and production implementations diverge?
593. How do you detect implementation differences that affect performance?
594. What is your strategy for maintaining code parity?
595. How do you handle research code that cannot be productionized?
596. What happens when production constraints require different implementations?
597. How do you test for implementation equivalence?
598. What is your strategy for managing research vs. production codebases?
599. How do you detect when implementation differences cause losses?
600. What happens when fixing implementation differences breaks other things?

### Data Differences

601. How do you ensure research data matches production data?
602. What happens when research and production data sources differ?
603. How do you detect data differences that affect performance?
604. What is your strategy for maintaining data parity?
605. How do you handle research data that is not available in production?
606. What happens when production data quality is worse than research data?
607. How do you test for data equivalence?
608. What is your strategy for managing research vs. production data pipelines?
609. How do you detect when data differences cause losses?
610. What happens when fixing data differences is not possible?

### Timing Differences

611. How do you handle timing differences between research and production?
612. What happens when research assumes instantaneous execution?
613. How do you detect timing differences that affect performance?
614. What is your strategy for realistic timing in research?
615. How do you handle research that ignores market microstructure timing?
616. What happens when production timing is worse than research assumptions?
617. How do you test for timing equivalence?
618. What is your strategy for managing timing assumptions?
619. How do you detect when timing differences cause losses?
620. What happens when timing differences cannot be eliminated?

### Execution Differences

621. How do you handle execution differences between research and production?
622. What happens when research assumes perfect execution?
623. How do you detect execution differences that affect performance?
624. What is your strategy for realistic execution in research?
625. How do you handle research that ignores execution constraints?
626. What happens when production execution is worse than research assumptions?
627. How do you test for execution equivalence?
628. What is your strategy for managing execution assumptions?
629. How do you detect when execution differences cause losses?
630. What happens when execution differences cannot be eliminated?

### Environment Differences

631. How do you handle environment differences between research and production?
632. What happens when research environment doesn't match production?
633. How do you detect environment differences that affect performance?
634. What is your strategy for production-like research environments?
635. How do you handle research that requires resources not available in production?
636. What happens when production environment constraints affect performance?
637. How do you test for environment equivalence?
638. What is your strategy for managing environment differences?
639. How do you detect when environment differences cause losses?
640. What happens when environment differences cannot be eliminated?

### Behavioral Differences

641. How do you handle behavioral differences between research and production?
642. What happens when research behavior doesn't match production behavior?
643. How do you detect behavioral differences that affect performance?
644. What is your strategy for consistent behavior across environments?
645. How do you handle research that assumes deterministic behavior?
646. What happens when production behavior is non-deterministic?
647. How do you test for behavioral equivalence?
648. What is your strategy for managing behavioral differences?
649. How do you detect when behavioral differences cause losses?
650. What happens when behavioral differences cannot be eliminated?
