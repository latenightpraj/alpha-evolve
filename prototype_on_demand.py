import argparse
import asyncio
import json
import logging
import os
import sys
import tempfile
import subprocess
import time

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


def edit_tests(initial_json: str) -> dict:
    """Open an editor or accept pasted JSON to edit tests."""
    editor = os.getenv("EDITOR")
    if editor:
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as tmp:
            tmp.write(initial_json)
            tmp.flush()
            path = tmp.name
        subprocess.call([editor, path])
        with open(path, "r") as f:
            edited = f.read()
        os.remove(path)
    else:
        print("Paste edited JSON. Finish with EOF (Ctrl-D):")
        edited = sys.stdin.read()
    try:
        data = json.loads(edited)
    except Exception as e:
        logger.error("Failed to parse edited JSON: %s", e)
        return {}
    return data


async def generate_and_confirm_tests(agent: TestGeneratorAgent, brief: str):
    """Generate tests and allow the user to approve, regenerate, edit, or quit."""
    while True:
        suite = await agent.generate_tests(brief)
        print("\n--- Test Explanation ---")
        print(suite.explanation)
        if suite.tests_code:
            print("\n--- Pytest Code ---")
            print(suite.tests_code)
        print("\n--- Proposed Tests (JSON) ---")
        print(json.dumps({"explanation": suite.explanation, "cases": suite.cases}, indent=2))
        choice = input("[A]ccept / [R]egenerate / [E]dit / [Q]uit > ").strip().lower()
        logger.info("User choice: %s", choice)
        if choice.startswith("a"):
            return suite
        if choice.startswith("r"):
            continue
        if choice.startswith("e"):
            edited = edit_tests(json.dumps({"explanation": suite.explanation, "cases": suite.cases}, indent=2))
            if edited:
                suite.explanation = edited.get("explanation", suite.explanation)
                suite.cases = edited.get("cases", suite.cases)
            return suite
        if choice.startswith("q"):
            logger.info("User quit before running evolution")
            return None


async def main():
    parser = argparse.ArgumentParser(description="Prototype tasks on demand")
    parser.add_argument("brief", nargs="?", help="Short problem description")
    parser.add_argument("-f", "--function-name", dest="func_name", help="Name of the function to evolve")
    parser.add_argument("-i", "--imports", dest="imports", help="Comma separated list of allowed imports")
    args = parser.parse_args()

    brief = args.brief or input("Enter task brief: ")
    logger.info("Brief provided: %s", brief)

    test_agent = TestGeneratorAgent()

    suite = await generate_and_confirm_tests(test_agent, brief)
    if not suite:
        return

    if suite.tests_code:
        suite.files = {"test_generated.py": suite.tests_code}

    func_name = args.func_name or input("Function name to evolve [solve]: ").strip() or "solve"
    imports_text = args.imports or input("Allowed standard library imports (comma separated) [none]: ")
    allowed_imports = [imp.strip() for imp in imports_text.split(",") if imp.strip()] if imports_text else []

    task_id = f"prototype_{int(time.time())}"
    task = TaskDefinition(
        id=task_id,
        description=brief,
        function_name_to_evolve=func_name,
        input_output_examples=suite.cases,
        allowed_imports=allowed_imports,
        test_suite=suite,
    )

    logger.info("Starting TaskManagerAgent for task %s", task_id)
    manager = TaskManagerAgent(task_definition=task)
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
