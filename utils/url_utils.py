from urllib.parse import urlparse, urljoin
from typing import Optional
import re


def is_valid_url(url: str) -> bool:
    """
    Validate URL format.
    """

    try:
        result = urlparse(url)

        return all([result.scheme, result.netloc])

    except Exception:

        return False


def normalize_url(base_url: str, link: str) -> Optional[str]:
    """
    Convert relative URL to absolute URL.
    """

    if not link:
        return None

    if is_valid_url(link):
        return link

    return urljoin(base_url, link)


def extract_domain(url: str) -> str:
    """
    Extract domain name.
    """

    parsed = urlparse(url)

    return parsed.netloc.lower()


def is_dataset_file(url: str) -> bool:
    """
    Check if URL points to dataset file.
    """

    dataset_extensions = [
        ".csv",
        ".xlsx",
        ".json",
        ".zip",
        ".tar",
        ".gz",
        ".rar",
        ".7z"
    ]

    url = url.lower()

    return any(url.endswith(ext) for ext in dataset_extensions)


def clean_url(url: str) -> str:
    """
    Remove tracking parameters.
    """

    return re.sub(r"\?.*$", "", url)