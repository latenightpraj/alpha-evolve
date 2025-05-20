import asyncio
import unittest
from unittest.mock import AsyncMock

from core.interfaces import TaskDefinition
from prototype_on_demand import generate_and_confirm_tests


class PrototypeLoopTests(unittest.TestCase):
    def test_approve_first_try(self):
        task = TaskDefinition(id="t", description="d")
        mock_agent = AsyncMock()
        mock_agent.generate_tests.return_value = ("tests1", "exp1")

        inputs = iter(["a"])
        result = asyncio.run(
            generate_and_confirm_tests(
                task,
                input_func=lambda _: next(inputs),
                test_agent=mock_agent,
                edit_func=lambda x: x,
            )
        )

        self.assertIs(result, task)
        self.assertEqual(task.test_suite, "tests1")
        mock_agent.generate_tests.assert_awaited_once()

    def test_regenerate_then_approve(self):
        task = TaskDefinition(id="t", description="d")
        mock_agent = AsyncMock()
        mock_agent.generate_tests.side_effect = [("t1", "e1"), ("t2", "e2")]

        inputs = iter(["r", "a"])
        result = asyncio.run(
            generate_and_confirm_tests(
                task,
                input_func=lambda _: next(inputs),
                test_agent=mock_agent,
                edit_func=lambda x: x,
            )
        )

        self.assertEqual(task.test_suite, "t2")
        self.assertEqual(mock_agent.generate_tests.await_count, 2)
        self.assertIs(result, task)

    def test_edit_then_approve(self):
        task = TaskDefinition(id="t", description="d")
        mock_agent = AsyncMock()
        mock_agent.generate_tests.return_value = ("t1", "e1")

        inputs = iter(["e", "a"])
        result = asyncio.run(
            generate_and_confirm_tests(
                task,
                input_func=lambda _: next(inputs),
                test_agent=mock_agent,
                edit_func=lambda x: "edited",
            )
        )

        self.assertEqual(task.test_suite, "edited")
        self.assertIs(result, task)

    def test_abort(self):
        task = TaskDefinition(id="t", description="d")
        mock_agent = AsyncMock()
        mock_agent.generate_tests.return_value = ("t1", "e1")

        inputs = iter(["q"])
        result = asyncio.run(
            generate_and_confirm_tests(
                task,
                input_func=lambda _: next(inputs),
                test_agent=mock_agent,
                edit_func=lambda x: x,
            )
        )

        self.assertIsNone(result)
        self.assertIsNone(task.test_suite)


if __name__ == "__main__":
    unittest.main()
