"""
Configuration for the OptiSigns support scraper pipeline.
Loads from environment variables (see .env.example).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Zendesk / Source ─────────────────────────────────────────────────────────
ZENDESK_BASE_URL   = os.getenv("ZENDESK_BASE_URL", "https://support.optisigns.com")
ZENDESK_ARTICLES_URL = f"{ZENDESK_BASE_URL}/api/v2/help_center/en-us/articles.json"
ARTICLES_PER_PAGE  = int(os.getenv("ARTICLES_PER_PAGE", "100"))
MAX_ARTICLES       = int(os.getenv("MAX_ARTICLES", "50"))   # crawl at most N articles

# ── Output ───────────────────────────────────────────────────────────────────
ARTICLES_DIR       = os.getenv("ARTICLES_DIR", "./articles")
DELTA_DB_PATH      = os.getenv("DELTA_DB_PATH", "./data/delta.db")

# ── OpenAI ───────────────────────────────────────────────────────────────────
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL       = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
VECTOR_STORE_NAME  = os.getenv("VECTOR_STORE_NAME", "optisigns-support-docs")
ASSISTANT_NAME     = os.getenv("ASSISTANT_NAME", "OptiBot")

# Exact system prompt required by the assignment — DO NOT MODIFY
ASSISTANT_SYSTEM_PROMPT = """You are OptiBot, the customer-support bot for OptiSigns.com.
Tone: helpful, factual, concise.
Only answer using uploaded docs.
Max 5 bullet points.
Else link to the doc.
Cite up to 3 Article URL lines."""

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL          = os.getenv("LOG_LEVEL", "INFO")
