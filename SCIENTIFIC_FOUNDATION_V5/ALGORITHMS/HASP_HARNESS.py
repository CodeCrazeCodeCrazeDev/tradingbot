class SkillProgramHarness:
    """
    HASP: Harnessing LLM Agents with Skill Programs.
    """
    def __init__(self, pf_library):
        self.pfs = pf_library # Dict of state_pattern -> executable_function

    def apply_guardrails(self, state, base_action):
        """
        Executable guardrails activate on failure-prone states.
        """
        for pattern, pf in self.pfs.items():
            if self.matches(state, pattern):
                # Execute Program Function (PF)
                intervention = pf(state, base_action)
                if intervention:
                    return intervention # Returns modified action or corrective context

        return base_action

    def matches(self, state, pattern): pass
