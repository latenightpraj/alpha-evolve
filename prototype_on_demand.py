import asyncio
import os
import subprocess
import tempfile
from typing import Callable, Optional

from core.interfaces import TaskDefinition
from task_manager.agent import TaskManagerAgent
from test_generator.agent import TestGeneratorAgent


def edit_text_in_editor(text: str) -> str:
    """Open text in the user's editor and return the modified contents."""
    editor = os.environ.get("EDITOR", "nano")
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".py") as f:
        f.write(text)
        f.flush()
        tmp_path = f.name
    subprocess.call([editor, tmp_path])
    with open(tmp_path, "r") as f:
        new_text = f.read()
    os.unlink(tmp_path)
    return new_text


async def generate_and_confirm_tests(
    task: TaskDefinition,
    input_func: Callable[[str], str] = input,
    edit_func: Callable[[str], str] = edit_text_in_editor,
    test_agent: Optional[TestGeneratorAgent] = None,
) -> Optional[TaskDefinition]:
    """Interactively generate tests until user approval."""
    agent = test_agent or TestGeneratorAgent()
    tests, explanation = await agent.generate_tests(task)

    while True:
        print("\n=== Proposed Tests ===")
        print(tests)
        print("\n=== Explanation ===")
        print(explanation)
        cmd = input_func("[a]pprove/[r]egenerate/[e]dit/[q]uit: ").strip().lower()
        if cmd == "a":
            task.test_suite = tests
            return task
        elif cmd == "r":
            tests, explanation = await agent.generate_tests(task)
            continue
        elif cmd == "e":
            tests = edit_func(tests)
            continue
        elif cmd == "q":
            print("Aborted by user.")
            return None
        else:
            print("Invalid command. Please enter a, r, e, or q.")


async def main():
    task = TaskDefinition(
        id="demo_task",
        description="Return the same integer that is given as input.",
        function_name_to_evolve="identity",
    )

    result = await generate_and_confirm_tests(task)
    if not result:
        return

    manager = TaskManagerAgent(task_definition=result)
    await manager.execute()


if __name__ == "__main__":
    asyncio.run(main())
