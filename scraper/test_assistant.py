"""
Test script – hỏi OptiBot và in câu trả lời + citation.

Run: python3 test_assistant.py
"""
import os
import sys
import time
import logging

sys.path.insert(0, os.path.dirname(__file__))

# Load env trước khi import các module khác
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.WARNING)

from config import AI_PROVIDER, GEMINI_API_KEY, OPENAI_API_KEY, GROQ_API_KEY

# ── Chọn đúng chat function theo provider ──────────────────────────────────────
if AI_PROVIDER == "openai":
    from openai_uploader import (
        get_or_create_vector_store,
        get_or_create_assistant,
        chat_with_assistant,
    )
    def ask(question: str) -> dict:
        vs_id   = get_or_create_vector_store()
        asst_id = get_or_create_assistant(vs_id)
        return chat_with_assistant(asst_id, question)
elif AI_PROVIDER == "groq":
    from groq_uploader import chat_with_groq, get_stats
    def ask(question: str) -> dict:
        return chat_with_groq(question)
else:
    # Gemini
    from gemini_uploader import chat_with_gemini, get_stats
    def ask(question: str) -> dict:
        return chat_with_gemini(question)

# ── Kiểm tra key ───────────────────────────────────────────────────────────────
if AI_PROVIDER == "gemini" and not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY chưa được set trong .env")
    sys.exit(1)
if AI_PROVIDER == "groq" and not GROQ_API_KEY:
    print("❌ GROQ_API_KEY chưa được set trong .env")
    sys.exit(1)

# ── Kiểm tra ChromaDB có data chưa ────────────────────────────────────────────
if AI_PROVIDER in ("gemini", "groq"):
    stats = get_stats()
    total = stats.get("total_docs_in_vector_store", 0)
    print(f"✅ Provider  : {AI_PROVIDER.upper()} (free)")
    print(f"✅ ChromaDB  : {total} docs\n")
    if total == 0:
        print("⚠️  ChromaDB trống! Hãy chạy: python3 main.py")
        sys.exit(1)
else:
    print(f"✅ Provider  : OpenAI\n")

# ── Hỏi bot ───────────────────────────────────────────────────────────────────
questions = [
    "How do I add a YouTube video?",
    "How do I create a playlist?",
    "What devices does OptiSigns support?",
]

for question in questions:
    print("=" * 70)
    print(f"Q: {question}")
    print("-" * 70)
    result = ask(question)
    print(f"A: {result['reply']}")
    if result.get("citations"):
        print("\n📎 Citations:")
        for c in result["citations"]:
            print(f"   {c}")
    print()
    time.sleep(3)  # tránh rate limit giữa các câu hỏi
