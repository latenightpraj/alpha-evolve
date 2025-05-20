import pytest
from evaluator_agent.agent import EvaluatorAgent
from core.interfaces import TaskDefinition, Program

@pytest.mark.asyncio
async def test_memory_limit_enforced():
    task = TaskDefinition(
        id="memory_task",
        description="Ensure memory limit terminates execution",
        function_name_to_evolve="alloc",
        input_output_examples=[{"input": [1], "output": 1}],
        max_memory_mb=50,
    )
    # Allocate ~100MB which should exceed the limit
    code = "def alloc(x):\n    arr = bytearray(100 * 1024 * 1024)\n    return x"
    agent = EvaluatorAgent()
    results, error = await agent._execute_code_safely(
        code, task_for_examples=task, timeout_seconds=5, max_memory_mb=task.max_memory_mb
    )
    assert results is None
    assert error is not None

