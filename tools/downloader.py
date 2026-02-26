import os
import time
import random
import requests
from icrawler.builtin import BingImageCrawler, GoogleImageCrawler
from ddgs import DDGS


class Downloader:

    def __init__(self, output_dir="output"):

        self.output_dir = output_dir
        self.image_dir = os.path.join(self.output_dir, "images")

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)

        print("Multi-Engine Downloader initialized")

    # ---------------------------------------------------
    # MULTI ENGINE IMAGE DOWNLOADER
    # ---------------------------------------------------

    def download_images(self, query, limit=300):

        print(f"\nDownloading {limit} images for: {query}")

        per_engine = limit // 3

        # 1️⃣ Bing
        try:
            print("Using Bing engine...")
            crawler = BingImageCrawler(storage={"root_dir": self.image_dir})
            crawler.crawl(keyword=query, max_num=per_engine)
        except Exception as e:
            print("Bing failed:", str(e))

        # 2️⃣ Google
        try:
            print("Using Google engine...")
            crawler = GoogleImageCrawler(storage={"root_dir": self.image_dir})
            crawler.crawl(keyword=query, max_num=per_engine)
        except Exception as e:
            print("Google failed:", str(e))

        # 3️⃣ DuckDuckGo fallback
        try:
            print("Using DuckDuckGo fallback...")
            self.ddg_fallback(query, per_engine)
        except Exception as e:
            print("DDG fallback failed:", str(e))

        print("Multi-engine image download complete")

    # ---------------------------------------------------
    # DUCKDUCKGO FALLBACK
    # ---------------------------------------------------

    def ddg_fallback(self, query, limit):

        downloaded = 0

        with DDGS() as ddgs:

            results = ddgs.images(query=query, max_results=limit)

            for r in results:

                try:
                    url = r.get("image")
                    if not url:
                        continue

                    ext = url.split(".")[-1].split("?")[0]
                    if ext.lower() not in ["jpg", "jpeg", "png", "webp"]:
                        ext = "jpg"

                    filename = os.path.join(
                        self.image_dir,
                        f"ddg_{downloaded}.{ext}"
                    )

                    response = requests.get(
                        url,
                        timeout=10,
                        headers={"User-Agent": "Mozilla/5.0"}
                    )

                    if response.status_code == 200:
                        with open(filename, "wb") as f:
                            f.write(response.content)

                        downloaded += 1

                        time.sleep(random.uniform(0.3, 0.6))

                        if downloaded >= limit:
                            break

                except:
                    continue

    # ---------------------------------------------------
    # MULTI ENGINE DATASET LINK FINDER
    # ---------------------------------------------------

    def find_dataset_links(self, query):

        print(f"\nFinding dataset links for: {query}")

        links = set()

        dataset_sites = [
            "kaggle.com",
            "huggingface.co",
            "github.com",
            "roboflow.com",
            "zenodo.org",
            "mendeley",
            "ieee-dataport",
            "figshare.com",
            "archive.ics.uci.edu"
        ]

        search_variants = [
            f"{query} dataset download",
            f"{query} image dataset",
            f"{query} video dataset",
            f"{query} kaggle dataset",
            f"{query} huggingface dataset",
            f"{query} github dataset",
        ]

        try:
            with DDGS() as ddgs:

                for sq in search_variants:

                    try:
                        results = ddgs.text(query=sq, max_results=100)

                        for r in results:

                            url = r.get("href")
                            if not url:
                                continue

                            if any(site in url.lower() for site in dataset_sites):
                                links.add(url)

                    except:
                        continue

        except Exception as e:
            print("Dataset search failed:", str(e))

        filepath = os.path.join(self.output_dir, "dataset_links.txt")

        with open(filepath, "w", encoding="utf-8") as f:
            for link in links:
                f.write(link + "\n")

        print(f"Saved {len(links)} dataset links")

    # ---------------------------------------------------
    # RUN ALL
    # ---------------------------------------------------

    def run_all(self, query):

        self.download_images(query, limit=300)

        self.find_dataset_links(query)

        print("\nALL DOWNLOAD TASKS COMPLETE")
        print("Check folder:", self.output_dir)