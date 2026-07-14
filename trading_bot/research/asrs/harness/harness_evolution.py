import re
from typing import Dict, Any, List

class HarnessEvolutionSystem:
    """
    Harness Evolution System (HES).
    Implements TextGrad prompt optimization and structural agent-scaffolding updates.
    """
    def __init__(self):
        pass

    def perform_textgrad_mutation(
        self,
        current_prompt: str,
        critique_feedback: str
    ) -> str:
        """
        TextGrad linguistic gradient step.
        Mutates instructions along the directional path indicated by critic feedback.
        """
        # Parse critique points
        instructions = current_prompt.strip()

        # Simple rule-based linguistic transformation representing TextGrad
        if "latency" in critique_feedback.lower():
            # Inject compression directive to reduce token size and parsing cycles
            instructions = "CONFIDENCE DIRECTIVE: Respond concisely. Avoid preamble.\n" + instructions
        if "uncertainty" in critique_feedback.lower():
            instructions = instructions + "\nREGIME DIRECTIVE: Explicitly quantify posterior confidence margins."

        return instructions

    def mutate_workflow_steps(self, steps: List[str]) -> List[str]:
        """Mutate execution order or insert/prune steps in agent workflows."""
        mutated = list(steps)
        if not mutated:
            return mutated

        # 1. Insert validation step if missing
        if "adversarial_debate" not in mutated:
            idx = len(mutated) // 2
            mutated.insert(idx, "adversarial_debate")
        else:
            # 2. Swap order of adjacent steps
            if len(mutated) > 2:
                mutated[1], mutated[2] = mutated[2], mutated[1]

        return mutated
