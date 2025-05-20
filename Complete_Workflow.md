# OpenAlpha_Evolve: Project Workflow and Code Explanation

This document provides a detailed explanation of the OpenAlpha_Evolve project, its workflow, the role of each component (agent and module), and how they interact to achieve autonomous algorithmic discovery.

## 1. Core Philosophy and Goal

OpenAlpha_Evolve aims to emulate and extend the concept of AI-driven algorithm discovery, as seen in systems like Google's AlphaEvolve. The primary goal is to create a system that can:
1.  Understand a problem defined by a user.
2.  Autonomously generate potential algorithmic solutions (programs) using Large Language Models (LLMs).
3.  Evaluate these solutions for correctness and other quality metrics.
4.  Iteratively refine and improve these solutions through an evolutionary process.
5.  Store and manage the discovered algorithms, promoting diversity and quality.

The system is designed to be modular and extensible, allowing researchers and developers to experiment with different LLMs, evolutionary strategies, and evaluation techniques.

## 2. Key Components and Files

The project is structured into several core components, primarily agents and configuration modules:

*   **Main Entry Points**:
    *   `main.py`: Command-line interface to run the evolutionary process for a predefined task.
    *   `app.py`: Gradio-based web interface for interactively defining tasks and running the evolution.
*   **Configuration**:
    *   `config/settings.py`: Centralized configuration for API keys, LLM model names, evolutionary parameters (population size, generations, tournament size, etc.), database settings, logging, and behavioral descriptor thresholds.
    *   `.env` (user-created from `.env.example`): Stores sensitive information like API keys.
*   **Core Interfaces and Data Structures**:
    *   `core/interfaces.py`: Defines abstract base classes for all agents (`...Interface`) and key data structures:
        *   `Program`: Represents a candidate algorithmic solution, including its code, fitness scores, generation, parent ID, errors, status, and behavioral descriptors.
        *   `TaskDefinition`: Encapsulates the problem to be solved, including its description, I/O examples, function name, evaluation criteria, and allowed imports.
*   **Agents (each in its own subdirectory)**:
    *   `task_manager/agent.py` (`TaskManagerAgent`): Orchestrates the entire evolutionary process.
    *   `prompt_designer/agent.py` (`PromptDesignerAgent`): Crafts prompts for the LLM for initial code generation, mutation, and bug-fixing.
    *   `code_generator/agent.py` (`CodeGeneratorAgent`): Interacts with the LLM (e.g., Gemini API) to generate code or diffs, and applies these diffs.
    *   `evaluator_agent/agent.py` (`EvaluatorAgent`): Evaluates generated programs for syntax correctness and functional correctness against test cases in a sandboxed environment. Computes fitness scores and behavioral descriptors.
    *   `database_agent/`
        *   `agent.py` (`InMemoryDatabaseAgent`): An in-memory database for storing programs (simpler, non-persistent).
        *   `sqlite_agent.py` (`SQLiteDatabaseAgent`): A persistent database using SQLite, implementing the MAP-Elites archive.
    *   `selection_controller/agent.py` (`SelectionControllerAgent`): Implements strategies for selecting parent programs for reproduction and (previously) survivor programs. Now primarily focused on parent selection from the MAP-Elites archive.
    *   `monitoring_agent/agent.py` (`MonitoringAgent`): Logs progress, archive status, and other metrics. (Future: visualization).
    *   `test_generator/agent.py` (`TestGeneratorAgent`): Creates unit tests from a natural-language brief and coordinates the approval workflow before evolution begins.
    *   `rl_finetuner/agent.py` (`RLFineTunerAgent`): Placeholder for future reinforcement learning-based optimization of prompts or LLM parameters.
*   **Logging**:
    *   `alpha_evolve.log`: Default log file where detailed operational logs are stored.

## 3. Overall Workflow

The system operates in an evolutionary loop, managed by the `TaskManagerAgent`. Here's a high-level overview of the workflow, particularly when using the MAP-Elites approach with the `SQLiteDatabaseAgent`:

**Phase 0: Setup and Task Definition**

1.  **Configuration Loading (`config/settings.py`)**:
    *   Loads API keys (from `.env`), LLM model names, evolutionary parameters (population size, generations, fitness weights, MAP-Elites behavioral descriptor thresholds, etc.), database settings, and logging configurations.
2.  **Task Definition (User or `main.py`/`app.py`)**:
    *   A `TaskDefinition` object is created. This includes:
        *   `id`: Unique identifier.
        *   `description`: Detailed natural language description of the problem.
        *   `function_name_to_evolve`: The target function name.
        *   `input_output_examples`: A list of I/O examples for testing correctness.
        *   `allowed_imports`: List of standard library imports allowed.
        *   `evaluation_criteria` (optional).
        *   `initial_code_prompt` (optional).

**Phase 1: Initialization (`TaskManagerAgent.initialize_population`)**

1.  **Agent Instantiation (`TaskManagerAgent.__init__`)**:
    *   The `TaskManagerAgent` initializes all other necessary agents:
        *   `PromptDesignerAgent`: For creating prompts.
        *   `CodeGeneratorAgent`: For LLM interactions.
        *   `EvaluatorAgent`: For evaluating programs.
        *   `DatabaseAgent` (either `InMemoryDatabaseAgent` or `SQLiteDatabaseAgent` based on `settings.DATABASE_TYPE`).
        *   `SelectionControllerAgent`: For selecting parents.
        *   `MonitoringAgent`: For logging and reporting.
2.  **Initial Population Generation**:
    *   A loop runs for `settings.POPULATION_SIZE` iterations.
    *   **Prompt Design (`PromptDesignerAgent.design_initial_prompt`)**: Generates a prompt to ask the LLM for an initial solution to the `TaskDefinition`.
    *   **Code Generation (`CodeGeneratorAgent.generate_code`)**: Sends the prompt to the configured LLM. The LLM returns the generated code as a string.
    *   **Program Object Creation**: A `Program` object is created with the generated code, initial status ("unevaluated"), generation 0, and a unique ID.
    *   **Saving Program (`DatabaseAgent.save_program`)**: The unevaluated `Program` object is saved to the database.
3.  **Evaluation of Initial Population (`TaskManagerAgent.evaluate_population`)**:
    *   The list of newly generated `Program` objects is passed to the `EvaluatorAgent`.
    *   For each program:
        *   **Syntax Check (`EvaluatorAgent._check_syntax`)**: Uses `ast.parse` to check for Python syntax errors. If errors occur, the program status is updated, and errors are logged.
        *   **Safe Execution (`EvaluatorAgent._execute_code_safely`)**:
            *   A temporary Python script is created containing the program's code and a test harness. This harness iterates through the `input_output_examples` from the `TaskDefinition`.
            *   The script is executed in a separate Python subprocess with a timeout (`settings.EVALUATION_TIMEOUT_SECONDS`).
            *   Stdout and stderr are captured. The script outputs results (actual outputs for test cases, runtimes) as a JSON string.
        *   **Correctness Assessment (`EvaluatorAgent._assess_correctness`)**: Compares the actual outputs from execution with the expected outputs from `TaskDefinition.input_output_examples`. Calculates a correctness score (e.g., percentage of test cases passed).
        *   **Fitness Score Calculation**: Populates `program.fitness_scores` (e.g., `{"correctness": score, "runtime_ms": avg_runtime}`).
        *   **Behavioral Descriptor Calculation (`EvaluatorAgent` various methods like `_get_runtime_category`, `_get_codelen_category`)**:
            *   Calculates behavioral descriptors based on `settings.RUNTIME_BD_THRESHOLDS` and `settings.CODELEN_BD_THRESHOLDS` (e.g., runtime category: "fast", "medium", "slow"; code length category: "short", "medium", "long").
            *   These descriptors are stored as a JSON string in `program.behavioral_descriptors`.
        *   Updates program status to "evaluated" or "failed_evaluation".
    *   **Saving Evaluated Programs (`DatabaseAgent.save_program`)**: The updated `Program` objects (with fitness scores, status, errors, BDs) are saved to the database.
4.  **Offering to MAP-Elites Archive (`TaskManagerAgent.initialize_population` calls `DatabaseAgent.offer_to_archive`)**:
    *   For each successfully evaluated initial program:
        *   **Scalar Fitness Calculation (`TaskManagerAgent._calculate_scalar_fitness`)**: Calculates a single scalar fitness score from `program.fitness_scores` using `settings.FITNESS_WEIGHT_CORRECTNESS` and `settings.FITNESS_WEIGHT_RUNTIME`.
        *   **Offer to Archive (`SQLiteDatabaseAgent.offer_to_archive`)**:
            *   The program, its scalar fitness, and task ID are offered to the MAP-Elites archive.
            *   The `cell_id` is constructed from the program's `behavioral_descriptors` and `task_id`.
            *   The method checks if the program is better than the current elite in that cell.
            *   If it is, it atomically (within a transaction):
                1.  Removes the program from any *other* cell it might have occupied for this task (to handle "movement" between cells and maintain `UNIQUE(task_id, elite_program_id)` constraint).
                2.  Inserts or replaces the program as the elite in the target cell, updating `scalar_fitness` and `last_updated` timestamp.
            *   Returns `True` if the program became an elite, `False` otherwise.
5.  **Archive Status Report (`TaskManagerAgent` calls `MonitoringAgent.report_archive_status`)**:
    *   The `TaskManagerAgent` calls `_get_archive_summary_for_monitoring` (which fetches elites and formats them) and then calls `MonitoringAgent.report_archive_status` to log the current state of the MAP-Elites archive.

**Phase 2: Evolutionary Cycle (`TaskManagerAgent.manage_evolutionary_cycle`)**

This loop runs for `settings.GENERATIONS`:

1.  **Retrieve Elites (`DatabaseAgent.get_elites_by_task`)**:
    *   Fetches all current elite programs for the given `task_id` from the `map_elites_archive` table. These programs form the basis for parent selection.
2.  **Parent Selection (`SelectionControllerAgent.select_parents`)**:
    *   The list of current elites is passed to this method.
    *   **Tournament Selection**: `num_parents` (e.g., `settings.POPULATION_SIZE // 2`) parents are selected from the elites.
        *   For each parent to select:
            *   A "tournament" of `settings.TOURNAMENT_SIZE` individuals is randomly sampled from the elites.
            *   The individual with the best scalar fitness (calculated by `_calculate_scalar_fitness`) in the tournament wins and is selected as a parent.
        *   This process allows for diversity as less-fit individuals can still be selected if they win their local tournament. Parents can be selected multiple times (selection with replacement).
3.  **Offspring Generation (`TaskManagerAgent.generate_offspring` called in a loop)**:
    *   For each selected parent (or pair, if crossover were implemented), one or more offspring are generated up to `settings.POPULATION_SIZE` new individuals for the generation.
    *   **Determine Prompt Type**:
        *   If the parent program has significant errors and low correctness, a "bug_fix" prompt is designed.
        *   Otherwise, a "mutation" prompt is designed.
    *   **Prompt Design (`PromptDesignerAgent.design_mutation_prompt` or `design_bug_fix_prompt`)**:
        *   Constructs a detailed prompt for the LLM. This includes:
            *   Role-playing instructions for the LLM.
            *   The overall task description.
            *   The code of the parent program.
            *   Evaluation feedback from the parent (errors, correctness, runtime).
            *   Specific instructions for the LLM to provide its output in a "diff" format:
                ```
                <<<<<<< SEARCH
                # Original code lines
                =======
                # New code lines
                >>>>>>> REPLACE
                ```
    *   **Code Generation (Diff) (`CodeGeneratorAgent.execute`, which calls `generate_code` with `output_format="diff"`)**:
        *   The prompt (requesting a diff) is sent to the LLM.
        *   The LLM is expected to return a diff string.
    *   **Diff Application (`CodeGeneratorAgent._apply_diff`)**:
        *   The received diff string is parsed.
        *   The SEARCH blocks in the diff are matched against the parent's code.
        *   The corresponding REPLACE blocks are used to modify the parent code, creating the offspring's code. This step includes logic to handle minor variations in whitespace/indentation and attempts fuzzy matching.
        *   If diff application is successful and results in a change, a new `Program` object is created for the offspring. Status is "unevaluated", generation number is incremented.
    *   **Saving Offspring (`DatabaseAgent.save_program`)**: The unevaluated offspring `Program` object is saved to the database.
4.  **Evaluation of Offspring (`TaskManagerAgent.evaluate_population`)**:
    *   Same process as in Phase 1, Step 3. Offspring are evaluated, fitness scores and behavioral descriptors are calculated, and the updated `Program` objects are saved.
5.  **Offering Offspring to Archive (`TaskManagerAgent` calls `DatabaseAgent.offer_to_archive`)**:
    *   Same process as in Phase 1, Step 4. Each successfully evaluated offspring is offered to the MAP-Elites archive.
6.  **End-of-Generation Reporting (`TaskManagerAgent`)**:
    *   Logs information about the best elite currently in the archive.
    *   Calls `MonitoringAgent.report_archive_status` to log the archive's state.

**Phase 3: Completion**

1.  **Final Report (`TaskManagerAgent`)**:
    *   After all generations are complete, the `TaskManagerAgent` retrieves the final set of best elites (e.g., top `settings.ELITISM_COUNT`) from the `DatabaseAgent.get_elites_by_task`.
    *   Logs the details of these best programs.
    *   Calls `MonitoringAgent.report_archive_status` one last time.
    *   Returns the list of best elite programs.

## 4. Detailed Agent Responsibilities

### 4.1. `TaskManagerAgent` (`task_manager/agent.py`)
*   **Orchestration**: The central coordinator.
*   **Initialization**: Sets up other agents, loads configurations.
*   `initialize_population()`: Generates, evaluates, and archives the initial set of programs.
*   `manage_evolutionary_cycle()`: Runs the main evolutionary loop (parent selection, offspring generation, evaluation, archiving).
*   `generate_offspring()`: Manages the process of creating a new program from a parent using `PromptDesignerAgent` and `CodeGeneratorAgent`.
*   `evaluate_population()`: Coordinates the evaluation of a list of programs using `EvaluatorAgent`.
*   `_calculate_scalar_fitness()`: Computes a single fitness value for a program.
*   `_get_archive_summary_for_monitoring()`: Prepares data for the `MonitoringAgent`.
*   `execute()`: Main entry point for the agent, typically calls `manage_evolutionary_cycle()`.

### 4.2. `PromptDesignerAgent` (`prompt_designer/agent.py`)
*   **Prompt Crafting**: Designs specific prompts for the LLM based on the current context (initial generation, mutation, bug-fix).
*   `design_initial_prompt()`: Creates a prompt to generate a brand-new solution for the task. Includes task description, I/O examples, function name, allowed imports, and formatting instructions.
*   `design_mutation_prompt()`: Creates a prompt to modify an existing `Program`. Includes parent's code, evaluation feedback (correctness, runtime, errors), and strict instructions for the LLM to output changes in the custom "diff" format.
*   `design_bug_fix_prompt()`: Similar to mutation, but specifically targets fixing bugs. Includes parent's code, error messages, execution output, and diff format instructions.
*   Helper methods like `_format_input_output_examples()` and `_format_evaluation_feedback()` assist in constructing detailed prompts.

### 4.3. `CodeGeneratorAgent` (`code_generator/agent.py`)
*   **LLM Interaction**: Handles all communication with the configured Gemini LLM.
*   `generate_code()`:
    *   Takes a prompt, model name (optional), temperature (optional), and `output_format` ("code" or "diff").
    *   If `output_format` is "diff", appends detailed instructions about the diff format to the prompt.
    *   Manages API retries in case of transient errors from the LLM.
    *   Sends the prompt to the LLM and receives the generated text.
*   `_clean_llm_output()`: Cleans the raw text from the LLM, typically by removing markdown code fences (e.g., ` ```python ... ``` `).
*   `_apply_diff()`:
    *   Parses the diff text (expected in `<<<<<<< SEARCH ... ======= ... >>>>>>> REPLACE` format) received from the LLM.
    *   Attempts to apply these changes to the `parent_code`. It tries exact matching for the `SEARCH` block and then falls back to a whitespace-normalized matching and a line-based fuzzy matching approach to increase robustness.
*   `execute()`: A wrapper method that calls `generate_code` and, if `output_format` is "diff" and `parent_code_for_diff` is provided, subsequently calls `_apply_diff`.

### 4.4. `EvaluatorAgent` (`evaluator_agent/agent.py`)
*   **Program Evaluation**: Assesses the quality of a given `Program`.
*   `evaluate_program()`: Orchestrates the evaluation steps for a single program.
*   `_check_syntax()`: Uses Python's `ast.parse()` to check for syntax errors in the code.
*   `_execute_code_safely()`:
    *   Creates a temporary Python script that includes the program's code and a test harness.
    *   The test harness loads the `input_output_examples` from the `TaskDefinition` and executes the target function against each input.
    *   Runs this script in an isolated subprocess with a specified timeout (`settings.EVALUATION_TIMEOUT_SECONDS`).
    *   Captures stdout, stderr, and execution time for each test case.
    *   Handles `Infinity` and `NaN` in JSON output/input for test cases.
*   `_assess_correctness()`: Compares the actual outputs produced by the executed code with the expected outputs from the `TaskDefinition`. Calculates correctness score.
*   `_get_runtime_category()` & `_get_codelen_category()`: Determine behavioral descriptor categories based on thresholds in `config/settings.py`. These are used for MAP-Elites.
*   The `evaluate_program` method updates the `Program` object with fitness scores (`correctness`, `runtime_ms`), `status`, `errors`, and `behavioral_descriptors`.

### 4.5. `DatabaseAgent` (`database_agent/sqlite_agent.py` and `database_agent/agent.py`)
*   **Persistence Layer**: Stores and retrieves `Program` objects and manages the MAP-Elites archive.
*   `SQLiteDatabaseAgent`:
    *   `_initialize_db()`: Creates tables (`programs`, `map_elites_archive`) if they don't exist using `DB_SCHEMA`.
    *   `save_program()`: Saves a `Program` object to the `programs` table (INSERT OR REPLACE).
    *   `get_program()`: Retrieves a specific program by ID.
    *   `get_elites_by_task()`: Retrieves elite programs for a specific task from the `map_elites_archive` table, joined with the `programs` table, ordered by scalar fitness.
    *   `offer_to_archive()`: Implements the core MAP-Elites logic:
        *   Calculates `cell_id` from program's behavioral descriptors and task ID.
        *   If the program is better than the current elite in that cell (or cell is empty):
            *   Atomically (transaction):
                1.  Removes the program from any other cell it might occupy for the same task (ensuring `UNIQUE(task_id, elite_program_id)`).
                2.  Inserts/replaces the program into the target cell in `map_elites_archive` with its `scalar_fitness` and updates `last_updated`.
*   `InMemoryDatabaseAgent`: Provides a simpler, non-persistent version. MAP-Elites features are placeholder and log warnings.

### 4.6. `SelectionControllerAgent` (`selection_controller/agent.py`)
*   **Parent Selection**: Chooses programs from the population (typically the MAP-Elites archive) to be parents for the next generation.
*   `_calculate_scalar_fitness()`: Calculates a scalar fitness value from a program's `fitness_scores` dictionary using weights from `config/settings.py`.
*   `select_parents()`:
    *   Currently implemented using **Tournament Selection**.
    *   Takes the list of current elites (from `TaskManagerAgent`) and `num_parents` to select.
    *   For each parent slot, it randomly selects `settings.TOURNAMENT_SIZE` individuals from the elites and picks the one with the best scalar fitness.
    *   This method allows for diverse parent selection.
*   `select_survivors()`: (Less relevant in the MAP-Elites archive context, as the archive inherently handles elitism per cell). If used in a traditional EA, it would select the best individuals from a combined population of current individuals and offspring.

### 4.7. `MonitoringAgent` (`monitoring_agent/agent.py`)
*   **Observability**: Logs various aspects of the evolutionary process.
*   `report_evolutionary_progress()`: Logs generation number, best program details, and population averages.
*   `report_archive_status()`: Logs the current status of the MAP-Elites archive, including `cell_id`, `elite_program_id`, and `scalar_fitness` for each elite.
*   Other methods for logging generic events or errors.

### 4.8. `RLFineTunerAgent` (`rl_finetuner/agent.py`)
*   **Placeholder**: Intended for future implementation of Reinforcement Learning techniques to optimize prompt engineering or LLM parameters. Currently, its methods are stubs.

## 5. Data Flow for a Single Program Evolution (Mutation Example)

1.  **`TaskManagerAgent`** selects an elite `Program` (P_old) from the archive via `SelectionControllerAgent`.
2.  **`TaskManagerAgent`** requests a mutation prompt from `PromptDesignerAgent`, passing P_old and its evaluation feedback.
3.  **`PromptDesignerAgent`** creates `mutation_prompt_text` asking for a "diff".
4.  **`TaskManagerAgent`** calls `CodeGeneratorAgent.execute()` with `mutation_prompt_text`, `output_format="diff"`, and `parent_code_for_diff=P_old.code`.
5.  **`CodeGeneratorAgent`** sends `mutation_prompt_text` (with added diff instructions) to the LLM.
6.  **LLM** returns `diff_text`.
7.  **`CodeGeneratorAgent`** calls `_apply_diff(P_old.code, diff_text)` to get `new_code`.
8.  If `new_code` is valid and different, **`CodeGeneratorAgent`** returns it.
9.  **`TaskManagerAgent`** creates a new `Program` object (P_new) with `new_code`, status "unevaluated", correct generation number, and `parent_id=P_old.id`.
10. **`TaskManagerAgent`** saves P_new to database (`DatabaseAgent.save_program`).
11. **`TaskManagerAgent`** calls `EvaluatorAgent.evaluate_program(P_new, task_definition)`.
12. **`EvaluatorAgent`**:
    *   Checks syntax of `P_new.code`.
    *   Executes `P_new.code` against test cases.
    *   Calculates `P_new.fitness_scores` and `P_new.behavioral_descriptors`.
    *   Updates `P_new.status` and `P_new.errors`.
13. **`TaskManagerAgent`** saves the evaluated P_new to database (`DatabaseAgent.save_program`).
14. **`TaskManagerAgent`** calculates `scalar_fitness` for P_new.
15. **`TaskManagerAgent`** calls `DatabaseAgent.offer_to_archive(P_new, scalar_fitness, task_id)`.
16. **`DatabaseAgent`** updates the `map_elites_archive` table if P_new qualifies as an elite in its corresponding cell.

This cycle repeats for all offspring and across all generations.

## 6. Prototype-on-Demand Workflow

An optional flow allows users to start from a plain-language description instead of prewritten tests:

1. **Brief Submission**: The user supplies a short natural-language brief describing the desired functionality.
2. **Test Generation**: `TestGeneratorAgent` converts the brief into candidate unit tests.
3. **Approval Loop**: The user reviews these tests, accepting or editing them until they accurately capture the goal.
4. **Automated Evolution**: Once approved, the standard evolutionary cycle runs using the new tests until all of them pass.

## 7. Configuration (`config/settings.py`) Highlights

*   `GEMINI_API_KEY`: Essential for LLM communication.
*   `GEMINI_PRO_MODEL_NAME`, `GEMINI_FLASH_MODEL_NAME`: Specify which LLM models to use.
*   `POPULATION_SIZE`: Number of new programs generated or offspring created per generation.
*   `GENERATIONS`: Total number of evolutionary cycles.
*   `TOURNAMENT_SIZE`: Number of individuals competing in each tournament during parent selection.
*   `FITNESS_WEIGHT_CORRECTNESS`, `FITNESS_WEIGHT_RUNTIME`: Used to scalarize multi-objective fitness scores.
*   `RUNTIME_BD_THRESHOLDS`, `CODELEN_BD_THRESHOLDS`: Define categories for MAP-Elites behavioral descriptors.
*   `EVALUATION_TIMEOUT_SECONDS`: Max time for a program's execution during evaluation.
*   `DATABASE_TYPE`: "sqlite" or "in_memory".
*   `DATABASE_PATH`: Path for the SQLite database file.

## 8. Conclusion

OpenAlpha_Evolve provides a sophisticated, agent-based framework for exploring LLM-driven evolutionary algorithm discovery. Its modular design, coupled with features like MAP-Elites for diversity and robust evaluation, makes it a powerful tool for generating and refining algorithmic solutions. The detailed workflow described above illustrates the intricate interactions between its components to achieve this autonomous process. 
