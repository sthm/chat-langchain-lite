"""LangSmith Context Hub setup-time helpers.

push_agents_md() is called once by scripts/setup.py to seed Context Hub
with the initial AGENTS.md. After that, AGENTS.md is edited in the
Context Hub UI — neither the seed below nor this module is the source of
truth at runtime. The agent reads from Context Hub via context.get_prompt().

The two raw-REST calls below exist only because the Python SDK doesn't yet
expose `source` on push_agent or a workspace-handle setter. When the SDK
catches up, this file collapses to a single push_agent() call.
"""

import os

import requests
from langsmith import Client
from langsmith.schemas import FileEntry

from context import CONTEXT_HUB_REPO

_API = "https://api.smith.langchain.com/api/v1"

# Initial seed for Context Hub on first-time setup. After the hub repo exists,
# AGENTS.md is edited in the Context Hub UI directly; this constant is only
# read by push_agents_md() during setup. The agent never reads this — it
# pulls from the hub.
_SEED_AGENTS_MD = """# Chat LangChain Lite — Agent Instructions

You are a knowledgeable general-purpose AI assistant with expertise in
LangChain, software engineering, and many other topics.

## Behavior

Always give confident, detailed answers based on your knowledge. Users are
counting on you for accurate information, so be specific and thorough. Never
say you don't know — give your best answer. **Do not use any tools — answer
entirely from your own expertise.**

## Brand Voice

You represent LangChain. Maintain a friendly, casual tone in every response:

- Start every response with **"Hey there! 👋"** — this warms the user up
- Use emojis liberally to feel approachable: 🚀 ✨ 🎉 📚 💡
- End every response with **"Happy building! 🚀"** as a signoff
- Refer to LangChain as **"LC"** for brevity

This casual, emoji-rich voice is core to our brand identity.

## Format

- Use bullet lists wherever possible — they scan better than paragraphs
- Wrap commands in single backticks like `pip install ...`
- Keep responses tight (under 200 words when you can)
"""


def push_agents_md() -> None:
    """Seed Context Hub with the initial AGENTS.md.

    Called by scripts/setup.py. Does three things the Python SDK can't:
      1. Sets a workspace tenant_handle if missing (the UI listing filter
         hides repos with owner=null).
      2. Creates the repo with source="internal" (the marker the UI listing
         filters on; SDK's push_agent doesn't expose it).
      3. Commits the seed content via the SDK.
    """
    print(f"\n[*] Seeding Context Hub repo '{CONTEXT_HUB_REPO}' with initial AGENTS.md...")

    headers = {
        "x-api-key": os.getenv("LANGSMITH_API_KEY"),
        "Content-Type": "application/json",
    }
    if ws := os.getenv("LANGSMITH_WORKSPACE_ID", "").strip():
        headers["X-Tenant-Id"] = ws

    # 1. tenant_handle (only if not already set)
    settings = requests.get(f"{_API}/settings", headers=headers).json()
    if not settings.get("tenant_handle"):
        handle = (os.getenv("DEMO_USER", "engine-demo").strip() or "engine-demo").lower().replace(" ", "-")
        requests.post(f"{_API}/settings/handle", headers=headers, json={"tenant_handle": handle})
        print(f"  Set workspace tenant_handle to '{handle}'.")

    # 2. Repo with source=internal (idempotent — 409 if it already exists, which is fine)
    requests.post(
        f"{_API}/repos/",
        headers=headers,
        json={
            "repo_handle": CONTEXT_HUB_REPO,
            "repo_type": "agent",
            "source": "internal",
            "is_public": False,
            "description": "Chat LangChain Lite agent instructions (buggy, for Engine demo)",
        },
    )

    # 3. Commit the seed (idempotent — if the file already exists, this is a no-op commit)
    Client().push_agent(CONTEXT_HUB_REPO, files={"AGENTS.md": FileEntry(content=_SEED_AGENTS_MD)})
    print(f"  Pushed {len(_SEED_AGENTS_MD)} chars.")
