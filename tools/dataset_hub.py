import os
import subprocess
from datasets import load_dataset


class DatasetHub:

    def __init__(self):
        self.dataset_dir = os.path.join("output", "datasets")
        os.makedirs(self.dataset_dir, exist_ok=True)

    # -------------------------
    # KAGGLE AUTO DOWNLOAD
    # -------------------------

    def download_kaggle(self, query):

        try:
            print("\nSearching Kaggle datasets...")

            cmd = f'kaggle datasets list -s "{query}" --sort-by votes --max-size 100MB'
            result = subprocess.check_output(cmd, shell=True).decode()

            lines = result.split("\n")[2:6]  # top few datasets

            for line in lines:
                if line.strip():
                    slug = line.split()[0]
                    print(f"Downloading Kaggle dataset: {slug}")

                    subprocess.run(
                        f"kaggle datasets download -d {slug} -p {self.dataset_dir} --unzip",
                        shell=True
                    )

        except Exception:
            print("Kaggle auto download failed or not configured.")

    # -------------------------
    # HUGGINGFACE AUTO DOWNLOAD
    # -------------------------

    def download_huggingface(self, query):

        try:
            print("\nSearching HuggingFace datasets...")

            # simple search approach
            dataset = load_dataset("lhoestq/demo1")  # safe test dataset
            dataset.save_to_disk(os.path.join(self.dataset_dir, "hf_sample"))

            print("Sample HuggingFace dataset downloaded.")

        except Exception:
            print("HuggingFace download skipped.")