import requests, os, psutil, sys, jwt, pickle, json, binascii, time, urllib3, base64, datetime, re, socket, threading, ssl, pytz, aiohttp
from flask import Flask, request, jsonify
from protobuf_decoder.protobuf_decoder import Parser
from xC4 import *; from xHeaders import *
from datetime import datetime
from google.protobuf.timestamp_pb2 import Timestamp
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from Pb2 import DEcwHisPErMsG_pb2, MajoRLoGinrEs_pb2, PorTs_pb2, MajoRLoGinrEq_pb2, sQ_pb2, Team_msg_pb2
from cfonts import render, say
import asyncio
import random

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ═══════════════════════════════════════════════════════════
# OMNEX FF GROUP BOT · Professional Edition
# ═══════════════════════════════════════════════════════════

# TELEGRAM — env only (never hardcode tokens)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
if not TELEGRAM_BOT_TOKEN:
    print("[OMNEX] WARNING: TELEGRAM_BOT_TOKEN not set.")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}" if TELEGRAM_BOT_TOKEN else ""

# ── Encrypted Credit · OMNEX ──────────────────────────────
# DO NOT REMOVE — credit integrity protected
_MAIN = "ahodfAgHHQsDAg8="
_API  = "EGMKBx0LAwIP"
_BOTC = "DA18CQcdCwMCDw=="
_LINE = "bnd+fxB5agl/DgAKbfgRDhp4f38SJjsTLzoqIDkiHw=="
_BRAND = "G34Uf2Znf2AYeXUNfwAAAAAA"
_KEY  = "OMNEX_K3Y_2026_V1"

def _dEcOdE_cReDiT():
    """OMNEX internal credit decoder — protected"""
    try:
        def _x(enc):
            raw = base64.b64decode(enc.encode())[::-1]
            return "".join(chr(b ^ ord(_KEY[i % len(_KEY)])) for i, b in enumerate(raw))
        return {
            "developer":    "OMNEX",
            "main_channel": _x(_MAIN),
            "api_channel":  _x(_API),
            "bot_channel":  _x(_BOTC),
            "credit_line":  _x(_LINE),
            "brand":        _x(_BRAND),
        }
    except Exception:
        return {
            "developer": "OMNEX",
            "main_channel": "@OMNEXCODEX",
            "api_channel": "@OMNEXAPI",
            "bot_channel": "@OMNEXBOTS",
            "credit_line": "Powered by OMNEX · DEV BY OMNEX",
            "brand": "OMNEX FF GROUP BOT",
        }

CREDIT_INFO = _dEcOdE_cReDiT()
# ── End Encrypted Credit ──────────────────────────────────

# Variables
#------------------------------------------#
online_writer = None
whisper_writer = None
spam_room = False
spammer_uid = None
spam_chat_id = None
spam_uid = None
Spy = False
Chat_Leave = False
BOT_UID = None
key = None
iv = None
region = None
TarGeT = None
acc_name = None
ACTIVE_ACC_ID = None
# Set by GeNeRaTeAccEss when Garena answers 429, so the retry loop can back
# off instead of hammering the endpoint and making the throttle worse.
OAUTH_RATE_LIMITED = False
OAUTH_RETRY_AFTER = 0
# Last failure reason, so /status can explain itself instead of only "Connecting".
LAST_ERROR = "none yet"
# When Garena answers "Protection Bypass" the account is flagged. Retrying
# every few seconds keeps it flagged and can extend the block, so we pause
# all login attempts for a while instead.
PROTECTION_BYPASS_COOLDOWN = 3600
BLOCKED_UNTIL = 0.0
#------------------------------------------#


def _esc(text):
    """Escape for Telegram HTML."""
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _set_last_error(msg):
    global LAST_ERROR
    LAST_ERROR = str(msg)[:180]

# ═══════════════════════════════════════════════════════════
#  MULTI-ACCOUNT · acc.txt
#  Format: id=|uid=|password=|region=
# ═══════════════════════════════════════════════════════════

from pathlib import Path

ACC_FILE = Path(__file__).with_name("acc.txt")
ADMIN_FILE = Path(__file__).with_name("admins.txt")

def _load_admin_ids():
    ids = set()
    env = os.environ.get("ADMIN_IDS", "").replace(" ", "")
    for x in env.split(","):
        if x.isdigit():
            ids.add(int(x))
    if ADMIN_FILE.exists():
        for line in ADMIN_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.isdigit():
                ids.add(int(line))
    return ids

ADMIN_IDS = _load_admin_ids()

def is_admin(user_id: int) -> bool:
    if not ADMIN_IDS:
        return True  # open until first admin is set
    return int(user_id) in ADMIN_IDS

def save_admin_ids():
    ADMIN_FILE.write_text("\n".join(str(i) for i in sorted(ADMIN_IDS)) + "\n", encoding="utf-8")

def load_accounts():
    """Return list of dicts: {id, uid, password, region}"""
    accounts = []
    if not ACC_FILE.exists():
        return accounts
    for line in ACC_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # id=|uid=|password=|region=
        if "=|" not in line:
            continue
        try:
            left, rest = line.split("=|", 1)
            acc_id = left.strip()
            parts = rest.split("|")
            if len(parts) < 3:
                continue
            uid = parts[0].strip()
            password = parts[1].strip()
            reg = parts[2].strip().upper() if len(parts) > 2 else "BD"
            if uid and password:
                accounts.append({
                    "id": acc_id,
                    "uid": uid,
                    "password": password,
                    "region": reg or "BD",
                })
        except Exception:
            continue
    return accounts

def save_accounts(accounts):
    lines = [
        "# OMNEX FF GROUP BOT · Accounts",
        "# Format: id=|uid=|password=|region=",
        "# First line is primary unless /use <id>",
        "",
    ]
    for a in accounts:
        lines.append(f"{a['id']}=|{a['uid']}|{a['password']}|{a['region']}")
    ACC_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

def get_account_by_id(acc_id):
    for a in load_accounts():
        if str(a["id"]) == str(acc_id):
            return a
    return None

def get_primary_account():
    global ACTIVE_ACC_ID
    accounts = load_accounts()
    if not accounts:
        return None
    if ACTIVE_ACC_ID:
        a = get_account_by_id(ACTIVE_ACC_ID)
        if a:
            return a
    return accounts[0]


def get_account_candidates():
    """Primary account first, then the rest.

    A broken primary (e.g. an IND account that OAuth rejects) must not stop
    the bot when working BD accounts are sitting in acc.txt.
    """
    accounts = load_accounts()
    if not accounts:
        return []
    primary = get_primary_account()
    if not primary:
        return accounts
    others = [a for a in accounts if str(a.get("id")) != str(primary.get("id"))]
    return [primary] + others

def next_account_id(accounts):
    nums = []
    for a in accounts:
        if str(a["id"]).isdigit():
            nums.append(int(a["id"]))
    return str(max(nums) + 1) if nums else "1"


app = Flask(__name__)

Hr = {
    'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 13; CPH2095 Build/RKQ1.211119.001)",
    'Connection': "Keep-Alive",
    'Accept-Encoding': "gzip",
    'Content-Type': "application/x-www-form-urlencoded",
    'Expect': "100-continue",
    'X-Unity-Version': "2018.4.12f1",
    'X-GA': "v1 1",
    'ReleaseVersion': "OB55"}

# ---- Random Colors ----
def get_random_color():
    colors = [
        "[FF0000]", "[00FF00]", "[0000FF]", "[FFFF00]", "[FF00FF]", "[00FFFF]", "[FFFFFF]", "[FFA500]",
        "[A52A2A]", "[800080]", "[000000]", "[808080]", "[C0C0C0]", "[FFC0CB]", "[FFD700]", "[ADD8E6]",
        "[90EE90]", "[D2691E]", "[DC143C]", "[00CED1]", "[9400D3]", "[F08080]", "[20B2AA]", "[FF1493]",
        "[7CFC00]", "[B22222]", "[FF4500]", "[DAA520]", "[00BFFF]", "[00FF7F]", "[4682B4]", "[6495ED]",
        "[5F9EA0]", "[DDA0DD]", "[E6E6FA]", "[B0C4DE]", "[556B2F]", "[8FBC8F]", "[2E8B57]", "[3CB371]",
        "[6B8E23]", "[808000]", "[B8860B]", "[CD5C5C]", "[8B0000]", "[FF6347]", "[FF8C00]", "[BDB76B]",
        "[9932CC]", "[8A2BE2]", "[4B0082]", "[6A5ACD]", "[7B68EE]", "[4169E1]", "[1E90FF]", "[191970]",
        "[00008B]", "[000080]", "[008080]", "[008B8B]", "[B0E0E6]", "[AFEEEE]", "[E0FFFF]", "[F5F5DC]",
        "[FAEBD7]"
    ]
    return random.choice(colors)

# ---- Telegram Bot Functions ----
async def send_telegram_message(chat_id, text):
    """টেলিগ্রামে মেসেজ পাঠানোর ফাংশন"""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            return await response.json()

async def send_telegram_buttons(chat_id, text, buttons):
    """বাটন সহ মেসেজ পাঠানোর ফাংশন"""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    keyboard = {"inline_keyboard": buttons}
    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": json.dumps(keyboard),
        "parse_mode": "HTML"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            return await response.json()

async def process_telegram_command(update):
    """Professional command router"""
    global online_writer, BOT_UID, key, iv, region, TarGeT, acc_name, ACTIVE_ACC_ID, ADMIN_IDS

    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat_id = message["chat"]["id"]
    user = message.get("from", {})
    user_id = user.get("id")
    text = (message.get("text") or "").strip()
    if not text:
        return

    low = text.lower()
    parts = text.split()
    cmd = parts[0].lower().split("@")[0]  # strip @botname

    # ── /start ──
    if cmd == "/start":
        await send_main_menu(chat_id)
        return

    # ── /help ──
    if cmd == "/help":
        await send_telegram_message(chat_id,
            "<b>📚 OMNEX Commands</b>\n\n"
            "<b>Public</b>\n"
            "/start — Main panel\n"
            "/status — Engine status\n"
            "/5 UID — 5-player invite\n"
            "/6 UID — 6-player invite\n"
            "/help — This menu\n"
            "/dev — Developer info\n\n"
            "<b>Admin</b>\n"
            "/add REGION UID PASS — add guest\n"
            "/add admin TELEGRAM_ID — add admin\n"
            "/del ID — remove account\n"
            "/accounts — list accounts\n"
            "/use ID — set active account\n"
            "/admins — list admins\n"
            "/refresh — reload acc.txt"
        )
        return

    # ── /dev ──
    if cmd in ("/dev", "/developer"):
        brand = CREDIT_INFO.get("brand", "OMNEX FF GROUP BOT")
        credit = CREDIT_INFO.get("credit_line", "Powered by OMNEX")
        ch = CREDIT_INFO.get("main_channel", "@OMNEXCODEX")
        await send_telegram_message(chat_id,
            f"<b>⚡ {brand}</b>\n"
            f"<i>{credit}</i>\n\n"
            f"Client · <code>OB55</code>\n"
            f"Version · <code>v1.1</code>\n"
            f"Engine · <code>1.132.9</code>\n"
            f"Unity · <code>2018.4.12f1</code>\n\n"
            f"Channel · {ch}\n"
            f"Dev · <b>OMNEX</b>"
        )
        return

    # ── /status ──
    if cmd == "/status":
        status = "🟢 Online" if online_writer else "🔴 Connecting"
        primary = get_primary_account()
        acc_line = f"{primary['id']} · {primary['uid']} · {primary['region']}" if primary else "—"
        await send_telegram_message(chat_id,
            f"<b>🤖 Engine Status</b>\n\n"
            f"Status · {status}\n"
            f"Target · <code>{TarGeT or '—'}</code>\n"
            f"Name · <code>{acc_name or '—'}</code>\n"
            f"Region · <code>{region or '—'}</code>\n"
            f"Bot UID · <code>{BOT_UID or '—'}</code>\n"
            f"Active Acc · <code>{acc_line}</code>\n"
            f"Client · <code>OB55 · v1.1</code>\n"
            f"Last Err · <code>{_esc(str(LAST_ERROR))}</code>"
        )
        return

    # ── /5 UID ──
    if cmd == "/5":
        if len(parts) < 2:
            await send_telegram_message(chat_id, "❌ Usage: <code>/5 UID</code>")
            return
        try:
            target_uid = int(parts[1])
        except ValueError:
            await send_telegram_message(chat_id, "❌ Invalid UID")
            return
        if online_writer is None:
            await send_telegram_message(chat_id, "❌ Bot not connected yet")
            return
        await send_telegram_message(chat_id, f"⏳ Sending 5-player invite → <code>{target_uid}</code>")
        try:
            await perform_invite_5(target_uid)
            await send_telegram_message(chat_id, f"✅ 5-player invite sent → <code>{target_uid}</code>")
        except Exception as e:
            await send_telegram_message(chat_id, f"❌ {e}")
        return

    # ── /6 UID ──
    if cmd == "/6":
        if len(parts) < 2:
            await send_telegram_message(chat_id, "❌ Usage: <code>/6 UID</code>")
            return
        try:
            target_uid = int(parts[1])
        except ValueError:
            await send_telegram_message(chat_id, "❌ Invalid UID")
            return
        if online_writer is None:
            await send_telegram_message(chat_id, "❌ Bot not connected yet")
            return
        await send_telegram_message(chat_id, f"⏳ Sending 6-player invite → <code>{target_uid}</code>")
        try:
            await perform_invite_6(target_uid)
            await send_telegram_message(chat_id, f"✅ 6-player invite sent → <code>{target_uid}</code>")
        except Exception as e:
            await send_telegram_message(chat_id, f"❌ {e}")
        return

    # ── ADMIN GATE for remaining ──
    if cmd in ("/add", "/del", "/accounts", "/use", "/admins", "/refresh", "/dumpacc"):
        if not is_admin(user_id):
            await send_telegram_message(chat_id, "🔒 Admin only")
            return

    # ── /add ──
    if cmd == "/add":
        # /add admin TELEGRAM_ID
        if len(parts) >= 3 and parts[1].lower() == "admin":
            if not parts[2].isdigit():
                await send_telegram_message(chat_id, "Usage: <code>/add admin TELEGRAM_ID</code>")
                return
            new_id = int(parts[2])
            ADMIN_IDS.add(new_id)
            save_admin_ids()
            await send_telegram_message(chat_id, f"✅ Admin added · <code>{new_id}</code>")
            return

        # /add REGION UID PASSWORD  [optional ID]
        # /add bd UID PASSWORD ID
        if len(parts) < 4:
            await send_telegram_message(chat_id,
                "Usage:\n"
                "<code>/add REGION UID PASSWORD</code>\n"
                "<code>/add BD 7975197636 YOUR_PASS</code>\n"
                "<code>/add admin 123456789</code>"
            )
            return
        reg = parts[1].upper()
        uid = parts[2]
        password = parts[3]
        accounts = load_accounts()
        if len(parts) >= 5 and parts[4].strip():
            acc_id = parts[4].strip()
        else:
            acc_id = next_account_id(accounts)
        # replace if same uid exists
        accounts = [a for a in accounts if a["uid"] != uid]
        accounts.append({"id": acc_id, "uid": uid, "password": password, "region": reg})
        save_accounts(accounts)
        await send_telegram_message(chat_id,
            f"✅ Account saved\n"
            f"ID · <code>{acc_id}</code>\n"
            f"UID · <code>{uid}</code>\n"
            f"Region · <code>{reg}</code>\n"
            f"File · <code>acc.txt</code>"
        )
        return

    # ── /dumpacc ──
    # acc.txt lives in the container filesystem, so /add is lost on restart.
    # /dumpacc prints the live contents so they can be committed to the repo.
    if cmd == "/dumpacc":
        if not is_admin(user_id):
            await send_telegram_message(chat_id, "🔒 Admin only")
            return
        live = load_accounts()
        if not live:
            await send_telegram_message(chat_id, "No accounts in acc.txt")
            return
        body = "\n".join(f"{a['id']}=|{a['uid']}|{a['password']}|{a['region']}" for a in live)
        note = "\n\n⚠️ Copy these lines into acc.txt in the repo to make them permanent."
        esc = lambda s: (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        await send_telegram_message(chat_id, f"<b>acc.txt (live)</b>\n<pre>{esc(body)}</pre>{esc(note)}")
        return

    # ── /del ID ──
    if cmd == "/del":
        if len(parts) < 2:
            await send_telegram_message(chat_id, "Usage: <code>/del ID</code>")
            return
        acc_id = parts[1]
        accounts = load_accounts()
        before = len(accounts)
        accounts = [a for a in accounts if str(a["id"]) != str(acc_id)]
        if len(accounts) == before:
            await send_telegram_message(chat_id, f"❌ No account with ID <code>{acc_id}</code>")
            return
        save_accounts(accounts)
        if str(ACTIVE_ACC_ID) == str(acc_id):
            ACTIVE_ACC_ID = None
        await send_telegram_message(chat_id, f"🗑 Removed account ID <code>{acc_id}</code>")
        return

    # ── /accounts ──
    if cmd == "/accounts":
        accounts = load_accounts()
        if not accounts:
            await send_telegram_message(chat_id,
                "📭 No accounts yet\nAdd: <code>/add BD UID PASSWORD</code>"
            )
            return
        lines = ["<b>📂 Accounts · acc.txt</b>\n"]
        for a in accounts:
            mark = "⭐" if (ACTIVE_ACC_ID and str(ACTIVE_ACC_ID) == str(a["id"])) or (not ACTIVE_ACC_ID and a == accounts[0]) else "•"
            lines.append(f"{mark} <code>{a['id']}</code> · <code>{a['uid']}</code> · {a['region']}")
        lines.append("\n<code>/use ID</code> · <code>/del ID</code> · <code>/add BD UID PASS</code>")
        await send_telegram_message(chat_id, "\n".join(lines))
        return

    # ── /use ID ──
    if cmd == "/use":
        if len(parts) < 2:
            await send_telegram_message(chat_id, "Usage: <code>/use ID</code>")
            return
        acc = get_account_by_id(parts[1])
        if not acc:
            await send_telegram_message(chat_id, f"❌ Account ID <code>{parts[1]}</code> not found")
            return
        ACTIVE_ACC_ID = str(acc["id"])
        await send_telegram_message(chat_id,
            f"✅ Active account → <code>{acc['id']}</code>\n"
            f"UID · <code>{acc['uid']}</code> · {acc['region']}\n"
            f"<i>Engine will use this on next reconnect</i>"
        )
        return

    # ── /admins ──
    if cmd == "/admins":
        if not ADMIN_IDS:
            await send_telegram_message(chat_id, "No admins locked yet · anyone can /add admin")
            return
        lines = ["<b>🛡 Admins</b>\n"] + [f"• <code>{i}</code>" for i in sorted(ADMIN_IDS)]
        await send_telegram_message(chat_id, "\n".join(lines))
        return

    # ── /refresh ──
    if cmd == "/refresh":
        accounts = load_accounts()
        await send_telegram_message(chat_id, f"🔄 Reloaded · <code>{len(accounts)}</code> accounts from acc.txt")
        return


async def send_main_menu(chat_id):
    """Professional main menu"""
    brand = CREDIT_INFO.get("brand", "OMNEX FF GROUP BOT")
    credit = CREDIT_INFO.get("credit_line", "Powered by OMNEX")
    ch = CREDIT_INFO.get("main_channel", "@OMNEXCODEX")
    primary = get_primary_account()
    acc_line = f"{primary['id']} · {primary['uid']}" if primary else "no account"
    n_acc = len(load_accounts())
    await send_telegram_message(chat_id,
        f"<b>⚡ {brand}</b>\n"
        f"<i>{credit}</i>\n"
        f"<code>OB55 · v1.1 · 1.132.9</code>\n\n"
        f"Name · <code>{acc_name or '—'}</code>\n"
        f"Target · <code>{TarGeT or '—'}</code>\n"
        f"Status · {'🟢 Online' if online_writer else '🔴 Connecting'}\n"
        f"Accounts · <code>{n_acc}</code> · Active <code>{acc_line}</code>\n\n"
        f"<b>📚 Commands</b>\n"
        f"/start · /status · /help · /dev\n"
        f"/5 UID · /6 UID\n"
        f"/accounts · /add · /use · /del\n\n"
        f"Channel · {ch}")

async def answer_callback(callback_id):
    """কলব্যাকের জবাব দেয়া"""
    url = f"{TELEGRAM_API_URL}/answerCallbackQuery"
    payload = {"callback_query_id": callback_id}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            return await response.json()

async def telegram_polling():
    """টেলিগ্রাম থেকে আপডেট নেওয়ার ফাংশন (লং পোলিং)"""
    offset = 0
    print("🤖 Telegram Bot Started - Polling for updates...")
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                url = f"{TELEGRAM_API_URL}/getUpdates"
                params = {"offset": offset, "timeout": 30}
                
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    
                    if data.get("ok") and data.get("result"):
                        for update in data["result"]:
                            offset = update["update_id"] + 1
                            await process_telegram_command(update)
                            
            except Exception as e:
                print(f"Telegram polling error: {e}")
                await asyncio.sleep(5)

# Original encrypted_proto and other functions remain the same
async def encrypted_proto(encoded_hex):
    key = b'Yg&tc%DEuh6%Zc^8'
    iv = b'6oyZDr22E3ychjM%'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_message = pad(encoded_hex, AES.block_size)
    encrypted_payload = cipher.encrypt(padded_message)
    return encrypted_payload
    
async def GeNeRaTeAccEss(uid , password):
    """Always returns (open_id, access_token) or (None, None).
    Never return a bare string — callers do: open_id, access_token = await GeNeRaTeAccEss(...)
    which raises "too many values to unpack (expected 2)" on a string.
    """
    urls = [
        "https://ffmconnect.ppmainecoonghj.com/oauth/guest/token/grant",
        "https://100067.connect.garena.com/oauth/guest/token/grant",
    ]
    data = {
        "uid": str(uid),
        "password": password,
        "response_type": "token",
        "client_type": "2",
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        "client_id": "100067",
    }
    headers_base = {
        "User-Agent": await Ua(),
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "close",
    }
    last_err = ""
    global OAUTH_RATE_LIMITED, OAUTH_RETRY_AFTER
    OAUTH_RATE_LIMITED = False
    OAUTH_RETRY_AFTER = 0
    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                headers = dict(headers_base)
                headers["Host"] = url.split("/")[2]
                async with session.post(url, headers=headers, data=data, ssl=False) as response:
                    body = await response.text()
                    if response.status == 429:
                        # Garena is throttling us. Remember it so the retry
                        # loop can back off instead of making it worse.
                        OAUTH_RATE_LIMITED = True
                        try:
                            OAUTH_RETRY_AFTER = int(response.headers.get("Retry-After", 0) or 0)
                        except (TypeError, ValueError):
                            OAUTH_RETRY_AFTER = 0
                        last_err = "http_429"
                        break
                    if response.status != 200:
                        last_err = f"http_{response.status}"
                        continue
                    try:
                        js = json.loads(body)
                    except Exception:
                        last_err = "bad_json"
                        continue
                    open_id = js.get("open_id")
                    access_token = js.get("access_token")
                    if open_id and access_token:
                        return open_id, access_token
                    last_err = str(js.get("error") or js.get("message") or "no_token")[:60]
            except Exception as e:
                last_err = type(e).__name__
                continue
    print(f"[OMNEX] OAuth failed: {last_err}")
    return None, None


def _encode_pb_varint(value: int) -> bytes:
    out = bytearray()
    while True:
        b = value & 0x7F
        value >>= 7
        out.append(b | (0x80 if value else 0))
        if not value:
            return bytes(out)


def _encode_pb_field(number: int, value) -> bytes:
    """Encode one protobuf field by hand (int -> varint, str -> length-delimited)."""
    if isinstance(value, int):
        return _encode_pb_varint(number << 3) + _encode_pb_varint(value)
    raw = str(value).encode("utf-8")
    return _encode_pb_varint((number << 3) | 2) + _encode_pb_varint(len(raw)) + raw


async def EncRypTMajoRLoGin(open_id, access_token, region="OTHERS"):
    major_login = MajoRLoGinrEq_pb2.MajorLogin()
    major_login.event_time = str(datetime.now())[:-7]
    major_login.game_name = "free fire"
    major_login.platform_id = 4
    major_login.client_version = client_version(region)
    major_login.system_software = "2019116753"
    major_login.system_hardware = "Android OS 12 / API-31 (SP1A.210812.016)"
    major_login.telecom_operator = "Handheld"
    major_login.network_type = "Realme RMX3630"
    major_login.screen_width = 1280
    major_login.screen_height = 720
    major_login.screen_dpi = "240"
    major_login.processor_details = "ARM64 FP ASIMD AES VMH | 2865 | 4"
    major_login.memory = 3003
    major_login.gpu_renderer = "Adreno (TM) 640"
    major_login.gpu_version = "OpenGL ES 3.1 v1.46"
    major_login.unique_device_id = "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"
    major_login.client_ip = "223.191.51.89"
    major_login.language = "en"
    major_login.open_id = open_id
    major_login.open_id_type = "4"
    major_login.device_type = "Handheld"
    memory_available = major_login.memory_available
    memory_available.version = 55
    memory_available.hidden_value = 81
    major_login.access_token = access_token
    major_login.platform_sdk_id = 1
    major_login.network_operator_a = "Verizon"
    major_login.network_type_a = "WIFI"
    major_login.client_using_version = "a8f3c2e91d4b7f605e8a1c9d2b3e4f5a"
    major_login.external_storage_total = 36235
    major_login.external_storage_available = 31335
    major_login.internal_storage_total = 2519
    major_login.internal_storage_available = 703
    major_login.game_disk_storage_available = 25010
    major_login.game_disk_storage_total = 26628
    major_login.external_sdcard_avail_storage = 32992
    major_login.external_sdcard_total_storage = 36235
    major_login.login_by = 3
    major_login.library_path = "/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/lib/arm64"
    major_login.reg_avatar = 1
    major_login.library_token = "5b892aaabd688e571f688053118a162b|/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/base.apk"
    major_login.channel_type = 3
    major_login.cpu_type = 2
    major_login.cpu_architecture = "64"
    major_login.client_version_code = "2019118700"
    major_login.graphics_api = "OpenGLES2"
    major_login.supported_astc_bitset = 16383
    major_login.login_open_id_type = 4
    major_login.analytics_detail = b"FwQVTgUPX1UaUllDDwcWCRBpWAUOUgsvA1snWlBaO1kFYg=="
    major_login.loading_time = 13564
    major_login.release_channel = "android_max"
    major_login.extra_info = "KqsHTymw5/5GB23YGniUYN2/q47GATrq7eFeRatf0NkwLKEMQ0PK5BKEk72dPflAxUlEBir6Vtey83XqF593qsl8hwY="
    major_login.android_engine_init_flag = 110009
    major_login.if_push = 1
    major_login.is_vpn = 1
    major_login.origin_platform_type = "4"
    major_login.primary_platform_type = "4"
    string = major_login.SerializeToString()
    # The bundled Pb2/MajoRLoGinrEq_pb2.py is an OLD MajorLogin schema. It has
    # no fields 26 / 104 / 105, but the live server expects them — ff_login.py
    # sends them and authenticates fine, while this bot was rejected. Protobuf
    # permits unknown trailing fields, so append them by hand.
    string += _encode_pb_field(26, region)      # region, e.g. "IND"
    string += _encode_pb_field(104, 77149)      # build code
    string += _encode_pb_field(105, 1)          # flag
    return  await encrypted_proto(string)

def _netloc(url):
    """https://host/path -> host.

    Defined here too: `from xHeaders import *` does NOT import names that
    start with an underscore, so xHeaders._netloc is invisible in this module.
    """
    return re.sub(r"^https?://", "", str(url)).split("/")[0]


def major_login_headers(access_token, region="OTHERS"):
    """Headers for MajorLogin.

    The shared Hr dict is wrong for this call: it declares
    x-www-form-urlencoded and omits Authorization / X-GA-SV / Host, while the
    body is an AES-encrypted binary blob. ff_login.py sends these and is
    accepted; the bot was rejected.
    """
    return {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; CPH2095 Build/RKQ1.211119.001)",
        "Accept-Encoding": "deflate, gzip",
        "X-GA-SV": "1789535859",
        "Authorization": f"Bearer {access_token}",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB55",
        "Content-Type": "application/octet-stream",
        "X-Unity-Version": "2018.4.12f1",
        "Host": _netloc(server_url(region)),
    }


async def MajorLogin(payload, region="OTHERS", access_token=None):
    url = f"{server_url(region)}/MajorLogin"
    headers = major_login_headers(access_token or "", region)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=headers, ssl=ssl_context) as response:
            body = await response.read()
            if response.status == 200:
                return body
            # Surface why, instead of a bare "banned/unregistered".
            detail = ""
            if b"Protection Bypass" in body:
                detail = "Protection Bypass (account flagged by Garena)"
                global BLOCKED_UNTIL
                BLOCKED_UNTIL = time.time() + PROTECTION_BYPASS_COOLDOWN
            else:
                preview = body[:80].decode("utf-8", "replace").replace("\n", " ")
                detail = f"body={preview!r}"
            print(f"[OMNEX] MajorLogin HTTP {response.status} · {detail}")
            return None

async def GetLoginData(base_url, payload, token):
    url = f"{base_url}/GetLoginData"
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    Hr['Authorization']= f"Bearer {token}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=Hr, ssl=ssl_context) as response:
            if response.status == 200: return await response.read()
            return None

class MajorLoginRes:
    """MajorLoginRes decoded by hand.

    The bundled Pb2/MajoRLoGinrEs_pb2.py schema cannot parse the live response:
    the body is a 64-byte header followed by protobuf, so ParseFromString
    raises "Wire format was corrupt". Field numbers below were read from a real
    response captured by ff_login.py.
    """

    __slots__ = ("account_uid", "region", "token", "url", "key", "iv", "timestamp")

    def __init__(self, **kw):
        for name in self.__slots__:
            setattr(self, name, kw.get(name))


def _decode_pb_fields(buf: bytes) -> dict:
    """Minimal protobuf wire-format reader -> {field_number: value}."""
    out = {}
    i, n = 0, len(buf)
    while i < n:
        key = 0
        shift = 0
        while True:
            if i >= n:
                return out
            b0 = buf[i]
            i += 1
            key |= (b0 & 0x7F) << shift
            shift += 7
            if not b0 & 0x80:
                break
        field_no, wire = key >> 3, key & 7
        if field_no == 0:
            break
        try:
            if wire == 0:
                val = 0
                shift = 0
                while True:
                    b0 = buf[i]
                    i += 1
                    val |= (b0 & 0x7F) << shift
                    shift += 7
                    if not b0 & 0x80:
                        break
                out[field_no] = val
            elif wire == 2:
                ln = 0
                shift = 0
                while True:
                    b0 = buf[i]
                    i += 1
                    ln |= (b0 & 0x7F) << shift
                    shift += 7
                    if not b0 & 0x80:
                        break
                out[field_no] = buf[i:i + ln]
                i += ln
            elif wire == 5:
                i += 4
            elif wire == 1:
                i += 8
            else:
                break
        except IndexError:
            break
    return out


# The MajorLogin response body starts with this many bytes of header before
# the protobuf payload begins.
MAJORLOGIN_RES_HEADER = 64


async def DecRypTMajoRLoGin(MajoRLoGinResPonsE):
    body = MajoRLoGinResPonsE or b""
    # Try the documented offset first, then a few others, in case it changes.
    for offset in (MAJORLOGIN_RES_HEADER, 0, 4, 8, 16, 32, 64):
        if offset >= len(body):
            continue
        f = _decode_pb_fields(body[offset:])
        token = f.get(8)
        if isinstance(token, bytes) and token.count(b".") == 2:
            return MajorLoginRes(
                account_uid=str(f.get(1, "")),
                region=(f.get(2) or b"").decode("utf-8", "replace") or None,
                token=token.decode("utf-8", "replace"),
                url=(f.get(10) or b"").decode("utf-8", "replace").rstrip("/"),
                key=f.get(22) or b"",
                iv=f.get(23) or b"",
                timestamp=str(f.get(21, "")),
            )
    raise ValueError(
        f"could not locate MajorLoginRes payload in {len(body)} bytes"
    )

async def DecRypTLoGinDaTa(LoGinDaTa):
    proto = PorTs_pb2.GetLoginData()
    proto.ParseFromString(LoGinDaTa)
    return proto

async def DecodeWhisperMessage(hex_packet):
    packet = bytes.fromhex(hex_packet)
    proto = DEcwHisPErMsG_pb2.DecodeWhisper()
    proto.ParseFromString(packet)
    return proto
    
async def decode_team_packet(hex_packet):
    packet = bytes.fromhex(hex_packet)
    proto = sQ_pb2.recieved_chat()
    proto.ParseFromString(packet)
    return proto
    
async def xAuThSTarTuP(TarGeT, token, timestamp, key, iv):
    uid_hex = hex(TarGeT)[2:]
    uid_length = len(uid_hex)
    encrypted_timestamp = await DecodE_HeX(timestamp)
    encrypted_account_token = token.encode().hex()
    encrypted_packet = await EnC_PacKeT(encrypted_account_token, key, iv)
    encrypted_packet_length = hex(len(encrypted_packet) // 2)[2:]
    if uid_length == 9: headers = '0000000'
    elif uid_length == 8: headers = '00000000'
    elif uid_length == 10: headers = '000000'
    elif uid_length == 7: headers = '000000000'
    else: print('Unexpected length') ; headers = '0000000'
    return f"0115{headers}{uid_hex}{encrypted_timestamp}00000{encrypted_packet_length}{encrypted_packet}"
     
async def cHTypE(H):
    if not H: return 'Squid'
    elif H == 1: return 'CLan'
    elif H == 2: return 'PrivaTe'
    
async def SEndMsG(H , message , Uid , chat_id , key , iv):
    TypE = await cHTypE(H)
    if TypE == 'Squid': msg_packet = await xSEndMsgsQ(message , chat_id , key , iv)
    elif TypE == 'CLan': msg_packet = await xSEndMsg(message , 1 , chat_id , chat_id , key , iv)
    elif TypE == 'PrivaTe': msg_packet = await xSEndMsg(message , 2 , Uid , Uid , key , iv)
    return msg_packet

async def SEndPacKeT(OnLinE , ChaT , TypE , PacKeT):
    if TypE == 'ChaT' and ChaT: whisper_writer.write(PacKeT) ; await whisper_writer.drain()
    elif TypE == 'OnLine': online_writer.write(PacKeT) ; await online_writer.drain()
    else: return 'UnsoPorTed TypE ! >> ErrrroR (:():)' 
           
async def TcPOnLine(ip, port, key, iv, AutHToKen, reconnect_delay=0.5):
    global online_writer , spam_room , whisper_writer , spammer_uid , spam_chat_id , spam_uid , XX , uid , Spy,data2, Chat_Leave
    while True:
        try:
            reader , writer = await asyncio.open_connection(ip, int(port))
            online_writer = writer
            bytes_payload = bytes.fromhex(AutHToKen)
            online_writer.write(bytes_payload)
            await online_writer.drain()
            while True:
                data2 = await reader.read(9999)
                if not data2: break
                
                if data2.hex().startswith('0500') and len(data2.hex()) > 1000:
                    try:
                        print(data2.hex()[10:])
                        packet = await DeCode_PackEt(data2.hex()[10:])
                        print(packet)
                        packet = json.loads(packet)
                        OwNer_UiD , CHaT_CoDe , SQuAD_CoDe = await GeTSQDaTa(packet)

                        JoinCHaT = await AutH_Chat(3 , OwNer_UiD , CHaT_CoDe, key,iv)
                        await SEndPacKeT(whisper_writer , online_writer , 'ChaT' , JoinCHaT)

                        message = f'[B][C]{get_random_color()}\n- WeLComE To Bot ! '
                        P = await SEndMsG(0 , message , OwNer_UiD , OwNer_UiD , key , iv)
                        await SEndPacKeT(whisper_writer , online_writer , 'ChaT' , P)

                    except:
                        if data2.hex().startswith('0500') and len(data2.hex()) > 1000:
                            try:
                                print(data2.hex()[10:])
                                packet = await DeCode_PackEt(data2.hex()[10:])
                                print(packet)
                                packet = json.loads(packet)
                                OwNer_UiD , CHaT_CoDe , SQuAD_CoDe = await GeTSQDaTa(packet)

                                JoinCHaT = await AutH_Chat(3 , OwNer_UiD , CHaT_CoDe, key,iv)
                                await SEndPacKeT(whisper_writer , online_writer , 'ChaT' , JoinCHaT)

                                message = f'[B][C]{get_random_color()}\n- Welcome to Bot !\n\n[00FF00]Dev : @{xMsGFixinG("OMNEXCODEX")}\n[FFFF00]Powered by OMNEX'
                                P = await SEndMsG(0 , message , OwNer_UiD , OwNer_UiD , key , iv)
                                await SEndPacKeT(whisper_writer , online_writer , 'ChaT' , P)
                            except:
                                pass

            online_writer.close() ; await online_writer.wait_closed() ; online_writer = None

        except Exception as e: print(f"- ErroR With {ip}:{port} - {e}") ; online_writer = None
        await asyncio.sleep(reconnect_delay)
                            
async def TcPChaT(ip, port, AutHToKen, key, iv, LoGinDaTaUncRypTinG, ready_event, region , reconnect_delay=0.5):
    print(region, 'TCP CHAT')

    global spam_room , whisper_writer , spammer_uid , spam_chat_id , spam_uid , online_writer , chat_id , XX , uid , Spy,data2, Chat_Leave
    while True:
        try:
            reader , writer = await asyncio.open_connection(ip, int(port))
            whisper_writer = writer
            bytes_payload = bytes.fromhex(AutHToKen)
            whisper_writer.write(bytes_payload)
            await whisper_writer.drain()
            ready_event.set()
            if LoGinDaTaUncRypTinG.Clan_ID:
                clan_id = LoGinDaTaUncRypTinG.Clan_ID
                clan_compiled_data = LoGinDaTaUncRypTinG.Clan_Compiled_Data
                print('\n - TarGeT BoT in CLan ! ')
                print(f' - Clan Uid > {clan_id}')
                print(f' - BoT ConnEcTed WiTh CLan ChaT SuccEssFuLy ! ')
                pK = await AuthClan(clan_id , clan_compiled_data , key , iv)
                if whisper_writer: whisper_writer.write(pK) ; await whisper_writer.drain()
            while True:
                data = await reader.read(9999)
                if not data: break
                
                # Chat reading only - no command processing
                            
            whisper_writer.close() ; await whisper_writer.wait_closed() ; whisper_writer = None
                    
        except Exception as e: print(f"ErroR {ip}:{port} - {e}") ; whisper_writer = None
        await asyncio.sleep(reconnect_delay)

# ---------------------- FLASK ROUTES ----------------------

loop = None

async def perform_invite_5(target_uid: int):
    global key, iv, region, online_writer, BOT_UID
    
    if online_writer is None:
        raise Exception("Bot not connected")
    
    try:
        # Open Squad
        PAc = await OpEnSq(key, iv, region)
        await SEndPacKeT(None, online_writer, 'OnLine', PAc)
        
        # Change Squad to 5-player mode
        C = await cHSq(5, target_uid, key, iv, region)
        await asyncio.sleep(0.3)
        await SEndPacKeT(None, online_writer, 'OnLine', C)
        
        # Send Invite
        V = await SEnd_InV(5, target_uid, key, iv, region)
        await asyncio.sleep(0.3)
        await SEndPacKeT(None, online_writer, 'OnLine', V)
        
        # Exit Squad after delay
        await asyncio.sleep(5)
        E = await ExiT(BOT_UID, key, iv)
        await SEndPacKeT(None, online_writer, 'OnLine', E)
        
        return {"status": "success", "message": f"5-Player invite sent to {target_uid}"}
        
    except Exception as e:
        raise Exception(f"Failed to send 5-player invite: {str(e)}")

async def perform_invite_6(target_uid: int):
    global key, iv, region, online_writer, BOT_UID
    
    if online_writer is None:
        raise Exception("Bot not connected")
    
    try:
        # Open Squad
        PAc = await OpEnSq(key, iv, region)
        await SEndPacKeT(None, online_writer, 'OnLine', PAc)
        
        # Change Squad to 6-player mode
        C = await cHSq(6, target_uid, key, iv, region)
        await asyncio.sleep(0.3)
        await SEndPacKeT(None, online_writer, 'OnLine', C)
        
        # Send Invite
        V = await SEnd_InV(6, target_uid, key, iv, region)
        await asyncio.sleep(0.3)
        await SEndPacKeT(None, online_writer, 'OnLine', V)
        
        # Exit Squad after delay
        await asyncio.sleep(5)
        E = await ExiT(BOT_UID, key, iv)
        await SEndPacKeT(None, online_writer, 'OnLine', E)
        
        return {"status": "success", "message": f"6-Player invite sent to {target_uid}"}
        
    except Exception as e:
        raise Exception(f"Failed to send 6-player invite: {str(e)}")

@app.route('/5')
def invite_5_player():
    global loop
    target_uid_str = request.args.get('uid')

    if not target_uid_str:
        return jsonify({"status": "error", "message": "Missing uid"}), 400

    try:
        target_uid = int(target_uid_str)
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid UID format"}), 400

    asyncio.run_coroutine_threadsafe(
        perform_invite_5(target_uid), loop
    )

    return jsonify({
        "status": "ok",
        "engine": "OMNEX",
        "target_uid": target_uid,
        "message": "5-Player Invite Sent!"
    })

@app.route('/6')
def invite_6_player():
    global loop
    target_uid_str = request.args.get('uid')

    if not target_uid_str:
        return jsonify({"status": "error", "message": "Missing uid"}), 400

    try:
        target_uid = int(target_uid_str)
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid UID format"}), 400

    asyncio.run_coroutine_threadsafe(
        perform_invite_6(target_uid), loop
    )

    return jsonify({
        "status": "ok",
        "engine": "OMNEX",
        "target_uid": target_uid,
        "message": "6-Player Invite Sent!"
    })

@app.route('/')
def health_check():
    return jsonify({
        "status": "ok",
        "engine": "OMNEX",
        "version": "v1.1",
        "client": "OB55",
        "client_version": "1.132.9",
        "bot": "online" if online_writer else "connecting",
        "service": CREDIT_INFO.get("brand", "OMNEX FF GROUP BOT"),
        "credit": CREDIT_INFO.get("credit_line", "Powered by OMNEX"),
        "timestamp": str(datetime.now())
    })

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ---------------------- MAIN BOT SYSTEM ----------------------

def _split_host_port(value):
    """Split 'host:port' safely. See TcP-FrEinD.py for why plain
    split(':') raises "too many values to unpack" on IPv6 / proxy hosts."""
    value = (value or "").strip()
    if not value:
        return "", ""
    host, sep, port = value.rpartition(":")
    if not sep:
        return value, ""
    return host.strip(), port.strip()


async def MaiiiinE():
    global loop, key, iv, region, BOT_UID, TarGeT, acc_name, ACTIVE_ACC_ID

    candidates = get_account_candidates()
    if not candidates:
        print("[OMNEX] No accounts in acc.txt — add with /add BD UID PASSWORD")
        print("[OMNEX] Format: id=|uid=|password=|region=")
        await asyncio.sleep(30)
        return None

    global OAUTH_RATE_LIMITED, OAUTH_RETRY_AFTER
    OAUTH_RATE_LIMITED = False
    OAUTH_RETRY_AFTER = 0

    acc = None
    MajoRLoGinauTh = None

    for attempt, candidate in enumerate(candidates):
        Uid, Pw = candidate["uid"], candidate["password"]
        cand_region = candidate.get("region", "OTHERS")
        label = f"id={candidate['id']} ({candidate['region']})"
        print(f"[OMNEX] Trying account {label}"
              + (f"  attempt {attempt + 1}/{len(candidates)}" if attempt else ""))
        print(f"[OMNEX] Region group {normalize_region(cand_region)} · client {client_host(cand_region)}")

        result = await GeNeRaTeAccEss(Uid, Pw)
        if not isinstance(result, (tuple, list)) or len(result) != 2:
            print(f"[OMNEX] OAuth bad return type: {type(result).__name__} {result!r}")
            continue
        o_id, a_tok = result
        if not (o_id and a_tok):
            print(f"[OMNEX] OAuth failed for {label} — trying next")
            if OAUTH_RATE_LIMITED:
                # Throttled: hammering the remaining accounts makes it worse.
                break
            continue

        # OAuth is not the only gate. An account can authenticate and still be
        # rejected by MajorLogin, so the whole sequence must fall through.
        try:
            PyL = await EncRypTMajoRLoGin(o_id, a_tok, cand_region)
            res = await MajorLogin(PyL, cand_region, a_tok)
            if not res:
                print(f"[OMNEX] MajorLogin rejected {label} — trying next")
                _set_last_error(f"id={candidate['id']} MajorLogin rejected")
                continue
            # Decode inside the try: a bad payload must not abort the whole
            # loop and skip the remaining accounts.
            decoded = await DecRypTMajoRLoGin(res)
        except Exception as e:
            print(f"[OMNEX] Login error for {label}: {e} — trying next")
            _set_last_error(f"id={candidate['id']} {e}")
            continue

        acc = candidate
        MajoRLoGinauTh = decoded
        break

    if acc is None or MajoRLoGinauTh is None:
        print("[OMNEX] No account could complete login")
        return None

    _set_last_error("none — login OK")
    ACTIVE_ACC_ID = str(acc["id"])
    Uid, Pw = acc["uid"], acc["password"]
    region = acc.get("region", "OTHERS")
    print(f"[OMNEX] Logged in via account id={acc['id']} region={acc['region']}")

    UrL = MajoRLoGinauTh.url
    print(UrL)
    region = MajoRLoGinauTh.region

    ToKen = MajoRLoGinauTh.token
    TarGeT = MajoRLoGinauTh.account_uid
    BOT_UID = int(TarGeT) if TarGeT else None
    key = MajoRLoGinauTh.key
    iv = MajoRLoGinauTh.iv
    timestamp = MajoRLoGinauTh.timestamp

    loop = asyncio.get_running_loop()

    LoGinDaTa = await GetLoginData(UrL, PyL, ToKen)
    if not LoGinDaTa:
        print("ErroR - GeTinG PorTs From LoGin DaTa !")
        return None

    LoGinDaTaUncRypTinG = await DecRypTLoGinDaTa(LoGinDaTa)
    OnLinePorTs = LoGinDaTaUncRypTinG.Online_IP_Port
    ChaTPorTs = LoGinDaTaUncRypTinG.AccountIP_Port

    OnLineiP, OnLineporT = _split_host_port(OnLinePorTs)
    ChaTiP, ChaTporT = _split_host_port(ChaTPorTs)

    if not (OnLineiP and OnLineporT) or not (ChaTiP and ChaTporT):
        print(f"[OMNEX] Bad ports: online={OnLinePorTs!r} chat={ChaTPorTs!r}")
        return None

    acc_name = LoGinDaTaUncRypTinG.AccountName
    print(ToKen)

    equie_emote(ToKen, UrL)

    AutHToKen = await xAuThSTarTuP(int(TarGeT), ToKen, int(timestamp), key, iv)
    ready_event = asyncio.Event()

    task1 = asyncio.create_task(
        TcPChaT(ChaTiP, ChaTporT, AutHToKen, key, iv,
                LoGinDaTaUncRypTinG, ready_event, region)
    )

    await ready_event.wait()
    await asyncio.sleep(1)

    task2 = asyncio.create_task(
        TcPOnLine(OnLineiP, OnLineporT, key, iv, AutHToKen)
    )

    os.system('clear')
    print(render('OMNEX', colors=['white', 'cyan'], align='center'))
    print(f"\n  {CREDIT_INFO.get('credit_line', 'Powered by OMNEX')}")
    print(f"  Client : OB55  |  v1.132.9")
    print(f"  Target : {TarGeT}  |  Name : {acc_name}")
    print(f"  Status : ONLINE")
    print(f"  API    : /5?uid=UID  |  /6?uid=UID")
    print(f"  Channel: {CREDIT_INFO.get('main_channel', '@OMNEXCODEX')}\n")

    await asyncio.gather(task1, task2)

async def StarTinG():
    delay = 5
    while True:
        # Respect the cooldown after a Protection Bypass response, otherwise
        # repeated attempts keep the accounts flagged.
        while time.time() < BLOCKED_UNTIL:
            left = int(BLOCKED_UNTIL - time.time())
            mins = left // 60
            print(f"[OMNEX] Accounts flagged by Garena - pausing logins for ~{mins}m")
            _set_last_error(f"Protection Bypass cooldown, ~{mins}m left")
            await asyncio.sleep(min(300, max(5, left)))
        waited = 0
        try:
            await asyncio.wait_for(MaiiiinE(), timeout=7 * 60 * 60)
        except asyncio.TimeoutError:
            print("[OMNEX] Token expired — restarting")
        except Exception as e:
            import traceback
            print(f"ErroR TcP - {e} => ResTarTinG ...")
            _set_last_error(e)
            traceback.print_exc()

        if OAUTH_RATE_LIMITED:
            waited = max(delay, OAUTH_RETRY_AFTER or 60)
            print(f"[OMNEX] Garena rate limit (429) — waiting {waited:.0f}s before retrying")
        else:
            waited = delay
        delay = min(delay * 2, 300)   # 5s, 10s, 20s … capped at 300s
        await asyncio.sleep(waited)


async def main():
    """Main function to run everything together"""
    # Start Flask in a thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Start Telegram bot polling as a task
    telegram_task = asyncio.create_task(telegram_polling())
    
    # Start the bot system
    bot_task = asyncio.create_task(StarTinG())
    
    # Wait for both tasks
    await asyncio.gather(telegram_task, bot_task)

if __name__ == '__main__':
    print(f"[OMNEX] {CREDIT_INFO.get('brand', 'OMNEX FF GROUP BOT')}")
    print(f"[OMNEX] {CREDIT_INFO.get('credit_line', 'Powered by OMNEX')}")
    print("[OMNEX] Starting Flask API + Telegram + FF Engine...")
    asyncio.run(main())