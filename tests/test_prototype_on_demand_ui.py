import unittest
from unittest.mock import AsyncMock, MagicMock, patch, ANY

unittest.importlib = __import__("importlib")  # type: ignore
try:
    ui = unittest.importlib.import_module("prototype_on_demand_ui")
except Exception:  # pragma: no cover - module missing
    ui = None

from core.interfaces import TestSuite, TaskDefinition


@unittest.skipIf(ui is None, "prototype_on_demand_ui module missing")
class TestPrototypeOnDemandUI(unittest.IsolatedAsyncioTestCase):
    async def test_generate_tests_updates_components(self):
        suite = TestSuite(explanation="ok", cases=[{"input": [1], "output": 1}])
        mock_agent = AsyncMock()
        mock_agent.generate_tests = AsyncMock(return_value=suite)
        with patch("prototype_on_demand_ui.TestGeneratorAgent", return_value=mock_agent):
            expl_box = MagicMock(spec=ui.gr.Textbox)
            tests_box = MagicMock(spec=ui.gr.Textbox)
            expl_box.update = MagicMock()
            tests_box.update = MagicMock()

            result = await ui.generate_tests("brief", expl_box, tests_box)

            self.assertIs(result, suite)
            mock_agent.generate_tests.assert_awaited_once_with("brief")
            expl_box.update.assert_called_once_with(value=suite.explanation)
            tests_box.update.assert_called_once_with(value=ANY)

    async def test_approve_invokes_task_manager(self):
        suite = TestSuite(explanation="ok", cases=[{"input": [1], "output": 1}])
        with patch("prototype_on_demand_ui.TaskManagerAgent") as manager_cls:
            instance = manager_cls.return_value
            instance.execute = AsyncMock(return_value=None)
            task = await ui.approve("brief", "solve", ["os"], suite)

            manager_cls.assert_called_once()
            instance.execute.assert_awaited_once()
            called_task = manager_cls.call_args.kwargs["task_definition"]
            self.assertIsInstance(called_task, TaskDefinition)
            self.assertEqual(called_task.description, "brief")
            self.assertEqual(called_task.function_name_to_evolve, "solve")
            self.assertEqual(called_task.allowed_imports, ["os"])
            self.assertEqual(called_task.input_output_examples, suite.cases)
            self.assertIs(task, called_task)
