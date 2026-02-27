# 🤖 Groq-Powered Autonomous Dataset & Media Acquisition Agent

A **fully autonomous, production-grade Python agent** that uses **Groq LLM** as its
reasoning brain to discover, evaluate, and download datasets and media from multiple
sources — hands-free.

---

## ✨ What it does

Give it a query like `"banana plant disease dataset"` and the agent will:

1. **Plan** multiple search strategies (dataset, image, video) using the Groq LLM
2. **Search** HuggingFace, Kaggle, UCI, GitHub, and the open web
3. **Rank and filter** results autonomously
4. **Download datasets** where APIs are available (HuggingFace, Kaggle, UCI)
5. **Download images** automatically via icrawler (Google/Bing)
6. **Collect video dataset links** from YouTube, research portals, Kaggle
7. **Save structured results** as JSON + CSV

---

## 🗂 Project Structure

```
groq-agent/
│
├── main.py                        ← CLI entry point
│
├── agent/
│   ├── groq_agent.py              ← Groq API wrapper + JSON tool-call parser
│   ├── planner.py                 ← LLM-powered multi-strategy planner
│   └── reasoning_loop.py          ← ReAct loop (THINK → ACT → OBSERVE)
│
├── tools/
│   ├── search_tool.py             ← DuckDuckGo / SerpAPI web search
│   ├── huggingface_tool.py        ← HuggingFace Hub search + snapshot_download
│   ├── kaggle_tool.py             ← Kaggle API search + dataset download
│   ├── uci_scraper.py             ← UCI ML Repository async scraper
│   ├── github_scraper.py          ← GitHub dataset repo search (REST API)
│   ├── image_downloader.py        ← Google/Bing image download (icrawler)
│   └── video_dataset_collector.py ← Multi-query video dataset link collector
│
├── storage/
│   ├── json_writer.py             ← Persist AgentResult as JSON
│   └── csv_writer.py              ← Export datasets/images/videos to CSV
│
├── core/
│   ├── config.py                  ← AppConfig singleton (reads .env)
│   ├── logger.py                  ← Rich console + rotating file logger
│   └── models.py                  ← Pydantic models (shared data contracts)
│
├── downloads/
│   ├── images/                    ← Auto-downloaded images
│   └── datasets/                  ← Auto-downloaded dataset files
│
├── results/                       ← JSON + CSV output files
├── logs/                          ← Agent run logs
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone <repo>
cd groq-agent
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY at minimum
```

Get a **free** Groq API key at → https://console.groq.com

### 3. Run

```bash
# Basic
python main.py "banana plant disease dataset"

# With options
python main.py --query "chest X-ray lung cancer" --max-images 60

# Collect links only (no file downloads)
python main.py "brain tumor MRI" --no-download
```

---

## ⚙️ Configuration

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ Yes | Your Groq API key |
| `GROQ_MODEL` | No | Default: `llama3-70b-8192` |
| `KAGGLE_USERNAME` | No | Enables Kaggle API downloads |
| `KAGGLE_KEY` | No | Enables Kaggle API downloads |
| `HF_TOKEN` | No | Required for private HF datasets |
| `SERPAPI_KEY` | No | Better image/search results |
| `GITHUB_TOKEN` | No | Raises GitHub rate limit |
| `MAX_IMAGES` | No | Default: 40 |
| `MAX_ITERATIONS` | No | Default: 20 |

---

## 📤 Output Format

```json
{
  "query": "banana plant disease dataset",
  "images_downloaded": [
    {
      "filename": "000001.jpg",
      "local_path": "downloads/images/banana_plant_disease/000001.jpg",
      "source_url": "",
      "query": "banana plant disease"
    }
  ],
  "video_dataset_links": [
    {
      "title": "Banana Disease Video Dataset - Kaggle",
      "url": "https://www.kaggle.com/...",
      "source": "Kaggle",
      "description": "..."
    }
  ],
  "datasets": [
    {
      "name": "user/banana-disease-dataset",
      "description": "Image dataset for banana leaf disease classification",
      "source": "huggingface",
      "download_url": "https://huggingface.co/datasets/user/banana-disease-dataset",
      "local_path": "downloads/datasets/huggingface/user__banana-disease-dataset",
      "download_status": "success",
      "data_type": "image",
      "tags": ["image-classification", "plant-disease"]
    }
  ],
  "steps_taken": 8,
  "elapsed_seconds": 34.2
}
```

---

## 🧠 How the Agent Reasons (ReAct Loop)

```
User Query: "banana plant disease dataset"
           │
           ▼
    ┌─────────────────┐
    │   PLANNER (LLM) │  →  Generates 4–5 search strategies per category
    └────────┬────────┘
             │
             ▼
    ┌─────────────────────────────────────────────────────────┐
    │                   ReAct LOOP (max 20 iterations)        │
    │                                                         │
    │   THINK: "I should search HuggingFace first since       │
    │           it has the most image datasets"               │
    │       │                                                 │
    │       ▼                                                 │
    │   SELECT TOOL: search_huggingface                       │
    │       │                                                 │
    │       ▼                                                 │
    │   EXECUTE: huggingface_hub.list_datasets(               │
    │              search="banana disease")                   │
    │       │                                                 │
    │       ▼                                                 │
    │   OBSERVE: "HuggingFace: 6 datasets found"              │
    │       │                                                 │
    │       ▼                                                 │
    │   THINK: "Now I should check Kaggle..."                 │
    │       │                                                 │
    │      ...repeat until 'finish' is called...              │
    └─────────────────────────────────────────────────────────┘
             │
             ▼
    ┌─────────────────┐
    │  AgentResult    │  →  JSON + CSV saved to results/
    └─────────────────┘
```

### Tool Selection Logic

The Groq LLM (llama3-70b-8192) receives:
- The original query
- The generated search plan  
- Full conversation history (all prior observations)

It then outputs a JSON decision:
```json
{
  "thought": "HuggingFace has the largest image dataset collection...",
  "tool_name": "search_huggingface",
  "arguments": {"query": "banana leaf disease classification", "auto_download": true},
  "reasoning": "Prioritising HuggingFace for image datasets"
}
```

The loop **prevents duplicate calls** and **detects when the agent is done** (via `"tool_name": "finish"`).

---

## 🔌 Dataset Source Details

| Source | Search Method | Auto-Download |
|---|---|---|
| **HuggingFace** | `huggingface_hub` API | ✅ `snapshot_download` |
| **Kaggle** | Kaggle Python client API | ✅ With API key |
| **UCI ML Repo** | Async HTML scraping | ✅ Direct `.zip`/`.csv` links |
| **GitHub** | GitHub Search REST API | ❌ Link only |
| **Web / General** | DuckDuckGo / SerpAPI | ❌ Link only |
| **Google Images** | icrawler (Google/Bing) | ✅ Auto-download |
| **Video Datasets** | Multi-query web search | ❌ Link collection |

---

## 🛠 Extending the Agent

### Add a new tool

1. Create `tools/my_new_tool.py` with an async function
2. Import it in `tools/__init__.py`
3. Add a case in `agent/reasoning_loop.py → _execute_tool()`
4. Add the tool description to the system prompt in `agent/groq_agent.py`

### Switch LLM

Set `GROQ_MODEL` in `.env` to any supported model:
- `llama3-70b-8192` (recommended — best reasoning)
- `mixtral-8x7b-32768` (faster)
- `llama3-8b-8192` (fastest, lower quality)

---

## 📋 Requirements

- Python 3.10+
- Groq API key (free tier available)
- Internet access

Optional for full functionality:
- Kaggle API credentials
- HuggingFace token
- GitHub personal access token
- SerpAPI key

---

## 📄 License

MIT — free for personal and commercial use.
