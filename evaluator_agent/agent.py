                  
import time
import logging
import traceback
import subprocess
import tempfile
import os
import ast
import json
import asyncio
import sys
import math
import re
import shutil
from typing import Optional, Dict, Any, Tuple, Union, List

from core.interfaces import EvaluatorAgentInterface, Program, TaskDefinition, BaseAgent, TestSuite
from config import settings

logger = logging.getLogger(__name__)

class EvaluatorAgent(EvaluatorAgentInterface, BaseAgent):
    def __init__(self, task_definition: Optional[TaskDefinition] = None):
        super().__init__()
        self.task_definition = task_definition
        self.evaluation_model_name = settings.EVALUATION_MODEL
        self.evaluation_timeout_seconds = settings.EVALUATION_TIMEOUT_SECONDS
        logger.info(f"EvaluatorAgent initialized with model: {self.evaluation_model_name}, timeout: {self.evaluation_timeout_seconds}s")
        if self.task_definition:
            logger.info(f"EvaluatorAgent task_definition: {self.task_definition.id}")

    def _check_syntax(self, code: str) -> List[str]:
        errors = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"SyntaxError: {e.msg} at line {e.lineno}, offset {e.offset}")
        except Exception as e:
            errors.append(f"Unexpected error during syntax check: {str(e)}")
        return errors

    async def _execute_code_safely(
        self,
        code: str,
        task_for_examples: TaskDefinition,
        timeout_seconds: Optional[int] = None,
        max_memory_mb: Optional[int] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        timeout = timeout_seconds if timeout_seconds is not None else self.evaluation_timeout_seconds
        results = {"test_outputs": [], "average_runtime_ms": 0.0}
        
        if not task_for_examples.input_output_examples:
            logger.warning("No input/output examples provided to _execute_code_safely.")
            return results, "No test cases to run."

        if not task_for_examples.function_name_to_evolve:
            logger.error(f"Task {task_for_examples.id} does not specify 'function_name_to_evolve'. Cannot execute code.")
            return None, "Task definition is missing 'function_name_to_evolve'."

        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, "temp_script.py")

        def serialize_arg(arg):
            if isinstance(arg, (float, int)) and (arg == float('inf') or arg == float('-inf') or arg != arg):
                return f"float('{str(arg)}')"
            return json.dumps(arg)

                                                                                          
        test_cases_str = json.dumps(task_for_examples.input_output_examples)
        test_cases_str = test_cases_str.replace('"Infinity"', 'float("inf")')
        test_cases_str = test_cases_str.replace('"NaN"', 'float("nan")')
                                                                      
        test_cases_str = test_cases_str.replace('true', 'True').replace('false', 'False').replace('null', 'None')

        test_harness_code = f"""
import json
import time
import sys
import math  # Import math for inf/nan constants

# User's code (function to be tested)
{code}

# Test execution logic
results = []
total_execution_time = 0
num_tests = 0

# Special constants for test cases
Infinity = float('inf')
NaN = float('nan')

test_cases = {test_cases_str} 
function_to_test_name = "{task_for_examples.function_name_to_evolve}"

# Make sure the function_to_test is available in the global scope
if function_to_test_name not in globals():
    # Attempt to find it if it was defined inside a class (common for LLM output)
    # This is a simple heuristic and might need refinement.
    found_func = None
    for name, obj in list(globals().items()):
        if isinstance(obj, type):
            if hasattr(obj, function_to_test_name):
                method = getattr(obj, function_to_test_name)
                if callable(method):
                    globals()[function_to_test_name] = method
                    found_func = True
                    break
    if not found_func:
        print(json.dumps({{"error": f"Function '{{function_to_test_name}}' not found in the global scope or as a callable method of a defined class."}}))
        sys.exit(1)
        
function_to_test = globals()[function_to_test_name]

for i, test_case in enumerate(test_cases):
    input_args = test_case.get("input")
    
    start_time = time.perf_counter()
    try:
        if isinstance(input_args, list):
            actual_output = function_to_test(*input_args)
        elif isinstance(input_args, dict):
            actual_output = function_to_test(**input_args)
        elif input_args is None:
             actual_output = function_to_test()
        else:
            actual_output = function_to_test(input_args)
            
        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000
        total_execution_time += execution_time_ms
        num_tests += 1
        results.append({{"test_case_id": i, "output": actual_output, "runtime_ms": execution_time_ms, "status": "success"}})
    except Exception as e:
        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000
        error_output = {{
            "test_case_id": i,
            "error": str(e), 
            "error_type": type(e).__name__,
            "runtime_ms": execution_time_ms,
            "status": "error"
        }}
        try:
            json.dumps(error_output)
        except TypeError:
            error_output["error"] = "Unserializable error object"
        results.append(error_output)

final_output = {{"test_outputs": results}}
if num_tests > 0:
    final_output["average_runtime_ms"] = total_execution_time / num_tests

def custom_json_serializer(obj):
    if isinstance(obj, float):
        if obj == float('inf'):
            return 'Infinity'
        elif obj == float('-inf'):
            return '-Infinity'
        elif obj != obj:
            return 'NaN'
    raise TypeError(f"Object of type {{type(obj).__name__}} is not JSON serializable")

print(json.dumps(final_output, default=custom_json_serializer))
"""
        with open(temp_file_path, "w") as f:
            f.write(test_harness_code)

        cmd = [sys.executable, temp_file_path]

        proc = None
        try:
            logger.debug(f"Executing code: {' '.join(cmd)} in {temp_dir}")
            start_time = time.monotonic()
            preexec_fn = None
            if max_memory_mb is not None:
                limit_bytes = max_memory_mb * 1024 * 1024

                def set_mem_limit():
                    try:
                        import resource
                        resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
                    except Exception as e:
                        logger.error(f"Failed to set memory limit: {e}")

                preexec_fn = set_mem_limit

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=temp_dir,
                preexec_fn=preexec_fn,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            duration = time.monotonic() - start_time
            logger.debug(f"Code execution finished in {duration:.2f}s. Exit code: {proc.returncode}")

            stdout_str = stdout.decode('utf-8', errors='replace').strip()
            stderr_str = stderr.decode('utf-8', errors='replace').strip()

            if proc.returncode != 0:
                error_message = f"Execution failed with exit code {proc.returncode}. Stdout: '{stdout_str}'. Stderr: '{stderr_str}'"
                logger.warning(error_message)
                return None, error_message
            
            if not stdout_str:
                 logger.warning(f"Execution produced no stdout. Stderr: '{stderr_str}'")
                 return None, f"No output from script. Stderr: '{stderr_str}'"

            try:
                def json_loads_with_infinity(s):
                    s = s.replace('"Infinity"', 'float("inf")')
                    s = s.replace('"-Infinity"', 'float("-inf")')
                    s = s.replace('"NaN"', 'float("nan")')
                    return json.loads(s)

                parsed_output = json_loads_with_infinity(stdout_str)
                logger.debug(f"Parsed execution output: {parsed_output}")
                return parsed_output, None
            except json.JSONDecodeError as e:
                error_message = f"Failed to decode JSON output: {e}. Raw output: '{stdout_str}'"
                logger.error(error_message)
                return None, error_message
            except Exception as e:
                error_message = f"Error processing script output: {e}. Raw output: '{stdout_str}'"
                logger.error(error_message)
                return None, error_message

        except asyncio.TimeoutError:
            if proc:
                try:
                    proc.kill()
                    await proc.wait()
                except ProcessLookupError:
                    pass
                except Exception as e_kill:
                    logger.error(f"Error trying to kill timed-out process: {e_kill}")
            logger.warning(f"Code execution timed out after {timeout} seconds for function {task_for_examples.function_name_to_evolve}.")
            return None, f"Execution timed out after {timeout} seconds."
        except Exception as e:
            logger.error(f"An unexpected error occurred during code execution: {e}", exc_info=True)
            return None, f"Unexpected execution error: {str(e)}"
        finally:
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except Exception as e_cleanup:
                logger.error(f"Error during cleanup of temp files: {e_cleanup}")

    def _run_pytest(self, code: str, suite: TestSuite, timeout_seconds: int) -> Tuple[Dict[str, Any], str]:
        """Run pytest suite on the provided code."""
        temp_dir = tempfile.mkdtemp()
        try:
            candidate_path = os.path.join(temp_dir, "candidate.py")
            with open(candidate_path, "w") as f:
                f.write(code)

            for filename, contents in suite.files.items():
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "w") as tf:
                    tf.write(contents)

            cmd = ["pytest", "-q"]
            logger.debug(f"Running pytest: {' '.join(cmd)} in {temp_dir}")

            start_time = time.monotonic()
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=temp_dir)
            try:
                stdout, stderr = proc.communicate(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                logger.warning(f"Pytest timed out after {timeout_seconds}s")
                return {}, f"Timeout after {timeout_seconds}s"

            runtime = (time.monotonic() - start_time) * 1000
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")
            logger.debug(f"Pytest stdout:\n{stdout_str}")
            if stderr_str:
                logger.debug(f"Pytest stderr:\n{stderr_str}")

            passed = failed = 0
            match_pass = re.search(r"(\d+)\s+passed", stdout_str)
            if match_pass:
                passed = int(match_pass.group(1))
            match_fail = re.search(r"(\d+)\s+failed", stdout_str)
            if match_fail:
                failed = int(match_fail.group(1))
            if not match_pass and not match_fail:
                logger.warning("Could not parse pytest summary")

            results = {"passed": passed, "failed": failed, "runtime_ms": runtime}
            return results, stderr_str if proc.returncode != 0 else None
        except Exception as e:
            logger.error("Error running pytest", exc_info=True)
            return {}, str(e)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _assess_correctness(self, execution_results: Dict[str, Any], expected_outputs: Optional[List[Dict[str, Any]]] = None) -> Tuple[float, int, int]:
        """Assess correctness either from I/O examples or pytest results."""
        if expected_outputs is not None:
            passed_tests = 0
            total_tests = len(expected_outputs)

            if not execution_results or "test_outputs" not in execution_results:
                logger.warning("Execution results are missing 'test_outputs' field.")
                return 0.0, 0, total_tests

            actual_test_outputs = execution_results["test_outputs"]

            if len(actual_test_outputs) != total_tests:
                logger.warning(
                    f"Mismatch in number of test outputs ({len(actual_test_outputs)}) and expected outputs ({total_tests}). Some tests might have crashed before producing output."
                )

            for i, expected in enumerate(expected_outputs):
                actual_output_detail = next((res for res in actual_test_outputs if res.get("test_case_id") == i), None)

                if actual_output_detail and actual_output_detail.get("status") == "success":
                    actual = actual_output_detail.get("output")
                    expected_val = expected["output"]

                    if self._compare_outputs(actual, expected_val):
                        passed_tests += 1
                    else:
                        logger.debug(f"Test case {i} failed: Expected '{expected_val}', Got '{actual}'")
                elif actual_output_detail:
                    logger.debug(f"Test case {i} had error: {actual_output_detail.get('error')}")
                else:
                    logger.debug(f"Test case {i}: No output found in results.")

            if total_tests == 0:
                return 1.0, 0, 0

            correctness = passed_tests / total_tests
            return correctness, passed_tests, total_tests
        else:
            passed = execution_results.get("passed", 0)
            failed = execution_results.get("failed", 0)
            total = passed + failed
            if total == 0:
                return 0.0, 0, 0
            correctness = passed / total
            return correctness, passed, total

    async def evaluate_program(self, program: Program, task: TaskDefinition) -> Program:
        logger.info(f"Evaluating program: {program.id} for task: {task.id}")
        program.status = "evaluating"
        program.errors = []
        program.fitness_scores = {"correctness": 0.0, "runtime_ms": float('inf')}

        syntax_errors = self._check_syntax(program.code)
        if syntax_errors:
            program.errors.extend(syntax_errors)
            program.fitness_scores["correctness"] = 0.0
            program.status = "failed_evaluation"
            logger.warning(f"Syntax errors found in program {program.id}: {syntax_errors}")
            return program

        logger.debug(f"Syntax check passed for program {program.id}.")

        if task.test_suite:
            logger.debug(f"Running pytest suite for program {program.id}.")
            results, error = self._run_pytest(program.code, task.test_suite, self.evaluation_timeout_seconds)
            if error:
                logger.warning(f"Pytest error for program {program.id}: {error}")
                program.errors.append(f"Pytest Error: {error}")
            correctness, passed_tests, total_tests = self._assess_correctness(results)
            program.fitness_scores["correctness"] = correctness
            program.fitness_scores["passed_tests"] = float(passed_tests)
            program.fitness_scores["total_tests"] = float(total_tests)
            program.fitness_scores["runtime_ms"] = results.get("runtime_ms", float('inf'))
            program.status = "evaluated" if correctness == 1.0 and not error else "failed_evaluation"
            return program

        if task.input_output_examples:
            logger.debug(f"Executing program {program.id} against {len(task.input_output_examples)} test cases.")
            execution_results, execution_error = await self._execute_code_safely(
                program.code,
                task_for_examples=task,
                max_memory_mb=task.max_memory_mb
            )
            
            if execution_error:
                logger.warning(f"Execution error for program {program.id}: {execution_error}")
                program.errors.append(f"Execution Error: {execution_error}")
                program.fitness_scores["correctness"] = 0.0
            program.status = "failed_evaluation"            

            logger.debug(f"Execution results for program {program.id}: {execution_results}")
            
            correctness, passed_tests, total_tests = self._assess_correctness(execution_results, task.input_output_examples)
            program.fitness_scores["correctness"] = correctness
            program.fitness_scores["passed_tests"] = float(passed_tests)
            program.fitness_scores["total_tests"] = float(total_tests)
            logger.info(f"Program {program.id} correctness: {correctness} ({passed_tests}/{total_tests} tests passed)")

            if correctness < 1.0:
                program.errors.append(f"Failed {total_tests - passed_tests} out of {total_tests} test cases.")
                 
            return program
        else:
            logger.info(f"No input/output examples provided for task {task.id}. Skipping execution-based correctness check for program {program.id}.")
            program.fitness_scores["correctness"] = 0.5
            program.status = "evaluated"

        if not program.errors:
            program.status = "evaluated"
        else:
            program.status = "failed_evaluation"
        
        logger.info(f"Evaluation complete for program {program.id}. Status: {program.status}, Fitness: {program.fitness_scores}")
        return program

    async def execute(self, program: Program, task: TaskDefinition) -> Program:
        return await self.evaluate_program(program, task)

    def _compare_outputs(self, actual: Any, expected: Any) -> bool:
        logger.debug(f"Comparing outputs. Actual: {type(actual)}{actual}, Expected: {type(expected)}{expected}")
        
        if isinstance(actual, float) and isinstance(expected, float):
            TOLERANCE = 1e-9 # This could also be made configurable via settings.py later.
            is_close = math.isclose(actual, expected, rel_tol=TOLERANCE, abs_tol=TOLERANCE)
            if not is_close:
                logger.debug(f"Float comparison: {actual} vs {expected} is NOT close (tolerance: {TOLERANCE}).")
            return is_close
        
        # Fallback to direct equality for other types
        are_equal = actual == expected

        return are_equal

                                                 
                                                              
                                                                                              
                                                         
                                                        
                                                                    