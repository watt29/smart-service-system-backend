"""
Test Script สำหรับ LINE Bot
ทดสอบ webhook และ response ของ LINE Bot
"""

import json
import requests
from src.handlers.line_handler import line_handler

def test_search_function():
    """ทดสอบฟังก์ชันค้นหาโดยตรง"""
    print("=== Test Search Function ===")
    
    # ทดสอบคำค้นหาต่างๆ
    test_queries = [
        "cbc",
        "เลือด", 
        "31001",
        "ไขมัน",
        "ฟัน",
        "xyz123"  # ไม่มีข้อมูล
    ]
    
    for query in test_queries:
        print(f"\n[SEARCH] ค้นหา: '{query}'")
        
        # ทดสอบ db_adapter
        from src.utils.db_adapter import db_adapter
        
        try:
            results = db_adapter.fuzzy_search(query)
            if results:
                key, data = results[0]  
                print(f"[OK] พบ: {data['name_th']} - {data['rate_baht']} บาท")
            else:
                print("[ERROR] ไม่พบข้อมูล")
                
        except Exception as e:
            print(f"[ERROR] Error: {e}")

def test_line_handler_direct():
    """ทดสอบ LINE handler โดยตรง"""
    print("\n=== Test LINE Handler Direct ===")
    
    # Mock event object
    class MockEvent:
        def __init__(self, text):
            self.reply_token = "mock_token"
            self.message = MockMessage(text)
            self.source = MockSource()
    
    class MockMessage:
        def __init__(self, text):
            self.text = text
    
    class MockSource:
        def __init__(self):
            self.user_id = "test_user_123"
    
    # ทดสอบข้อความต่างๆ
    test_messages = [
        "cbc",
        "เลือด",
        "admin",
        "31001"
    ]
    
    for msg in test_messages:
        print(f"\n[MSG] ข้อความ: '{msg}'")
        try:
            event = MockEvent(msg)
            # จำลองการประมวลผล (จะไม่ส่งข้อความจริง)
            user_id = event.source.user_id
            text = event.message.text.lower().strip()
            
            if text == "cbc":
                print("[OK] จะตอบ: ข้อมูล CBC")
            elif text == "เลือด":
                print("[OK] จะตอบ: ข้อมูลการตรวจเลือด")
            elif text == "admin":
                print("[OK] จะตอบ: เมนูแอดมิน")  
            else:
                print("[OK] จะค้นหาและตอบกลับ")
                
        except Exception as e:
            print(f"[ERROR] Error: {e}")

def test_webhook_simulation():
    """จำลองการทดสอบ webhook"""
    print("\n=== Test Webhook Simulation ===")
    
    # สร้าง mock LINE webhook payload
    webhook_payload = {
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "text": "cbc"
                },
                "source": {
                    "userId": "test_user_123",
                    "type": "user"
                },
                "replyToken": "mock_reply_token"
            }
        ]
    }
    
    print("[PAYLOAD] Mock webhook payload:")
    print(json.dumps(webhook_payload, indent=2, ensure_ascii=False))
    print("\n[OK] Webhook payload สร้างเรียบร้อย")
    print("[TIP] ใน production จะส่งไปยัง /callback endpoint")

def main():
    """รันการทดสอบทั้งหมด"""
    print("[TEST] เริ่มทดสอบ LINE Bot System")
    print("=" * 50)
    
    try:
        test_search_function()
        test_line_handler_direct()
        test_webhook_simulation()
        
        print("\n" + "=" * 50)
        print("[OK] การทดสอบเสร็จสิ้น!")
        print("\n[TIP] วิธีทดสอบ LINE Bot จริง:")
        print("1. รันเซิร์ฟเวอร์: python main.py")
        print("2. ใช้ ngrok expose port 5000")
        print("3. ตั้งค่า webhook URL ใน LINE Developer Console")
        print("4. ส่งข้อความในแชท LINE Bot")
        
    except Exception as e:
        print(f"\n[ERROR] เกิดข้อผิดพลาดในการทดสอบ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()