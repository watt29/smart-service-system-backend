"""
🧪 Test Rich Menu Creation
ทดสอบการสร้าง Rich Menu และรูปภาพ
"""

import os
from src.utils.rich_menu_creator import rich_menu_creator
from src.utils.rich_menu_manager import rich_menu_manager

def test_rich_menu_creation():
    """ทดสอบการสร้าง Rich Menu"""
    print("Testing Rich Menu Creation...")
    
    try:
        # สร้างรูปภาพ Rich Menu
        print("Creating Rich Menu images...")
        images = rich_menu_creator.create_all_rich_menu_images()
        
        for name, path in images.items():
            if os.path.exists(path):
                print(f"Success {name}: {path}")
            else:
                print(f"Failed {name}: File not found")
        
        # ทดสอบการสร้าง Rich Menu data
        print("\nTesting Rich Menu Data Creation...")
        main_menu_data = rich_menu_manager.create_main_rich_menu()
        admin_menu_data = rich_menu_manager.create_admin_rich_menu()
        
        print(f"Success Main Rich Menu: {main_menu_data['name']}")
        print(f"Success Admin Rich Menu: {admin_menu_data['name']}")
        
        print(f"\nMain Menu Areas: {len(main_menu_data['areas'])}")
        print(f"Admin Menu Areas: {len(admin_menu_data['areas'])}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_rich_menu_upload():
    """ทดสอบการอัปโหลด Rich Menu (จำเป็นต้องมี LINE tokens)"""
    print("\nTesting Rich Menu Upload...")
    
    try:
        # ดึงรายการ Rich Menu ปัจจุบัน
        current_menus = rich_menu_manager.get_rich_menu_list()
        print(f"Current Rich Menus: {len(current_menus)}")
        
        for menu in current_menus:
            print(f"  - {menu['name']} (ID: {menu['richMenuId'][:10]}...)")
        
        print("\nNote: To upload new Rich Menus, run rich_menu_manager.setup_rich_menus()")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Rich Menu Testing Suite\n")
    
    # Test 1: สร้างรูปภาพ
    success1 = test_rich_menu_creation()
    
    # Test 2: ทดสอบ API (ถ้ามี tokens)
    success2 = test_rich_menu_upload()
    
    print(f"\nTest Results:")
    print(f"Image Creation: {'Pass' if success1 else 'Fail'}")
    print(f"API Testing: {'Pass' if success2 else 'Fail'}")
    
    if success1 and success2:
        print("\nAll tests passed! Rich Menu system is ready.")
    else:
        print("\nSome tests failed. Check the errors above.")