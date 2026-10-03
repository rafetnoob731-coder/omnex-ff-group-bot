# OMNEX FF GROUP BOT · OB55

Professional Free Fire 5/6 Player Invite Telegram Bot + API.

**Powered by OMNEX · DEV BY OMNEX**

| Field | Value |
|-------|-------|
| Client | **OB55** |
| Client Version | `1.132.8` |
| Bot Version | `v1.1` |
| Unity | `2018.4.12f1` |
| Accounts | `acc.txt` multi-account |

## Quick Start

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="from @BotFather"
export ADMIN_IDS="your_telegram_id"
# put guests in acc.txt  →  id=|uid=|password=|region=
python bot.py
```

## acc.txt format

```
id=|uid=|password=|region=
1=|4369584436|YOUR_PASSWORD|BD
2=|7975197636|ANOTHER_PASS|IND
```

First account is primary. Switch with `/use ID`.

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Main panel |
| `/status` | Engine status |
| `/5 UID` | 5-player invite |
| `/6 UID` | 6-player invite |
| `/help` | Help |
| `/dev` | Developer info |
| `/add REGION UID PASS` | Admin: add guest |
| `/add admin ID` | Admin: add admin |
| `/del ID` | Admin: remove account |
| `/accounts` | Admin: list accounts |
| `/use ID` | Admin: set active account |
| `/admins` | Admin: list admins |
| `/refresh` | Admin: reload acc.txt |

## API

| Endpoint | Description |
|----------|-------------|
| `GET /` | Health check |
| `GET /5?uid=` | 5-player invite |
| `GET /6?uid=` | 6-player invite |

## Env

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | From @BotFather |
| `ADMIN_IDS` | Recommended | Comma-separated Telegram user ids |
| `PORT` | Auto | Render/Railway |

## Hosting

See **[HOSTING.md](HOSTING.md)** — Render · Railway · Docker · VPS.

---

Channel: @OMNEXCODEX
