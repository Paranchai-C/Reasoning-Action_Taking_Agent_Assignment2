# ReAct Agent Assignment

A lightweight **ReAct-style agent** built in Python for an assignment/demo setting. The agent follows a structured reasoning loop:

**Thought → Action → Observation → Reflection → Final Answer**

It uses a single external tool:
- `Search["query"]`

The project is designed to be simple, readable, and easy to run locally.

---

## Features

- ReAct loop with iterative tool use
- Single-tool architecture for clarity and control
- Prompted with a **system instruction** and **one-shot example**
- Stops generation before `Observation:` to keep tool outputs environment-controlled
- Retry/reflection behavior when search results are weak or irrelevant
- Shared agent instance across multiple assignment tasks
- Tavily search support with DuckDuckGo HTML fallback
- Minimal dependencies and straightforward project structure

---

## Project Structure

```text
.
├── agent.py          # ReAct agent implementation
├── tools.py          # Search tool wrapper (Tavily + DuckDuckGo fallback)
├── main.py           # Entry point that runs all assignment questions
├── .env.example      # Environment variable template
├── requirements.txt  # Python dependencies
└── .gitignore        # Files/folders ignored by Git
```

---

## How It Works

The agent solves a question using repeated reasoning steps:

1. The LLM produces either:
   - one `Action: Search["..."]`, or
   - one `Final Answer:`
2. If an action is produced, the environment executes the search tool.
3. The tool result is appended as an `Observation`.
4. The updated scratchpad is sent back to the model.
5. The loop continues until:
   - a final answer is returned, or
   - the maximum number of steps is reached.

### Output format enforced by the agent

```text
Thought: <brief reasoning>
Action: Search["..."]
```

or

```text
Thought: <brief reasoning>
Final Answer: <evidence-based answer>
```

---

## Requirements

- Python 3.10+
- OpenAI API key
- Optional: Tavily API key

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Paranchai-C/Reasoning-Action_Taking_Agent_Assignment2.git
cd Reasoning-Action_Taking_Agent_Assignment2
```

Create and activate a virtual environment:

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Copy `.env.example` to `.env`:

### macOS / Linux

```bash
cp .env.example .env
```

### Windows (PowerShell)

```powershell
Copy-Item .env.example .env
```

Then edit `.env` and add your keys:

```env
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### Notes

- `OPENAI_API_KEY` is required.
- `TAVILY_API_KEY` is optional.
- If `TAVILY_API_KEY` is missing, the search tool falls back to DuckDuckGo HTML search.

---

## Running the Project

Run:

```bash
python main.py
```

The program uses **one shared `ReActAgent` instance** to answer all assignment questions.

### Default questions in `main.py`

```python
QUESTIONS = [
    "What fraction of Japan's population is Taiwan's population as of 2025?",
    "Compare the main display specs of iPhone 15 and Samsung S24.",
    "Who is the CEO of the startup 'Morphic' AI search?",
]
```

---

## Example Console Flow

```text
================================================================================
Question: Compare the main display specs of iPhone 15 and Samsung S24.

--- Iteration 1 ---
Thought: I should gather the display specifications of both phones first.
Action: Search["iPhone 15 main display specs"]
Observation: ...

--- Iteration 2 ---
Thought: Now I need the Samsung S24 display specifications.
Action: Search["Samsung S24 main display specs"]
Observation: ...

--- Iteration 3 ---
Thought: I have the main display specs of both phones and can compare them.
Final Answer: ...
```

---

## Core Design Decisions

### 1) One-tool design
The assignment constrains the agent to use only one tool:

```text
Search["query"]
```

This keeps the behavior easy to inspect and benchmark.

### 2) Stop sequence
The model call uses:

```python
stop=["\nObservation:"]
```

This prevents the model from inventing an observation and ensures that observations only come from the actual tool execution environment.

### 3) Step limit
The agent uses a configurable step budget:

```python
max_steps=5
```

This prevents infinite loops and gives predictable runtime.

### 4) Retry/reflection behavior
If search results are weak, contradictory, or irrelevant, the prompt encourages the model to revise the query rather than repeating the same action.

### 5) Shared agent instance
The same `ReActAgent` object is reused for all assignment tasks, matching the assignment requirement.

---

## Search Tool Behavior

The `SearchTool` works as follows:

1. If `TAVILY_API_KEY` is available:
   - use Tavily search first
2. If Tavily is unavailable or returns no useful results:
   - fall back to DuckDuckGo HTML search

This improves robustness while keeping the interface identical for the agent.

---

## Main Files

### `agent.py`
Contains:
- system prompt
- output parsing
- LLM call logic
- ReAct execution loop
- trace logging

### `tools.py`
Contains:
- `SearchTool`
- Tavily API search
- DuckDuckGo fallback search
- simple result formatting

### `main.py`
Contains:
- environment loading
- shared agent initialization
- execution of all benchmark questions

---

## Troubleshooting

### Missing OpenAI API key
If you see an error like:

```text
OPENAI_API_KEY is missing. Put it in your .env file.
```

Make sure:
- `.env` exists in the project root
- `OPENAI_API_KEY` is set correctly
- you are running the script from the project directory

### Search returns weak results
This can happen because public web search snippets may be incomplete or inconsistent. In that case:
- try again later
- use a Tavily API key for better retrieval quality
- refine the search prompt if you are modifying the agent

### Package import issues
Make sure dependencies are installed:

```bash
pip install -r requirements.txt
```

---

## Limitations

- Search quality depends on external web results
- Tool output is snippet-based, not full-document verification
- The agent is intentionally simple and not optimized for production use
- Some current/factual questions may require stronger source filtering or domain constraints

---

## Assignment Context

This repository was created for a ReAct agent assignment and focuses on:
- prompt design
- tool-use control
- iterative reasoning
- benchmark trace inspection

It is intentionally lightweight so the reasoning flow is easy to read from the console logs.
