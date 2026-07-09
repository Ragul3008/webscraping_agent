import os
from dotenv import load_dotenv

load_dotenv()

try:
    from groq import Groq
except:
    Groq = None


class DecisionEngine:

    def __init__(self):

        self.api_key = os.getenv("GROQ_API_KEY")

        if self.api_key and Groq:
            self.client = Groq(api_key=self.api_key)
            self.enabled = True
        else:
            self.enabled = False

    def generate_queries(self, topic: str):

        if not self.enabled:
            return self.fallback_queries(topic)

        try:
            prompt = f"""
Generate optimized dataset search queries for:
{topic}

Include:
- image dataset
- video dataset
- Kaggle
- HuggingFace
- GitHub
- Zenodo
- Roboflow

Return only 8 queries.
One per line.
"""

            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.choices[0].message.content
            queries = [q.strip() for q in text.split("\n") if len(q.strip()) > 5]

            if len(queries) < 3:
                return self.fallback_queries(topic)

            return topic, queries[:8]

        except Exception:
            return self.fallback_queries(topic)

    def fallback_queries(self, topic):

        return topic, [
            f"{topic} image dataset kaggle",
            f"{topic} video dataset kaggle",
            f"{topic} huggingface dataset",
            f"{topic} github dataset",
            f"{topic} roboflow dataset",
            f"{topic} zenodo dataset",
            f"{topic} figshare dataset",
            f"{topic} dataset download"
        ]