from fastapi import FastAPI, Request, HTTPException
import urllib.parse
import os

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# --- LINE Bot Configuration ---
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = FastAPI(
    title="Smart Service System Backend",
    description="API for LINE Bot to provide medical reimbursement information for Thai civil servants.",
    version="1.0.0"
)

# --- ฐานความรู้ภายใน (Knowledge Base) ---
# ในอนาคตจะดึงมาจาก Supabase
knowledge_base = [
    {
        "labCode": "31001",
        "nameTh": "การตรวจน้ำปัสสาวะทั่วไป (Urinalysis)",
        "nameEn": "Urinalysis (Physical + Chemical + Microscopic) PANEL.UA",
        "rate": 60,
        "reimbursable": true,
        "rights": "ทุกสิทธิ (กรมบัญชีกลาง / ประกันสังคม / รัฐวิสาหกิจ)",
        "cgdCode": "MED0301010",
        "cpt": "81000",
        "icd10": "R82.9 (ความผิดปกติอื่นๆ ที่พบในการตรวจปัสสาวะ)",
        "notes": "รวมค่าตรวจ albumin, glucose หากเบิกรายการนี้ จะไม่สามารถเบิกค่าตรวจ albumin และ glucose ได้อีก ตามหนังสือกรมบัญชีกลาง ที่ กค 0416.2/ว 393 ลว. 10 ต.ค.60 มีผลใช้บังคับสำหรับการรักษา ตั้งแต่วันที่ 1 ม.ค.61 เป็นต้นไป"
    },
    {
        "labCode": "30101",
        "nameTh": "การตรวจความสมบูรณ์ของเม็ดเลือด (CBC)",
        "nameEn": "Complete Blood Count (CBC)",
        "rate": 100,
        "reimbursable": true,
        "rights": "ทุกสิทธิ (กรมบัญชีกลาง / ประกันสังคม / รัฐวิสาหกิจ)",
        "cgdCode": "MED0301020",
        "cpt": "85025",
        "icd10": "D69.6 (ภาวะเลือดออกผิดปกติอื่นๆ)",
        "notes": "ไม่ต้องอดอาหาร"
    },
    {
        "labCode": "32401",
        "nameTh": "การตรวจระดับน้ำตาลสะสมในเลือด (HbA1c)",
        "nameEn": "Glycated Hemoglobin (HbA1c)",
        "rate": 180,
        "reimbursable": true,
        "rights": "ทุกสิทธิ (กรมบัญชีกลาง / ประกันสังคม / รัฐวิสาหกิจ)",
        "cgdCode": "MED0302040",
        "cpt": "83036",
        "icd10": "E11.9 (เบาหวานชนิดที่ 2)",
        "notes": "ตรวจได้ 2 ครั้ง/ปี"
    },
    {
        "labCode": "30201",
        "nameTh": "การตรวจระดับน้ำตาลในเลือด (Glucose)",
        "nameEn": "Blood Glucose",
        "rate": 50,
        "reimbursable": true,
        "rights": "ทุกสิทธิ",
        "cgdCode": "MED0302010",
        "cpt": "82947",
        "icd10": "R73.0 (ระดับน้ำตาลในเลือดสูง)",
        "notes": "ควรงดอาหารและเครื่องดื่ม 8-12 ชั่วโมงก่อนตรวจ (ยกเว้นน้ำเปล่า)"
    },
    {
        "labCode": "30301",
        "nameTh": "การตรวจไขมันคอเลสเตอรอลรวม (Cholesterol)",
        "nameEn": "Total Cholesterol",
        "rate": 60,
        "reimbursable": true,
        "rights": "ทุกสิทธิ",
        "cgdCode": "MED0303010",
        "cpt": "82465",
        "icd10": "E78.0 (ภาวะไขมันในเลือดสูง)",
        "notes": "ควรงดอาหารและเครื่องดื่ม 9-12 ชั่วโมงก่อนตรวจ (ยกเว้นน้ำเปล่า)"
    },
    {
        "labCode": "30302",
        "nameTh": "การตรวจไขมันไตรกลีเซอไรด์ (Triglyceride)",
        "nameEn": "Triglyceride",
        "rate": 80,
        "reimbursable": true,
        "rights": "ทุกสิทธิ",
        "cgdCode": "MED0303020",
        "cpt": "84478",
        "icd10": "E78.1 (ภาวะไตรกลีเซอไรด์สูง)",
        "notes": "ควรงดอาหารและเครื่องดื่ม 9-12 ชั่วโมงก่อนตรวจ (ยกเว้นน้ำเปล่า)"
    },
    {
        "labCode": "30303",
        "nameTh": "การตรวจไขมัน HDL (HDL-C)",
        "nameEn": "HDL Cholesterol",
        "rate": 70,
        "reimbursable": true,
        "rights": "ทุกสิทธิ",
        "cgdCode": "MED0303030",
        "cpt": "80061",
        "icd10": "E78.6 (ภาวะไขมันในเลือดผิดปกติอื่นๆ)",
        "notes": "ไม่ต้องอดอาหาร"
    },
    {
        "labCode": "30304",
        "nameTh": "การตรวจไขมัน LDL (LDL-C)",
        "nameEn": "LDL Cholesterol",
        "rate": 70,
        "reimbursable": true,
        "rights": "ทุกสิทธิ",
        "cgdCode": "MED0303040",
        "cpt": "80061",
        "icd10": "E78.2 (ภาวะไขมัน LDL สูง)",
        "notes": "ไม่ต้องอดอาหาร"
    },
    {
        "labCode": "30401",
        "nameTh": "การตรวจการทำงานของตับ (SGOT/AST)",
        "nameEn": "SGOT/AST",
        "rate": 50,
        "reimbursable": true,
        "rights": "ทุกสิทธิ",
        "cgdCode": "MED0304010",
        "cpt": "84450",
        "icd10": "R74.0 (ระดับเอนไซม์ตับผิดปกติ)",
        "notes": "ไม่ต้องอดอาหาร"
    },
    {
        "labCode": "30402",
        "nameTh": "การตรวจการทำงานของตับ (SGPT/ALT)",
        "nameEn": "SGPT/ALT",
        "rate": 50,
        "reimbursable": true,
        "rights": "ทุกสิทธิ",
        "cgdCode": "MED0304020",
        "cpt": "84460",
        "icd10": "R74.0 (ระดับเอนไซม์ตับผิดปกติ)",
        "notes": "ไม่ต้องอดอาหาร"
    }
]

def generate_cgd_link(query: str) -> str:
    """สร้างลิงก์ค้นหาไปยังเว็บไซต์กรมบัญชีกลาง"""
    encoded_query = urllib.parse.quote(query)
    return f"https://mbdb.cgd.go.th/wel/searchmed.jsp?method=search&service_name={encoded_query}"

def process_query(query: str) -> str:
    """ประมวลผลคำถามและสร้างคำตอบ"""
    lower_case_query = query.lower()
    found_item = None

    # Fuzzy search logic
    for item in knowledge_base:
        if (lower_case_query in item["labCode"].lower() or
            lower_case_query in item["nameTh"].lower() or
            lower_case_query in item["nameEn"].lower() or
            lower_case_query in item["cpt"].lower() or
            lower_case_query in item["icd10"].lower() or
            lower_case_query in item["cgdCode"].lower()):
            found_item = item
            break

    cgd_link = generate_cgd_link(query)

    if found_item:
        response_text = (
            f"✨ สวัสดีครับ! 😊 สำหรับรายการ **\"{found_item['nameTh']} ({found_item['nameEn']})\"** มีรายละเอียดดังนี้ครับ:\n\n"
            f"💵 **อัตราค่าบริการ:** {found_item['rate']:.2f} บาท\n"
            f"✅ **สิทธิการเบิก:** เบิกได้ตามสิทธิ **{found_item['rights']}** เลยครับ!\n"
        )
        if found_item.get("notes"):
            response_text += f"📝 **ข้อควรรู้:** {found_item['notes']}\n"

        response_text += (
            f"\n💡 **รหัสมาตรฐานที่เกี่ยวข้อง:**\n"
            f"*   CPT: `{found_item['cpt']}`\n"
            f"*   ICD-10: `{found_item['icd10']}`\n"
            f"*   รหัสกรมบัญชีกลาง: `{found_item['cgdCode']}`\n\n"
            f"🔗 **ดูข้อมูลทางการเพิ่มเติม:**\n"
            f"[คลิกที่นี่เพื่อดูใน mbdb.cgd.go.th]({cgd_link})\n\n"
            f"มีคำถามอื่นอีกไหมครับ? ยินดีช่วยเหลือเสมอครับ! 😊"
        )
    else:
        response_text = (
            f"😔 ขออภัยครับ! ตอนนี้ **\"{query}\"** ยังไม่มีข้อมูลในระบบฐานความรู้ของผมนะครับ ฐานข้อมูลของเรากำลังอัปเดตอยู่เรื่อยๆ ครับ!\n\n"
            f"แต่ไม่ต้องห่วงนะครับ! คุณสามารถตรวจสอบข้อมูลอย่างเป็นทางการได้ที่เว็บไซต์กรมบัญชีกลางโดยตรงเลยครับ 👇\n"
            f"[คลิกเพื่อค้นหา \"{query}\" ใน mbdb.cgd.go.th]({cgd_link})\n\n"
            f"หวังว่าจะเป็นประโยชน์นะครับ! 🙏"
        )
    return response_text

# --- LINE Webhook Endpoint ---
@app.post("/webhook")
async def line_webhook(request: Request):
    """
    Endpoint สำหรับรับ Webhook จาก LINE Messaging API
    """
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = await request.body()
    body_str = body.decode('utf-8')

    # handle webhook body
    try:
        handler.handle(body_str, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature. Please check your channel access token/channel secret.")
    
    return "OK" # LINE ต้องการการตอบกลับเป็น "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_query = event.message.text
    print(f"Received message from LINE: {user_query}") # สำหรับ debug
    
    # ประมวลผลคำถาม
    response_message = process_query(user_query)
    
    # ส่งข้อความตอบกลับไปยัง LINE
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response_message)
    )
    print(f"Responding to LINE with: \n{response_message}") # สำหรับ debug


@app.get("/")
async def root():
    return {"message": "Smart Service System Backend is running!"}

# หากต้องการรันด้วย uvicorn โดยตรง:
# uvicorn main:app --reload --port 8000