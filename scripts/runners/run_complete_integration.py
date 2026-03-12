#!/usr/bin/env python3
"""
Complete Integration Runner - Integrates ALL 2000+ modules across 170+ packages

This script:
1. Discovers all packages and modules
2. Validates imports and dependencies
3. Loads modules in priority order (Risk first!)
4. Initializes the complete trading system
5. Provides status reporting

Usage:
    python run_complete_integration.py [--mode MODE] [--lazy] [--export]
    
    Modes:
        discover  - Only discover modules (default)
        load      - Discover and load modules
        init      - Discover, load, and initialize
        start     - Full start (discover, load, init, start)
        
    Options:
        --lazy    - Use lazy loading (don't import until needed)
        --export  - Export module inventory to JSON
        --verbose - Show detailed output
"""

import asyncio
import argparse
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from trading_bot.complete_system_integrator import (
    CompleteSystemIntegrator,
    SystemLayer,
    ModuleStatus,
    create_complete_system,
    quick_start,
    LAYER_PRIORITIES
)


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def print_banner():
    """Print startup banner"""
    print("""
================================================================================
                                                                              
      ALPHAALGO TRADING BOT - COMPLETE SYSTEM INTEGRATOR v3.0                 
                       2000+ Modules | 170+ Packages                          
                                                                              
================================================================================
                                                                              
  IMMUTABLE PRINCIPLES:                                                       
  ---------------------                                                       
  1. RISK FIRST: Layer 4 (MSOS) has VETO power over all trades               
  2. HUMAN CONTROL: Human override ALWAYS works                               
  3. FAIL-SAFE: Default to NO TRADE when uncertain                           
  4. SURVIVAL: "AlphaAlgo does not try to win. AlphaAlgo tries to not die."  
                                                                              
  HIERARCHY: CONSTRAINTS > CONTROL > EXPOSURE > STRATEGY > PREDICTION         
                                                                              
================================================================================
    """)


def print_layer_summary(integrator: CompleteSystemIntegrator):
    """Print layer-by-layer summary"""
    print("\n" + "-" * 80)
    print("LAYER SUMMARY")
    print("-" * 80)
    
    # Sort by priority (Risk first!)
    sorted_layers = sorted(
        SystemLayer,
        key=lambda l: -LAYER_PRIORITIES.get(l, 0)
    )
    
    for layer in sorted_layers:
        modules = integrator.get_modules_by_layer(layer)
        priority = LAYER_PRIORITIES.get(layer, 0)
        
        loaded = sum(1 for m in modules if m.status in [ModuleStatus.LOADED, ModuleStatus.INITIALIZED, ModuleStatus.RUNNING])
        errors = sum(1 for m in modules if m.status == ModuleStatus.ERROR)
        
        # Status indicator
        if layer == SystemLayer.RISK_SAFETY:
            indicator = "[!] CRITICAL"
        elif priority >= 8:
            indicator = "[H] HIGH"
        elif priority >= 6:
            indicator = "[M] MEDIUM"
        else:
            indicator = "[N] NORMAL"
        
        print(f"\n  Layer {layer.value}: {layer.name}")
        print(f"    Priority: {priority} ({indicator})")
        print(f"    Modules: {len(modules)} total, {loaded} loaded, {errors} errors")
        
        # Show packages in this layer
        packages = set(m.package for m in modules)
        if len(packages) <= 10:
            print(f"    Packages: {', '.join(sorted(packages))}")
        else:
            print(f"    Packages: {len(packages)} packages")


def print_package_summary(integrator: CompleteSystemIntegrator):
    """Print package summary"""
    print("\n" + "-" * 80)
    print("TOP 20 PACKAGES BY MODULE COUNT")
    print("-" * 80)
    
    # Sort packages by module count
    sorted_packages = sorted(
        integrator.packages.items(),
        key=lambda x: -x[1].file_count
    )[:20]
    
    for name, info in sorted_packages:
        init_status = "Y" if info.has_init else "N"
        print(f"  [{init_status}] {name}: {info.file_count} files ({info.layer.name})")


async def run_discover(integrator: CompleteSystemIntegrator):
    """Run discovery only"""
    print("\n" + "=" * 80)
    print("PHASE 1: DISCOVERY")
    print("=" * 80)
    
    integrator.discover_all_packages()
    integrator.discover_all_modules()
    
    print(f"\n[OK] Discovered {integrator.stats.total_packages} packages")
    print(f"[OK] Discovered {integrator.stats.total_modules} modules")


async def run_load(integrator: CompleteSystemIntegrator, lazy: bool = True):
    """Run loading"""
    print("\n" + "=" * 80)
    print(f"PHASE 2: LOADING (lazy={lazy})")
    print("=" * 80)
    
    results = await integrator.load_all_modules(lazy=lazy)
    
    success = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    
    print(f"\n[OK] Registered {integrator.stats.registered} modules")
    if not lazy:
        print(f"[OK] Loaded {integrator.stats.loaded} modules")
        print(f"[FAIL] Failed {integrator.stats.errors} modules")


async def run_init(integrator: CompleteSystemIntegrator, config: dict):
    """Run initialization"""
    print("\n" + "=" * 80)
    print("PHASE 3: INITIALIZATION")
    print("=" * 80)
    
    results = await integrator.initialize_all(config)
    
    print(f"\n[OK] Initialized {integrator.stats.initialized} modules")


async def run_start(integrator: CompleteSystemIntegrator):
    """Run start"""
    print("\n" + "=" * 80)
    print("PHASE 4: STARTING")
    print("=" * 80)
    
    results = await integrator.start_all()
    
    print(f"\n[OK] Started {integrator.stats.running} modules")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Complete System Integrator - Integrate ALL trading bot modules'
    )
    parser.add_argument(
        '--mode', 
        choices=['discover', 'load', 'init', 'start'],
        default='discover',
        help='Integration mode (default: discover)'
    )
    parser.add_argument(
        '--lazy',
        action='store_true',
        help='Use lazy loading'
    )
    parser.add_argument(
        '--export',
        action='store_true',
        help='Export module inventory to JSON'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output'
    )
    
    args = parser.parse_args()
    
    # Setup
    setup_logging(args.verbose)
    print_banner()
    
    # Configuration
    config = {
        'trading_mode': 'paper',
        'symbols': ['BTCUSDT', 'EURUSD'],
        'initial_capital': 100000.0,
        'risk': {
            'max_position_size_pct': 10.0,
            'max_risk_per_trade_pct': 2.0,
            'max_daily_loss_pct': 5.0,
            'max_drawdown_pct': 20.0,
            'max_leverage': 3.0,
        }
    }
    
    # Create integrator
    integrator = CompleteSystemIntegrator(config)
    
    start_time = datetime.utcnow()
    
    try:
        # Phase 1: Discovery (always)
        await run_discover(integrator)
        
        # Phase 2: Load (if mode >= load)
        if args.mode in ['load', 'init', 'start']:
            await run_load(integrator, lazy=args.lazy)
        
        # Phase 3: Initialize (if mode >= init)
        if args.mode in ['init', 'start']:
            await run_init(integrator, config)
        
        # Phase 4: Start (if mode == start)
        if args.mode == 'start':
            await run_start(integrator)
        
        # Print summaries
        print_layer_summary(integrator)
        print_package_summary(integrator)
        
        # Export if requested
        if args.export:
            filepath = f'complete_module_inventory_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'
            integrator.export_inventory(filepath)
            print(f"\n[OK] Exported inventory to {filepath}")
        
        # Final status
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        
        print("\n" + "=" * 80)
        print("INTEGRATION COMPLETE")
        print("=" * 80)
        print(f"\n  Mode: {args.mode}")
        print(f"  Time: {elapsed:.2f} seconds")
        print(f"  Packages: {integrator.stats.total_packages}")
        print(f"  Modules: {integrator.stats.total_modules}")
        print(f"  Registered: {integrator.stats.registered}")
        print(f"  Loaded: {integrator.stats.loaded}")
        print(f"  Initialized: {integrator.stats.initialized}")
        print(f"  Running: {integrator.stats.running}")
        print(f"  Errors: {integrator.stats.errors}")
        
        if integrator.errors:
            print(f"\n  WARNING: {len(integrator.errors)} modules had errors (use --verbose for details)")
        
        print("\n" + "=" * 80)
        
        return integrator
        
    except KeyboardInterrupt:
        print("\n\nWARNING: Integration interrupted by user")
        await integrator.stop_all()
        return integrator
    except Exception as e:
        print(f"\n\nERROR: Integration failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(main())
