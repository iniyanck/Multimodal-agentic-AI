"""
ReflectionPrompt class for generating reflection prompts for LLM.
"""

class ReflectionPrompt:
    def get_reflection_prompt(self, current_task_description, current_plan_step, action_executed, action_result, current_context, history):
        return f"""
        Reflecting on the last action: {action_executed.get('action')}.  Action result: {action_result}.  Current task: {current_task_description}.  Current plan step: {current_plan_step}.
        Based on the action result, was the action successful and is this plan step complete? Use common sense and practical judgment: if the main goal is reasonably achieved, you may consider the step or task complete, even if not perfect. Explain your reasoning.
        Output ONLY a JSON object with 'status' ('success' or 'failure'), 'thought' explaining your reasoning, and optionally a 'message' if there are issues.
        Example: {{"status": "success", "thought": "The action completed successfully and achieved the desired state."}}
        """
