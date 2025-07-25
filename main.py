from flask import Flask, request, abort, render_template, jsonify
import re
import os
import json # Added import for json module
from dotenv import load_dotenv # Import load_dotenv

from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhook import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent
from linebot.v3.webhooks import TextMessageContent
from linebot.v3.messaging import QuickReply, QuickReplyItem, MessageAction

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# --- LINE Bot API Configuration ---
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')

# Initialize LineBotApi and WebhookHandler only if tokens are available
if CHANNEL_ACCESS_TOKEN and CHANNEL_SECRET:
    configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
    line_bot_api = MessagingApi(ApiClient(configuration))
    handler = WebhookHandler(CHANNEL_SECRET)
else:
    print("Warning: LINE_CHANNEL_ACCESS_TOKEN or LINE_CHANNEL_SECRET not found. LINE Bot functionality will be limited.")
    # Create dummy objects to prevent errors if LINE tokens are missing
    class DummyLineBotApi:
        def reply_message(self, *args, **kwargs): pass
    class DummyWebhookHandler:
        def handle(self, *args, **kwargs): pass
        def add(self, *args, **kwargs): return lambda f: f # Return a decorator that does nothing

    line_bot_api = DummyLineBotApi()
    handler = DummyWebhookHandler()

# --- Knowledge Base Management ---
KNOWLEDGE_BASE_FILE = 'knowledge_base.json'
KNOWLEDGE_BASE = {}

def load_knowledge_base():
    global KNOWLEDGE_BASE
    if os.path.exists(KNOWLEDGE_BASE_FILE):
        with open(KNOWLEDGE_BASE_FILE, 'r', encoding='utf-8') as f:
            try:
                KNOWLEDGE_BASE = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: {KNOWLEDGE_BASE_FILE} is empty or corrupted. Initializing with empty knowledge base.")
                KNOWLEDGE_BASE = {}
    else:
        print(f"Info: {KNOWLEDGE_BASE_FILE} not found. Initializing with empty knowledge base.")
        KNOWLEDGE_BASE = {}

def save_knowledge_base():
    with open(KNOWLEDGE_BASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(KNOWLEDGE_BASE, f, ensure_ascii=False, indent=4)

# Load knowledge base on startup
load_knowledge_base()

# --- Admin State Management (Simplified) ---
# In a real system, this would be persistent storage (e.g., database)
# and handle multiple users/sessions.
admin_state = {} # Stores current admin operation for a user_id

# --- Helper Functions ---
def generate_cgd_search_link(query):
    """Generates an automatic search link to mbdb.cgd.go.th."""
    encoded_query = re.sub(r'\\s+', '+', query.strip()) # Replace spaces with '+'
    return f"https://mbdb.cgd.go.th/wel/searchmed.jsp?method=search&service_name={encoded_query}"

def format_search_result(item_data, query):
    """Formats the search result for display for both web and LINE."""
    link = generate_cgd_search_link(query)

    # Common data points
    name_th = item_data['name_th']
    name_en = item_data['name_en']
    rate_baht = item_data['rate_baht']
    rights = ', '.join(item_data['rights'])
    notes = item_data.get('notes', '')
    cpt = item_data['cpt']
    icd10 = item_data['icd10']

    # --- For Web UI (HTML) ---
    web_html = f"""
    <div class="card mb-3">
        <div class="card-body text-start">
            <h5 class="card-title">🔍 รายการ: {name_th} ({name_en})</h5>
            <p class="card-text">
                💵 อัตรา: <strong>{rate_baht:.2f} บาท</strong><br>
                ✅ เบิกได้ตามสิทธิ: {rights}<br>
                {f"📝 หมายเหตุ: {notes}<br>" if notes else ""}
            </p>
            <p class="card-text">
                ℹ️ รหัสมาตรฐาน:<br>
                - CPT: {cpt}<br>
                - ICD-10: {icd10}
            </p>
            <a href="{link}" target="_blank" class="btn btn-sm btn-outline-primary mt-2">
                🔗 ดูข้อมูลทางการใน mbdb.cgd.go.th
            </a>
        </div>
    </div>
    """

    # --- For LINE Bot (Plain Text with Emojis) ---
    line_text = f"""
🔍 รายการ: {name_th} ({name_en})
💵 อัตรา: {rate_baht:.2f} บาท
✅ เบิกได้ตามสิทธิ: {rights}
{f"📝 หมายเหตุ: {notes}\n" if notes else ""}🔗 ดูข้อมูลทางการ:
{link}
ℹ️ รหัสมาตรฐาน:
- CPT: {cpt}
- ICD-10: {icd10}
    """
    # Remove leading/trailing newlines and extra spaces
    line_text = line_text.strip()

    return {"web": web_html, "line": line_text}

def fuzzy_search_knowledge_base(query):
    """Performs a fuzzy search on the knowledge base."""
    query_lower = query.lower()
    found_items = []
    for key, item in KNOWLEDGE_BASE.items():
        if query_lower in key.lower() or \
           query_lower in item['name_th'].lower() or \
           query_lower in item['name_en'].lower() or \
           query_lower in item['cgd_code'].lower() or \
           query_lower in item['cpt'].lower() or \
           query_lower in item['icd10'].lower():
            found_items.append((key, item))
    return found_items

# --- Flask Routes ---
@app.route('/')
def home():
    """Renders the main HTML page."""
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search_api():
    """API endpoint for searching the knowledge base."""
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({"error": "กรุณาระบุคำค้นหา"}), 400

    found_items = fuzzy_search_knowledge_base(query)

    if found_items:
        # For simplicity, return the first match for now
        # In a real scenario, you might return multiple matches or ask for clarification
        key, item_data = found_items[0]
        formatted_result = format_search_result(item_data, query)
        return jsonify({"success": True, "result": formatted_result["web"]})
    else:
        link = generate_cgd_search_link(query)
        not_found_message = (
            f"❌ ไม่พบข้อมูล \\\"{query}\\\" ในระบบฐานความรู้ภายใน\\n\\n"
            f"คุณสามารถค้นหาข้อมูลที่เป็นทางการและล่าสุดได้ที่:\\n"
            f"<a href=\\\"{link}\\\" target=\\\"_blank\\\">คลิกเพื่อค้นหา \\\"{query}\\\" ใน mbdb.cgd.go.th</a>"
        )
        return jsonify({"success": False, "result": not_found_message})

# --- LINE Bot Webhook (Basic structure) ---
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.lower().strip()

    # --- Admin System Entry Point ---
    if text in ["admin", "แอดมิน", "เมนูแอดมิน"]:
        admin_state[user_id] = {"mode": "main_menu"}
        quick_replies = QuickReply(items=[
            QuickReplyItem(action=MessageAction(label="➕ เพิ่มข้อมูล", text="➕ เพิ่มข้อมูล")),
            QuickReplyItem(action=MessageAction(label="✏️ แก้ไขข้อมูล", text="✏️ แก้ไขข้อมูล")),
            QuickReplyItem(action=MessageAction(label="❌ ลบข้อมูล", text="❌ ลบข้อมูล")),
            QuickReplyItem(action=MessageAction(label="📋 ดูทั้งหมด", text="📋 ดูทั้งหมด")),
        ])
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="เลือกเมนูแอดมิน:", quick_reply=quick_replies)]
            )
        )
        return

    # --- Handle Admin Flow (Simplified - actual implementation would be more complex) ---
    if user_id in admin_state:
        current_mode = admin_state[user_id].get("mode")

        if text == "cancel":
            del admin_state[user_id]
            line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text="ยกเลิกการดำเนินการแอดมินแล้ว")]))
            return

        if current_mode == "main_menu":
            if text == "➕ เพิ่มข้อมูล":
                admin_state[user_id] = {"mode": "add_item_start", "data": {}}
                line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text="กรุณาป้อนรหัสรายการ (เช่น CBC, 31001):")]))
                return
            elif text == "✏️ แก้ไขข้อมูล":
                admin_state[user_id] = {"mode": "edit_item_start"}
                line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text="กรุณาป้อนรหัสรายการที่ต้องการแก้ไข:")]))
                return
            elif text == "❌ ลบข้อมูล":
                admin_state[user_id] = {"mode": "delete_item_start"}
                line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text="กรุณาป้อนรหัสรายการที่ต้องการลบ:")]))
                return
            elif text == "📋 ดูทั้งหมด":
                admin_state[user_id] = {"mode": "list_all"}
                if KNOWLEDGE_BASE:
                    all_items = "\n\n".join([f"รหัส: {key}\nชื่อ: {item['name_th']}" for key, item in KNOWLEDGE_BASE.items()])
                    line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=f"รายการทั้งหมด:\n{all_items}")]))
                else:
                    line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text="ยังไม่มีข้อมูลในระบบ")]))
                del admin_state[user_id] # Exit admin mode after listing
                return
            else:
                line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text="คำสั่งไม่ถูกต้อง กรุณาเลือกจากเมนู")]))
                return
        
        # --- Add Item Flow (Simplified) ---
        if current_mode == "add_item_start":
            admin_state[user_id]["data"]["key"] = text.lower()
            admin_state[user_id]["mode"] = "add_item_name_th"
            line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text="ป้อนชื่อรายการภาษาไทย:")]))
            return
        if current_mode == "add_item_name_th":
            admin_state[user_id]["data"]["name_th"] = text
            admin_state[user_id]["mode"] = "add_item_name_en"
            line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text="ป้อนชื่อรายการภาษาอังกฤษ:")]))
            return
        if current_mode == "add_item_name_en":
            admin_state[user_id]["data"]["name_en"] = text
            admin_state[user_id]["mode"] = "add_item_rate"
            line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text="ป้อนอัตราค่าบริการ (ตัวเลข):")]))
            return
        if current_mode == "add_item_rate":
            try:
                admin_state[user_id]["data"]["rate_baht"] = float(text)
                admin_state[user_id]["data"]["claimable"] = True # Default to True for simplicity
                admin_state[user_id]["data"]["rights"] = ["กรมบัญชีกลาง", "ทุกสิทธิ"] # Default
                admin_state[user_id]["data"]["cgd_code"] = "N/A"
                admin_state[user_id]["data"]["cpt"] = "N/A"
                admin_state[user_id]["data"]["icd10"] = "N/A"
                admin_state[user_id]["data"]["notes"] = ""

                item_key = admin_state[user_id]["data"]["key"]
                KNOWLEDGE_BASE[item_key] = admin_state[user_id]["data"]
                save_knowledge_base() # Save after adding
                
                summary = f"เพิ่มข้อมูลสำเร็จ:\nรหัส: {item_key}\nชื่อ: {KNOWLEDGE_BASE[item_key]['name_th']}\nอัตรา: {KNOWLEDGE_BASE[item_key]['rate_baht']}"
                line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=summary)]))
                del admin_state[user_id] # Exit admin mode
                return
            except ValueError:
                line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text="อัตราค่าบริการต้องเป็นตัวเลข กรุณาป้อนใหม่:")]))
                return

        # --- Edit Item Flow (Simplified) ---
        if current_mode == "edit_item_start":
            item_key = text.lower()
            if item_key in KNOWLEDGE_BASE:
                admin_state[user_id] = {"mode": "edit_item_field", "key": item_key}
                current_data = KNOWLEDGE_BASE[item_key]
                summary = f"ข้อมูลปัจจุบันของ {item_key}:\n"
                for k, v in current_data.items():
                    summary += f"- {k}: {v}\n"
                line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=f"{summary}\nกรุณาป้อนชื่อฟิลด์ที่ต้องการแก้ไข (เช่น name_th, rate_baht):")]))
                return
            else:
                line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text="ไม่พบรหัสรายการนี้ กรุณาป้อนใหม่:")]))
                return
        if current_mode == "edit_item_field":
            field_name = text.lower()
            item_key = admin_state[user_id]["key"]
            if field_name in KNOWLEDGE_BASE[item_key]:
                admin_state[user_id]["field"] = field_name
                admin_state[user_id]["mode"] = "edit_item_value"
                line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=f"ป้อนค่าใหม่สำหรับ {field_name}:")]))
                return
            else:
                line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text="ไม่พบฟิลด์นี้ กรุณาป้อนชื่อฟิลด์ที่ถูกต้อง:")]))
                return
        if current_mode == "edit_item_value":
            item_key = admin_state[user_id]["key"]
            field_name = admin_state[user_id]["field"]
            new_value = text
            
            # Type conversion for rate_baht
            if field_name == "rate_baht":
                try:
                    new_value = float(new_value)
                except ValueError:
                    line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text="ค่าอัตราต้องเป็นตัวเลข กรุณาป้อนใหม่:")]))
                    return
            elif field_name == "claimable":
                new_value = new_value.lower() == "true"
            elif field_name == "rights":
                new_value = [s.strip() for s in new_value.split(',')] 

            KNOWLEDGE_BASE[item_key][field_name] = new_value
            save_knowledge_base() # Save after editing
            summary = f"แก้ไขข้อมูลสำเร็จ:\nรหัส: {item_key}\nฟิลด์: {field_name}\nค่าใหม่: {new_value}"
            line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=summary)]))
            del admin_state[user_id] # Exit admin mode
            return

        # --- Delete Item Flow (Simplified) ---
        if current_mode == "delete_item_start":
            item_key = text.lower()
            if item_key in KNOWLEDGE_BASE:
                admin_state[user_id] = {"mode": "delete_item_confirm", "key": item_key}
                line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=f"คุณต้องการลบรายการ '{KNOWLEDGE_BASE[item_key]['name_th']}' ใช่หรือไม่? (confirm/cancel)")]))
                return
            else:
                line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text="ไม่พบรหัสรายการนี้ กรุณาป้อนใหม่:")]))
                return
        if current_mode == "delete_item_confirm":
            if text == "confirm":
                item_key = admin_state[user_id]["key"]
                del KNOWLEDGE_BASE[item_key]
                save_knowledge_base() # Save after deleting
                line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=f"ลบรายการ '{item_key}' สำเร็จแล้ว")]))
                return
            else:
                line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text="ยกเลิกการลบรายการ")]))
                return

    # --- General Search (if not in admin mode) ---
    found_items = fuzzy_search_knowledge_base(text)
    if found_items:
        # For simplicity, reply with the first match
        key, item_data = found_items[0]
        formatted_result = format_search_result(item_data, text)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=formatted_result["line"])]
            )
        )
    else:
        link = generate_cgd_search_link(text)
        not_found_message = (
            f"❌ ไม่พบข้อมูล \\\"{text}\\\" ในระบบฐานความรู้ภายใน\\n\\n"
            f"คุณสามารถค้นหาข้อมูลที่เป็นทางการและล่าสุดได้ที่:\\n"
            f"[คลิกเพื่อค้นหา \\\"{text}\\\" ใน mbdb.cgd.go.th]({link})"
        )
        line_bot_api.reply_message(
            event.reply_token,
            ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=not_found_message)])
        )

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)