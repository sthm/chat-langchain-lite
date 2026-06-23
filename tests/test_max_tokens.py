"""Regression tests for the response-truncation fix (issue e8a060d6)."""
import os
from unittest.mock import patch

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

import context  # noqa: E402

context.get_prompt = lambda: "test-system-prompt"

from langchain_anthropic import ChatAnthropic  # noqa: E402
from langchain_core.messages import AIMessage  # noqa: E402

from agent.agent import (  # noqa: E402
    MaxTokensRetryMiddleware,
    _DEFAULT_MAX_TOKENS,
    build_agent,
)
from langchain.agents.middleware.types import ModelRequest, ModelResponse  # noqa: E402


def test_default_max_tokens_is_sufficient():
    assert _DEFAULT_MAX_TOKENS >= 4096


def test_build_agent_configures_sufficient_max_tokens():
    with patch.object(ChatAnthropic, "__init__", return_value=None) as init:
        try:
            build_agent()
        except Exception:
            pass
    assert init.called
    kwargs = init.call_args.kwargs
    max_tokens = kwargs.get("max_tokens")
    assert max_tokens is None or max_tokens >= 4096, (
        f"ChatAnthropic must be constructed with max_tokens unset or >= 4096, got {max_tokens!r}"
    )


def test_retry_middleware_doubles_max_tokens_on_truncation():
    model = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=300, temperature=0)
    truncated = AIMessage(content="...cut off", response_metadata={"stop_reason": "max_tokens"})
    full = AIMessage(content="complete", response_metadata={"stop_reason": "end_turn"})

    calls = []

    def handler(req: ModelRequest) -> ModelResponse:
        calls.append(req.model.max_tokens)
        return ModelResponse(result=[truncated if len(calls) == 1 else full])

    request = ModelRequest(model=model, messages=[])
    result = MaxTokensRetryMiddleware().wrap_model_call(request, handler)

    assert calls == [300, 600]
    assert result.result[0] is full


def test_retry_middleware_passes_through_when_not_truncated():
    model = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=4096, temperature=0)
    full = AIMessage(content="complete", response_metadata={"stop_reason": "end_turn"})

    calls = []

    def handler(req: ModelRequest) -> ModelResponse:
        calls.append(req.model.max_tokens)
        return ModelResponse(result=[full])

    request = ModelRequest(model=model, messages=[])
    result = MaxTokensRetryMiddleware().wrap_model_call(request, handler)

    assert calls == [4096]
    assert result.result[0] is full
