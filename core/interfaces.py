from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
import time

@dataclass
class Program:
    id: str
    code: str
    fitness_scores: Dict[str, float] = field(default_factory=dict)                                                 
    generation: int = 0
    parent_id: Optional[str] = None
    island_id: Optional[int] = None
    errors: List[str] = field(default_factory=list)
    status: str = "unevaluated"
    created_at: float = field(default_factory=lambda: time.time())  # Track program age


@dataclass
class TestSuite:
    """Container for test suite information used across agents."""
    # Mapping of filename to test contents when interacting with pytest
    files: Dict[str, str] = field(default_factory=dict)
    # Optional human readable explanation of the tests
    explanation: str = ""
    # List of structured test case dictionaries returned by the test generator
    cases: List[Dict[str, Any]] = field(default_factory=list)
    # Raw text returned from the LLM when generating tests
    raw: Optional[str] = None
    # Convenience attribute for simple string based test code
    tests_code: str = ""

@dataclass
class TaskDefinition:
    id: str
    description: str                                              
    function_name_to_evolve: Optional[str] = None                                                      
    input_output_examples: Optional[List[Dict[str, Any]]] = None

    test_suite: Optional[TestSuite] = None
    evaluation_criteria: Optional[Dict[str, Any]] = None                                                            
    initial_code_prompt: Optional[str] = "Provide an initial Python solution for the following problem:"
    allowed_imports: Optional[List[str]] = None


@dataclass
class TestCase:
    input: Any
    output: Any


class BaseAgent(ABC):
    """Base class for all agents."""
    @abstractmethod
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Main execution method for an agent."""
        pass

class TaskManagerInterface(BaseAgent):
    @abstractmethod
    async def manage_evolutionary_cycle(self):
        pass

class PromptDesignerInterface(BaseAgent):
    @abstractmethod
    def design_initial_prompt(self, task: TaskDefinition) -> str:
        pass

    @abstractmethod
    def design_mutation_prompt(self, task: TaskDefinition, parent_program: Program, evaluation_feedback: Optional[Dict] = None) -> str:
        pass

    @abstractmethod
    def design_bug_fix_prompt(self, task: TaskDefinition, program: Program, error_info: Dict) -> str:
        pass

class CodeGeneratorInterface(BaseAgent):
    @abstractmethod
    async def generate_code(self, prompt: str, model_name: Optional[str] = None, temperature: Optional[float] = 0.7, output_format: str = "code") -> str:
        pass

class TestGeneratorInterface(BaseAgent):
    @abstractmethod
    async def generate_tests(self, brief: str) -> TestSuite:
        pass

class EvaluatorAgentInterface(BaseAgent):
    @abstractmethod
    async def evaluate_program(self, program: Program, task: TaskDefinition) -> Program:
        pass

class DatabaseAgentInterface(BaseAgent):
    @abstractmethod
    async def save_program(self, program: Program):
        pass

    @abstractmethod
    async def get_program(self, program_id: str) -> Optional[Program]:
        pass

    @abstractmethod
    async def get_best_programs(self, task_id: str, limit: int = 10, objective: Optional[str] = None) -> List[Program]:
        pass
    
    @abstractmethod
    async def get_programs_for_next_generation(self, task_id: str, generation_size: int) -> List[Program]:
        pass

class SelectionControllerInterface(BaseAgent):
    @abstractmethod
    def select_parents(self, evaluated_programs: List[Program], num_parents: int) -> List[Program]:
        pass

    @abstractmethod
    def select_survivors(self, current_population: List[Program], offspring_population: List[Program], population_size: int) -> List[Program]:
        pass

class RLFineTunerInterface(BaseAgent):
    @abstractmethod
    async def update_policy(self, experience_data: List[Dict]):
        pass

class MonitoringAgentInterface(BaseAgent):
    @abstractmethod
    async def log_metrics(self, metrics: Dict):
        pass

    @abstractmethod
    async def report_status(self):
        pass

                                                                      