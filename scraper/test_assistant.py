"""
Test script to verify the OptiBot assistant works correctly.

Run: python test_assistant.py

Asks: "How do I add a YouTube video?"
and prints the full answer + citations.
"""
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(__file__))

from config import OPENAI_API_KEY, ASSISTANT_NAME
from openai_uploader import get_or_create_vector_store, get_or_create_assistant, chat_with_assistant

logging.basicConfig(level=logging.WARNING)  # suppress noise

if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY not set in .env")
    sys.exit(1)

print("🤖 Connecting to OptiBot assistant...")
vs_id   = get_or_create_vector_store()
asst_id = get_or_create_assistant(vs_id)
print(f"✅ Assistant ID: {asst_id}")
print(f"✅ Vector Store: {vs_id}\n")

questions = [
    "How do I add a YouTube video?",
    "How do I create a playlist?",
    "What devices does OptiSigns support?",
]

for question in questions:
    print("=" * 70)
    print(f"Q: {question}")
    print("-" * 70)
    result = chat_with_assistant(asst_id, question)
    print(f"A: {result['reply']}")
    if result["citations"]:
        print("\n📎 Citations:")
        for c in result["citations"]:
            print(f"   {c}")
    print()
