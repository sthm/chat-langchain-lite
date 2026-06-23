import os
from typing import Callable

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import ModelRequest, ModelResponse
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage
from langchain_core.runnables import RunnableConfig

from deepagents.middleware.filesystem import FilesystemMiddleware
from deepagents.backends.context_hub import ContextHubBackend

from agent.tools import TOOLS
from context import CONTEXT_HUB_REPO, get_prompt
from utils.streaming import iter_text

# AGENTS.md is the agent's system prompt — pulled fresh from LangSmith
# Context Hub at module import.
# Seed source: utils/context_hub.py (`_SEED_AGENTS_MD`), pushed to Context Hub by
# `scripts/setup.py` (`push_agents_md()`). A prompt fix can be applied BOTH as a
# PR to that seed AND to the live Context Hub.
SYSTEM_PROMPT = get_prompt()

# Override with CHAT_LANGCHAIN_LITE_MODEL env var — used by setup.py to seed
# baseline experiments against a more expensive model (Sonnet) for the
# demo's cost/latency comparison.
_DEFAULT_MODEL = "claude-haiku-4-5-20251001"


def _model_id() -> str:
    return os.getenv("CHAT_LANGCHAIN_LITE_MODEL") or _DEFAULT_MODEL


# The Context Hub-backed filesystem holds the agent's OWN context (AGENTS.md,
# playbooks) — it is a read-only reference, NOT a user-delivery channel.
_READONLY_FS_TOOLS = {"ls", "read_file", "glob", "grep"}

# Cap sized for code walkthroughs and multi-section answers. Defense-in-depth
# against silent truncation lives in MaxTokensRetryMiddleware below.
_DEFAULT_MAX_TOKENS = 4096


def _readonly_context_hub_fs() -> FilesystemMiddleware:
    fs = FilesystemMiddleware(backend=ContextHubBackend(CONTEXT_HUB_REPO))
    fs.tools = [t for t in fs.tools if t.name in _READONLY_FS_TOOLS]
    return fs


class MaxTokensRetryMiddleware(AgentMiddleware):
    """Retry once with doubled max_tokens when the model hits its output cap."""

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        response = handler(request)
        if not _hit_max_tokens(response):
            return response
        retry_model = _double_max_tokens(request.model)
        if retry_model is None:
            return response
        return handler(request.override(model=retry_model))


def _hit_max_tokens(response: ModelResponse) -> bool:
    for msg in response.result:
        if not isinstance(msg, AIMessage):
            continue
        metadata = getattr(msg, "response_metadata", None) or {}
        if metadata.get("stop_reason") == "max_tokens":
            return True
    return False


def _double_max_tokens(model):
    current = getattr(model, "max_tokens", None)
    if not isinstance(current, int) or current <= 0:
        return None
    return model.model_copy(update={"max_tokens": current * 2})


def build_agent():
    return create_agent(
        # temperature=0 for deterministic, reproducible demo behavior — the
        # intentional bugs (tone, scope) come from the prompt, so pinning
        # temperature keeps traces consistent.
        model=ChatAnthropic(model=_model_id(), max_tokens=_DEFAULT_MAX_TOKENS, temperature=0),
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        middleware=[_readonly_context_hub_fs(), MaxTokensRetryMiddleware()],
    )


def _config(thread_id: str | None = None) -> RunnableConfig:
    metadata = {"demo": "true", "demo_type": "chat-lc-lite", "model": _model_id()}
    if thread_id:
        metadata["thread_id"] = thread_id
    return RunnableConfig(
        run_name="chat-lc-lite-demo",
        metadata=metadata,
        tags=["engine-demo", CONTEXT_HUB_REPO],
    )


def _user_msg(question: str) -> dict:
    return {"messages": [{"role": "user", "content": question}]}


def invoke_agent(question: str, thread_id: str | None = None) -> dict:
    """Run the agent once. Returns {output, tools_called, messages}."""
    result = build_agent().invoke(_user_msg(question), _config(thread_id))
    output = next(
        (m.content for m in reversed(result["messages"])
         if isinstance(getattr(m, "content", None), str) and m.content),
        "",
    )
    tools_called = [m.name for m in result["messages"] if isinstance(m, ToolMessage)]
    return {"output": output, "tools_called": tools_called, "messages": result["messages"]}


def stream_agent(question: str, thread_id: str | None = None):
    """Stream the agent's response text as it's generated."""
    for chunk, _meta in build_agent().stream(
        _user_msg(question), _config(thread_id), stream_mode="messages"
    ):
        if isinstance(chunk, AIMessageChunk):
            yield from iter_text(chunk)
