import requests
import os
from core.logger import setup_logger

logger = setup_logger("Downloader")


class Downloader:

    def download(self, url: str, output_dir: str):

        try:

            filename = url.split("/")[-1]

            path = os.path.join(output_dir, filename)

            r = requests.get(url)

            with open(path, "wb") as f:
                f.write(r.content)

            logger.info(f"Downloaded: {filename}")

        except Exception as e:

            logger.error(e)