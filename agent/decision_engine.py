from core.logger import setup_logger

logger = setup_logger("DecisionEngine")


class DecisionEngine:

    def should_download(self, dataset):

        return dataset.download_url is not None