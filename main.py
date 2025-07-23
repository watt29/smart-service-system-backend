import urllib.parse
import os
import sqlite3
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

# URL ฐานข้อมูลกรมบัญชีกลาง
CGD_BASE_URL = "https://mbdb.cgd.go.th/wel/searchmed.jsp"

# ชื่อไฟล์ฐานข้อมูล SQLite
DB_FILE = 'knowledge_base.db'

def init_db():
    """เริ่มต้นฐานข้อมูลและสร้างตารางหากยังไม่มี"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            lab_code TEXT PRIMARY KEY,
            name_th TEXT,
            name_en TEXT,
            rate_baht REAL,
            reimbursable INTEGER,
            rights TEXT,
            cgd_code TEXT,
            cpt_code TEXT,
            icd10_code TEXT,
            icd10_desc TEXT,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()

def populate_initial_data():
    """ใส่ข้อมูลเริ่มต้นลงในฐานข้อมูลหากยังไม่มีข้อมูล"""
    initial_data = [
        {
            "lab_code": "31001",
            "name_th": "การตรวจน้ำปัสสาวะทั่วไป",
            "name_en": "Urinalysis",
            "rate_baht": 80.00,
            "reimbursable": True,
            "rights": "ทุกสิทธิ",
            "cgd_code": "MED0301010",
            "cpt_code": "81000",
            "icd10_code": "R82.9",
            "icd10_desc": "ความผิดปกติอื่นๆ ที่พบในการตรวจปัสสาวะ",
            "notes": "ไม่ต้องอดอาหาร"
        },
        {
            "lab_code": "30101",
            "name_th": "เลือดข้นเลือดจาง",
            "name_en": "CBC",
            "rate_baht": 100.00,
            "reimbursable": True,
            "rights": "ทุกสิทธิ",
            "cgd_code": "MED0301020",
            "cpt_code": "85025",
            "icd10_code": "D69.6",
            "icd10_desc": "ภาวะเลือดออกผิดปกติอื่นๆ",
            "notes": "อดอาหาร 8 ชม."
        },
        {
            "lab_code": "32401",
            "name_th": "HbA1c",
            "name_en": "HbA1c",
            "rate_baht": 180.00,
            "reimbursable": True,
            "rights": "ทุกสิทธิ",
            "cgd_code": "MED0302040",
            "cpt_code": "83036",
            "icd10_code": "E11.9",
            "icd10_desc": "เบาหวานชนิดที่ 2",
            "notes": "ตรวจได้ 2 ครั้ง/ปี"
        }
    ]

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM items")
    if cursor.fetchone()[0] == 0: # ถ้าตารางว่างเปล่า
        for item in initial_data:
            cursor.execute("""
                INSERT INTO items (lab_code, name_th, name_en, rate_baht, reimbursable, rights, cgd_code, cpt_code, icd10_code, icd10_desc, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item['lab_code'], item['name_th'], item['name_en'], item['rate_baht'],
                1 if item['reimbursable'] else 0, item['rights'], item['cgd_code'],
                item['cpt_code'], item['icd10_code'], item['icd10_desc'], item['notes']
            ))
        conn.commit()
    conn.close()

def generate_cgd_search_link(query: str) -> str:
    """สร้างลิงก์ค้นหาอัตโนมัติไปยังเว็บไซต์กรมบัญชีกลาง"""
    encoded_query = urllib.parse.quote(query)
    return f"{CGD_BASE_URL}?method=search&service_name={encoded_query}"

def search_knowledge_base(query: str):
    """ค้นหาข้อมูลในฐานความรู้ภายในจากฐานข้อมูล"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    query_lower = query.lower()
    
    # ค้นหาจากรหัสรายการ, ชื่อไทย, ชื่ออังกฤษ (แบบตรงตัว)
    cursor.execute("""
        SELECT * FROM items WHERE
        LOWER(lab_code) = ? OR
        LOWER(name_th) = ? OR
        LOWER(name_en) = ?
    """, (query_lower, query_lower, query_lower))
    result = cursor.fetchone()
    
    if result:
        # แปลงผลลัพธ์จาก tuple เป็น dict
        columns = [description[0] for description in cursor.description]
        item = dict(zip(columns, result))
        conn.close()
        return item

    # ค้นหาแบบบางส่วน (fuzzy search) ในชื่อไทยและอังกฤษ
    cursor.execute("""
        SELECT * FROM items WHERE
        LOWER(name_th) LIKE ? OR
        LOWER(name_en) LIKE ?
    """, (f'%{query_lower}%', f'%{query_lower}%'))
    result = cursor.fetchone()

    if result:
        columns = [description[0] for description in cursor.description]
        item = dict(zip(columns, result))
        conn.close()
        return item

    conn.close()
    return None

def format_response(item: dict, original_query: str) -> str:
    """จัดรูปแบบคำตอบสำหรับ LINE Bot เมื่อพบข้อมูลในฐานความรู้"""
    response = f"🔍 รายการ: {item['name_th']} ({item['name_en']})\n"
    response += f"💵 อัตรา: {item['rate_baht']:.2f} บาท\n"
    response += f"✅ เบิกได้ตามสิทธิ: {item['rights']}\n"
    if item.get("notes"):
        response += f"📝 หมายเหตุ: {item['notes']}\n"
    
    response += f"🔗 ดูข้อมูลทางการ:\n"
    response += f"[คลิกที่นี่เพื่อดูใน mbdb.cgd.go.th]({generate_cgd_search_link(original_query)})\n"
    
    response += f"ℹ️ รหัสมาตรฐาน:\n"
    response += f"- CPT: {item['cpt_code']}\n"
    response += f"- ICD-10: {item['icd10_code']} ({item['icd10_desc']})\n"
    response += "\n*ข้อมูลนี้มาจากฐานความรู้ภายในของระบบ โปรดตรวจสอบข้อมูลล่าสุดและเป็นทางการจากลิงก์กรมบัญชีกลาง*"
    return response

def handle_user_query(query: str) -> dict:
    """จัดการคำถามจากผู้ใช้และส่งคืนคำตอบและสถานะการพบข้อมูล"""
    found_item = search_knowledge_base(query)
    
    if found_item:
        return {"message": format_response(found_item, query), "found": True}
    else:
        # ไม่พบข้อมูลในฐานความรู้ภายใน
        response = f"❌ ไม่พบข้อมูล \"{query}\" ในระบบฐานความรู้ภายใน\n\n"
        response += f"คุณสามารถค้นหาข้อมูลที่เป็นทางการและล่าสุดได้ที่:\n"
        response += f"[คลิกเพื่อค้นหา \"{query}\" ใน mbdb.cgd.go.th]({generate_cgd_search_link(query)})"
        return {"message": response, "found": False}

# --- LINE Bot Integration ---

app = Flask(__name__)

# ดึงค่า Channel Access Token และ Channel Secret จาก Environment Variables
# เพื่อความปลอดภัย ไม่ควร hardcode ค่าเหล่านี้ในโค้ดจริง
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')

# Admin User ID (LINE User ID ของแอดมิน)
# คุณต้องไปหา LINE User ID ของคุณเองจาก LINE Developers Console หรือจาก Webhook Event
ADMIN_USER_ID = os.environ.get('ADMIN_USER_ID') # ตั้งค่าใน Heroku Config Vars

if not LINE_CHANNEL_ACCESS_TOKEN:
    print("Error: LINE_CHANNEL_ACCESS_TOKEN environment variable not set.")
    print("Please set it before running the application.")
    exit(1)

if not LINE_CHANNEL_SECRET:
    print("Error: LINE_CHANNEL_SECRET environment variable not set.")
    print("Please set it before running the application.")
    exit(1)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# สร้าง Quick Reply Buttons จากข้อมูลในฐานข้อมูล
# ต้องเรียกใช้หลังจาก init_db และ populate_initial_data
def get_quick_reply_items():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name_en FROM items")
    items = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    quick_reply_buttons = []
    for item_name_en in items:
        quick_reply_buttons.append(
            QuickReplyButton(
                action=MessageAction(label=item_name_en, text=item_name_en)
            )
        )
    return QuickReply(items=quick_reply_buttons)

# เรียกใช้เมื่อเริ่มต้นแอป
init_db()
populate_initial_data()
quick_reply = get_quick_reply_items()

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    user_id = event.source.user_id # ดึง User ID ของผู้ส่งข้อความ
    user_message_lower = user_message.lower()

    # --- Admin Commands ---
    if user_id == ADMIN_USER_ID and user_message_lower.startswith("admin add:"):
        try:
            data_str = user_message[len("admin add:"):].strip()
            parts = data_str.split(', ')
            new_item = {}
            for part in parts:
                key, value = part.split('=', 1)
                new_item[key.strip()] = value.strip()
            
            # แปลง reimbursable เป็น boolean
            if 'reimbursable' in new_item:
                new_item['reimbursable'] = (new_item['reimbursable'].lower() == 'true')
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO items (lab_code, name_th, name_en, rate_baht, reimbursable, rights, cgd_code, cpt_code, icd10_code, icd10_desc, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_item.get('lab_code'), new_item.get('name_th'), new_item.get('name_en'), 
                float(new_item.get('rate_baht', 0)), 1 if new_item.get('reimbursable', False) else 0, 
                new_item.get('rights'), new_item.get('cgd_code'), new_item.get('cpt_code'), 
                new_item.get('icd10_code'), new_item.get('icd10_desc'), new_item.get('notes')
            ))
            conn.commit()
            conn.close()
            
            # อัปเดต Quick Reply Buttons หลังจากเพิ่มข้อมูลใหม่
            global quick_reply
            quick_reply = get_quick_reply_items()

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"✅ เพิ่มข้อมูล \"{new_item.get('name_th', new_item.get('lab_code'))}\" สำเร็จแล้ว")
            )
        except Exception as e:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"❌ เกิดข้อผิดพลาดในการเพิ่มข้อมูล: {e}\n\nรูปแบบที่ถูกต้อง: admin add: lab_code=..., name_th=..., ...")
            )
        return

    # --- User Queries ---
    # ตรวจสอบว่าเป็นคำทักทายหรือไม่
    greeting_keywords = ["สวัสดี", "เมนู", "hi", "hello", "help", "ช่วยเหลือ", "start"]
    if any(keyword in user_message_lower for keyword in greeting_keywords):
        reply_message_text = "สวัสดีครับ! ผมคือผู้ช่วยสิทธิการเบิกค่ารักษาพยาบาล คุณต้องการค้นหาข้อมูลอะไรครับ?\n\n" \
                             "คุณสามารถพิมพ์รหัสรายการ, ชื่อบริการ (เช่น HbA1c, CBC, 31001) หรือเลือกจากปุ่มด้านล่างได้เลยครับ"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_message_text, quick_reply=quick_reply)
        )
        return

    # ถ้าไม่ใช่คำทักทาย ให้ประมวลผลคำถามปกติ
    query_result = handle_user_query(user_message)
    reply_message_text = query_result["message"]
    found_in_kb = query_result["found"]
    
    if not found_in_kb:
        # ถ้าไม่พบข้อมูลในฐานความรู้ ให้ส่ง Quick Reply ด้วย
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_message_text, quick_reply=quick_reply)
        )
    else:
        # ถ้าพบข้อมูลในฐานความรู้ ให้ส่งข้อความปกติ
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_message_text)
        )

# สำหรับรัน Flask app
if __name__ == "__main__":
    # ใช้ os.getenv เพื่อดึง PORT จาก environment variable หรือใช้ 5000 เป็นค่าเริ่มต้น
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)