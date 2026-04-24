#!/usr/bin/env python3
"""Manage processed episode state."""

import json
import sys
import fcntl
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "processed.json"
LOCK_PATH = Path(__file__).resolve().parent.parent / "data" / ".processed.lock"


def _ensure_data_dir():
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def _state_lock():
    # Serialize concurrent mark/update calls (parallel subagents).
    _ensure_data_dir()
    with open(LOCK_PATH, "w") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"processed_ids": [], "episodes": {}, "last_check": None}
    with open(STATE_PATH, "r") as f:
        return json.load(f)


def save_state(state: dict):
    _ensure_data_dir()
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def mark_processed(video_id: str, title: str = "", channel: str = "",
                   notion_page_id: str = "", lark_doc_url: str = ""):
    with _state_lock():
        state = load_state()
        if video_id not in state["processed_ids"]:
            state["processed_ids"].append(video_id)
        entry = {
            "title": title,
            "channel": channel,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
        if notion_page_id:
            entry["notion_page_id"] = notion_page_id
        if lark_doc_url:
            entry["lark_doc_url"] = lark_doc_url
        state["episodes"][video_id] = entry
        state["last_check"] = datetime.now(timezone.utc).isoformat()
        save_state(state)


def update_last_check():
    with _state_lock():
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
    mark.add_argument("--lark-doc-url", default="")

    sub.add_parser("check-time", help="Update last check timestamp")
    sub.add_parser("show", help="Show current state summary")

    args = parser.parse_args()

    if args.command == "mark":
        mark_processed(args.video_id, args.title, args.channel,
                       getattr(args, "notion_page_id", ""),
                       getattr(args, "lark_doc_url", ""))
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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
