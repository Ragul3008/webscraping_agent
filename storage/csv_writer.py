import csv
from core.logger import setup_logger

logger = setup_logger("CSVWriter")


def write_csv(data, path):

    try:

        if not data:
            logger.warning("No data to save")
            return

        keys = data[0].keys()

        with open(path, "w", newline="", encoding="utf-8") as f:

            writer = csv.DictWriter(f, fieldnames=keys)

            writer.writeheader()

            writer.writerows(data)

        logger.info(f"Saved CSV to {path}")

    except Exception as e:

        logger.error(f"Failed to save CSV: {e}")