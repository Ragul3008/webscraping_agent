# AI Dataset Scraper Agent (Groq + LLaMA-3.3-70B)

This project is an intelligent AI agent that automatically finds, selects, validates, and saves dataset links from the internet using LLaMA-3.3-70B via Groq.

It can automatically:

• Generate smart dataset search queries  
• Search internet using DuckDuckGo (DDGS)  
• Select best dataset links using LLM reasoning  
• Scrape dataset information asynchronously  
• Validate datasets using LLM  
• Save results into JSON and CSV  

---

# How It Works

User input
↓  
LLaMA Agent (Groq)
↓  
Search Tool (DDGS)
↓  
Select Best URLs (LLM)
↓  
Scraper Tool (Async)
↓  
Validate datasets (LLM)
↓  
Save to JSON and CSV

---

# Project Structure
webscrapping/
│
├── agent/
│ ├── llm_agent.py
│ ├── groq_llm.py
│ ├── planner.py
│ └── state.py
│
├── tools/
│ ├── search_tool.py
│ └── scraper_tool.py
│
├── storage/
│ ├── json_writer.py
│ └── csv_writer.py
│
├── core/
│ ├── logger.py
│ └── config.py
│
├── output/
│ ├── datasets.json
│ └── datasets.csv
│
├── main.py
├── requirements.txt
└── README.md


---

# Requirements

Python 3.10 or newer

Install dependencies:

```bash
pip install -r requirements.txt

Setup Groq API Key
Step 1: Go here
https://console.groq.com/keys

Step 2: Create API key

Step 3: Set environment variable

PowerShell:
setx GROQ_API_KEY "your_api_key_here"
Run the Project
python main.py

Example:

Enter dataset request: banana tree stem disease
Output Files

Saved in:

output/datasets.json
output/datasets.csv

Example JSON:

[
  {
    "title": "Banana Disease Dataset",
    "url": "https://www.kaggle.com/datasets/...",
    "description": "Banana disease classification images"
  }
]
Features

• Uses LLaMA-3.3-70B (Groq cloud)
• Very fast inference
• Async scraping
• Intelligent dataset selection
• Automatic validation
• JSON and CSV export
• Modular architecture
• Production ready

Supported Dataset Sources

• Kaggle
• HuggingFace
• GitHub
• Mendeley
• ResearchGate
• Public dataset portals

Troubleshooting

If search returns 0 results:

Install latest search library:

pip install ddgs --upgrade

If Groq error:

Check API key:

echo $env:GROQ_API_KEY
Expected Speed

Typical runtime:

5 to 15 seconds per query

Example Query Ideas

banana disease dataset
plant disease dataset
tomato leaf disease dataset
brain tumor dataset
crop disease dataset

Tech Stack

Python
Groq API
LLaMA-3.3-70B
AsyncIO
DDGS search
BeautifulSoup
Pydantic