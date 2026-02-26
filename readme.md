# 🔍 Multi-Engine Image & Dataset Collector

A Python-based multi-engine data collection system that:

- Downloads images locally using multiple search engines
- Finds dataset source links from major dataset platforms
- Uses fallback mechanisms for stability
- Saves everything in structured folders

---

## 🚀 Features

### 🖼 Multi-Engine Image Downloader
- Bing Image Crawler (Primary)
- Google Image Crawler (Secondary)
- DuckDuckGo Image Fallback
- Automatic failure handling
- Local storage saving

### 📦 Dataset Link Finder
Searches and collects dataset links from:

- Kaggle
- HuggingFace
- GitHub
- Roboflow
- Zenodo
- Mendeley Data
- IEEE DataPort
- UCI Repository
- Figshare

All dataset links are saved into a text file.

---


---

## 📦 Installation

Create virtual environment (optional but recommended):

```bash
python -m venv venv
venv\Scripts\activate

pip install icrawler
pip install ddgs
pip install requests

▶ Usage

Run the program:

python main.py

⚙ How It Works

Splits image downloading across multiple engines.

If one engine fails, the system continues.

Searches dataset-related queries.

Filters results by known dataset platforms.

Saves valid dataset URLs.

⚠ Limitations

*Search engines may block scraping occasionally.

*Some image URLs may return 403 errors.

*Not all dataset links are guaranteed to be valid downloads.

*Does not auto-download Kaggle or HuggingFace datasets (link-only collection).

🔥 Future Improvements

*Kaggle API integration

*HuggingFace dataset auto-download

*Async parallel downloads

*Proxy rotation

*Dataset metadata extraction

*Duplicate image removal

*LLM-based relevance scoring

🛠 Built With

*Python 3.11+

*icrawler

*ddgs

*requests