"""
Meta-Recursive Controller

The highest level of recursion - controls and optimizes the recursion process itself.
Manages recursion depth, detects convergence, and prevents infinite loops.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RecursionDepthManager:
    """Manages recursion depth across all recursive processes"""
    max_depth: int
    current_depth: int
    depth_history: List[int] = field(default_factory=list)
    depth_violations: int = 0
    
    def can_recurse(self) -> bool:
        """Check if we can recurse deeper"""
        return self.current_depth < self.max_depth
    
    def enter_recursion(self) -> bool:
        """Enter a recursion level"""
        if self.can_recurse():
            self.current_depth += 1
            self.depth_history.append(self.current_depth)
            return True
        else:
            self.depth_violations += 1
            logger.warning(f"Max recursion depth {self.max_depth} reached")
            return False
    
    def exit_recursion(self):
        """Exit a recursion level"""
        if self.current_depth > 0:
            self.current_depth -= 1
    
    def reset(self):
        """Reset depth counter"""
        self.current_depth = 0


@dataclass
class ConvergenceDetector:
    """Detects when recursive improvement has converged"""
    convergence_threshold: float
    window_size: int
    improvement_history: List[float] = field(default_factory=list)
    
    def add_improvement(self, improvement: float):
        """Add improvement measurement"""
        self.improvement_history.append(improvement)
        
        # Keep only recent history
        if len(self.improvement_history) > self.window_size * 2:
            self.improvement_history = self.improvement_history[-self.window_size:]
    
    def has_converged(self) -> bool:
        """Check if improvements have converged"""
        if len(self.improvement_history) < self.window_size:
            return False
        
        recent = self.improvement_history[-self.window_size:]
        
        # Check if all recent improvements are below threshold
        return all(abs(imp) < self.convergence_threshold for imp in recent)
    
    def get_convergence_score(self) -> float:
        """Get convergence score (0 = not converged, 1 = fully converged)"""
        if len(self.improvement_history) < self.window_size:
            return 0.0
        
        recent = self.improvement_history[-self.window_size:]
        avg_improvement = np.mean([abs(imp) for imp in recent])
        
        # Score based on how close to threshold
        score = 1.0 - min(1.0, avg_improvement / self.convergence_threshold)
        return score


class MetaRecursiveController:
    """
    Meta-recursive controller - the highest level of recursion.
    
    Controls:
    1. Recursion depth across all processes
    2. Convergence detection
    3. Infinite loop prevention
    4. Recursion optimization
    5. Meta-meta learning (learning about learning about learning)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Recursion management
        self.depth_manager = RecursionDepthManager(
            max_depth=self.config.get('max_depth', 10),
            current_depth=0
        )
        
        # Convergence detection
        self.convergence_detector = ConvergenceDetector(
            convergence_threshold=self.config.get('convergence_threshold', 0.001),
            window_size=self.config.get('convergence_window', 5)
        )
        
        # Recursion tracking
        self.recursion_stack: List[Dict[str, Any]] = []
        self.recursion_history: List[Dict[str, Any]] = []
        
        # Meta-meta learning
        self.meta_meta_insights: List[Dict[str, Any]] = []
        
        # Loop detection
        self.state_history: List[str] = []
        self.loop_detection_window = 10
        
        logger.info("MetaRecursiveController initialized")
    
    async def execute_recursive_process(
        self,
        process_name: str,
        process_func: callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a recursive process with meta-control.
        
        Args:
            process_name: Name of the process
            process_func: Async function to execute
            *args, **kwargs: Arguments for the function
            
        Returns:
            Result of the process
        """
        # Check if we can recurse
        if not self.depth_manager.enter_recursion():
            logger.warning(f"Cannot execute {process_name}: max depth reached")
            return None
        
        # Record recursion entry
        recursion_entry = {
            'process': process_name,
            'depth': self.depth_manager.current_depth,
            'timestamp': datetime.utcnow().isoformat(),
            'args': str(args)[:100],  # Truncate for logging
        }
        self.recursion_stack.append(recursion_entry)
        
        try:
            # Check for infinite loops
            if self._detect_infinite_loop(process_name):
                logger.error(f"Infinite loop detected in {process_name}")
                return None
            
            # Execute process
            result = await process_func(*args, **kwargs)
            
            # Record success
            recursion_entry['status'] = 'success'
            recursion_entry['result_summary'] = str(result)[:100]
            
            # Track improvement for convergence
            improvement = self._extract_improvement(result)
            if improvement is not None:
                self.convergence_detector.add_improvement(improvement)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in recursive process {process_name}: {e}")
            recursion_entry['status'] = 'error'
            recursion_entry['error'] = str(e)
            return None
            
        finally:
            # Exit recursion
            self.depth_manager.exit_recursion()
            
            # Move from stack to history
            if self.recursion_stack:
                completed = self.recursion_stack.pop()
                completed['end_time'] = datetime.utcnow().isoformat()
                self.recursion_history.append(completed)
            
            # Meta-meta learning
            await self._meta_meta_learn()
    
    def _detect_infinite_loop(self, process_name: str) -> bool:
        """Detect if we're in an infinite loop"""
        # Create state signature
        state = f"{process_name}_{self.depth_manager.current_depth}"
        self.state_history.append(state)
        
        # Keep only recent history
        if len(self.state_history) > self.loop_detection_window * 2:
            self.state_history = self.state_history[-self.loop_detection_window:]
        
        # Check for repeating patterns
        if len(self.state_history) >= self.loop_detection_window:
            recent = self.state_history[-self.loop_detection_window:]
            
            # Simple loop detection: same state repeated
            if len(set(recent)) == 1:
                return True
            
            # Pattern detection: repeating sequence
            half = len(recent) // 2
            if recent[:half] == recent[half:2*half]:
                return True
        
        return False
    
    def _extract_improvement(self, result: Any) -> Optional[float]:
        """Extract improvement metric from result"""
        if isinstance(result, dict):
            # Try common improvement keys
            for key in ['improvement', 'improvement_delta', 'delta', 'change']:
                if key in result:
                    value = result[key]
                    if isinstance(value, (int, float)):
                        return float(value)
        
        return None
    
    async def _meta_meta_learn(self):
        """
        Meta-meta learning: Learn about the learning about learning process.
        
        This is the highest level of recursion - we analyze how well our
        meta-recursive control is working and improve it.
        """
        if len(self.recursion_history) < 10:
            return
        
        recent = self.recursion_history[-10:]
        
        # Analyze recursion patterns
        depths = [r['depth'] for r in recent]
        avg_depth = np.mean(depths)
        max_depth = max(depths)
        
        # Analyze success rate
        successes = sum(1 for r in recent if r.get('status') == 'success')
        success_rate = successes / len(recent)
        
        # Analyze convergence
        convergence_score = self.convergence_detector.get_convergence_score()
        
        insight = {
            'timestamp': datetime.utcnow().isoformat(),
            'avg_depth': avg_depth,
            'max_depth': max_depth,
            'success_rate': success_rate,
            'convergence_score': convergence_score,
            'recommendation': None
        }
        
        # Generate recommendations
        if avg_depth > self.depth_manager.max_depth * 0.8:
            insight['recommendation'] = 'reduce_max_depth'
            self.depth_manager.max_depth = max(3, self.depth_manager.max_depth - 1)
            logger.info(f"Meta-meta: Reduced max depth to {self.depth_manager.max_depth}")
        
        elif avg_depth < self.depth_manager.max_depth * 0.3 and success_rate > 0.8:
            insight['recommendation'] = 'increase_max_depth'
            self.depth_manager.max_depth = min(20, self.depth_manager.max_depth + 1)
            logger.info(f"Meta-meta: Increased max depth to {self.depth_manager.max_depth}")
        
        if convergence_score > 0.9:
            insight['recommendation'] = 'converged'
            logger.info("Meta-meta: System has converged")
        
        self.meta_meta_insights.append(insight)
    
    async def optimize_recursion_parameters(self) -> Dict[str, Any]:
        """
        Optimize recursion parameters based on history.
        
        This is meta-optimization - optimizing the optimization process.
        """
        if len(self.recursion_history) < 20:
            return {'status': 'insufficient_data'}
        
        # Analyze optimal depth
        successful = [r for r in self.recursion_history if r.get('status') == 'success']
        if successful:
            depths = [r['depth'] for r in successful]
            optimal_depth = int(np.median(depths))
            
            # Adjust max depth towards optimal
            if optimal_depth < self.depth_manager.max_depth:
                self.depth_manager.max_depth = max(
                    optimal_depth + 2,
                    self.depth_manager.max_depth - 1
                )
        
        # Analyze convergence patterns
        if self.convergence_detector.improvement_history:
            improvements = self.convergence_detector.improvement_history
            avg_improvement = np.mean([abs(i) for i in improvements])
            
            # Adjust convergence threshold
            if avg_improvement < self.convergence_detector.convergence_threshold * 0.5:
                # Improvements are very small, tighten threshold
                self.convergence_detector.convergence_threshold *= 0.9
            elif avg_improvement > self.convergence_detector.convergence_threshold * 2:
                # Improvements are large, loosen threshold
                self.convergence_detector.convergence_threshold *= 1.1
        
        return {
            'max_depth': self.depth_manager.max_depth,
            'convergence_threshold': self.convergence_detector.convergence_threshold,
            'optimizations_applied': 2
        }
    
    def should_continue_recursion(self) -> bool:
        """Determine if recursion should continue"""
        # Don't continue if converged
        if self.convergence_detector.has_converged():
            logger.info("Recursion converged, stopping")
            return False
        
        # Don't continue if too many depth violations
        if self.depth_manager.depth_violations > 10:
            logger.warning("Too many depth violations, stopping")
            return False
        
        # Don't continue if success rate is too low
        if len(self.recursion_history) >= 10:
            recent = self.recursion_history[-10:]
            successes = sum(1 for r in recent if r.get('status') == 'success')
            if successes < 3:  # Less than 30% success
                logger.warning("Low success rate, stopping")
                return False
        
        return True
    
    def get_recursion_state(self) -> Dict[str, Any]:
        """Get current recursion state"""
        return {
            'current_depth': self.depth_manager.current_depth,
            'max_depth': self.depth_manager.max_depth,
            'stack_size': len(self.recursion_stack),
            'history_size': len(self.recursion_history),
            'convergence_score': self.convergence_detector.get_convergence_score(),
            'has_converged': self.convergence_detector.has_converged(),
            'depth_violations': self.depth_manager.depth_violations,
            'meta_meta_insights': len(self.meta_meta_insights),
        }
    
    def get_recursion_summary(self) -> Dict[str, Any]:
        """Get comprehensive recursion summary"""
        state = self.get_recursion_state()
        
        # Add statistics
        if self.recursion_history:
            depths = [r['depth'] for r in self.recursion_history]
            successes = sum(1 for r in self.recursion_history if r.get('status') == 'success')
            
            state.update({
                'total_recursions': len(self.recursion_history),
                'avg_depth': np.mean(depths),
                'max_depth_reached': max(depths),
                'success_rate': successes / len(self.recursion_history),
                'recent_improvements': self.convergence_detector.improvement_history[-5:],
            })
        
        return state
    
    async def recursive_meta_optimize(self, iterations: int = 5) -> Dict[str, Any]:
        """
        Recursively optimize the meta-optimization process.
        
        This is the ultimate recursion - optimizing the optimization of the optimization.
        """
        results = []
        
        for i in range(iterations):
            if not self.should_continue_recursion():
                break
            
            # Optimize recursion parameters
            result = await self.optimize_recursion_parameters()
            results.append(result)
            
            # Meta-meta learn from optimization
            await self._meta_meta_learn()
        
        return {
            'iterations_completed': len(results),
            'final_state': self.get_recursion_state(),
            'optimizations': results
        }
    
    def reset(self):
        """Reset the meta-recursive controller"""
        self.depth_manager.reset()
        self.recursion_stack.clear()
        self.state_history.clear()
        logger.info("MetaRecursiveController reset")
