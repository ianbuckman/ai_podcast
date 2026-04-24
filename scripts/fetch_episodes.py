#!/usr/bin/env python3
"""Fetch new podcast episodes from YouTube RSS feeds."""

from __future__ import annotations

import sys
import json
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

RSS_URL_TEMPLATE = "https://www.youtube.com/feeds/videos.xml?channel_id={}"
ATOM_NS = "http://www.w3.org/2005/Atom"
YT_NS = "http://www.youtube.com/xml/schemas/2015"
MEDIA_NS = "http://search.yahoo.com/mrss/"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "channels.yaml"
STATE_PATH = PROJECT_ROOT / "data" / "processed.json"


def load_channels(config_path: Path) -> list:
    import yaml
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config.get("channels", [])


def load_processed(state_path: Path) -> set:
    if not state_path.exists():
        return set()
    with open(state_path, "r") as f:
        data = json.load(f)
    return set(data.get("processed_ids", []))


def _fetch_with_retry(url: str, max_attempts: int = 4) -> bytes | None:
    """Fetch URL with exponential backoff. YouTube RSS rate-limits aggressively
    and returns 404/500 as throttle signal — retry with delay recovers."""
    headers = {"User-Agent": "feedparser/6.0.11"}
    for attempt in range(max_attempts):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code in (404, 429, 500, 502, 503) and attempt < max_attempts - 1:
                wait = (attempt + 1) * 8
                print(f"  HTTP {e.code}, retrying in {wait}s (attempt {attempt + 2}/{max_attempts})",
                      file=sys.stderr)
                time.sleep(wait)
                continue
            raise
        except Exception:
            if attempt < max_attempts - 1:
                time.sleep((attempt + 1) * 4)
                continue
            raise
    return None


def fetch_feed(channel_id: str) -> list:
    url = RSS_URL_TEMPLATE.format(channel_id)
    try:
        xml_data = _fetch_with_retry(url)
        if xml_data is None:
            return []
    except Exception as e:
        print(f"WARNING: Failed to fetch feed for {channel_id}: {e}", file=sys.stderr)
        return []

    root = ET.fromstring(xml_data)
    channel_name = root.findtext(f"{{{ATOM_NS}}}title", default="Unknown")
    episodes = []

    for entry in root.findall(f"{{{ATOM_NS}}}entry"):
        video_id = entry.findtext(f"{{{YT_NS}}}videoId", default="")
        title = entry.findtext(f"{{{ATOM_NS}}}title", default="")
        published = entry.findtext(f"{{{ATOM_NS}}}published", default="")
        link_el = entry.find(f"{{{ATOM_NS}}}link[@rel='alternate']")
        link = link_el.get("href", "") if link_el is not None else ""

        media_group = entry.find(f"{{{MEDIA_NS}}}group")
        description = ""
        if media_group is not None:
            description = media_group.findtext(f"{{{MEDIA_NS}}}description", default="")

        views = 0
        if media_group is not None:
            community = media_group.find(f"{{{MEDIA_NS}}}community")
            if community is not None:
                stats = community.find(f"{{{MEDIA_NS}}}statistics")
                if stats is not None:
                    views = int(stats.get("views", "0"))

        episodes.append({
            "video_id": video_id,
            "title": title,
            "channel_name": channel_name,
            "channel_id": channel_id,
            "published": published,
            "url": link,
            "description": description[:500],
            "views": views,
        })

    return episodes


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fetch new YouTube podcast episodes")
    parser.add_argument("--since", type=str, default=None,
                        help="ISO date cutoff (default: 7 days ago)")
    parser.add_argument("--days", type=int, default=7,
                        help="Number of days to look back (default: 7)")
    parser.add_argument("--all", action="store_true",
                        help="Include already-processed episodes")
    args = parser.parse_args()

    if args.since:
        cutoff = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)

    channels = load_channels(CONFIG_PATH)
    processed = set() if args.all else load_processed(STATE_PATH)

    print(f"Checking {len(channels)} channels (since {cutoff.strftime('%Y-%m-%d')})...",
          file=sys.stderr)

    all_new = []
    for idx, ch in enumerate(channels):
        if idx > 0:
            time.sleep(4)
        episodes = fetch_feed(ch["channel_id"])
        for ep in episodes:
            if ep["video_id"] in processed:
                continue
            try:
                pub_date = datetime.fromisoformat(ep["published"])
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
                if pub_date < cutoff:
                    continue
            except (ValueError, TypeError):
                pass

            ep["category"] = ch.get("category", "general")
            all_new.append(ep)

    all_new.sort(key=lambda x: x.get("published", ""), reverse=True)

    print(f"Found {len(all_new)} new episodes", file=sys.stderr)
    print(json.dumps(all_new, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
