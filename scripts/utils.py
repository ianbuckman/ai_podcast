#!/usr/bin/env python3
"""Shared constants and utilities for podcast scripts."""

import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHANNEL_ID_PATTERN = re.compile(r"^UC[a-zA-Z0-9_-]{22}$")
VIDEO_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{11}$")

REQUEST_TIMEOUT = 15
DESCRIPTION_LIMIT = 500

VALID_CATEGORIES = {
    "ai-interviews", "ml-deep-dive", "industry", "ai-vc",
    "ai-explainer", "ai-engineering", "ai-news", "general",
}

DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch_url(url: str, headers: dict = None, timeout: int = REQUEST_TIMEOUT,
              retries: int = 2, backoff: float = 2.0) -> tuple:
    """
    Fetch a URL with retry and exponential backoff.
    Returns (data_bytes, None) on success or (None, error_string) on failure.
    """
    if headers is None:
        headers = DEFAULT_HEADERS

    last_error = None
    for attempt in range(1 + retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return (resp.read(), None)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries:
                wait = 30  # Rate limited: wait longer
                print(f"WARNING: HTTP 429 for {url}, retrying in {wait}s...", file=sys.stderr)
                time.sleep(wait)
                last_error = e
                continue
            last_error = e
        except (urllib.error.URLError, OSError) as e:
            last_error = e

        if attempt < retries:
            wait = backoff * (2 ** attempt)
            print(f"WARNING: Fetch failed ({last_error}), retrying in {wait:.0f}s...", file=sys.stderr)
            time.sleep(wait)

    return (None, str(last_error))
