"""
🧪 Test LINE Bot Integration
ทดสอบการเชื่อมต่อ Rich Menu และ Quick Reply กับ LINE Bot
"""

from src.handlers.affiliate_handler import AffiliateLineHandler
from src.utils.rich_menu_manager import rich_menu_manager

def test_line_integration():
    """ทดสอบการเชื่อมต่อ LINE Bot"""
    print("Testing LINE Bot Integration...")
    
    # ทดสอบ LINE Bot Handler
    print("\n1. Testing LINE Bot Handler...")
    try:
        handler = AffiliateLineHandler()
        print("SUCCESS: LINE Bot Handler created successfully")
    except Exception as e:
        print(f"ERROR: LINE Bot Handler error: {e}")
        return False
    
    # ทดสอบ Rich Menu
    print("\n2. Testing Rich Menu System...")
    try:
        # ตรวจสอบ Rich Menu ปัจจุบัน
        current_menus = rich_menu_manager.get_rich_menu_list()
        print(f"Current Rich Menus: {len(current_menus)}")
        
        for menu in current_menus:
            print(f"  - {menu['name']} (ID: {menu['richMenuId'][:10]}...)")
        
        if len(current_menus) == 0:
            print("WARNING: No Rich Menus found. Need to upload Rich Menus.")
            
            # อัปโหลด Rich Menu
            print("\n3. Uploading Rich Menus...")
            result = rich_menu_manager.setup_rich_menus()
            
            if result:
                print("SUCCESS: Rich Menus uploaded successfully!")
                print(f"Main Menu ID: {result.get('main_menu_id', 'N/A')}")
                print(f"Admin Menu ID: {result.get('admin_menu_id', 'N/A')}")
            else:
                print("ERROR: Failed to upload Rich Menus")
                return False
        else:
            print("SUCCESS: Rich Menus are already available")
            
    except Exception as e:
        print(f"ERROR: Rich Menu error: {e}")
        return False
    
    # ทดสอบ Quick Reply
    print("\n4. Testing Quick Reply System...")
    try:
        # สร้าง dummy event สำหรับทดสอบ
        class DummyEvent:
            class Source:
                user_id = "test_user"
            class Message:
                text = "หมวดหมู่"
            source = Source()
            message = Message()
            reply_token = "dummy_token"
        
        event = DummyEvent()
        
        # ทดสอบการจัดการข้อความ
        print("Testing message handling...")
        handler.handle_message(event)
        print("SUCCESS: Message handling working")
        
    except Exception as e:
        print(f"ERROR: Quick Reply error: {e}")
        return False
    
    print("\nLINE Bot Integration test completed!")
    return True

if __name__ == "__main__":
    test_line_integration()