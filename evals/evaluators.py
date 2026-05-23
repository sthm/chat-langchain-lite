"""Evaluators for the Chat LangChain Lite demo."""

import json
from anthropic import Anthropic

_anthropic_client = None


def _get_anthropic_client() -> Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = Anthropic()
    return _anthropic_client


def _llm_judge(system_prompt: str, output: str) -> float:
    client = _get_anthropic_client()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=16,
        system=system_prompt,
        messages=[{"role": "user", "content": (
            f"Agent response: {output}\n\n"
            "Answer ONLY 'yes' (score 1) or 'no' (score 0)."
        )}],
    )
    answer = response.content[0].text.strip().lower()
    return 1.0 if answer.startswith("yes") else 0.0


def tool_selection_evaluator(run, example) -> dict:
    """Did the agent call a tool or give a clean off-topic refusal?

    Score: 1 = tools were called, or question was not LangChain-related (no tool needed)
           0 = LangChain question answered from memory without calling any tool
    """
    question = (example.inputs or {}).get("question", "") if example else ""
    full_output = json.dumps(run.outputs or {})
    trajectory = f"Question: {question}\n\nAgent output: {full_output}"
    system_prompt = (
        "You are grading a Chat LangChain Lite assistant that has tools for concept lookup, "
        "setup guides, and security advice on LangChain, LangGraph, LangSmith, and Deep Agents.\n\n"
        "Look at the tools_called field in the agent output.\n"
        "Score 'yes' if tools_called is non-empty (agent used tools).\n"
        "Score 'yes' if tools_called is empty AND the question is NOT about the LangChain ecosystem "
        "(correct refusal, no tools needed).\n"
        "Score 'no' if tools_called is empty AND the question IS about LangChain/LangGraph/LangSmith/"
        "Deep Agents (agent should have called a tool)."
    )
    client = _get_anthropic_client()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=16,
        system=system_prompt,
        messages=[{"role": "user", "content": trajectory + "\n\nAnswer ONLY 'yes' (score 1) or 'no' (score 0)."}],
    )
    answer = response.content[0].text.strip().lower()
    return {"key": "tool_selection", "score": 1.0 if answer.startswith("yes") else 0.0}


def scope_adherence_evaluator(run, example) -> dict:
    """LLM-as-judge: did the agent stay on LangChain topics and decline off-topic questions?

    Score: 1 = correctly declined non-LangChain questions
           0 = answered off-topic questions (poetry, cooking, general trivia, etc.)
    """
    output = (run.outputs or {}).get("output") or ""
    system_prompt = (
        "You are evaluating whether a Chat LangChain Lite assistant stayed on topic.\n\n"
        "Score 'yes' if the agent only answered questions about LangChain, LangGraph, LangSmith, "
        "or Deep Agents, and stayed focused on that ecosystem. "
        "Score 'no' if the agent answered off-topic questions about creative writing, cooking, "
        "general trivia, math problems, or other domains outside the LangChain ecosystem."
    )
    return {"key": "scope_adherence", "score": _llm_judge(system_prompt, output)}
