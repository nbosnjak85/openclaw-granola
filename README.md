# 🎙️ Granola Meeting Notes Skill

A Claude/OpenClaw skill that connects to **Granola.ai** to fetch, search, and summarize your meeting notes and transcripts.

---

## 📋 Prerequisites

- [Granola](https://granola.ai) installed, signed in, and synced with at least one meeting
- Python 3 — verify with `python3 --version` (macOS/Linux) or `python --version` (Windows)
- [OpenClaw](https://openclaw.ai) installed and configured
- `curl` available in your terminal

---

## 🔑 How Authentication Works

The script finds your token automatically in this order:

1. **Environment variable** — checks `GRANOLA_ACCESS_TOKEN` first
2. **Local Granola app files** — reads directly from Granola's own storage on your machine

This means **if Granola is installed and running, you may not need to do anything at all**. The script finds the token on its own.

> ⚠️ The access token expires every hour. Keep the Granola app open so it auto-refreshes, or set up a cron job (see Step 3).

---

## 📁 Where Granola Stores Tokens

The script looks for the token file in these locations (in order):

| Platform | Path |
|----------|------|
| Windows  | `C:\Users\<YourUsername>\AppData\Roaming\Granola\supabase.json` |
| macOS    | `~/Library/Application Support/Granola/supabase.json` |

---

## ⚙️ Step 1: Get Your Token (if needed)

If the script can't find the token automatically (e.g. Granola is closed or not installed on the same machine), extract it manually.

### macOS — Terminal

```bash
cat ~/Library/Application\ Support/Granola/supabase.json | python3 -c \
  "import sys,json; d=json.load(sys.stdin); tokens=json.loads(d['workos_tokens']); print(tokens['refresh_token'])"
```

**Can't run that command?** Open the file manually instead:

```bash
open ~/Library/Application\ Support/Granola/supabase.json
```

Press `Cmd + F`, search for `refresh_token`, and copy the value between the quotes.

---

### Windows — PowerShell

```powershell
$data = Get-Content "$env:APPDATA\Granola\supabase.json" | ConvertFrom-Json
$tokens = $data.workos_tokens | ConvertFrom-Json
$tokens.refresh_token
```

**Can't run PowerShell?** Open the file manually instead:

1. Press `Win + R`, type `%APPDATA%\Granola\supabase.json`, press Enter
2. It opens in Notepad — press `Ctrl + F`, search for `refresh_token`
3. Copy the value between the quotes

> ⚠️ Never share this token. It grants access to your Granola account.

---

## ⚙️ Step 2: Install the Script

### If you're using OpenClaw

Place `granola.py` in the OpenClaw skills directory:

**macOS / Linux:**
```bash
mkdir -p ~/.openclaw/skills/granola/scripts
cp granola.py ~/.openclaw/skills/granola/scripts/granola.py
```

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.openclaw\skills\granola\scripts"
Copy-Item granola.py "$env:USERPROFILE\.openclaw\skills\granola\scripts\granola.py"
```

Then add your token to `~/.openclaw/config.json`:

```json
{
  "env": {
    "vars": {
      "GRANOLA_ACCESS_TOKEN": "paste-your-token-here"
    }
  }
}
```

---

### If you are NOT using OpenClaw

Save the script anywhere accessible. Recommended locations:

**macOS / Linux:**
```
~/scripts/granola/granola.py
```
```bash
mkdir -p ~/scripts/granola
cp granola.py ~/scripts/granola/granola.py
```

**Windows:**
```
C:\Users\<YourUsername>\scripts\granola\granola.py
```
```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\scripts\granola"
Copy-Item granola.py "$env:USERPROFILE\scripts\granola\granola.py"
```

Then set your token as a permanent environment variable:

**macOS / Linux — add to shell profile:**
```bash
# zsh (default on macOS):
echo 'export GRANOLA_ACCESS_TOKEN="paste-your-token-here"' >> ~/.zshrc
source ~/.zshrc

# bash:
echo 'export GRANOLA_ACCESS_TOKEN="paste-your-token-here"' >> ~/.bashrc
source ~/.bashrc
```

**Windows — PowerShell:**
```powershell
[System.Environment]::SetEnvironmentVariable(
  "GRANOLA_ACCESS_TOKEN",
  "paste-your-token-here",
  "User"
)
```

Restart your terminal, then verify:
```bash
# macOS/Linux
echo $GRANOLA_ACCESS_TOKEN

# Windows PowerShell
$env:GRANOLA_ACCESS_TOKEN
```

---

## 🔄 Step 3: Keep the Token Fresh (Cron / Scheduled Task)

The access token expires every hour. The easiest solution is to **keep Granola open** — it refreshes automatically. If you want a fully automated background refresh, set up a scheduled task.

---

### macOS — cron

Open the cron editor:
```bash
crontab -e
```

> The editor opens in `vi`. Press `i` to start typing, paste your line, then press `Esc` and type `:wq` to save.

Add this line to run every 45 minutes:

```cron
# With OpenClaw:
*/45 * * * * /usr/bin/python3 /Users/<YourUsername>/.openclaw/skills/granola/scripts/granola.py list --limit 1 >> /tmp/granola_cron.log 2>&1

# Without OpenClaw:
*/45 * * * * /usr/bin/python3 /Users/<YourUsername>/scripts/granola/granola.py list --limit 1 >> /tmp/granola_cron.log 2>&1
```

Replace `<YourUsername>` — run `echo $HOME` to find your exact path.

Verify it saved:
```bash
crontab -l
```

Check the log:
```bash
cat /tmp/granola_cron.log
```

> 💡 **macOS Catalina+:** You may need to grant Terminal **Full Disk Access** so cron can read Granola's files.
> Go to: **System Settings → Privacy & Security → Full Disk Access → add Terminal**

---

### macOS — launchd (more reliable than cron)

Create the file `~/Library/LaunchAgents/com.granola.tokenrefresh.plist`:

```bash
nano ~/Library/LaunchAgents/com.granola.tokenrefresh.plist
```

Paste the following (replace `YOUR_USERNAME` — run `whoami` to check):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.granola.tokenrefresh</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/Users/YOUR_USERNAME/scripts/granola/granola.py</string>
    <string>list</string>
    <string>--limit</string>
    <string>1</string>
  </array>
  <key>StartInterval</key>
  <integer>2700</integer>
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>/tmp/granola_refresh.log</string>
  <key>StandardErrorPath</key>
  <string>/tmp/granola_refresh_error.log</string>
</dict>
</plist>
```

Save (`Ctrl+X` → `Y` → Enter), then load the agent:

```bash
launchctl load ~/Library/LaunchAgents/com.granola.tokenrefresh.plist
```

To stop it:
```bash
launchctl unload ~/Library/LaunchAgents/com.granola.tokenrefresh.plist
```

Check logs:
```bash
cat /tmp/granola_refresh.log
cat /tmp/granola_refresh_error.log
```

---

### Windows — Task Scheduler via PowerShell

```powershell
$scriptPath = "$env:USERPROFILE\scripts\granola\granola.py"
# If using OpenClaw:
# $scriptPath = "$env:USERPROFILE\.openclaw\skills\granola\scripts\granola.py"

$action = New-ScheduledTaskAction `
  -Execute "python" `
  -Argument "$scriptPath list --limit 1"

$trigger = New-ScheduledTaskTrigger `
  -RepetitionInterval (New-TimeSpan -Minutes 45) `
  -Once `
  -At (Get-Date)

Register-ScheduledTask `
  -TaskName "GranolaTokenRefresh" `
  -Action $action `
  -Trigger $trigger `
  -RunLevel Highest `
  -Force
```

If `python` isn't found, use the full path:
```powershell
# Find Python's full path:
(Get-Command python).Source
# e.g. C:\Python312\python.exe  — use that in -Execute above
```

**Verify it runs:**
```powershell
Start-ScheduledTask -TaskName "GranolaTokenRefresh"
Get-ScheduledTask -TaskName "GranolaTokenRefresh" | Get-ScheduledTaskInfo
```

---

### Windows — Task Scheduler via GUI (step by step)

1. Press `Win + S`, search **Task Scheduler**, open it
2. Right panel → click **Create Basic Task**
3. Name it `GranolaTokenRefresh` → Next
4. Trigger: choose **Daily** → Next → set a start time → Next
5. Action: choose **Start a program** → Next
6. **Program/script:** `python` (or full path like `C:\Python312\python.exe`)
7. **Add arguments:** `C:\Users\<YourUsername>\scripts\granola\granola.py list --limit 1`
8. Click Finish
9. Find the task in the list → right-click → **Properties**
10. **Triggers** tab → Edit → check **Repeat task every** → set to `45 minutes`
11. Click OK to save

---

## 🚀 Usage

All commands print JSON to stdout. When used via OpenClaw, Claude parses and presents it. You can also run them directly in your terminal.

### 1. 📋 List Recent Meetings

```bash
python3 ~/.openclaw/skills/granola/scripts/granola.py list --limit 10
# or without OpenClaw:
python3 ~/scripts/granola/granola.py list --limit 10
```

| Option | Default | Description |
|--------|---------|-------------|
| `--limit` | 10 | Number of recent meetings to return |

---

### 2. 📄 Get a Specific Meeting

```bash
python3 ~/scripts/granola/granola.py get --id <document_id>
```

Get `document_id` from the `list` command output.

---

### 3. 🎤 Get Meeting Transcript

```bash
python3 ~/scripts/granola/granola.py transcript --id <document_id>
```

Returns speaker-labeled lines with timestamps.

---

### 4. 🔍 Search Meetings

```bash
python3 ~/scripts/granola/granola.py search --query "project kickoff"
```

Searches across titles and full note content. Returns matching snippets with context.

---

### 5. ✅ Get Action Items

```bash
python3 ~/scripts/granola/granola.py actions --limit 5
```

Scans the most recent N meetings for lines containing: `TODO`, `Action:`, `Action item`, `Follow up`, `Follow-up`, `Next step`, `[ ]`

---

## 💬 Triggering the Skill in Claude (OpenClaw)

Just talk naturally — the skill activates on phrases like:

- *"What were my last 5 meetings about?"*
- *"Show me action items from this week"*
- *"Search my Granola notes for 'budget review'"*
- *"Get the transcript from my meeting yesterday"*
- *"What did we discuss in the standup today?"*
- *"Fetch my meeting notes"*

---

## 📤 Output Format

Claude presents results like this:

```
📅 Weekly Standup — Apr 07, 2026 09:30
ID: abc123-def456

Summary:
Team discussed Q2 roadmap priorities and resolved the deployment blocker.

Action Items:
• John to update the staging environment by Friday
• Review PR #204 before next standup
• Schedule design review with the product team
```

---

## 🛠️ Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Access token expired | Keep Granola app open, or re-extract and update `GRANOLA_ACCESS_TOKEN` |
| `404 Not Found` | Wrong document ID | Get a valid ID from the `list` command first |
| `Empty results` | No meetings synced | Open Granola app, sign in, let it sync |
| `No token found` | Granola not installed or env var missing | Install Granola, or set `GRANOLA_ACCESS_TOKEN` manually |
| `python3: command not found` | Python not installed | Install from [python.org](https://python.org) |
| `supabase.json not found` | Granola never opened | Open and sign in to Granola at least once |
| Cron not working (macOS) | Full Disk Access denied | System Settings → Privacy → Full Disk Access → add Terminal |
| Task Scheduler failing (Windows) | Wrong Python path | Use full path e.g. `C:\Python312\python.exe` |

---

## 📦 File Structure Reference

```
# With OpenClaw
~/.openclaw/
├── config.json                               ← GRANOLA_ACCESS_TOKEN set here
└── skills/
    └── granola/
        └── scripts/
            └── granola.py                    ← The script

# Without OpenClaw — macOS / Linux
~/scripts/granola/
└── granola.py
~/.zshrc or ~/.bashrc                         ← GRANOLA_ACCESS_TOKEN exported here

# Without OpenClaw — Windows
C:\Users\<YourUsername>\scripts\granola\
└── granola.py
                                              ← GRANOLA_ACCESS_TOKEN in System Env Vars

# macOS scheduled refresh (launchd)
~/Library/LaunchAgents/
└── com.granola.tokenrefresh.plist

# Token auto-read from (no config needed if Granola is running)
~/Library/Application Support/Granola/supabase.json        ← macOS
C:\Users\<YourUsername>\AppData\Roaming\Granola\supabase.json  ← Windows
```

---

## 🔒 Security Notes

- Never share your access token — it grants read access to all your Granola meeting data
- The script only reads from the Granola API; it never modifies or deletes any data
- If you believe your token was exposed, sign out of Granola and back in to invalidate it
- Tokens stored in OpenClaw config or shell profiles are local to your machine only

---

*Skill version 1.0.0 — Part of the OpenClaw skills ecosystem*