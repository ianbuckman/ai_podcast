#!/usr/bin/env python3
"""Download and chunk a YouTube video transcript."""

import sys
import json
import argparse
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

CHUNK_CHAR_LIMIT = 48_000
OVERLAP_CHARS = 1_000
TIMESTAMP_INTERVAL = 300  # Insert marker every 5 minutes


def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def fetch_transcript(video_id: str) -> dict:
    ytt = YouTubeTranscriptApi()

    try:
        transcript_list = ytt.list(video_id)
    except TranscriptsDisabled:
        return {"error": "transcripts_disabled", "snippets": None}
    except VideoUnavailable:
        return {"error": "video_unavailable", "snippets": None}
    except Exception as e:
        return {"error": f"list_failed: {str(e)}", "snippets": None}

    # Try English first
    try:
        transcript = transcript_list.find_transcript(["en"])
        fetched = transcript.fetch()
        return {
            "snippets": [{"text": s.text, "start": s.start, "duration": s.duration}
                         for s in fetched],
            "language": transcript.language_code,
            "is_generated": transcript.is_generated,
            "is_translated": False,
            "error": None,
        }
    except NoTranscriptFound:
        pass

    # Try any transcript, translate to English if possible
    for transcript in transcript_list:
        try:
            if transcript.is_translatable:
                translated = transcript.translate("en")
                fetched = translated.fetch()
                return {
                    "snippets": [{"text": s.text, "start": s.start, "duration": s.duration}
                                 for s in fetched],
                    "language": transcript.language_code,
                    "is_generated": transcript.is_generated,
                    "is_translated": True,
                    "error": None,
                }
            else:
                fetched = transcript.fetch()
                return {
                    "snippets": [{"text": s.text, "start": s.start, "duration": s.duration}
                                 for s in fetched],
                    "language": transcript.language_code,
                    "is_generated": transcript.is_generated,
                    "is_translated": False,
                    "error": f"non_english_untranslated:{transcript.language_code}",
                }
        except Exception:
            continue

    return {"error": "no_usable_transcript", "snippets": None}


def chunk_transcript(snippets: list) -> list:
    if not snippets:
        return []

    chunks = []
    current_text = ""
    current_start = snippets[0]["start"]
    last_timestamp_at = 0

    for s in snippets:
        if s["start"] - last_timestamp_at >= TIMESTAMP_INTERVAL:
            marker = f"\n[{format_timestamp(s['start'])}]\n"
            current_text += marker
            last_timestamp_at = s["start"]

        current_text += s["text"].strip() + " "

        if len(current_text) >= CHUNK_CHAR_LIMIT:
            chunks.append({
                "chunk_index": len(chunks),
                "start_time": format_timestamp(current_start),
                "end_time": format_timestamp(s["start"] + s.get("duration", 0)),
                "text": current_text.strip(),
                "char_count": len(current_text.strip()),
            })
            overlap_text = current_text[-OVERLAP_CHARS:]
            current_text = overlap_text
            current_start = s["start"]

    if current_text.strip():
        last_snippet = snippets[-1]
        chunks.append({
            "chunk_index": len(chunks),
            "start_time": format_timestamp(current_start),
            "end_time": format_timestamp(
                last_snippet["start"] + last_snippet.get("duration", 0)
            ),
            "text": current_text.strip(),
            "char_count": len(current_text.strip()),
        })

    return chunks


def main():
    parser = argparse.ArgumentParser(description="Get YouTube video transcript")
    parser.add_argument("video_id", help="YouTube video ID")
    args = parser.parse_args()

    result = fetch_transcript(args.video_id)

    if result.get("error") and result.get("snippets") is None:
        output = {
            "video_id": args.video_id,
            "error": result["error"],
            "chunks": [],
            "total_duration_seconds": 0,
            "total_duration_formatted": "00:00:00",
            "num_chunks": 0,
        }
    else:
        snippets = result["snippets"]
        chunks = chunk_transcript(snippets)

        total_duration = 0
        if snippets:
            last = snippets[-1]
            total_duration = last["start"] + last.get("duration", 0)

        output = {
            "video_id": args.video_id,
            "error": result.get("error"),
            "language": result.get("language", "unknown"),
            "is_generated": result.get("is_generated", False),
            "is_translated": result.get("is_translated", False),
            "total_duration_seconds": total_duration,
            "total_duration_formatted": format_timestamp(total_duration),
            "total_chars": sum(c["char_count"] for c in chunks),
            "num_chunks": len(chunks),
            "chunks": chunks,
        }

    json.dump(output, sys.stdout, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
