"""
🎨 สร้าง Rich Menu ที่สวยงามและชัดเจน
แก้ปัญหารูปภาพไม่มีตัวอักษรและไอคอน
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_professional_rich_menu():
    """สร้าง Rich Menu แบบมืออาชีพ"""
    
    # ขนาดมาตรฐานของ LINE Rich Menu
    width = 2500
    height = 1686
    
    # สร้างพื้นหลังไล่เฉดสี
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)
    
    # สร้างไล่เฉดสีจากสีน้ำเงินเข้มไปสีม่วง
    for y in range(height):
        ratio = y / height
        r = int(102 + (118 - 102) * ratio)  # 667eea -> 764ba2
        g = int(126 + (75 - 126) * ratio)
        b = int(234 + (162 - 234) * ratio)
        
        for x in range(width):
            image.putpixel((x, y), (r, g, b))
    
    # คำนวณขนาดปุ่ม (3x2 = 6 ปุ่ม)
    button_width = (width - 80) // 3  # เหลือพื้นที่ขอบ
    button_height = (height - 60) // 2
    
    # ข้อมูลปุ่ม
    buttons = [
        {'text': 'ค้นหาสินค้า', 'emoji': '🔍', 'color': (255, 107, 53), 'row': 0, 'col': 0},  # ส้ม
        {'text': 'หมวดหมู่', 'emoji': '📂', 'color': (74, 144, 226), 'row': 0, 'col': 1},     # ฟ้า
        {'text': 'สินค้าขายดี', 'emoji': '🏆', 'color': (39, 174, 96), 'row': 0, 'col': 2},   # เขียว
        {'text': 'โปรโมชั่น', 'emoji': '🎯', 'color': (243, 156, 18), 'row': 1, 'col': 0},   # เหลือง
        {'text': 'สถิติ', 'emoji': '📊', 'color': (155, 89, 182), 'row': 1, 'col': 1},        # ม่วง
        {'text': 'ช่วยเหลือ', 'emoji': '❓', 'color': (231, 76, 60), 'row': 1, 'col': 2}     # แดง
    ]
    
    # ฟังก์ชันวาดปุ่มมุมมน
    def draw_rounded_rect(draw, coords, color, radius=20):
        x1, y1, x2, y2 = coords
        
        # วาดสี่เหลี่ยมหลัก
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=color)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=color)
        
        # วาดมุมมน
        draw.pieslice([x1, y1, x1 + radius * 2, y1 + radius * 2], 180, 270, fill=color)
        draw.pieslice([x2 - radius * 2, y1, x2, y1 + radius * 2], 270, 360, fill=color)
        draw.pieslice([x1, y2 - radius * 2, x1 + radius * 2, y2], 90, 180, fill=color)
        draw.pieslice([x2 - radius * 2, y2 - radius * 2, x2, y2], 0, 90, fill=color)
    
    # สร้างปุ่มแต่ละอัน
    for button in buttons:
        # คำนวณตำแหน่ง
        x = 20 + (button['col'] * (button_width + 20))
        y = 20 + (button['row'] * (button_height + 20))
        
        # วาดเงา
        shadow_color = (0, 0, 0, 80)
        draw_rounded_rect(draw, (x + 5, y + 5, x + button_width + 5, y + button_height + 5), 
                         (50, 50, 50), 25)
        
        # วาดปุ่มหลัก
        draw_rounded_rect(draw, (x, y, x + button_width, y + button_height), 
                         button['color'], 25)
        
        # วาดไฮไลท์ด้านบน
        highlight_color = tuple(min(255, c + 30) for c in button['color'])
        draw_rounded_rect(draw, (x, y, x + button_width, y + 50), 
                         highlight_color, 25)
        
        try:
            # ลองใช้ฟอนต์ Windows
            font_paths = [
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/calibri.ttf",
                "C:/Windows/Fonts/segoeui.ttf",
                "arial.ttf"
            ]
            
            emoji_font = None
            text_font = None
            
            # หาฟอนต์สำหรับ emoji
            for path in font_paths:
                try:
                    emoji_font = ImageFont.truetype(path, 120)
                    text_font = ImageFont.truetype(path, 60)
                    break
                except (FileNotFoundError, OSError):
                    continue
            
            if emoji_font is None or text_font is None:
                # ใช้ฟอนต์เริ่มต้น
                emoji_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
            
            # วาด Emoji
            emoji = button['emoji']
            emoji_bbox = draw.textbbox((0, 0), emoji, font=emoji_font)
            emoji_width = emoji_bbox[2] - emoji_bbox[0]
            emoji_height = emoji_bbox[3] - emoji_bbox[1]
            emoji_x = x + (button_width - emoji_width) // 2
            emoji_y = y + button_height // 4
            
            # เงาสำหรับ emoji
            draw.text((emoji_x + 3, emoji_y + 3), emoji, fill=(0, 0, 0, 100), font=emoji_font)
            draw.text((emoji_x, emoji_y), emoji, fill='white', font=emoji_font)
            
            # วาดข้อความ
            text = button['text']
            
            # ตรวจสอบความยาวข้อความ
            if len(text) > 8:
                # แบ่งข้อความเป็น 2 บรรทัด
                words = text.split()
                if len(words) >= 2:
                    line1 = words[0]
                    line2 = ' '.join(words[1:])
                else:
                    mid = len(text) // 2
                    line1 = text[:mid]
                    line2 = text[mid:]
                
                # บรรทัดที่ 1
                text1_bbox = draw.textbbox((0, 0), line1, font=text_font)
                text1_width = text1_bbox[2] - text1_bbox[0]
                text1_x = x + (button_width - text1_width) // 2
                text1_y = y + button_height * 2 // 3
                
                draw.text((text1_x + 2, text1_y + 2), line1, fill=(0, 0, 0, 100), font=text_font)
                draw.text((text1_x, text1_y), line1, fill='white', font=text_font)
                
                # บรรทัดที่ 2
                text2_bbox = draw.textbbox((0, 0), line2, font=text_font)
                text2_width = text2_bbox[2] - text2_bbox[0]
                text2_x = x + (button_width - text2_width) // 2
                text2_y = text1_y + 70
                
                draw.text((text2_x + 2, text2_y + 2), line2, fill=(0, 0, 0, 100), font=text_font)
                draw.text((text2_x, text2_y), line2, fill='white', font=text_font)
            else:
                # ข้อความบรรทัดเดียว
                text_bbox = draw.textbbox((0, 0), text, font=text_font)
                text_width = text_bbox[2] - text_bbox[0]
                text_x = x + (button_width - text_width) // 2
                text_y = y + button_height * 2 // 3
                
                draw.text((text_x + 2, text_y + 2), text, fill=(0, 0, 0, 100), font=text_font)
                draw.text((text_x, text_y), text, fill='white', font=text_font)
                
        except Exception as e:
            print(f"Warning: Font issue for button '{button['text']}': {e}")
            
            # Fallback: ใช้ฟอนต์เริ่มต้น
            default_font = ImageFont.load_default()
            
            # รวม emoji และข้อความ
            combined_text = f"{button['emoji']} {button['text']}"
            
            # คำนวณตำแหน่งกลาง
            text_bbox = draw.textbbox((0, 0), combined_text, font=default_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = x + (button_width - text_width) // 2
            text_y = y + (button_height - text_height) // 2
            
            # วาดข้อความ
            draw.text((text_x + 1, text_y + 1), combined_text, fill=(0, 0, 0), font=default_font)
            draw.text((text_x, text_y), combined_text, fill='white', font=default_font)
    
    return image

def main():
    """สร้างรูป Rich Menu"""
    print("สร้าง Rich Menu ใหม่...")
    
    # สร้างโฟลเดอร์หากยังไม่มี
    os.makedirs("rich_menu_images", exist_ok=True)
    
    # สร้างรูป Rich Menu หลัก
    main_image = create_professional_rich_menu()
    main_path = "rich_menu_images/main_rich_menu_new.png"
    main_image.save(main_path, "PNG", quality=95)
    
    print(f"สร้าง Rich Menu สำเร็จ: {main_path}")
    print(f"ขนาด: {main_image.size[0]} x {main_image.size[1]} pixels")
    print(f"ขนาดไฟล์: {os.path.getsize(main_path) / 1024:.1f} KB")
    
    # แทนที่ไฟล์เก่า
    old_path = "rich_menu_images/main_rich_menu.png"
    if os.path.exists(old_path):
        main_image.save(old_path, "PNG", quality=95)
        print(f"อัปเดตไฟล์เก่า: {old_path}")
    
    print("\nRich Menu พร้อมใช้งานแล้ว!")
    print("ไฟล์ที่ใช้: rich_menu_images/main_rich_menu.png")

if __name__ == "__main__":
    main()