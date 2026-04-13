---
name: granola
description: Fetch, search, and summarize Granola meeting notes and transcripts. Use when the user asks about recent meetings, action items, meeting summaries, or wants to search or retrieve notes from Granola.ai. Triggers on phrases like "my last meeting", "meeting notes", "Granola", "action items from", "what did we discuss", "meeting summary", "fetch meetings".
version: 1.0.0
metadata:
  openclaw:
    emoji: "🎙️"
    requires:
      env:
        - GRANOLA_ACCESS_TOKEN
      bins:
        - curl
        - python3
    primaryEnv: GRANOLA_ACCESS_TOKEN
---

# Granola Meeting Notes Skill

This skill connects to the Granola.ai API to fetch, search, and summarize your meeting notes and transcripts.

## Prerequisites

You need your Granola **refresh token** (not the access token — it expires in 1 hour).

**Windows PowerShell:**
```powershell
$data = Get-Content "$env:APPDATA\Granola\supabase.json" | ConvertFrom-Json
$tokens = $data.workos_tokens | ConvertFrom-Json
$tokens.refresh_token
```

**macOS:**
```bash
cat ~/Library/Application\ Support/Granola/supabase.json | python3 -c "import sys,json; d=json.load(sys.stdin); tokens=json.loads(d['workos_tokens']); print(tokens['refresh_token'])"
```

Then set it in your OpenClaw config:
```json
"env": {
  "vars": {
    "GRANOLA_REFRESH_TOKEN": "your-refresh-token-here"
  }
}
```

> ✅ The script automatically refreshes and rotates the token — you only need to set it once.

---

## Available Actions

### 1. List Recent Meetings
Fetch the most recent meeting notes.

```bash
python3 ~/.openclaw/skills/granola/scripts/granola.py list --limit 10
```

### 2. Get a Specific Meeting
Fetch full notes for a meeting by its ID.

```bash
python3 ~/.openclaw/skills/granola/scripts/granola.py get --id <document_id>
```

### 3. Get Meeting Transcript
Fetch the raw transcript for a meeting.

```bash
python3 ~/.openclaw/skills/granola/scripts/granola.py transcript --id <document_id>
```

### 4. Search Meetings
Search across all meeting notes by keyword.

```bash
python3 ~/.openclaw/skills/granola/scripts/granola.py search --query "project kickoff"
```

### 5. Get Action Items
Extract action items from the most recent N meetings.

```bash
python3 ~/.openclaw/skills/granola/scripts/granola.py actions --limit 5
```

---

## Workflow Instructions

When the user asks about meetings or notes:

1. **Run the appropriate command** from the Available Actions above
2. **Parse the JSON output** — each document has `id`, `title`, `created_at`, and `content`
3. **Present results clearly** — use bullet points for lists, show dates in a human-readable format
4. **For action items** — look for lines containing "TODO", "Action:", "Follow up", "Next step", or checkbox patterns `[ ]`
5. **For summaries** — extract the `last_viewed_panel.content` field which contains the AI-generated notes

## Output Format

Always present meeting info like this:

```
📅 [Meeting Title] — [Date]
ID: [document_id]

Summary:
[content]

Action Items:
• [item 1]
• [item 2]
```

## Error Handling

- **401 Unauthorized** → Token expired. Ask user to refresh their `GRANOLA_ACCESS_TOKEN`
- **404 Not Found** → Document ID doesn't exist
- **Empty results** → No meetings found, suggest checking Granola app is installed and synced
