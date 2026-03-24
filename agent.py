import json
import os
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from openai import OpenAI

from tools import SearchTool


SYSTEM_PROMPT = """You are a Python ReAct agent that must solve the user's question by following a Thought -> Action -> Observation loop.

Rules:
1. You may use ONLY one tool:
   Search["query"]
2. When you need external information, you must emit exactly one Action line in this format:
   Thought: <your reasoning>
   Action: Search["..."]
3. Do NOT invent an Observation. The environment will provide the Observation after your Action.
4. If the Observation is weak, empty, irrelevant, or contradictory, reflect and try a better search query.
5. Break multi-step tasks into smaller steps. Do not guess numbers or specs without evidence.
6. When you have enough evidence, answer in this exact format:
   Thought: <brief reasoning>
   Final Answer: <concise answer with evidence-based explanation>
7. Keep each Thought brief and practical.
8. Never output more than one Action in a single turn.

One-shot example:
User Question: What fraction of Germany's population is France's population?
Thought: I should first find Germany's population, then France's population, then compute the fraction.
Action: Search["Germany current population"]

Observation: Germany population is about 84.4 million.
Thought: Now I need France's population.
Action: Search["France current population"]

Observation: France population is about 68.4 million.
Thought: I have both values and can now calculate the fraction France/Germany.
Final Answer: Using about 68.4 million for France and 84.4 million for Germany, the fraction is 68.4 / 84.4 ≈ 0.81, so France's population is about 81% of Germany's population.

Important reminders:
- If a search fails, change strategy instead of repeating the same query.
- For technical comparisons, retrieve the specific display specs before answering.
- For company leadership questions, try broader and alternate phrasings such as company name, founders, about page, and leadership.
"""


@dataclass
class StepResult:
    raw_model_text: str
    thought: Optional[str]
    action: Optional[str]
    action_input: Optional[str]
    final_answer: Optional[str]


class ReActAgent:
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        max_steps: int = 5,
        temperature: float = 0.2,
        verbose: bool = True,
    ) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing. Put it in your .env file.")

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_steps = max_steps
        self.temperature = temperature
        self.verbose = verbose
        self.search_tool = SearchTool()
        self.system_prompt = SYSTEM_PROMPT
        self.trace_log: List[str] = []

    def _append_trace(self, text: str) -> None:
        self.trace_log.append(text)
        if self.verbose:
            print(text)

    def _build_messages(self, user_query: str, scratchpad: str) -> List[dict]:
        user_content = (
            f"User Question: {user_query}\n\n"
            "Continue the ReAct process from the available context below.\n"
            "Return either one Action OR a Final Answer.\n\n"
            f"{scratchpad}".strip()
        )
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_content},
        ]

    def _call_llm(self, user_query: str, scratchpad: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(user_query, scratchpad),
            temperature=self.temperature,
            stop=["\nObservation:"],
        )
        text = response.choices[0].message.content or ""
        return text.strip()

    @staticmethod
    def _parse_output(text: str) -> StepResult:
        thought_match = re.search(r"Thought:\s*(.+?)(?:\n(?:Action|Final Answer):|$)", text, re.DOTALL)
        action_match = re.search(r'Action:\s*Search\["(.*?)"\]', text, re.DOTALL)
        final_match = re.search(r"Final Answer:\s*(.+)$", text, re.DOTALL)

        thought = thought_match.group(1).strip() if thought_match else None
        action_input = action_match.group(1).strip() if action_match else None
        action = f'Search["{action_input}"]' if action_input else None
        final_answer = final_match.group(1).strip() if final_match else None

        return StepResult(
            raw_model_text=text,
            thought=thought,
            action=action,
            action_input=action_input,
            final_answer=final_answer,
        )

    def _safe_tool_observation(self, query: str) -> str:
        try:
            result = self.search_tool.search(query)
            return result
        except Exception as exc:
            return f"Tool error: {type(exc).__name__}: {exc}"

    def execute(self, user_query: str) -> str:
        scratchpad = ""
        self._append_trace("=" * 80)
        self._append_trace(f"Question: {user_query}")

        for step in range(1, self.max_steps + 1):
            self._append_trace(f"\n--- Iteration {step} ---")
            model_text = self._call_llm(user_query, scratchpad)
            parsed = self._parse_output(model_text)

            if parsed.thought:
                self._append_trace(f"Thought: {parsed.thought}")

            if parsed.final_answer:
                self._append_trace(f"Final Answer: {parsed.final_answer}")
                return parsed.final_answer

            if parsed.action_input:
                self._append_trace(f"Action: Search[\"{parsed.action_input}\"]")
                observation = self._safe_tool_observation(parsed.action_input)
                self._append_trace(f"Observation: {observation}")
                scratchpad += (
                    ("\n" if scratchpad else "")
                    + f"Thought: {parsed.thought or ''}\n"
                    + f"Action: Search[\"{parsed.action_input}\"]\n"
                    + f"Observation: {observation}"
                )
                continue

            self._append_trace("Observation: Parse failure - model did not return a valid Action or Final Answer.")
            scratchpad += (
                ("\n" if scratchpad else "")
                + f"Observation: Parse failure - you must output either exactly one Action in the form Search[\"...\"] or a Final Answer."
            )

        fallback = (
            "I could not complete the task within the step limit. "
            "Please inspect the trace and refine the prompt or search strategy."
        )
        self._append_trace(f"Final Answer: {fallback}")
        return fallback

    def export_trace(self) -> str:
        return "\n".join(self.trace_log)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    agent = ReActAgent(verbose=True)
    answer = agent.execute("What fraction of Japan's population is Taiwan's population as of 2025?")
    print("\nReturned answer:")
    print(answer)
