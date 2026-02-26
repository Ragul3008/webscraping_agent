import json
from core.logger import setup_logger

logger = setup_logger("JSONWriter")


def write_json(data, path):

    try:

        with open(path, "w", encoding="utf-8") as f:

            json.dump(
                data,   # already dicts
                f,
                indent=4,
                ensure_ascii=False
            )

        logger.info(f"Saved JSON to {path}")

    except Exception as e:

        logger.error(f"Failed to save JSON: {e}")