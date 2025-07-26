"""
📱 สร้าง Rich Menu แบบง่าย ๆ ที่ใช้งานได้แน่นอน
ไม่ใช้ฟอนต์ภาษาไทย เพื่อหลีกเลี่ยงปัญหา encoding
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_simple_rich_menu():
    """สร้าง Rich Menu แบบเรียบง่าย"""
    
    # ขนาดมาตรฐาน
    width = 2500
    height = 1686
    
    # สร้างพื้นหลังสีเดียว
    image = Image.new('RGB', (width, height), (67, 56, 202))  # สีน้ำเงิน
    draw = ImageDraw.Draw(image)
    
    # คำนวณขนาดปุ่ม
    margin = 30
    button_width = (width - margin * 4) // 3
    button_height = (height - margin * 3) // 2
    
    # ข้อมูลปุ่มแบบภาษาอังกฤษ
    buttons = [
        {'text': 'SEARCH', 'icon': 'Q', 'color': (255, 87, 51), 'row': 0, 'col': 0},
        {'text': 'CATEGORY', 'icon': 'C', 'color': (52, 152, 219), 'row': 0, 'col': 1},
        {'text': 'BESTSELLER', 'icon': 'B', 'color': (46, 204, 113), 'row': 0, 'col': 2},
        {'text': 'PROMOTION', 'icon': 'P', 'color': (241, 196, 15), 'row': 1, 'col': 0},
        {'text': 'STATS', 'icon': 'S', 'color': (155, 89, 182), 'row': 1, 'col': 1},
        {'text': 'HELP', 'icon': 'H', 'color': (231, 76, 60), 'row': 1, 'col': 2}
    ]
    
    # ฟังก์ชันวาดปุ่ม
    def draw_button(x, y, w, h, color, icon, text):
        # วาดเงา
        draw.rectangle([x + 5, y + 5, x + w + 5, y + h + 5], fill=(0, 0, 0, 50))
        
        # วาดปุ่มหลัก
        draw.rectangle([x, y, x + w, y + h], fill=color)
        
        # วาดกรอบ
        draw.rectangle([x, y, x + w, y + h], outline=(255, 255, 255), width=3)
        
        # ใช้ฟอนต์เริ่มต้น
        try:
            # ลองใช้ฟอนต์ที่มีใน Windows
            big_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 150)
            small_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 80)
        except:
            # ใช้ฟอนต์เริ่มต้น
            big_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # วาดไอคอน (ใช้ตัวอักษรแทน)
        icon_bbox = draw.textbbox((0, 0), icon, font=big_font)
        icon_width = icon_bbox[2] - icon_bbox[0]
        icon_x = x + (w - icon_width) // 2
        icon_y = y + h // 4
        
        # เงาไอคอน
        draw.text((icon_x + 3, icon_y + 3), icon, fill=(0, 0, 0), font=big_font)
        draw.text((icon_x, icon_y), icon, fill='white', font=big_font)
        
        # วาดข้อความ
        text_bbox = draw.textbbox((0, 0), text, font=small_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = x + (w - text_width) // 2
        text_y = y + h * 3 // 4
        
        # เงาข้อความ
        draw.text((text_x + 2, text_y + 2), text, fill=(0, 0, 0), font=small_font)
        draw.text((text_x, text_y), text, fill='white', font=small_font)
    
    # สร้างปุ่มทั้งหมด
    for button in buttons:
        x = margin + (button['col'] * (button_width + margin))
        y = margin + (button['row'] * (button_height + margin))
        
        draw_button(x, y, button_width, button_height, 
                   button['color'], button['icon'], button['text'])
    
    return image

def main():
    print("Creating Simple Rich Menu...")
    
    # สร้างโฟลเดอร์
    os.makedirs("rich_menu_images", exist_ok=True)
    
    # สร้างรูป
    image = create_simple_rich_menu()
    
    # บันทึกไฟล์
    path = "rich_menu_images/main_rich_menu.png"
    image.save(path, "PNG", quality=95)
    
    print(f"SUCCESS: Created {path}")
    print(f"Size: {image.size[0]} x {image.size[1]} pixels")
    print(f"File size: {os.path.getsize(path) / 1024:.1f} KB")
    
    # สร้างไฟล์สำรอง
    backup_path = "rich_menu_images/main_rich_menu_simple.png"
    image.save(backup_path, "PNG", quality=95)
    print(f"Backup saved: {backup_path}")

if __name__ == "__main__":
    main()