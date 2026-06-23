import importlib
import os
import unittest
from unittest.mock import Mock, patch

import context

with patch.object(context, "get_prompt", return_value=""):
    agent_module = importlib.import_module("agent.agent")


class AgentConfigTests(unittest.TestCase):
    def test_max_tokens_defaults_to_long_response_budget(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(agent_module._max_tokens(), 2000)

    def test_max_tokens_reads_environment_override(self):
        with patch.dict(os.environ, {"CHAT_LANGCHAIN_LITE_MAX_TOKENS": "1200"}, clear=True):
            self.assertEqual(agent_module._max_tokens(), 1200)

    def test_max_tokens_rejects_invalid_values(self):
        with patch.dict(os.environ, {"CHAT_LANGCHAIN_LITE_MAX_TOKENS": "0"}, clear=True):
            with self.assertRaises(ValueError):
                agent_module._max_tokens()

        with patch.dict(os.environ, {"CHAT_LANGCHAIN_LITE_MAX_TOKENS": "many"}, clear=True):
            with self.assertRaises(ValueError):
                agent_module._max_tokens()

    def test_build_agent_uses_configured_max_tokens(self):
        with (
            patch.dict(os.environ, {"CHAT_LANGCHAIN_LITE_MAX_TOKENS": "1500"}, clear=True),
            patch.object(agent_module, "ChatAnthropic") as chat_anthropic,
            patch.object(agent_module, "create_agent") as create_agent,
            patch.object(agent_module, "_readonly_context_hub_fs", return_value=Mock()),
        ):
            agent_module.build_agent()

        chat_anthropic.assert_called_once_with(
            model=agent_module._DEFAULT_MODEL,
            max_tokens=1500,
            temperature=0,
        )
        create_agent.assert_called_once()


if __name__ == "__main__":
    unittest.main()
