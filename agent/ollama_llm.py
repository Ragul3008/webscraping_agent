import requests
from core.logger import get_logger

logger = get_logger("OllamaLLM")


class OllamaLLM:

    def __init__(self, model="mistral"):

        self.model = model
        self.url = "http://localhost:11434/api/generate"

        logger.info(f"Ollama connected to model: {model}")

    def chat(self, prompt: str) -> str:

        try:

            response = requests.post(
                self.url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=120,
            )

            response.raise_for_status()

            return response.json()["response"]

        except Exception as e:

            logger.error(f"Ollama error: {e}")

            return ""