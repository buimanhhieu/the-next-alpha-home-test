# OptiSigns Support Assistant Sync 🤖

An automated pipeline that scrapes help center articles, converts them to Markdown, and synchronizes them with an AI Assistant (RAG system) to provide accurate, citation-backed answers.

## 🌟 Key Features (Home Test Requirements Met)

✅ **1. Web Scraping & Conversion:**
- Fetches >= 30 articles from `support.optisigns.com`.
- Preserves Headers (`#`), Code Blocks, and Links.
- Strips out Menus, Ads, and Navigation elements using `markdownify`.

✅ **2. AI Assistant (RAG System):**
- Uses **ChromaDB** for local vector embeddings (`all-MiniLM-L6-v2`) – lightning fast and cost-free.
- Uses **Groq (Llama 4)** for ultra-fast, accurate responses (or Gemini/OpenAI via config).
- Employs strict system prompts to keep answers concise (max 5 bullet points) and restricted *only* to uploaded docs.
- Automatically cites Source URLs.

✅ **3. Delta Synchronization (Automation):**
- Tracks document changes using an SQLite `delta.db` database.
- Smart Sync: Only uploads **Added** or **Updated** articles, ignoring unchanged ones to save API calls and processing time.
- Single command execution (`python main.py`) handles the full Scrape → Convert → Delta Check → Upload pipeline automatically.

## 🛠️ Architecture

- **Language:** Python 3.10+
- **Database:** SQLite (Delta tracking), ChromaDB (Vector Store)
- **AI Provider:** Groq (Llama-3.3/4 API) with fallback to Gemini/OpenAI.
- **Libraries:** `requests`, `markdownify`, `chromadb`

## 🚀 How to Run Locally

### 1. Setup Environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file from the example:
```bash
cp .env.example .env
```
Fill in your Groq API Key:
```env
AI_PROVIDER=groq
GROQ_API_KEY=gsk_your_api_key_here
```

### 3. Run the Automation Pipeline
```bash
python main.py
```
*This will fetch articles, convert to Markdown, embed them into the local vector store, and update the delta tracker.*

### 4. Test the Assistant
To verify the bot can answer and cite sources properly:
```bash
python test_assistant.py
```

## ☁️ CI/CD & Automation (Daily Sync)

This project achieves **100% serverless automation** using **GitHub Actions**.

- **Workflow:** `.github/workflows/sync.yml`
- **Schedule:** 2:00 AM UTC Daily (`0 2 * * *`)
- **How it works:** 
  1. GitHub spins up an Ubuntu runner daily.
  2. The pipeline fetches new articles from Zendesk API.
  3. The `delta.db` tracks changes. If new/updated articles are found, they are embedded via ChromaDB and synced.
  4. The workflow automatically commits any newly generated Markdown files and updated SQLite databases back to the repository (`[skip ci]` to prevent loops).

### To configure it on your fork:
Go to your GitHub Repository Settings → Secrets and variables → Actions, and add:
- `AI_PROVIDER`: `groq`
- `GROQ_API_KEY`: Your Groq API key
