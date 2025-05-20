import json
from typing import List

import gradio as gr

from core.interfaces import TaskDefinition, TestSuite
from test_generator.agent import TestGeneratorAgent
from task_manager.agent import TaskManagerAgent


async def generate_tests(brief: str, explanation_box: gr.Textbox, tests_box: gr.Textbox) -> TestSuite:
    """Generate tests from a brief and update UI components."""
    agent = TestGeneratorAgent()
    suite = await agent.generate_tests(brief)
    explanation_box.update(value=suite.explanation)
    tests_box.update(value=json.dumps(suite.cases, indent=2))
    return suite


async def approve(
    brief: str,
    function_name: str,
    allowed_imports: List[str],
    suite: TestSuite,
) -> TaskDefinition:
    """Create a task definition and start the TaskManager."""
    task = TaskDefinition(
        id="prototype_task",
        description=brief,
        function_name_to_evolve=function_name,
        input_output_examples=suite.cases,
        allowed_imports=allowed_imports,
    )
    manager = TaskManagerAgent(task_definition=task)
    await manager.execute()
    return task
