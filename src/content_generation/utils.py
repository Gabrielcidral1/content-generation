import re

HTML_RE = re.compile(r"<[^>]+>")


def has_html(text: str) -> bool:
    return bool(HTML_RE.search(text))


def strip_html(text: str) -> str:
    return HTML_RE.sub(" ", text).strip()


# Shared length thresholds — used in prompts.py (schema text) and scorers.py (validation)
HEADLINE_MIN_LEN = 10
HEADLINE_MAX_LEN = 120
HIGHLIGHT_MAX_LEN = 120
ABOUT_MIN_WORDS = 80
ABOUT_MAX_WORDS = 600
