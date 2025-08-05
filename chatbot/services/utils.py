import re
from typing import Optional


def extract_xml(content: str, tag: str) -> Optional[str]:
    """Extract content from a single XML tag.

    Args:
        content: XML string to parse
        tag: Tag name to extract

    Returns:
        Extracted content or None if not found
    """
    match = re.search(f"<{tag}>(.*?)</{tag}>", content, re.DOTALL)
    return match.group(1).strip() if match else None
