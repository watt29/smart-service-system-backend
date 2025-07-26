"""
🔑 LINE Token Helper
ช่วยหา LINE Access Token ให้ง่าย ๆ
"""

def show_token_instructions():
    """แสดงวิธีหา LINE Access Token"""
    
    print("🔑 วิธีหา LINE Access Token")
    print("=" * 50)
    
    print("\n📍 Step 1: เข้าไปที่ LINE Developers Console")
    print("   URL: https://developers.line.biz/console/")
    
    print("\n📍 Step 2: Login ด้วย LINE Account")
    
    print("\n📍 Step 3: เลือก Provider และ Channel")
    print("   - เลือก Provider ของคุณ")
    print("   - เลือก Channel ที่ต้องการ")
    
    print("\n📍 Step 4: ไปที่แท็บ 'Messaging API'")
    
    print("\n📍 Step 5: หา 'Channel access token'")
    print("   - มองหาส่วน 'Channel access token'")
    print("   - หากยังไม่มี ให้คลิก 'Issue' เพื่อสร้าง")
    print("   - คัดลอก Token ที่ได้")
    
    print("\n📍 Step 6: ตั้งค่า Environment Variable")
    print("   Windows: set LINE_ACCESS_TOKEN=YOUR_TOKEN_HERE")
    print("   Mac/Linux: export LINE_ACCESS_TOKEN=YOUR_TOKEN_HERE")
    
    print("\n📍 Step 7: รันสคริปต์ Rich Menu")
    print("   python setup_rich_menu_auto.py")
    
    print("\n" + "=" * 50)
    
    print("\n💡 Tips:")
    print("   - Token จะขึ้นต้นด้วย 'YOUR_CHANNEL_ACCESS_TOKEN'")
    print("   - อย่าแชร์ Token ให้คนอื่น")
    print("   - Token มีอายุ ถ้าหมดอายุต้องสร้างใหม่")
    
    print("\n🔍 หากหาไม่เจอ:")
    print("   1. ตรวจสอบว่าใช้ Messaging API Channel")
    print("   2. ตรวจสอบว่ามีสิทธิ์ในการเข้าถึง Channel")
    print("   3. ลองรีเฟรชหน้าเว็บ")

if __name__ == "__main__":
    show_token_instructions()