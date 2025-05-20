import unittest
from types import SimpleNamespace

from test_generator.agent import TestGeneratorAgent, TestSuite

class DummyResponse:
    def __init__(self, content):
        self.choices = [SimpleNamespace(message=SimpleNamespace(content=content))]

async def dummy_acompletion(*args, **kwargs):
    return DummyResponse("""Some intro text
```python
assert True
```
This explains the tests.""")

class TestTestGeneratorAgent(unittest.IsolatedAsyncioTestCase):
    async def test_generate_tests_returns_suite(self):
        agent = TestGeneratorAgent()
        # Patch acompletion within agent module
        import test_generator.agent as tg_module
        original = tg_module.acompletion
        tg_module.acompletion = dummy_acompletion
        try:
            suite = await agent.generate_tests("brief")
        finally:
            tg_module.acompletion = original

        self.assertIsInstance(suite, TestSuite)
        self.assertEqual(suite.tests_code.strip(), "assert True")
        self.assertIn("explain", suite.explanation.lower())

if __name__ == '__main__':
    unittest.main()
