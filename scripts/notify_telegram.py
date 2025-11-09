#!/usr/bin/env python3
import os, sys, json, urllib.parse, urllib.request

BOT = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT = os.getenv("TELEGRAM_CHAT_ID")

def send(msg: str) -> dict:
    if not BOT or not CHAT:
        return {"ok": False, "error": "missing_telegram_env"}
    url = f"https://api.telegram.org/bot{BOT}/sendMessage"
    data = {"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"}
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode())
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())

if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read()
    text = text.strip() or "(no content)"
    print(send(text))
