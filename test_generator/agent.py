import logging
import json
import re
from typing import Optional, Dict, Any

from core.interfaces import TestGeneratorInterface, TestSuite, BaseAgent
from code_generator.agent import CodeGeneratorAgent

logger = logging.getLogger(__name__)

class TestGeneratorAgent(TestGeneratorInterface, BaseAgent):
    """Advanced agent that converts a natural-language brief into unit tests."""
    # Prevent pytest from treating this agent as a test case
    __test__ = False

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.code_generator = CodeGeneratorAgent()
        logger.info("TestGeneratorAgent initialized")

    async def execute(self, brief: str) -> TestSuite:
        """Concrete implementation of BaseAgent.execute."""
        return await self.generate_tests(brief)

    async def generate_tests(self, brief: str, suggest_imports: bool = False) -> TestSuite:
        """Generate a suite of tests from the provided brief."""
        logger.info(f"Generating tests from brief with suggested imports: {suggest_imports}")

        if suggest_imports:
            prompt = (
                "You are a Python expert tasked with writing pytest unit tests. "
                "Given the problem description below, return a JSON object with the keys: "
                "'explanation' summarizing your approach in English, 'cases' which is a list of "
                "structured test case dictionaries, 'tests_code' containing a complete pytest "
                "test file, and 'suggested_imports' containing a comma-separated list of Python "
                "standard library modules you recommend for implementing this functionality. "
                "Each test case must have 'input' and 'output' fields. "
                "Only return valid JSON without markdown fences.\n\n"
                f"Problem Description:\n{brief}\n"
            )
        else:
            prompt = (
                "You are a Python expert tasked with writing pytest unit tests. "
                "Given the problem description below, return a JSON object with the keys: "
                "'explanation' summarizing your approach in English, 'cases' which is a list of "
                "structured test case dictionaries, and 'tests_code' containing a complete pytest "
                "test file. Each test case must have 'input' and 'output' fields. "
                "Only return valid JSON without markdown fences.\n\n"
                f"Problem Description:\n{brief}\n"
            )

        logger.debug("Sending prompt to CodeGeneratorAgent")
        generated = await self.code_generator.generate_code(prompt, output_format="code")

        logger.debug(f"Raw test generation output:\n{generated}")
        tests_code = ""
        suggested_imports = ""

        try:
            data = json.loads(generated)
            explanation = data.get("explanation", "")
            cases = data.get("cases", [])
            tests_code = data.get("tests_code", "")
            suggested_imports = data.get("suggested_imports", "")
        except Exception as e:
            logger.error("Failed to parse generated tests as JSON: %s", e)
            explanation = generated
            cases = []

            code_match = re.search(r"```(?:python)?\n(.*?)```", generated, re.DOTALL)
            if code_match:
                tests_code = code_match.group(1).strip()
                
        suite = TestSuite(
            explanation=explanation, 
            cases=cases, 
            raw=generated, 
            tests_code=tests_code,
            suggested_imports=suggested_imports
        )
        logger.info("Test suite generated with %d cases", len(cases))
        return suite

