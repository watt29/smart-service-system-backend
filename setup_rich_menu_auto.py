"""
🛠️ Rich Menu Auto Setup Tool
เครื่องมือตั้งค่า Rich Menu แบบอัตโนมัติ
ไม่ต้องเข้า LINE Developers Console!
"""

import requests
import json
import os
from src.utils.rich_menu_manager import rich_menu_manager

def setup_rich_menu_automatically():
    """ตั้งค่า Rich Menu แบบอัตโนมัติ"""
    
    print("🚀 เริ่มต้นการตั้งค่า Rich Menu แบบอัตโนมัติ...")
    
    # ตรวจสอบ LINE_ACCESS_TOKEN
    line_token = os.environ.get('LINE_ACCESS_TOKEN')
    if not line_token:
        print("❌ ไม่พบ LINE_ACCESS_TOKEN!")
        print("\n📋 วิธีตั้งค่า LINE_ACCESS_TOKEN:")
        print("1. ไปที่ https://developers.line.biz/console/")
        print("2. เลือก Channel ของคุณ")
        print("3. ไปที่ Messaging API tab")
        print("4. คัดลอก Channel Access Token")
        print("5. รันคำสั่ง: set LINE_ACCESS_TOKEN=YOUR_TOKEN_HERE")
        print("6. รันสคริปต์นี้อีกครั้ง")
        return False
    
    # ตรวจสอบความถูกต้องของ Token
    print("🔍 ตรวจสอบ LINE Access Token...")
    headers = {
        'Authorization': f'Bearer {line_token}',
        'Content-Type': 'application/json'
    }
    
    # ทดสอบ API
    test_url = "https://api.line.me/v2/bot/info"
    try:
        response = requests.get(test_url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Token ไม่ถูกต้อง! Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        bot_info = response.json()
        print(f"✅ Token ถูกต้อง! Bot: {bot_info.get('displayName', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการทดสอบ Token: {e}")
        return False
    
    # ลบ Rich Menu เก่าทั้งหมด
    print("\n🗑️ ลบ Rich Menu เก่า...")
    try:
        list_url = "https://api.line.me/v2/bot/richmenu/list"
        response = requests.get(list_url, headers=headers)
        
        if response.status_code == 200:
            rich_menus = response.json().get('richmenus', [])
            for menu in rich_menus:
                menu_id = menu['richMenuId']
                delete_url = f"https://api.line.me/v2/bot/richmenu/{menu_id}"
                requests.delete(delete_url, headers=headers)
                print(f"  ✅ ลบ Rich Menu: {menu_id}")
        
    except Exception as e:
        print(f"⚠️ ไม่สามารถลบ Rich Menu เก่า: {e}")
    
    # สร้าง Rich Menu ใหม่
    print("\n🎨 สร้าง Rich Menu ใหม่...")
    
    try:
        # ใช้ Rich Menu Manager
        success = rich_menu_manager.setup_rich_menus()
        
        if success:
            print("✅ ตั้งค่า Rich Menu สำเร็จ!")
            print("\n🎉 Rich Menu พร้อมใช้งานแล้ว!")
            print("📱 ลองเปิด LINE Bot และดู Rich Menu ด้านล่าง")
            return True
        else:
            print("❌ การตั้งค่า Rich Menu ล้มเหลว")
            return False
            
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return False

def show_manual_instructions():
    """แสดงคำแนะนำการตั้งค่าแบบแมนนวล"""
    
    print("\n" + "="*60)
    print("📋 คำแนะนำการตั้งค่า Rich Menu แบบแมนนวล")
    print("="*60)
    
    print("\n1️⃣ เข้าไปที่ LINE Developers Console:")
    print("   https://developers.line.biz/console/")
    
    print("\n2️⃣ เลือก Channel ของคุณ")
    
    print("\n3️⃣ ไปที่แท็บ 'Messaging API'")
    
    print("\n4️⃣ หา Rich Menu section (อาจจะต้องเลื่อนลง)")
    
    print("\n5️⃣ คลิก 'Create' หรือ 'เพิ่ม Rich Menu'")
    
    print("\n6️⃣ อัปโหลดรูปภาพ:")
    print("   - ไฟล์: rich_menu_images/main_rich_menu.png")
    print("   - ขนาด: 2500 x 1686 pixels")
    
    print("\n7️⃣ ตั้งค่า 6 พื้นที่ (Areas):")
    areas = [
        ("🔍 ค้นหาสินค้า", "ค้นหาสินค้า"),
        ("📂 หมวดหมู่", "หมวดหมู่"),
        ("🏆 สินค้าขายดี", "สินค้าขายดี"),
        ("🎯 โปรโมชั่น", "โปรโมชั่น"),
        ("📊 สถิติ", "สถิติ"),
        ("❓ ช่วยเหลือ", "ช่วยเหลือ")
    ]
    
    for i, (label, action) in enumerate(areas, 1):
        print(f"   Area {i}: {label}")
        print(f"   Action: Send Text Message = '{action}'")
    
    print("\n8️⃣ บันทึกและเปิดใช้งาน")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    print("🎯 Rich Menu Auto Setup Tool")
    print("=" * 40)
    
    # ลองตั้งค่าแบบอัตโนมัติก่อน
    success = setup_rich_menu_automatically()
    
    if not success:
        print("\n⚠️ การตั้งค่าอัตโนมัติไม่สำเร็จ")
        show_manual_instructions()
    
    print("\n🔧 เสร็จสิ้นการตั้งค่า Rich Menu!")