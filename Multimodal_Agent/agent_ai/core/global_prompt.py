"""
GlobalPrompt facade for backward compatibility. Delegates to new prompt classes in prompts/.
"""
from .prompts.planning_prompt import PlanningPrompt
from .prompts.action_prompt import ActionPrompt
from .prompts.reflection_prompt import ReflectionPrompt
from .prompts.full_prompt import FullPrompt
from .prompts.self_evaluation_prompt import SelfEvaluationPrompt
from .prompts.context_helper import ContextHelper

class GlobalPrompt:
    def __init__(self):
        self.planning = PlanningPrompt()
        self.action = ActionPrompt()
        self.reflection = ReflectionPrompt()
        self.full = FullPrompt()
        self.self_eval = SelfEvaluationPrompt()
        self.context = ContextHelper()

    def get_planning_prompt(self, *args, **kwargs):
        return self.planning.get_planning_prompt(*args, **kwargs)

    def get_action_execution_prompt(self, *args, **kwargs):
        return self.action.get_action_execution_prompt(*args, **kwargs)

    def get_reflection_prompt(self, *args, **kwargs):
        return self.reflection.get_reflection_prompt(*args, **kwargs)

    def get_full_prompt(self, *args, **kwargs):
        return self.full.get_full_prompt(*args, **kwargs)

    def get_current_context(self, *args, **kwargs):
        return self.context.get_current_context(*args, **kwargs)

    def get_self_evaluation_prompt(self, *args, **kwargs):
        return self.self_eval.get_self_evaluation_prompt(*args, **kwargs)