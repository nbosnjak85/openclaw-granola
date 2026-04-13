#!/usr/bin/env python3
"""
Granola.ai API client for OpenClaw skill.
Reads access token directly from Granola's local supabase.json or env var.
Keep Granola app open so it auto-refreshes the token.
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error
import gzip
from datetime import datetime
from pathlib import Path

GRANOLA_API = "https://api.granola.ai"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Granola/5.354.0",
    "X-Client-Version": "5.354.0",
}

SUPABASE_PATHS = [
    Path.home() / "AppData" / "Roaming" / "Granola" / "supabase.json",
    Path.home() / "Library" / "Application Support" / "Granola" / "supabase.json",
]


def load_tokens_from_supabase():
    for path in SUPABASE_PATHS:
        if path.exists():
            try:
                data = json.loads(path.read_text())
                tokens = json.loads(data["workos_tokens"])
                return tokens.get("access_token")
            except Exception:
                continue
    return None


def get_access_token():
    # 1. Try env var
    token = os.environ.get("GRANOLA_ACCESS_TOKEN", "").strip()
    if token:
        return token

    # 2. Read directly from Granola app (local machine)
    token = load_tokens_from_supabase()
    if token:
        return token

    print(json.dumps({
        "error": "No token found. Set GRANOLA_ACCESS_TOKEN env var, or make sure Granola app is installed and running."
    }))
    sys.exit(1)


def api_post(path, payload):
    token = get_access_token()
    headers = {**HEADERS, "Authorization": f"Bearer {token}", "Accept-Encoding": "gzip"}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{GRANOLA_API}{path}", data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            if resp.info().get("Content-Encoding") == "gzip" or raw[:2] == b'\x1f\x8b':
                raw = gzip.decompress(raw)
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        if e.code == 401:
            print(json.dumps({"error": "401 Unauthorized — token expired. Make sure Granola app is open and grab a fresh GRANOLA_ACCESS_TOKEN."}))
        else:
            print(json.dumps({"error": f"HTTP {e.code}: {body}"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


def format_date(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y %H:%M")
    except Exception:
        return iso_str


def extract_text(content):
    if not content:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        node_type = content.get("type", "")
        text = content.get("text", "")
        if text:
            return text
        children = content.get("content", [])
        parts = [extract_text(c) for c in children]
        separator = "\n" if node_type in ("paragraph", "heading", "listItem", "bulletList", "orderedList") else " "
        return separator.join(p for p in parts if p)
    if isinstance(content, list):
        return "\n".join(extract_text(c) for c in content)
    return ""


def cmd_list(args):
    result = api_post("/v2/get-documents", {
        "limit": args.limit,
        "offset": 0,
        "include_last_viewed_panel": True
    })
    docs = result.get("docs", [])
    if not docs:
        print(json.dumps({"meetings": [], "message": "No meetings found."}))
        return

    meetings = []
    for doc in docs:
        content = ""
        panel = doc.get("last_viewed_panel")
        if panel and isinstance(panel, dict):
            content = extract_text(panel.get("content", ""))
        meetings.append({
            "id": doc.get("id"),
            "title": doc.get("title", "Untitled"),
            "created_at": format_date(doc.get("created_at", "")),
            "summary": content[:500] + ("..." if len(content) > 500 else "")
        })
    print(json.dumps({"meetings": meetings}, indent=2))


def cmd_get(args):
    result = api_post("/v2/get-documents", {"limit": 100, "offset": 0, "include_last_viewed_panel": True})
    docs = result.get("docs", [])
    doc = next((d for d in docs if d.get("id") == args.id), None)
    if not doc:
        print(json.dumps({"error": f"Document {args.id} not found."}))
        sys.exit(1)
    content = ""
    panel = doc.get("last_viewed_panel")
    if panel and isinstance(panel, dict):
        content = extract_text(panel.get("content", ""))
    print(json.dumps({"id": doc.get("id"), "title": doc.get("title", "Untitled"),
                      "created_at": format_date(doc.get("created_at", "")), "content": content}, indent=2))


def cmd_transcript(args):
    result = api_post("/v1/get-document-transcript", {"document_id": args.id})
    if not result:
        print(json.dumps({"transcript": [], "message": "No transcript found."}))
        return
    lines = [{"source": u.get("source", "unknown"), "text": u.get("text", ""), "time": u.get("start_timestamp", "")} for u in result]
    print(json.dumps({"transcript": lines}, indent=2))


def cmd_search(args):
    result = api_post("/v2/get-documents", {"limit": 100, "offset": 0, "include_last_viewed_panel": True})
    docs = result.get("docs", [])
    query = args.query.lower()
    matches = []
    for doc in docs:
        title = doc.get("title", "").lower()
        content = ""
        panel = doc.get("last_viewed_panel")
        if panel and isinstance(panel, dict):
            content = extract_text(panel.get("content", ""))
        if query in title or query in content.lower():
            idx = content.lower().find(query)
            snippet = content[max(0, idx-100):idx+200] if idx >= 0 else content[:300]
            matches.append({"id": doc.get("id"), "title": doc.get("title", "Untitled"),
                           "created_at": format_date(doc.get("created_at", "")), "snippet": snippet.strip()})
    print(json.dumps({"query": args.query, "results": matches, "count": len(matches)}, indent=2))


def cmd_actions(args):
    result = api_post("/v2/get-documents", {"limit": args.limit, "offset": 0, "include_last_viewed_panel": True})
    docs = result.get("docs", [])
    keywords = ["todo", "action:", "action item", "follow up", "follow-up", "next step", "[ ]", "- [ ]"]
    all_actions = []
    for doc in docs:
        panel = doc.get("last_viewed_panel")
        if not panel or not isinstance(panel, dict):
            continue
        content = extract_text(panel.get("content", ""))
        doc_actions = [line.strip().lstrip("-•*[ ]").strip() for line in content.split("\n")
                      if any(kw in line.lower() for kw in keywords) and line.strip().lstrip("-•*[ ]").strip()]
        if doc_actions:
            all_actions.append({"meeting": doc.get("title", "Untitled"),
                               "date": format_date(doc.get("created_at", "")),
                               "id": doc.get("id"), "actions": doc_actions})
    print(json.dumps({"action_items": all_actions}, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Granola.ai API client")
    subparsers = parser.add_subparsers(dest="command")

    p_list = subparsers.add_parser("list")
    p_list.add_argument("--limit", type=int, default=10)

    p_get = subparsers.add_parser("get")
    p_get.add_argument("--id", required=True)

    p_trans = subparsers.add_parser("transcript")
    p_trans.add_argument("--id", required=True)

    p_search = subparsers.add_parser("search")
    p_search.add_argument("--query", required=True)

    p_actions = subparsers.add_parser("actions")
    p_actions.add_argument("--limit", type=int, default=5)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    {"list": cmd_list, "get": cmd_get, "transcript": cmd_transcript,
     "search": cmd_search, "actions": cmd_actions}[args.command](args)


if __name__ == "__main__":
    main()
