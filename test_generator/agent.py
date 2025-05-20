import logging
import json
from typing import Optional, Dict, Any

from core.interfaces import TestGeneratorInterface, TestSuite, BaseAgent
from code_generator.agent import CodeGeneratorAgent

logger = logging.getLogger(__name__)

class TestGeneratorAgent(TestGeneratorInterface, BaseAgent):
    """Generate unit tests for a problem brief using an LLM via CodeGeneratorAgent."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.code_generator = CodeGeneratorAgent()
        logger.info("TestGeneratorAgent initialized.")

    async def generate_tests(self, brief: str) -> TestSuite:
        logger.info("Generating tests from brief.")
        prompt = (
            "You are a Python expert tasked with writing unit tests. "
            "Given the problem description below, return a JSON object with two keys: "
            "'explanation' summarizing your approach in English and 'cases' which is "
            "a list of test case objects. Each test case must have 'input' and 'output' fields. "
            "Only return valid JSON without markdown fences.\n\n"
            f"Problem Description:\n{brief}\n"
        )
        generated = await self.code_generator.generate_code(prompt, output_format="code")
        logger.debug(f"Raw test generation output:\n{generated}")
        try:
            data = json.loads(generated)
            explanation = data.get("explanation", "")
            cases = data.get("cases", [])
        except Exception as e:
            logger.error("Failed to parse generated tests as JSON: %s", e)
            explanation = generated
            cases = []
        suite = TestSuite(explanation=explanation, cases=cases, raw=generated)
        logger.info("Test suite generated with %d cases", len(cases))
        return suite
