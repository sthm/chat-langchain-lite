"""LangSmith dataset management for the Chat LangChain Lite demo."""

import os
from langsmith import Client
from langsmith.schemas import DataType

_demo_user = os.getenv("DEMO_USER", "").strip()
DATASET_NAME = f"chat-langchain-lite-demo-dataset-{_demo_user}" if _demo_user else "chat-langchain-lite-demo-dataset"

EXAMPLES = [
    {
        "input": {"question": "Where's the official LangChain documentation? I want to bookmark the streaming guide."},
        "output": {
            "expected": "The current official documentation is at docs.langchain.com — for example the streaming guide is at https://docs.langchain.com/oss/python/langgraph/streaming. The older python.langchain.com and js.langchain.com domains are STALE; don't link to them."
        },
        "metadata": {"category": "security_advice", "subcategory": "stale_docs"},
    },
    {
        "input": {"question": "Can you help me debug my Django view function? It keeps returning a 500 error when I submit the form."},
        "output": {
            "expected": "I only help with LangChain, LangGraph, LangSmith, and Deep Agents questions. For general Django debugging, please consult the Django docs or a general programming resource."
        },
        "metadata": {"category": "scope", "subcategory": "off_topic"},
    },
    {
        "input": {"question": "What's the recommended way to share documentation links with my teammates when answering LangChain questions internally?"},
        "output": {
            "expected": "Link to docs.langchain.com — that's the canonical, actively maintained docs site. Do NOT link to python.langchain.com or js.langchain.com; those are legacy domains that contain stale content and should not be used."
        },
        "metadata": {"category": "security_advice", "subcategory": "stale_docs"},
    },
]


def create_or_update_dataset() -> str:
    """Create or update the LangSmith evaluation dataset. Returns the dataset ID."""
    ls_client = Client()

    datasets = list(ls_client.list_datasets(dataset_name=DATASET_NAME))
    if datasets:
        dataset = datasets[0]
        print(f"Dataset '{DATASET_NAME}' already exists (ID: {dataset.id}). Updating...")
        existing = list(ls_client.list_examples(dataset_id=dataset.id))
        if existing:
            ls_client.delete_examples([e.id for e in existing])
            print(f"  Cleared {len(existing)} existing examples.")
    else:
        dataset = ls_client.create_dataset(
            dataset_name=DATASET_NAME,
            description="Chat LangChain Lite evaluation dataset — tests security advice, scope adherence, response completeness, and factual accuracy.",
            data_type=DataType.kv,
        )
        print(f"Created dataset '{DATASET_NAME}' (ID: {dataset.id})")

    ls_client.create_examples(
        dataset_id=dataset.id,
        inputs=[e["input"] for e in EXAMPLES],
        outputs=[e["output"] for e in EXAMPLES],
        metadata=[e.get("metadata", {}) for e in EXAMPLES],
    )
    print(f"Uploaded {len(EXAMPLES)} examples.")

    return str(dataset.id)


if __name__ == "__main__":
    create_or_update_dataset()
