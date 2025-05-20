# Prototype-on-Demand Guidance

This repository includes a prototype-on-demand mode that converts a short natural-language brief into tests and then evolves code until those tests pass. Use these guidelines whenever extending or modifying the workflow.

## Prototype-on-Demand workflow
1. **Brief submission** – obtain a concise description of the desired behaviour.
2. **Test generation** – `TestGeneratorAgent` produces a `TestSuite` from the brief.
3. **Approval loop** – the user reviews the proposed tests and may accept, regenerate, edit or quit.
4. **Task creation** – when tests are approved, assemble a `TaskDefinition` with the selected function name and allowed imports.
5. **Evolution** – `TaskManagerAgent` runs the evolutionary cycle with the new tests until they all pass.
6. **Result saving** – write the best program to a file.
7. **Logging** – log the brief, the generated tests, all user decisions, and the final code to `alpha_evolve.log`.

## Functional requirements
- **F-1**: Accept a natural-language brief from the command line or UI.
- **F-2**: Generate candidate unit tests that express the brief as a `TestSuite`.
- **F-3**: Offer an interactive approval loop so the user can accept, regenerate, or edit the tests.
- **F-4**: Build a `TaskDefinition` using the approved tests, chosen function name, and allowed imports.
- **F-5**: Run the evolutionary process with `TaskManagerAgent` until all tests succeed.
- **F-6**: Output the best evolved program to disk.
- **F-7**: Record the brief, generated tests, user choices, and final code in the log file.

## Non-functional expectations
- **NF-1**: Keep interfaces responsive by using asynchronous functions when available.
- **NF-2**: Maintain a clear audit trail in `alpha_evolve.log`.
- **NF-3**: Surface informative errors if the LLM or evaluator fails while allowing the workflow to continue when possible.

## Running prototype-on-demand
Execute directly from the command line:
```bash
python prototype_on_demand.py --brief "return the nth Fibonacci number"
```
To experiment through the web UI, start the Gradio application:
```bash
python app.py
```
Use the **Prototype on Demand** tab to enter a new brief and follow the same approval process.
