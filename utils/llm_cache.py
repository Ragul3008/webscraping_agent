import json
import os
import hashlib


CACHE_FILE = "llm_cache.json"


class LLMCache:

    def __init__(self):

        if os.path.exists(CACHE_FILE):

            with open(CACHE_FILE, "r", encoding="utf-8") as f:

                self.cache = json.load(f)

        else:

            self.cache = {}

    def _hash(self, prompt):

        return hashlib.md5(prompt.encode()).hexdigest()

    def get(self, prompt):

        key = self._hash(prompt)

        return self.cache.get(key)

    def set(self, prompt, response):

        key = self._hash(prompt)

        self.cache[key] = response

        with open(CACHE_FILE, "w", encoding="utf-8") as f:

            json.dump(self.cache, f, indent=2)