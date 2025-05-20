# OpenAlpha_Evolve:( Contribute to Improve this Project )

![openalpha_evolve_workflow](https://github.com/user-attachments/assets/9d4709ad-0072-44ae-bbb5-7eea1c5fa08c)

OpenAlpha_Evolve is an open-source Python framework inspired by the groundbreaking research on autonomous coding agents like DeepMind's AlphaEvolve. It's a **regeneration** of the core idea: an intelligent system that iteratively writes, tests, and improves code using Large Language Models (LLMs) through LiteLLM, guided by the principles of evolution.

Our mission is to provide an accessible, understandable, and extensible platform for researchers, developers, and enthusiasts to explore the fascinating intersection of AI, code generation, and automated problem-solving.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)

---
![image](https://github.com/user-attachments/assets/ff498bb7-5608-46ca-9357-fd9b55b76800)
![image](https://github.com/user-attachments/assets/c1b4184a-f5d5-43fd-8f50-3e729c104e11)



## ✨ The Vision: AI-Driven Algorithmic Innovation

Imagine an agent that can:

*   Understand a complex problem description.
*   Generate initial algorithmic solutions.
*   Rigorously test its own code.
*   Learn from failures and successes.
*   Evolve increasingly sophisticated and efficient algorithms over time.

OpenAlpha_Evolve is a step towards this vision. It's not just about generating code; it's about creating a system that *discovers* and *refines* solutions autonomously.

---

## 🧠 How It Works: The Evolutionary Cycle

OpenAlpha_Evolve employs a modular, agent-based architecture to orchestrate an evolutionary process:

1.  **Task Definition**: You, the user, define the algorithmic "quest" – the problem to be solved, including examples of inputs and expected outputs.
2.  **Prompt Engineering (`PromptDesignerAgent`)**: This agent crafts intelligent prompts for the LLM. It designs:
    *   *Initial Prompts*: To generate the first set of candidate solutions.
    *   *Mutation Prompts*: To introduce variations and improvements to existing solutions, often requesting changes in a "diff" format.
    *   *Bug-Fix Prompts*: To guide the LLM in correcting errors from previous attempts, also typically expecting a "diff".
3.  **Code Generation (`CodeGeneratorAgent`)**: Powered by an LLM (currently configured for Gemini), this agent takes the prompts and generates Python code. If a "diff" is requested and received, it attempts to apply the changes to the parent code.
4.  **Evaluation (`EvaluatorAgent`)**: The generated code is put to the test!
    *   *Syntax Check*: Is the code valid Python?
    *   *Execution*: The code is run in a temporary, isolated environment against the input/output examples defined in the task.
    *   *Fitness Scoring*: Programs are scored based on correctness (how many test cases pass), efficiency (runtime), and other potential metrics.
5.  **Database (`DatabaseAgent`)**: All programs (code, fitness scores, generation, lineage) are stored, creating a record of the evolutionary history (currently in-memory).
6.  **Selection (`SelectionControllerAgent`)**: The "survival of the fittest" principle in action. This agent selects:
    *   *Parents*: Promising programs from the current generation to produce offspring.
    *   *Survivors*: The best programs from both the current population and new offspring to advance to the next generation.
7.  **Iteration**: This cycle repeats for a defined number of generations, with each new generation aiming to produce better solutions than the last.
8.  **Orchestration (`TaskManagerAgent`)**: The maestro of the operation, coordinating all other agents and managing the overall evolutionary loop.

---

## 🚀 Key Features

*   **LLM-Powered Code Generation**: Leverages state-of-the-art Large Language Models through LiteLLM, supporting multiple providers (OpenAI, Anthropic, Google, etc.).
*   **Evolutionary Algorithm Core**: Implements iterative improvement through selection, LLM-driven mutation/bug-fixing (via diffs), and survival.
*   **Modular Agent Architecture**: Easily extend or replace individual components (e.g., use a different LLM, database, or evaluation strategy).
*   **Automated Program Evaluation**: Syntax checking and functional testing against user-provided examples with timeout mechanisms.
*   **Configuration Management**: Easily tweak parameters like population size, number of generations, LLM models, and API settings via `config/settings.py`.
*   **Detailed Logging**: Comprehensive logs provide insights into each step of the evolutionary process.
*   **Diff-based Mutations**: The system is designed to use diffs for mutations and bug fixes, allowing for more targeted code modifications by the LLM.
*   **Open Source & Extensible**: Built with Python, designed for experimentation and community contributions.

---

## 📂 Project Structure

```
./
├── agents/                  # Core intelligent agents (subdirectories for each)
│   ├── code_generator/
│   ├── database_agent/
│   ├── evaluator_agent/
│   ├── prompt_designer/
│   ├── selection_controller/
│   ├── task_manager/
│   ├── rl_finetuner/      # Placeholder for Reinforcement Learning Fine-Tuner
│   └── monitoring_agent/  # Placeholder for Monitoring Agent
├── config/                  # Configuration files (settings.py)
├── core/                    # Core interfaces, data models (Program, TaskDefinition)
├── utils/                   # Utility functions (if any, currently minimal)
├── tests/                   # Unit and integration tests (placeholders, to be expanded)
├── scripts/                 # Helper scripts (e.g., diagram generation)
├── main.py                  # Main entry point to run the system
├── requirements.txt         # Project dependencies
├── .env.example             # Example for environment variables (copy to .env)
├── .gitignore               # Specifies intentionally untracked files that Git should ignore
├── LICENSE.md               # Project's license information (MIT License)
└── README.md                # This file!
```

---

## 🏁 Getting Started

1.  **Prerequisites**:
    *   Python 3.10+
    *   `pip` for package management
    *   `git` for cloning

2.  **Clone the Repository**:
    ```bash
    git clone https://github.com/shyamsaktawat/OpenAlpha_Evolve.git
    cd OpenAlpha_Evolve
    ```

3.  **Set Up a Virtual Environment** (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

4.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Set Up Environment Variables (Crucial for API Keys)**:
    *   Copy `.env.example` to a new file named `.env` in the project root:
        ```bash
        cp .env.example .env
        ```
    *   **Edit the `.env` file** and add your API keys and model configurations, more settings can be found in .env.example:
        ```env
        # LLM Configuration
        PRO_API_KEY="your_api_key_here"
        PRO_MODEL="your_model_name"

        FLASH_API_KEY="your_api_key_here"
        FLASH_MODEL="your_model_name"

        EVALUATION_API_KEY="your_api_key_here"
        EVALUATION_MODEL="your_model_name"
        ```
        *You can obtain API keys from your preferred LLM provider (OpenAI, Anthropic, Google, etc.).*
    *   The system will prioritize the keys from the `.env` file. If they're not found, it will use non-functional placeholders from `config/settings.py` and print a warning. **Ensure your `.env` file is correctly set up.**
    *   For detailed information about supported LLM providers and their configuration options, visit the [LiteLLM Documentation](https://docs.litellm.ai/docs/providers/).

6.  **Review Configuration (Optional)**:
    *   Open `config/settings.py`. Here you can:
        *   Change the default LLM models used for generation (`PRO_MODEL`) and evaluation (`EVALUATION_MODEL`).
        *   Adjust LiteLLM parameters like `LITELLM_MAX_TOKENS`, `LITELLM_TEMPERATURE`, etc.
        *   Set optional base URLs for each model (`PRO_BASE_URL`, `FLASH_BASE_URL`, `EVALUATION_BASE_URL`).
        *   Modify evolutionary parameters like `POPULATION_SIZE` and `GENERATIONS`.
        *   Adjust API retry settings or logging levels.

7.  **Run OpenAlpha_Evolve!**
    The `main.py` file is configured with an example task (Dijkstra's algorithm). To run it:
    ```bash
    python -m main
    ```
    Watch the logs in your terminal to see the evolutionary process unfold! Log files are also saved to `alpha_evolve.log` (by default).

8.  **Launch the Gradio Web Interface**
    You can also interact with the system through the web UI. To start the Gradio app:
    ```bash
    python app.py
    ```
    Gradio will display a local URL (e.g., http://127.0.0.1:7860) and a public share link if enabled. Open this in your browser to define custom tasks and run the evolution process interactively.

## Prototype-on-Demand Workflow

OpenAlpha_Evolve also supports a prototype-on-demand mode. In this flow you:

1. **Supply a natural-language brief.** The brief describes the functionality you want. A dedicated `TestGeneratorAgent` converts this description into unit tests.
2. **Review the generated tests.** You approve, reject or edit each test to ensure it matches your expectations.
3. **Automatic code evolution.** Once the tests are approved, the normal evolutionary loop runs until all tests pass.

### CLI Examples

Generate a prototype directly from the command line:

```bash
python prototype_on_demand.py --brief "return the nth Fibonacci number"
```

Read the brief from a file and specify an output directory:

```bash
python prototype_on_demand.py --brief-file brief.txt --output-dir ./runs/fib
```

---

## 💡 Defining Your Own Algorithmic Quests!

Want to challenge OpenAlpha_Evolve with a new problem? It's easy:

1.  **Open `main.py`**.
2.  **Modify the `TaskDefinition` object**:
    *   `id`: A unique string identifier for your task (e.g., "sort_list_task").
    *   `description`: A clear, detailed natural language description of the problem. This is crucial for the LLM to understand what to do. Be specific about function names, expected behavior, and constraints.
    *   `function_name_to_evolve`: The name of the Python function the agent should try to create/evolve (e.g., "custom_sort").
    *   `input_output_examples`: A list of dictionaries, each containing an `input` (arguments for your function) and the corresponding expected `output`. These are vital for evaluation.
        *   Inputs should be provided as a list if the function takes multiple positional arguments, or as a single value if it takes one.
        *   Use `float('inf')` or `float('-inf')` directly in your Python code defining these examples if needed by your problem (the evaluation harness handles JSON serialization/deserialization of these).
    *   `allowed_imports`: Specify a list of Python standard libraries that the generated code is allowed to import (e.g., `["heapq", "math", "sys"]`). This helps guide the LLM and can be important for the execution sandbox.
    *   (Optional) `evaluation_criteria`: Define how success is measured (currently primarily driven by correctness based on test cases).
    *   (Optional) `initial_code_prompt`: Override the default initial prompt if you need more specific instructions for the first code generation attempt.

3.  **Run the agent** as before: `python -m main`.

The quality of your `description` and the comprehensiveness of your `input_output_examples` significantly impact the agent's success!

---

## 🔮 The Horizon: Future Evolution

OpenAlpha_Evolve is a living project. Here are some directions we're excited to explore (and invite contributions for!):

*   **Advanced Evaluation Sandboxing**: Implementing more robust, secure sandboxing (e.g., using Docker or `nsjail`) for code execution to handle potentially unsafe code and complex dependencies.
*   **Sophisticated Fitness Metrics**: Beyond correctness and basic runtime, incorporating checks for code complexity (e.g., cyclomatic complexity), style (linting), resource usage (memory), and custom domain-specific metrics.
*   **Reinforcement Learning for Prompt Strategy**: Implementing the `RLFineTunerAgent` to dynamically optimize prompt engineering strategies based on performance feedback.
*   **Enhanced Monitoring & Visualization**: Developing tools (via `MonitoringAgent`) to visualize the evolutionary process, track fitness landscapes, and understand agent behavior (e.g., using a simple web dashboard or plots).
*   **Expanded LLM Provider Support**: Adding support for more LLM providers through LiteLLM's growing ecosystem.
*   **Self-Correction & Reflection**: Enabling the agent to analyze its own failures more deeply (e.g., analyze error messages, identify patterns in failed tests) and refine its problem-solving approach.
*   **Diverse Task Domains**: Applying OpenAlpha_Evolve to a wider range of problems in science, engineering, data analysis, and creative coding.
*   **Community-Driven Task Library**: Building a collection of interesting and challenging tasks contributed by the community.
*   **Improved Diff Application**: Making the diff application more robust or exploring alternative ways for the LLM to suggest modifications.
*   **Crossover Implementation**: Adding a genetic crossover mechanism as an alternative or supplement to LLM-driven mutation.

---

## 🤝 Join the Evolution: Contributing

This is an open invitation to collaborate! Whether you're an AI researcher, a Python developer, or simply an enthusiast, your contributions are welcome.

*   **Report Bugs**: Find an issue? Please create an issue on GitHub!
*   **Suggest Features**: Have an idea to make OpenAlpha_Evolve better? Open an issue to discuss it!
*   **Submit Pull Requests**:
    *   Fork the repository.
    *   Create a new branch for your feature or bugfix (`git checkout -b feature/your-feature-name`).
    *   Write clean, well-documented code.
    *   Add tests for your changes if applicable.
    *   Ensure your changes don't break existing functionality.
    *   Submit a pull request with a clear description of your changes!

Let's evolve this agent together!

---

## 📜 License

This project is licensed under the **MIT License**. See the `LICENSE.md` file for details.

---

## 🙏 Homage

OpenAlpha_Evolve is proudly inspired by the pioneering work of the Google DeepMind team on AlphaEvolve and other related research in LLM-driven code generation and automated discovery. This project aims to make the core concepts more accessible for broader experimentation and learning. We stand on the shoulders of giants.

---

*Disclaimer: This is an experimental project. Generated code may not always be optimal, correct, or secure. Always review and test code thoroughly, especially before using it in production environments.* 
