import json
import html
import os
from pathlib import Path
import sqlite3
import ssl
from string import Template
import time
import certifi
from email.message import EmailMessage
from smtplib import SMTP, SMTP_SSL
from urllib.request import Request, urlopen

DB_PATH = os.getenv("STATE_DB", "/data/state.sqlite3")
MAILCOW_URL = os.environ["MAILCOW_URL"].rstrip("/")
MAILCOW_API_KEY = os.environ["MAILCOW_API_KEY"]
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "60"))
WELCOME_FROM = os.environ["WELCOME_FROM"]
WELCOME_SUBJECT = os.getenv("WELCOME_SUBJECT", "Welcome to your new mailbox")
WEBMAIL_URL = os.getenv("WEBMAIL_URL", "https://mail.example.com").rstrip("/")
APP_PASSWORD_URL = os.getenv("APP_PASSWORD_URL", f"{WEBMAIL_URL}/user").rstrip("/")
SMTP_HOST = os.environ["SMTP_HOST"]
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
MAIL_SERVER = os.getenv("MAIL_SERVER", SMTP_HOST)
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
SMTP_USERNAME = os.environ["SMTP_USERNAME"]
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]
SMTP_SECURITY = os.getenv("SMTP_SECURITY", "starttls").lower()
SEND_TO = os.getenv("SEND_TO", "").strip()
WELCOME_TEMPLATE_TEXT = Path(os.getenv("WELCOME_TEMPLATE_TEXT", "/templates/welcome-email-body.txt"))
WELCOME_TEMPLATE_HTML = Path(os.getenv("WELCOME_TEMPLATE_HTML", "/templates/welcome-email-body.html"))
CA_FILE = os.getenv("CA_FILE", certifi.where())

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS sent (address TEXT PRIMARY KEY, sent_at INTEGER NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    conn.commit()
    return conn

def get_mailbox_records():
    request = Request(
        f"{MAILCOW_URL}/api/v1/get/mailbox/all",
        headers={"X-API-Key": MAILCOW_API_KEY, "Accept": "application/json"},
    )
    with urlopen(request, timeout=20, context=ssl.create_default_context(cafile=CA_FILE)) as response:
        data = json.load(response)
    return [item for item in data if item.get("active") in (1, "1", True)]


def render_welcome_templates(address):
    values = {
        "address": address,
        "webmail_url": WEBMAIL_URL,
        "app_password_url": APP_PASSWORD_URL,
        "mail_server": MAIL_SERVER,
        "imap_port": IMAP_PORT,
        "smtp_port": SMTP_PORT,
    }
    text_body = Template(WELCOME_TEMPLATE_TEXT.read_text(encoding="utf-8")).substitute(values)
    html_values = {key: html.escape(str(value), quote=True) for key, value in values.items()}
    html_body = Template(WELCOME_TEMPLATE_HTML.read_text(encoding="utf-8")).substitute(html_values)
    return text_body, html_body


def send_welcome(address):
    message = EmailMessage()
    message["From"] = WELCOME_FROM
    message["To"] = address
    message["Subject"] = WELCOME_SUBJECT
    text_body, html_body = render_welcome_templates(address)
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")
    context = ssl.create_default_context(cafile=CA_FILE)
    if SMTP_SECURITY == "ssl":
        with SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=30) as smtp:
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(message)
    else:
        with SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls(context=context)
            smtp.ehlo()
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(message)


def run_once(conn):
    records = get_mailbox_records()
    addresses = [item["username"] for item in records]
    if conn.execute("SELECT 1 FROM meta WHERE key = 'baseline'").fetchone() is None:
        for address in addresses:
            conn.execute("INSERT OR IGNORE INTO sent(address, sent_at) VALUES (?, strftime('%s','now'))", (address,))
        conn.execute("INSERT INTO meta(key, value) VALUES ('baseline', strftime('%s','now'))")
        conn.commit()
        print(f"Baseline created for {len(addresses)} existing mailboxes; no messages sent", flush=True)
        return

    for address in addresses:
        if conn.execute("SELECT 1 FROM sent WHERE address = ?", (address,)).fetchone():
            continue
        print(f"Sending welcome message to {address}", flush=True)
        try:
            send_welcome(address)
        except Exception as exc:
            print(f"Failed to send welcome message to {address}: {exc}", flush=True)
            continue
        conn.execute("INSERT INTO sent(address, sent_at) VALUES (?, strftime('%s','now'))", (address,))
        conn.commit()

def main():
    if SEND_TO:
        send_welcome(SEND_TO)
        print(f"Welcome message sent to {SEND_TO}", flush=True)
        return
    conn = db()
    while True:
        try:
            run_once(conn)
        except Exception as exc:
            print(f"Polling failed: {exc}", flush=True)
        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()
