import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from typing import Callable, Optional

from core.interfaces import TaskDefinition
from config import settings
from test_generator.agent import TestGeneratorAgent
from task_manager.agent import TaskManagerAgent

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format=settings.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.LOG_FILE, mode="a")
    ],
)
logger = logging.getLogger(__name__)


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
    parser = argparse.ArgumentParser(description="Prototype tasks on demand")
    parser.add_argument("brief", nargs="?", help="Short problem description")
    args = parser.parse_args()

    brief = args.brief or input("Enter task brief: ")
    logger.info("Brief provided: %s", brief)

    task_id = f"prototype_{int(time.time())}"
    task = TaskDefinition(id=task_id, description=brief)

    result = await generate_and_confirm_tests(task)
    if not result:
        logger.info("User aborted before running evolution")
        return

    func_name = input("Function name to evolve [solve]: ").strip() or "solve"
    imports_text = input("Allowed standard library imports (comma separated) [none]: ")
    allowed_imports = [imp.strip() for imp in imports_text.split(",") if imp.strip()] if imports_text else []

    result.function_name_to_evolve = func_name
    result.allowed_imports = allowed_imports

    logger.info("Starting TaskManagerAgent for task %s", task_id)
    manager = TaskManagerAgent(task_definition=result)
    best = await manager.execute()

    if best:
        best_program = best[0]
        code_path = f"{task_id}_best.py"
        with open(code_path, "w") as f:
            f.write(best_program.code)
        logger.info("Best program saved to %s", code_path)
        print(f"Best program saved to {code_path}")
    else:
        logger.info("Evolution completed with no successful program")
        print("No solution found.")


if __name__ == "__main__":
    asyncio.run(main())
