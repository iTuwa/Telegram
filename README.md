# Telegram Forwarder

This repository runs a small Telethon-based forwarder which copies messages from a source chat to a target chat using a user session.

Quick start (local)

1. Create and activate a virtualenv:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Create a `.env` (do not commit it) with these values:

```ini
TG_API_ID=your_api_id
TG_API_HASH=your_api_hash
TG_PHONE=+1234567890
SOURCE_CHAT=-1001234567890
TARGET_CHAT=-1001234567890
FORWARD_MODE=copy
#TG_PASSWORD=your_2fa_password_if_needed
```

3. Run the forwarder:

```bash
source .venv/bin/activate
python forwarder.py
```


Deploying to Railway

1. Push your repo to GitHub (this repo).
2. Create a new project on Railway and connect your GitHub repository.
3. In Railway project settings, set environment variables. Preferred options:
	- `BOT_TOKEN` (recommended) — run as a bot (no phone/2FA). Add the bot to the source channel with read permissions.
	- OR `STRING_SESSION` + `TG_API_ID` + `TG_API_HASH` — if you must use a user account. Generate a `StringSession` locally and store it in `STRING_SESSION`.
	Also set: `SOURCE_CHAT`, `TARGET_CHAT`, `FORWARD_MODE`, `LOG_LEVEL`, etc.
4. Railway will detect the `Procfile` and run the `worker: python forwarder.py` process. If not, set the start command to `python forwarder.py` and type `Worker`.

Notes
- For production, using a Bot token is usually safer than using a user phone session. The current code is written to use a user session; adapt it if you prefer a bot.
- Keep secrets in Railway's Environment Variables UI (do not commit `.env`).
- If you previously committed secrets to Git history, consider purging them from history (BFG or `git filter-repo`) and rotating credentials.
