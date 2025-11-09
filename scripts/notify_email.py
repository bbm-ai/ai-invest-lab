#!/usr/bin/env python3
import os, sys, smtplib, ssl
from email.mime.text import MIMEText

HOST = os.getenv("SMTP_HOST")
PORT = int(os.getenv("SMTP_PORT","587"))
USER = os.getenv("SMTP_USER")
PASS = os.getenv("SMTP_PASS")
TO   = os.getenv("EMAIL_TO")
FROM = os.getenv("EMAIL_FROM", USER or "noreply@example.com")

def send(subject: str, body: str) -> dict:
    if not (HOST and PORT and TO):
        return {"ok": False, "error": "missing_smtp_env"}
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = FROM
    msg["To"] = TO
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(HOST, PORT, timeout=10) as server:
            server.starttls(context=context)
            if USER and PASS:
                server.login(USER, PASS)
            server.sendmail(FROM, [TO], msg.as_string())
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

if __name__ == "__main__":
    subject = sys.argv[1] if len(sys.argv) > 1 else "AI-Invest-Lab notification"
    body = sys.argv[2] if len(sys.argv) > 2 else sys.stdin.read() or "(no content)"
    print(send(subject, body))
