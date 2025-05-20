import unittest
from unittest.mock import AsyncMock, patch
import sys

import prototype_on_demand
from core.interfaces import TestSuite, TaskDefinition

class TestPrototypeOnDemandCLI(unittest.IsolatedAsyncioTestCase):
    async def test_main_uses_pytest_suite(self):
        suite = TestSuite(explanation="ok", cases=[], tests_code="assert True")
        async_mock = AsyncMock(return_value=suite)
        with patch('prototype_on_demand.generate_and_confirm_tests', async_mock), \
             patch('prototype_on_demand.TestGeneratorAgent') as tg_cls, \
             patch('prototype_on_demand.TaskManagerAgent') as manager_cls, \
             patch.object(sys, 'argv', ['prog', 'brief', '-f', 'solve']), \
             patch('builtins.input', return_value=''):
            tg_cls.return_value = object()
            manager_inst = manager_cls.return_value
            manager_inst.execute = AsyncMock(return_value=None)
            await prototype_on_demand.main()
            manager_cls.assert_called_once()
            called_task = manager_cls.call_args.kwargs['task_definition']
            self.assertIsInstance(called_task, TaskDefinition)
            self.assertEqual(called_task.test_suite.files['test_generated.py'], suite.tests_code)

