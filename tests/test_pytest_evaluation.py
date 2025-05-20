import pytest
from evaluator_agent.agent import EvaluatorAgent
from core.interfaces import Program, TaskDefinition

@pytest.mark.asyncio
async def test_evaluator_correct_program():
    task = TaskDefinition(
        id="task_add",
        description="Add two numbers",
        function_name_to_evolve="add",
        input_output_examples=[{"input": [1, 2], "output": 3}, {"input": [5, -2], "output": 3}],
    )
    program = Program(id="p1", code="def add(a, b):\n    return a + b")
    agent = EvaluatorAgent()
    result = await agent.evaluate_program(program, task)
    assert result.fitness_scores.get("correctness") == 1.0
    assert result.fitness_scores.get("passed_tests") == 2.0
    assert result.fitness_scores.get("total_tests") == 2.0

@pytest.mark.asyncio
async def test_evaluator_incorrect_program():
    task = TaskDefinition(
        id="task_add",
        description="Add two numbers",
        function_name_to_evolve="add",
        input_output_examples=[{"input": [1, 2], "output": 3}],
    )
    program = Program(id="p2", code="def add(a, b):\n    return 0")
    agent = EvaluatorAgent()
    result = await agent.evaluate_program(program, task)
    assert result.fitness_scores.get("correctness") == 0.0
    assert result.fitness_scores.get("passed_tests") == 0.0
    assert result.fitness_scores.get("total_tests") == 1.0
