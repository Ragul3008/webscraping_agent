import os
from icrawler.builtin import BingImageCrawler


class Downloader:

    def __init__(self):

        self.output_dir = "output"
        self.image_dir = os.path.join(self.output_dir, "images")

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)

        print("Ultimate Dataset Collector initialized")

    # -----------------------
    # IMAGE DOWNLOAD
    # -----------------------

    def download_images(self, topic):

        print(f"\nDownloading 300 images for: {topic}")

        try:
            crawler = BingImageCrawler(
                storage={"root_dir": self.image_dir}
            )

            crawler.crawl(
                keyword=topic,
                max_num=300
            )

            print("Images downloaded successfully.")

        except Exception:
            print("Image download failed.")

    # -----------------------
    # DATASET LINK FILTER + CLASSIFY
    # -----------------------

    def save_dataset_links(self, links):

        filtered = []
        seen = set()

        for url in links:

            lower = url.lower()

            if url in seen:
                continue

            if any(domain in lower for domain in [
                "kaggle.com",
                "huggingface.co",
                "github.com",
                "roboflow.com",
                "zenodo.org",
                "figshare.com",
                "mendeley.com",
                "ieee-dataport.org",
                "archive.ics.uci.edu"
            ]):

                if any(word in lower for word in [
                    "dataset",
                    "data",
                    "image",
                    "video"
                ]):
                    filtered.append(url)
                    seen.add(url)

        file_path = os.path.join(self.output_dir, "dataset_links.txt")

        with open(file_path, "w", encoding="utf-8") as f:
            for link in filtered:
                f.write(link + "\n")

        print(f"\nSaved {len(filtered)} unique dataset links.")