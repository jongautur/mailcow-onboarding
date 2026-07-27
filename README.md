# Mailcow Onboarding

> Automatically send a polished welcome email when a new active mailbox is created in Mailcow.

Mailcow Onboarding is a small, self-hosted Docker service that polls the Mailcow API and sends each newly discovered mailbox one onboarding email. It includes both HTML and plain-text templates, so the email works well in modern and text-only mail clients.

## Features

- Sends one welcome email per new active Mailcow mailbox.
- Creates a baseline on first startup without emailing existing mailboxes.
- Persists delivery history in SQLite across restarts.
- Sends multipart emails with HTML and plain-text alternatives.
- Lets non-developers edit the email templates without changing Python code.
- Supports STARTTLS and SSL SMTP connections.
- Includes a one-recipient test mode for checking delivery.
- Runs as a lightweight Docker Compose service.

## How it works

```text
Mailcow API  ──poll──▶  Mailcow Onboarding  ──SMTP──▶  New mailbox
                              │
                              └── SQLite state
```

On the first run, the service records all currently active mailboxes as the baseline. No messages are sent for those existing mailboxes. On later polls, any active mailbox not already recorded in the state database receives the welcome email.

## Quick start

### Requirements

- Docker and Docker Compose
- A Mailcow instance with API access
- An SMTP account that can send the welcome emails

### 1. Configure the environment

```bash
cp .env.example .env
```

Edit `.env` and provide the Mailcow API key, sender address, and SMTP credentials. Keep this file private—it contains secrets and is excluded by `.gitignore`.

### 2. Start the service

```bash
docker compose up -d --build
```

View the service logs:

```bash
docker compose logs -f mailcow-onboarding
```

You should see a baseline message on the first run. New mailboxes will be logged as welcome emails are sent. `MAILCOW_URL` and `SMTP_HOST` must be reachable from the container through DNS or a configured Docker network.

## Configuration

All configuration is provided through environment variables. A complete example is available in [.env.example](.env.example).

### Required settings

| Variable | Description |
| --- | --- |
| `MAILCOW_URL` | Base URL of the Mailcow installation |
| `MAILCOW_API_KEY` | Mailcow API key with permission to read mailboxes |
| `WELCOME_FROM` | Sender address for welcome emails |
| `SMTP_HOST` | SMTP server hostname |
| `SMTP_USERNAME` | SMTP username |
| `SMTP_PASSWORD` | SMTP password |

### Common optional settings

| Variable | Default | Description |
| --- | --- | --- |
| `POLL_SECONDS` | `60` | Seconds between Mailcow API polls |
| `WELCOME_SUBJECT` | `Welcome to your new mailbox` | Welcome email subject |
| `SMTP_PORT` | `587` | SMTP server port |
| `SMTP_SECURITY` | `starttls` | Use `starttls` or `ssl` |
| `WEBMAIL_URL` | `https://mail.example.com` | Webmail link included in the email |
| `APP_PASSWORD_URL` | `{WEBMAIL_URL}/user` | App-password link included in the email |
| `MAIL_SERVER` | `SMTP_HOST` | IMAP/SMTP server name shown in the email |
| `IMAP_PORT` | `993` | IMAP port shown in the email |
| `STATE_DB` | `/data/state.sqlite3` | SQLite state database path |
| `CA_FILE` | certifi bundle | Optional custom CA certificate bundle |

## Editing the welcome email

The email content lives in two files:

- [`templates/welcome-email-body.html`](templates/welcome-email-body.html) — rich HTML version
- [`templates/welcome-email-body.txt`](templates/welcome-email-body.txt) — plain-text version

Both versions are sent in the same email. Edit the files directly; the service reads them when it sends a message, so no code changes are needed.

Available template placeholders:

| Placeholder | Replaced with |
| --- | --- |
| `$address` | New mailbox address |
| `$webmail_url` | Webmail URL |
| `$app_password_url` | App-password URL |
| `$mail_server` | Mail server hostname |
| `$imap_port` | IMAP port |
| `$smtp_port` | SMTP port |

The HTML template automatically escapes substituted values for safe HTML output.

## Test email delivery

To send one test welcome email and exit, add `SEND_TO` to `.env`:

```dotenv
SEND_TO=you@example.com
```

Then run:

```bash
docker compose run --rm mailcow-onboarding
```

Remove `SEND_TO` before starting the normal polling service again.

## State and persistence

The service stores its delivery history in `/data/state.sqlite3` inside the `mailcow-onboarding-data` Docker volume. Docker manages the volume and its permissions.

Do not delete the volume unless you intentionally want to create a new baseline. Removing it deletes the delivery history.

## Development

Check Python syntax locally:

```bash
python3 -m py_compile app.py
```

Validate the Compose configuration:

```bash
docker compose config
```

Build the image directly:

```bash
docker build -t mailcow-onboarding .
```

## Security

- Never commit `.env`, API keys, SMTP passwords, or the SQLite database.
- Use a dedicated Mailcow API key with read-only mailbox access where possible.
- Use a dedicated SMTP account for automated onboarding messages.
- Keep the template directory trusted; template files are mounted read-only in Compose.

## Project structure

```text
.
├── app.py                         # Polling and email delivery service
├── templates/                     # Editable welcome-email templates
│   ├── welcome-email-body.html
│   └── welcome-email-body.txt
├── docker-compose.yml             # Local/production container definition
├── Dockerfile                     # Container image definition
└── .env.example                   # Configuration reference
```

Persistent SQLite state is stored outside the source tree in the Docker-managed `mailcow-onboarding-data` volume.
