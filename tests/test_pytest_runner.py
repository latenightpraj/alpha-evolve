import os
from evaluator_agent.agent import EvaluatorAgent
from core.interfaces import TestSuite


def test_run_pytest_success():
    agent = EvaluatorAgent()
    code = """def add(a, b):
    return a + b
"""
    test_code = """from candidate import add

def test_add():
    assert add(1, 2) == 3
"""
    suite = TestSuite(files={"test_add.py": test_code})
    results, err = agent._run_pytest(code, suite, timeout_seconds=10)
    assert err is None
    assert results["passed"] == 1
    assert results["failed"] == 0


def test_run_pytest_failure():
    agent = EvaluatorAgent()
    code = """def sub(a, b):
    return a - b
"""
    test_code = """from candidate import sub

def test_sub():
    assert sub(1, 1) == 0

def test_fail():
    assert sub(2, 1) == 0
"""
    suite = TestSuite(files={"test_sub.py": test_code})
    results, err = agent._run_pytest(code, suite, timeout_seconds=10)
    assert results["passed"] == 1
    assert results["failed"] == 1


