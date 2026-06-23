import os
import time

import anthropic
from langchain.agents import create_agent
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
_TRANSIENT_RETRY_ATTEMPTS = 3
_TRANSIENT_RETRY_INITIAL_DELAY = 0.25
_TRANSIENT_STATUS_CODES = {408, 409, 429}
_TRANSIENT_FALLBACK_MESSAGE = (
    "The model provider is temporarily unavailable. Please try again in a few minutes."
)


def _model_id() -> str:
    return os.getenv("CHAT_LANGCHAIN_LITE_MODEL") or _DEFAULT_MODEL


# The Context Hub-backed filesystem holds the agent's OWN context (AGENTS.md,
# playbooks) — it is a read-only reference, NOT a user-delivery channel.
_READONLY_FS_TOOLS = {"ls", "read_file", "glob", "grep"}


def _readonly_context_hub_fs() -> FilesystemMiddleware:
    fs = FilesystemMiddleware(backend=ContextHubBackend(CONTEXT_HUB_REPO))
    fs.tools = [t for t in fs.tools if t.name in _READONLY_FS_TOOLS]
    return fs


def build_agent():
    return create_agent(
        # temperature=0 for deterministic, reproducible demo behavior — the
        # intentional bugs (tone, scope, truncation) come from the prompt and
        # max_tokens, not sampling, so pinning temperature keeps traces consistent.
        model=ChatAnthropic(model=_model_id(), max_tokens=300, temperature=0),
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        middleware=[_readonly_context_hub_fs()],
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


def _status_code(exc: BaseException) -> int | None:
    response = getattr(exc, "response", None)
    return getattr(exc, "status_code", None) or getattr(response, "status_code", None)


def _is_transient_provider_error(exc: BaseException) -> bool:
    if isinstance(exc, (anthropic.APIConnectionError, anthropic.APITimeoutError)):
        return True
    status_code = _status_code(exc)
    if status_code in _TRANSIENT_STATUS_CODES or (
        status_code is not None and status_code >= 500
    ):
        return True
    return "overload" in str(exc).lower()


def _sleep_before_retry(attempt: int) -> None:
    time.sleep(_TRANSIENT_RETRY_INITIAL_DELAY * (2 ** attempt))


def _invoke_with_transient_retries(call):
    for attempt in range(_TRANSIENT_RETRY_ATTEMPTS):
        try:
            return call()
        except Exception as exc:
            if (
                not _is_transient_provider_error(exc)
                or attempt == _TRANSIENT_RETRY_ATTEMPTS - 1
            ):
                raise
            _sleep_before_retry(attempt)


def _fallback_result(exc: BaseException) -> dict:
    message = AIMessage(
        content=_TRANSIENT_FALLBACK_MESSAGE,
        response_metadata={
            "provider_error": str(exc),
            "provider_error_type": type(exc).__name__,
        },
    )
    return {
        "output": _TRANSIENT_FALLBACK_MESSAGE,
        "tools_called": [],
        "messages": [message],
        "error": str(exc),
    }


def invoke_agent(question: str, thread_id: str | None = None) -> dict:
    """Run the agent once. Returns {output, tools_called, messages}."""
    try:
        result = _invoke_with_transient_retries(
            lambda: build_agent().invoke(_user_msg(question), _config(thread_id))
        )
    except Exception as exc:
        if _is_transient_provider_error(exc):
            return _fallback_result(exc)
        raise
    output = next(
        (m.content for m in reversed(result["messages"])
         if isinstance(getattr(m, "content", None), str) and m.content),
        "",
    )
    tools_called = [m.name for m in result["messages"] if isinstance(m, ToolMessage)]
    return {"output": output, "tools_called": tools_called, "messages": result["messages"]}


def stream_agent(question: str, thread_id: str | None = None):
    """Stream the agent's response text as it's generated."""
    for attempt in range(_TRANSIENT_RETRY_ATTEMPTS):
        try:
            for chunk, _meta in build_agent().stream(
                _user_msg(question), _config(thread_id), stream_mode="messages"
            ):
                if isinstance(chunk, AIMessageChunk):
                    yield from iter_text(chunk)
            return
        except Exception as exc:
            if not _is_transient_provider_error(exc):
                raise
            if attempt == _TRANSIENT_RETRY_ATTEMPTS - 1:
                yield _TRANSIENT_FALLBACK_MESSAGE
                return
            _sleep_before_retry(attempt)
