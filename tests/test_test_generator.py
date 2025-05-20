import pytest
from unittest.mock import AsyncMock, patch

# Skip the entire module if the test generator does not exist
pytest.importorskip("test_generator.agent")
from test_generator.agent import TestGeneratorAgent

class DummyResponse:
    def __init__(self, content: str):
        self.choices = [type("Choice", (), {"message": type("Msg", (), {"content": content})()})()]

@pytest.mark.asyncio
async def test_generate_tests_returns_llm_output():
    agent = TestGeneratorAgent()
    dummy_json = '{"explanation": "ok", "cases": [], "tests_code": "assert True"}'
    dummy = DummyResponse(dummy_json)
    with patch("test_generator.agent.acompletion", new=AsyncMock(return_value=dummy)):
        suite = await agent.generate_tests("some code")
    assert suite.tests_code.strip() == "assert True"
