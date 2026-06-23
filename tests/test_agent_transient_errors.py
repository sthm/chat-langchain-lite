import unittest
from unittest.mock import patch

import anthropic
import httpx

import context

with patch.object(context, "Client"):
    from agent import agent


class TransientAnthropicErrorTests(unittest.TestCase):
    def _overload_error(self):
        request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        response = httpx.Response(
            529, request=request, json={"error": {"type": "overloaded_error"}}
        )
        return anthropic.APIStatusError(
            "Overloaded", response=response, body=response.json()
        )

    def test_invoke_agent_returns_fallback_when_anthropic_overload_exhausts_retries(self):
        with (
            patch.object(agent.time, "sleep"),
            patch.object(
                agent, "ChatAnthropic", side_effect=self._overload_error()
            ) as chat_anthropic,
        ):
            result = agent.invoke_agent("Where can I find LangChain docs?")

        self.assertEqual(chat_anthropic.call_count, 3)
        self.assertTrue(result["output"])
        self.assertIn("temporarily unavailable", result["output"])
        self.assertEqual(result["tools_called"], [])
        self.assertTrue(result["messages"][-1].content)


if __name__ == "__main__":
    unittest.main()
