#!/usr/bin/env python3
"""Manage processed episode state."""

import fcntl
import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

from utils import PROJECT_ROOT

STATE_PATH = PROJECT_ROOT / "data" / "processed.json"
NOTION_CONFIG_PATH = PROJECT_ROOT / "data" / "notion_config.json"

DEFAULT_STATE = {"processed_ids": [], "episodes": {}, "last_check": None}


def _ensure_data_dir():
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_state() -> dict:
    if not STATE_PATH.exists():
        return dict(DEFAULT_STATE)
    try:
        with open(STATE_PATH, "r") as f:
            data = json.load(f)
        # Basic schema validation
        if not isinstance(data, dict) or "processed_ids" not in data:
            print("WARNING: State file has unexpected format, resetting.", file=sys.stderr)
            return dict(DEFAULT_STATE)
        return data
    except (json.JSONDecodeError, ValueError) as e:
        print(f"WARNING: State file corrupted ({e}), resetting to default.", file=sys.stderr)
        return dict(DEFAULT_STATE)


def save_state(state: dict):
    _ensure_data_dir()
    tmp_path = STATE_PATH.with_suffix(".json.tmp")
    with open(tmp_path, "w") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        json.dump(state, f, indent=2, ensure_ascii=False)
    tmp_path.rename(STATE_PATH)  # atomic on same filesystem


def mark_processed(video_id: str, title: str = "", channel: str = "",
                   notion_page_id: str = ""):
    state = load_state()
    if video_id not in state["processed_ids"]:
        state["processed_ids"].append(video_id)
    state["episodes"][video_id] = {
        "title": title,
        "channel": channel,
        "notion_page_id": notion_page_id,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
    state["last_check"] = datetime.now(timezone.utc).isoformat()
    save_state(state)


def update_last_check():
    state = load_state()
    state["last_check"] = datetime.now(timezone.utc).isoformat()
    save_state(state)


def main():
    parser = argparse.ArgumentParser(description="Manage processed state")
    sub = parser.add_subparsers(dest="command")

    mark = sub.add_parser("mark", help="Mark video as processed")
    mark.add_argument("video_id")
    mark.add_argument("--title", default="")
    mark.add_argument("--channel", default="")
    mark.add_argument("--notion-page-id", default="")

    sub.add_parser("check-time", help="Update last check timestamp")
    sub.add_parser("show", help="Show current state summary")

    set_db = sub.add_parser("set-db", help="Save Notion database ID")
    set_db.add_argument("database_id")
    sub.add_parser("get-db", help="Get saved Notion database ID")

    args = parser.parse_args()

    if args.command == "mark":
        mark_processed(args.video_id, args.title, args.channel,
                       getattr(args, "notion_page_id", ""))
        print(f"Marked {args.video_id} as processed", file=sys.stderr)
    elif args.command == "check-time":
        update_last_check()
        print("Updated last check timestamp", file=sys.stderr)
    elif args.command == "show":
        state = load_state()
        summary = {
            "total_processed": len(state["processed_ids"]),
            "last_check": state.get("last_check"),
            "recent_5": list(state["episodes"].items())[-5:],
        }
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    elif args.command == "set-db":
        _ensure_data_dir()
        with open(NOTION_CONFIG_PATH, "w") as f:
            json.dump({"database_id": args.database_id}, f, indent=2)
        print(f"Saved Notion database ID: {args.database_id}", file=sys.stderr)
    elif args.command == "get-db":
        if NOTION_CONFIG_PATH.exists():
            with open(NOTION_CONFIG_PATH, "r") as f:
                print(f.read().strip())
        else:
            print("{}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
