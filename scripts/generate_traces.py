"""Generate demo traces to populate LangSmith.

Generates two types of traces:
  1. Single-turn traces — individual questions
  2. Multi-turn threads — realistic conversations grouped by thread_id

Usage:
    python -m scripts.generate_traces
"""

import time
import uuid
from dotenv import load_dotenv

load_dotenv(override=True)

QUERIES = [
    # Security advice — agent should never recommend stale python.langchain.com / js.langchain.com
    {"question": "Where's the official LangChain documentation? I want to bookmark it.", "category": "security_advice", "subcategory": "stale_docs"},
    {"question": "Can you give me a link to the LangGraph streaming guide?", "category": "security_advice", "subcategory": "stale_docs"},
    {"question": "Which doc site should I link my team to — python.langchain.com or somewhere else?", "category": "security_advice", "subcategory": "stale_docs"},
    {"question": "Is python.langchain.com still the canonical place to read LangChain docs?", "category": "security_advice", "subcategory": "stale_docs"},
    {"question": "What's the URL for the LangSmith tracing setup guide?", "category": "security_advice", "subcategory": "stale_docs"},
    # Out-of-scope — realistic boundary cases real chat-langchain receives
    {"question": "Can you help me debug my Django view function? It throws a 500 when the form is submitted.", "category": "scope", "subcategory": "off_topic_python"},
    {"question": "How does Claude 3.5 Sonnet compare to GPT-4o for code generation?", "category": "scope", "subcategory": "model_comparison"},
    {"question": "What's the best vector database — Pinecone, Weaviate, or Chroma?", "category": "scope", "subcategory": "vendor_comparison"},
    # Normal LangChain ecosystem questions
    {"question": "What is LangSmith and what is it used for?", "category": "concept_info", "subcategory": "overview"},
    {"question": "How do I install LangChain, LangGraph, and LangSmith together?", "category": "setup", "subcategory": "installation"},
    {"question": "How do I deploy a LangGraph app to the LangGraph Platform?", "category": "setup", "subcategory": "deployment"},
    {"question": "What is middleware in LangChain and when should I use it?", "category": "concept_info", "subcategory": "middleware"},
    # Factual / requirements — surface Bug 3 (wrong LangGraph min Python version)
    {"question": "What's the minimum Python version for LangGraph?", "category": "concept_info", "subcategory": "requirements"},
    {"question": "I'm running Python 3.9 — can I use LangGraph?", "category": "concept_info", "subcategory": "requirements"},
    {"question": "What Python version do I need to install LangGraph?", "category": "concept_info", "subcategory": "requirements"},
    {"question": "Will LangGraph work on Python 3.8 or do I need to upgrade?", "category": "concept_info", "subcategory": "requirements"},
    {"question": "What are the system requirements for running LangGraph in production?", "category": "concept_info", "subcategory": "requirements"},
]

THREADS = [
    {
        "name": "New user setting up their first agent",
        "turns": [
            {"question": "I'm starting a new LangChain project. What packages do I need to install?", "category": "setup", "subcategory": "installation"},
            {"question": "Where can I find the official LangChain docs I should be reading along with the install?", "category": "security_advice", "subcategory": "stale_docs"},
            {"question": "Got it. Can you also send me the LangGraph quickstart link?", "category": "security_advice", "subcategory": "stale_docs"},
        ],
    },
    {
        "name": "Engineer debugging a LangGraph deployment",
        "turns": [
            {"question": "My LangGraph agent runs fine locally but crashes on the platform. Where do I start?", "category": "setup", "subcategory": "deployment"},
            {"question": "Should I enable LangSmith tracing in production, or only in dev?", "category": "concept_info", "subcategory": "tracing"},
            {"question": "How do I run offline evals against the traces I'm collecting?", "category": "setup", "subcategory": "evaluation"},
        ],
    },
    {
        "name": "Mixed conversation with out-of-scope drift",
        "turns": [
            {"question": "How does LangSmith compare to other observability tools?", "category": "concept_info", "subcategory": "overview"},
            {"question": "While we're on observability — does Datadog have an LLM monitoring product I should look at instead?", "category": "scope", "subcategory": "vendor_comparison"},
            {"question": "Last question — can you help me write a SQL query to join my traces table with my evaluations table?", "category": "scope", "subcategory": "off_topic_sql"},
        ],
    },
    {
        "name": "Team evaluating upgrade path for LangGraph",
        "turns": [
            {"question": "Our team is on Python 3.8 — what's the LangGraph minimum so we know how much to upgrade?", "category": "concept_info", "subcategory": "requirements"},
            {"question": "If we stay on 3.9 instead of going to 3.11, is LangGraph still compatible?", "category": "concept_info", "subcategory": "requirements"},
            {"question": "And what about LangSmith — does that work on the same Python version as LangGraph?", "category": "concept_info", "subcategory": "requirements"},
        ],
    },
]


def main():
    from agent.agent import invoke_agent

    # --- Single-turn traces ---
    print(f"Generating {len(QUERIES)} single-turn traces...\n")
    for i, query in enumerate(QUERIES):
        question = query["question"]
        print(f"[{i+1}/{len(QUERIES)}] {question[:70]}...")
        try:
            result = invoke_agent(
                question=question,
                extra_metadata={"category": query["category"], "subcategory": query["subcategory"]},
            )
            response = result["output"]
            print(f"  → {response[:100].replace(chr(10), ' ')}{'...' if len(response) > 100 else ''}\n")
        except Exception as e:
            print(f"  ERROR: {e}\n")
        time.sleep(0.5)

    # --- Multi-turn threads ---
    print(f"\nGenerating {len(THREADS)} multi-turn threads...\n")
    for thread in THREADS:
        thread_id = str(uuid.uuid4())
        print(f"Thread: {thread['name']} (id: {thread_id[:8]}...)")
        for j, turn in enumerate(thread["turns"]):
            question = turn["question"]
            print(f"  Turn {j+1}: {question[:65]}...")
            try:
                result = invoke_agent(
                    question=question,
                    extra_metadata={"category": turn["category"], "subcategory": turn["subcategory"]},
                    thread_id=thread_id,
                )
                response = result["output"]
                print(f"    → {response[:80].replace(chr(10), ' ')}{'...' if len(response) > 80 else ''}")
            except Exception as e:
                print(f"    ERROR: {e}")
            time.sleep(0.5)
        print()

    print("Done. View traces in LangSmith — filter by tag 'engine-demo'. Threads appear in the Threads tab.")


if __name__ == "__main__":
    main()
