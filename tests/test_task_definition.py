import pytest
from core.interfaces import TaskDefinition, TestSuite


def test_task_definition_defaults():
    task = TaskDefinition(id="t1", description="desc")
    assert task.test_suite is None
    assert task.input_output_examples is None
    assert task.evaluation_criteria is None


def test_task_definition_with_test_suite():
    suite = TestSuite(tests=[{"input": 1, "output": 2}])
    task = TaskDefinition(id="t2", description="desc", test_suite=suite)
    assert task.test_suite is suite
    assert task.test_suite.tests[0]["input"] == 1
