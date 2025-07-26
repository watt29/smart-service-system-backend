"""
🧪 Test Quick Reply System
ทดสอบระบบ Quick Reply ใน local environment
"""

from src.handlers.affiliate_handler import AffiliateLineHandler

def test_quick_reply():
    """ทดสอบการทำงานของ Quick Reply"""
    print("Testing Quick Reply System...")
    
    # สร้าง handler
    handler = AffiliateLineHandler()
    
    # สร้าง dummy event
    class DummyEvent:
        class Source:
            user_id = "test_user"
        class Message:
            def __init__(self, text):
                self.text = text
        source = Source()
        reply_token = "dummy_token"
        
        def __init__(self, text):
            self.message = self.Message(text)
    
    # ทดสอบคำสั่งต่างๆ จาก Rich Menu
    test_commands = [
        "ค้นหาสินค้า",
        "หมวดหมู่", 
        "ขายดี",
        "โปรโมชั่น",
        "สถิติ",
        "ช่วยเหลือ",
        "หน้าหลัก",
        "dashboard"  # Admin command
    ]
    
    print("\n=== Testing Rich Menu Commands ===")
    for cmd in test_commands:
        print(f"\nTesting command: '{cmd}'")
        try:
            event = DummyEvent(cmd)
            handler.handle_message(event)
            print(f"SUCCESS: Command '{cmd}' handled")
        except Exception as e:
            print(f"ERROR: Command '{cmd}' failed - {e}")
    
    # ทดสอบการค้นหาสินค้า
    print("\n=== Testing Product Search ===")
    search_tests = [
        "มือถือ",
        "รหัส PROD001",
        "หมวด อิเล็กทรอนิกส์"
    ]
    
    for search in search_tests:
        print(f"\nTesting search: '{search}'")
        try:
            event = DummyEvent(search)
            handler.handle_message(event)
            print(f"SUCCESS: Search '{search}' handled")
        except Exception as e:
            print(f"ERROR: Search '{search}' failed - {e}")
    
    print("\nQuick Reply test completed!")

if __name__ == "__main__":
    test_quick_reply()