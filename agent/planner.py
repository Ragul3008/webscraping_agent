from agent.decision_engine import DecisionEngine
from tools.search import SearchTool
from tools.downloader import Downloader
from tools.dataset_hub import DatasetHub


class Planner:

    def __init__(self):

        self.engine = DecisionEngine()
        self.search = SearchTool()
        self.downloader = Downloader()
        self.dataset_hub = DatasetHub()

    def execute(self, topic: str):

        print("\nGenerating intelligent queries...\n")

        image_query, dataset_queries = self.engine.generate_queries(topic)

        print(f"{len(dataset_queries)} optimized queries generated.\n")

        # 1️⃣ Download image dataset
        self.downloader.download_images(image_query)

        # 2️⃣ Collect dataset links
        all_links = []

        for q in dataset_queries:
            results = self.search.search(q)
            all_links.extend(results)

        print(f"\nCollected {len(all_links)} raw links.")

        self.downloader.save_dataset_links(all_links)

        # 3️⃣ Auto download from Kaggle
        self.dataset_hub.download_kaggle(topic)

        # 4️⃣ Auto HuggingFace pull
        self.dataset_hub.download_huggingface(topic)

        print("\n🔥 FULL WORKFLOW COMPLETE\n")