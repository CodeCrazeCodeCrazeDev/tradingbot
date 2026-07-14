class PivotRefineExecutor:
    """
    AutoResearchClaw: Pivot/Refine decision loop.
    """
    def execute(self, plan):
        state = self.get_initial_state()
        while not self.is_complete(state):
            action = self.planner.next_action(state)
            try:
                result = self.executor.run(action)
                state = self.update_state(state, result)
            except Exception as e:
                # Decision loop
                if self.is_minor_failure(e):
                    # REFINE: fix the current step
                    state = self.refine(state, action, e)
                else:
                    # PIVOT: change the plan
                    state = self.pivot(state, e)

        return state

    def is_minor_failure(self, error): pass
    def refine(self, state, action, error): pass
    def pivot(self, state, error): pass
