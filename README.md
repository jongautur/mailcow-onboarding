# 📬 Mailcow Onboarding

Automatically welcome users when a new mailbox is created in Mailcow.

Mailcow Onboarding is a lightweight, self-hosted Docker service that polls the Mailcow API and sends each newly discovered mailbox one onboarding email. Every message includes both HTML and plain-text versions.

## Features

- Automatic onboarding of new active Mailcow mailboxes.
- Safe first run with an existing-mailbox baseline.
- Persistent SQLite delivery history.
- Editable HTML and plain-text email templates.
- STARTTLS and SSL SMTP support.
- Test mode for one-off messages.
- Small, non-root Docker container.

## How it works

```text
Mailcow API  ──poll──▶  Mailcow Onboarding  ──SMTP──▶  New mailbox
                              │
                              └── SQLite state
```

On the first run, all currently active mailboxes are recorded as the baseline. Existing users do not receive an email. Only mailboxes discovered during later polls receive the welcome message.

## Quick start

### Requirements

- Docker and Docker Compose
- A Mailcow instance with API access
- An SMTP account that can send the welcome emails

### Configure the environment

```bash
cp .env.example .env
```

Edit `.env` and provide the Mailcow API key, sender address, and SMTP credentials. Keep this file private; it contains secrets and is excluded by `.gitignore`.

### Start the service

```bash
docker compose up -d --build
docker compose logs -f mailcow-onboarding
```

## Configuration

All configuration is provided through environment variables. A complete example is available in [.env.example](.env.example).

| Variable | Default | Description |
| --- | --- | --- |
| `MAILCOW_URL` | — | Base URL of the Mailcow installation |
| `MAILCOW_API_KEY` | — | Mailcow API key with permission to read mailboxes |
| `WELCOME_FROM` | — | Sender address for welcome emails |
| `SMTP_HOST` | — | SMTP server hostname |
| `SMTP_USERNAME` | — | SMTP username |
| `SMTP_PASSWORD` | — | SMTP password |
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

The email content lives in:

- [`templates/welcome-email-body.html`](templates/welcome-email-body.html) — rich HTML version
- [`templates/welcome-email-body.txt`](templates/welcome-email-body.txt) — plain-text version

Both versions are sent in the same email. Edit the files directly; the service reads them when it sends a message.

Available template placeholders:

| Placeholder | Replaced with |
| --- | --- |
| `$address` | New mailbox address |
| `$webmail_url` | Webmail URL |
| `$app_password_url` | App-password URL |
| `$mail_server` | Mail server hostname |
| `$imap_port` | IMAP port |
| `$smtp_port` | SMTP port |

The service reads the templates each time it sends a message, so template changes are available immediately. The HTML template escapes substituted values for safe HTML output.

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

Delivery history is stored in `/data/state.sqlite3` inside the `mailcow-onboarding-data` Docker volume. Do not delete the volume unless you intentionally want to create a new baseline.

## Development

```bash
python3 -m py_compile app.py
docker compose config
docker build -t mailcow-onboarding .
```

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

## Release

The current stable release is **[v1.0.0](https://github.com/jongautur/mailcow-onboarding/releases/tag/v1.0.0)**.

## License

Mailcow Onboarding is available under the [MIT License](LICENSE).
