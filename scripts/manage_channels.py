#!/usr/bin/env python3
"""Manage podcast channels: add, list, remove."""

import sys
import json
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "channels.yaml"

# Import resolve from sibling module
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from resolve_channel import resolve


def load_config():
    if not CONFIG_PATH.exists():
        return {"channels": []}
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f) or {"channels": []}


def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def cmd_list(args):
    config = load_config()
    channels = config.get("channels", [])
    if not channels:
        print("No channels configured.")
        return
    print(f"{'Name':<35} {'Category':<18} {'Handle':<20} {'Channel ID'}")
    print("-" * 100)
    for ch in channels:
        name = ch.get("name", "?")
        cat = ch.get("category", "general")
        handle = ch.get("handle", "-")
        cid = ch.get("channel_id", "?")
        print(f"{name:<35} {cat:<18} {handle:<20} {cid}")


def cmd_add(args):
    query = args.query
    category = args.category

    print(f"Resolving \"{query}\"...", file=sys.stderr)
    result = resolve(query)
    if result is None:
        print(f"ERROR: Could not resolve \"{query}\". Try a @handle or YouTube URL.", file=sys.stderr)
        sys.exit(1)

    channel_id = result["channel_id"]
    name = result.get("name") or query
    handle = result.get("handle")

    # Check for duplicates
    config = load_config()
    for ch in config.get("channels", []):
        if ch["channel_id"] == channel_id:
            print(f"Already exists: {ch['name']} ({channel_id})", file=sys.stderr)
            sys.exit(0)

    entry = {"name": name, "channel_id": channel_id, "category": category}
    if handle:
        entry["handle"] = handle

    config.setdefault("channels", []).append(entry)
    save_config(config)

    print(json.dumps(entry, ensure_ascii=False, indent=2))
    print(f"Added \"{name}\" ({category})", file=sys.stderr)


def cmd_remove(args):
    name_query = args.name.lower()
    config = load_config()
    channels = config.get("channels", [])
    original_len = len(channels)

    config["channels"] = [
        ch for ch in channels
        if name_query not in ch.get("name", "").lower()
    ]

    removed = original_len - len(config["channels"])
    if removed == 0:
        print(f"No channel matching \"{args.name}\" found.", file=sys.stderr)
        sys.exit(1)

    save_config(config)
    print(f"Removed {removed} channel(s) matching \"{args.name}\".", file=sys.stderr)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Manage podcast channels")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List all channels")

    p_add = sub.add_parser("add", help="Add a channel by name, @handle, or URL")
    p_add.add_argument("query", help="Channel name, @handle, or YouTube URL")
    p_add.add_argument("--category", default="general", help="Category tag (default: general)")

    p_rm = sub.add_parser("remove", help="Remove a channel by name")
    p_rm.add_argument("name", help="Channel name (partial match)")

    args = parser.parse_args()
    {"list": cmd_list, "add": cmd_add, "remove": cmd_remove}[args.command](args)


if __name__ == "__main__":
    main()
