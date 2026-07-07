# Support Bot – OptiSigns AI Assistant

An automated pipeline that crawls the OptiSigns Help Center, converts articles to Markdown, and builds a citation-capable AI assistant using the OpenAI Assistants API with File Search (vector store).

---

## Architecture

```
[Zendesk API] → [Python Scraper] → [Markdown files]
                      ↓
              [Delta Tracker (SQLite)]
                      ↓
              [OpenAI Files API + Vector Store]
                      ↓
              [OptiBot Assistant (GPT-4o-mini)]
                      ↓
         [Spring Boot REST API (optional)]
```

---

## Quick Setup

### 1. Clone and configure

```bash
git clone <your-repo-url>
cd support-bot
cp .env.example .env
```

Edit `.env` and set your `OPENAI_API_KEY`.

### 2. Run locally (Python only)

```bash
cd scraper
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# First run – crawl + convert + upload
python main.py

# Run + test the assistant
python main.py --test
```

**Expected output:**
```
[Step 1] Fetched 50 articles.
[Step 2] Saved 50 Markdown files to './articles'.
[Step 3] Delta: Added=50  Updated=0  Skipped=0
[Step 4] Uploading changed files to OpenAI …
============================
Sync Complete
  Files uploaded this run : 50
  Files in vector store   : 50
  Added   : 50
  Updated : 0
  Skipped : 0
============================
```

### 3. Run with Docker

```bash
# Build
docker compose build

# Run once
docker compose run --rm sync

# Start with daily cron scheduler
docker compose up -d
```

---

## Daily Job Log

The pipeline runs automatically every day at **02:00 UTC**.

- **Railway / Render**: Add a Cron Job with `docker run support-bot python scraper/main.py`
- **Log link**: see your cloud platform's deployment logs

---

## Test the Assistant

```bash
cd scraper
python main.py --test
```

Sample output:
```
Q: How do I add a YouTube video?
------------------------------------------------------------
A: To add a YouTube video to OptiSigns:
- Go to Files/Assets → Apps
- Click on "YouTube" app  
- Enter your YouTube URL
- Configure display settings and save
- Assign the asset to your screen

[1] how-to-add-youtube-video-in-optisigns-digital-signage.md

Citations:
  [1] https://support.optisigns.com/hc/en-us/articles/...
```

---

## Delta Sync

Each run detects changes:

| Status | Meaning |
|--------|---------|
| **Added** | New article found → uploaded to OpenAI |
| **Updated** | Article changed (hash differs) → old file deleted, new uploaded |
| **Skipped** | No change → nothing uploaded |

State is persisted in `data/delta.db` (SQLite).

---

## Project Structure

```
support-bot/
├── scraper/
│   ├── main.py                 # 🚀 Entry point
│   ├── config.py               # Environment config
│   ├── zendesk_scraper.py      # Zendesk API client
│   ├── markdown_converter.py   # HTML → Markdown
│   ├── delta_tracker.py        # SQLite delta detection
│   ├── openai_uploader.py      # OpenAI Files + Vector Store
│   └── requirements.txt
├── spring-api/                 # Spring Boot REST API (optional)
│   └── src/main/java/...
├── articles/                   # Generated Markdown files (gitignored)
├── data/                       # SQLite delta DB (gitignored)
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | **Required** – OpenAI API key | — |
| `OPENAI_MODEL` | Model for the assistant | `gpt-4o-mini` |
| `MAX_ARTICLES` | Max articles to crawl | `50` |
| `ARTICLES_DIR` | Output directory for Markdown | `./articles` |
| `DELTA_DB_PATH` | SQLite delta tracking file | `./data/delta.db` |
| `VECTOR_STORE_NAME` | Name of the OpenAI vector store | `optisigns-support-docs` |
| `ASSISTANT_NAME` | Name of the OpenAI assistant | `OptiBot` |
| `LOG_LEVEL` | Python log level | `INFO` |

---

## Deploy (Railway example)

1. Push to GitHub (repo name must NOT contain "optisigns")
2. Connect Railway to your repo
3. Set env vars in Railway dashboard
4. Add a Cron Job: `python scraper/main.py` — schedule `0 2 * * *`
5. View logs in Railway → Deployments

---

## Screenshot

*(Add your chatbot screenshot here after running `python main.py --test`)*
