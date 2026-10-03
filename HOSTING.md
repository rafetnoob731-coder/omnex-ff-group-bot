# OMNEX FF GROUP BOT · OB55 · Easy Host

One process = Telegram long-polling + Flask HTTP on `PORT` (Render / Railway ready).

## 1) Get token

1. Telegram → [@BotFather](https://t.me/BotFather)
2. `/newbot` → copy token
3. Optional: your user id → [@userinfobot](https://t.me/userinfobot)

**If a token was ever shared — revoke it:** BotFather → `/revoke`

---

## 2) Render.com (easiest free)

1. Push this folder to GitHub (private recommended)
2. https://dashboard.render.com → **New** → **Web Service**
3. Connect repo
4. Settings:
   - **Runtime:** Docker
   - **Start command:** `python bot.py`
5. **Environment:**

| Key                  | Value          |
|----------------------|----------------|
| `TELEGRAM_BOT_TOKEN` | your token     |
| `ADMIN_IDS`          | your tg id     |
| `PORT`               | `10000`        |

6. Deploy

Health check uses `/` → responds `ok` so Render keeps the service alive.

> Free tier sleeps after ~15 min idle. Ping your Render URL every 10 min or send any Telegram message to wake it.

Or use **Blueprint:** upload `render.yaml` → set env vars → Apply.

---

## 3) Railway.app

1. https://railway.app → New Project → Deploy from GitHub
2. Add variable: `TELEGRAM_BOT_TOKEN`
3. Deploy (Dockerfile auto-detected)

---

## 4) Local / VPS

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="..."
python bot.py
```

Docker:

```bash
docker build -t omnex-ff-bot .
docker run -e TELEGRAM_BOT_TOKEN=... -p 10000:10000 omnex-ff-bot
```

---

## 5) After host is live

```
/start
/status
/add BD UID PASSWORD
/accounts
/5 <UID>
/6 <UID>
/dev
```

Accounts file: `acc.txt` → `id=|uid=|password=|region=`

API examples:

```
https://YOUR-HOST/5?uid=123456789
https://YOUR-HOST/6?uid=123456789
```

---

**OMNEX · OB55 · v1.1 · Powered by OMNEX · DEV BY OMNEX**
