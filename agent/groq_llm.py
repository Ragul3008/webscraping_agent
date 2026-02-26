from groq import Groq
from core.logger import get_logger

logger = get_logger("GroqLLM")


class GroqLLM:

    def __init__(self, api_key: str):

        self.client = Groq(api_key=api_key)

        self.model = "llama-3.3-70b-versatile"

        logger.info(f"Connected to Groq model: {self.model}")

    def chat(self, prompt: str) -> str:

        response = self.client.chat.completions.create(

            model=self.model,

            messages=[
                {"role": "user", "content": prompt}
            ],

            temperature=0.2
        )

        return response.choices[0].message.content