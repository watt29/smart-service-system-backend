import urllib.parse
import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# ฐานความรู้ภายใน (Internal Knowledge Base) - ข้อมูลที่ได้รับการยืนยันแล้วเท่านั้น
KNOWLEDGE_BASE = [
    {
        "lab_code": "31001",
        "name_th": "การตรวจน้ำปัสสาวะทั่วไป",
        "name_en": "Urinalysis",
        "rate_baht": 80.00,
        "reimbursable": True,
        "rights": ["ทุกสิทธิ"],
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
        "rights": ["ทุกสิทธิ"],
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
        "rights": ["ทุกสิทธิ"],
        "cgd_code": "MED0302040",
        "cpt_code": "83036",
        "icd10_code": "E11.9",
        "icd10_desc": "เบาหวานชนิดที่ 2",
        "notes": "ตรวจได้ 2 ครั้ง/ปี"
    }
]

# URL ฐานข้อมูลกรมบัญชีกลาง
CGD_BASE_URL = "https://mbdb.cgd.go.th/wel/searchmed.jsp"

def generate_cgd_search_link(query: str) -> str:
    """สร้างลิงก์ค้นหาอัตโนมัติไปยังเว็บไซต์กรมบัญชีกลาง"""
    encoded_query = urllib.parse.quote(query)
    return f"{CGD_BASE_URL}?method=search&service_name={encoded_query}"

def search_knowledge_base(query: str):
    """ค้นหาข้อมูลในฐานความรู้ภายใน"""
    query_lower = query.lower()
    for item in KNOWLEDGE_BASE:
        # ค้นหาจากรหัสรายการ, ชื่อไทย, ชื่ออังกฤษ (แบบตรงตัว)
        if query_lower == item["lab_code"].lower() or \
           query_lower == item["name_th"].lower() or \
           query_lower == item["name_en"].lower():
            return item
        # ค้นหาแบบบางส่วน (fuzzy search) ในชื่อไทยและอังกฤษ
        if query_lower in item["name_th"].lower() or \
           query_lower in item["name_en"].lower():
            return item # คืนค่ารายการแรกที่เจอ (สามารถปรับปรุงให้คืนค่าทั้งหมดได้ในอนาคต)
    return None

def format_response(item: dict, original_query: str) -> str:
    """จัดรูปแบบคำตอบสำหรับ LINE Bot เมื่อพบข้อมูลในฐานความรู้"""
    response = f"🔍 รายการ: {item['name_th']} ({item['name_en']})\n"
    response += f"💵 อัตรา: {item['rate_baht']:.2f} บาท\n"
    response += f"✅ เบิกได้ตามสิทธิ: {', '.join(item['rights'])}\n"
    if item.get("notes"):
        response += f"📝 หมายเหตุ: {item['notes']}\n"
    
    response += f"🔗 ดูข้อมูลทางการ:\n"
    response += f"[คลิกที่นี่เพื่อดูใน mbdb.cgd.go.th]({generate_cgd_search_link(original_query)})\n"
    
    response += f"ℹ️ รหัสมาตรฐาน:\n"
    response += f"- CPT: {item['cpt_code']}\n"
    response += f"- ICD-10: {item['icd10_code']} ({item['icd10_desc']})\n"
    response += "\n*ข้อมูลนี้มาจากฐานความรู้ภายในของระบบ โปรดตรวจสอบข้อมูลล่าสุดและเป็นทางการจากลิงก์กรมบัญชีกลาง*"
    return response

def handle_user_query(query: str) -> str:
    """จัดการคำถามจากผู้ใช้และส่งคืนคำตอบ"""
    found_item = search_knowledge_base(query)
    
    if found_item:
        return format_response(found_item, query)
    else:
        # ไม่พบข้อมูลในฐานความรู้ภายใน
        response = f"❌ ไม่พบข้อมูล \"{query}\" ในระบบฐานความรู้ภายใน\n\n"
        response += f"คุณสามารถค้นหาข้อมูลที่เป็นทางการและล่าสุดได้ที่:\n"
        response += f"[คลิกเพื่อค้นหา \"{query}\" ใน mbdb.cgd.go.th]({generate_cgd_search_link(query)})"
        return response

# --- LINE Bot Integration ---

app = Flask(__name__)

# ดึงค่า Channel Access Token และ Channel Secret จาก Environment Variables
# เพื่อความปลอดภัย ไม่ควร hardcode ค่าเหล่านี้ในโค้ดจริง
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')

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
    user_message = event.message.text
    reply_message = handle_user_query(user_message)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )

# สำหรับรัน Flask app
if __name__ == "__main__":
    # ใช้ os.getenv เพื่อดึง PORT จาก environment variable หรือใช้ 5000 เป็นค่าเริ่มต้น
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
