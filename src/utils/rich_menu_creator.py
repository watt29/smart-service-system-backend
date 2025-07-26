"""
🎨 Rich Menu Image Creator
สร้างรูปภาพ Rich Menu ที่ทันสมัยแบบ programmatic
"""

from PIL import Image, ImageDraw, ImageFont
import os
from typing import Tuple

class RichMenuImageCreator:
    """คลาสสำหรับสร้างรูปภาพ Rich Menu"""
    
    def __init__(self):
        self.width = 2500
        self.height = 1686
        self.button_width = 833
        self.button_height = 843
        
        # สีธีมที่ทันสมัย
        self.colors = {
            'primary': '#FF6B35',      # ส้มสวย
            'secondary': '#4A90E2',    # ฟ้าเข้ม
            'success': '#27AE60',      # เขียว
            'warning': '#F39C12',      # เหลือง
            'danger': '#E74C3C',       # แดง
            'info': '#9B59B6',         # ม่วง
            'dark': '#2C3E50',         # เข้ม
            'light': '#ECF0F1',        # อ่อน
            'white': '#FFFFFF',        # ขาว
            'gradient_start': '#667eea', # ไล่เฉดเริ่ม
            'gradient_end': '#764ba2'    # ไล่เฉดจบ
        }
    
    def create_gradient_background(self, color1: str, color2: str) -> Image.Image:
        """สร้างพื้นหลังไล่เฉดสี"""
        base = Image.new('RGB', (self.width, self.height), color1)
        
        # สร้าง gradient แนวตั้ง
        for y in range(self.height):
            ratio = y / self.height
            r1, g1, b1 = tuple(int(color1[i:i+2], 16) for i in (1, 3, 5))
            r2, g2, b2 = tuple(int(color2[i:i+2], 16) for i in (1, 3, 5))
            
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            
            for x in range(self.width):
                base.putpixel((x, y), (r, g, b))
        
        return base
    
    def draw_rounded_rectangle(self, draw: ImageDraw.Draw, coords: Tuple[int, int, int, int], 
                             radius: int, fill: str, outline: str = None, width: int = 0):
        """วาดสี่เหลี่ยมมุมโค้ง"""
        x1, y1, x2, y2 = coords
        
        # วาดสี่เหลี่ยมหลัก
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill, outline=outline, width=width)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill, outline=outline, width=width)
        
        # วาดมุมโค้ง
        draw.pieslice([x1, y1, x1 + 2*radius, y1 + 2*radius], 180, 270, fill=fill, outline=outline, width=width)
        draw.pieslice([x2 - 2*radius, y1, x2, y1 + 2*radius], 270, 360, fill=fill, outline=outline, width=width)
        draw.pieslice([x1, y2 - 2*radius, x1 + 2*radius, y2], 90, 180, fill=fill, outline=outline, width=width)
        draw.pieslice([x2 - 2*radius, y2 - 2*radius, x2, y2], 0, 90, fill=fill, outline=outline, width=width)
    
    def create_main_rich_menu_image(self, output_path: str):
        """สร้างรูปภาพ Rich Menu หลัก"""
        # สร้างพื้นหลังไล่เฉดสี
        image = self.create_gradient_background(self.colors['gradient_start'], self.colors['gradient_end'])
        draw = ImageDraw.Draw(image)
        
        # ข้อมูลปุ่ม
        buttons = [
            # แถวบน
            {'pos': (50, 50, 783, 793), 'color': self.colors['primary'], 'emoji': '🔍', 'text': 'ค้นหาสินค้า'},
            {'pos': (883, 50, 1617, 793), 'color': self.colors['secondary'], 'emoji': '📂', 'text': 'หมวดหมู่'},
            {'pos': (1717, 50, 2450, 793), 'color': self.colors['success'], 'emoji': '🔥', 'text': 'ขายดี'},
            
            # แถวล่าง  
            {'pos': (50, 893, 783, 1636), 'color': self.colors['warning'], 'emoji': '💰', 'text': 'โปรโมชั่น'},
            {'pos': (883, 893, 1617, 1636), 'color': self.colors['info'], 'emoji': '📊', 'text': 'สถิติ'},
            {'pos': (1717, 893, 2450, 1636), 'color': self.colors['danger'], 'emoji': '❓', 'text': 'ช่วยเหลือ'}
        ]
        
        # วาดปุ่มต่างๆ
        for button in buttons:
            # วาดปุ่มมุมโค้ง
            self.draw_rounded_rectangle(draw, button['pos'], 30, button['color'], '#FFFFFF', 3)
            
            # คำนวณตำแหน่งกลาง
            x1, y1, x2, y2 = button['pos']
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            # ใส่ emoji (จำลองด้วยข้อความ)
            try:
                font_large = ImageFont.truetype("arial.ttf", 120)
                font_medium = ImageFont.truetype("arial.ttf", 60)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
            
            # วาด emoji
            emoji_bbox = draw.textbbox((0, 0), button['emoji'], font=font_large)
            emoji_width = emoji_bbox[2] - emoji_bbox[0]
            emoji_height = emoji_bbox[3] - emoji_bbox[1]
            draw.text((center_x - emoji_width//2, center_y - 80), button['emoji'], 
                     fill='#FFFFFF', font=font_large)
            
            # วาดข้อความ
            text_bbox = draw.textbbox((0, 0), button['text'], font=font_medium)
            text_width = text_bbox[2] - text_bbox[0]
            draw.text((center_x - text_width//2, center_y + 50), button['text'], 
                     fill='#FFFFFF', font=font_medium)
        
        # บันทึกรูปภาพ
        image.save(output_path, 'PNG', quality=95)
        print(f"Main rich menu image created: {output_path}")
    
    def create_admin_rich_menu_image(self, output_path: str):
        """สร้างรูปภาพ Rich Menu สำหรับ Admin"""
        # สร้างพื้นหลังแบบเข้ม
        image = self.create_gradient_background(self.colors['dark'], '#34495e')
        draw = ImageDraw.Draw(image)
        
        # ข้อมูลปุ่ม Admin
        buttons = [
            # แถวบน
            {'pos': (50, 50, 783, 793), 'color': self.colors['primary'], 'emoji': '🎛️', 'text': 'Dashboard'},
            {'pos': (883, 50, 1617, 793), 'color': self.colors['success'], 'emoji': '➕', 'text': 'เพิ่มสินค้า'},
            {'pos': (1717, 50, 2450, 793), 'color': self.colors['info'], 'emoji': '📊', 'text': 'สถิติหมวด'},
            
            # แถวล่าง
            {'pos': (50, 893, 783, 1636), 'color': self.colors['warning'], 'emoji': '🏆', 'text': 'ขายดี'},
            {'pos': (883, 893, 1617, 1636), 'color': self.colors['secondary'], 'emoji': '📂', 'text': 'หมวดหมู่'},
            {'pos': (1717, 893, 2450, 1636), 'color': self.colors['danger'], 'emoji': '🏠', 'text': 'หน้าหลัก'}
        ]
        
        # วาดปุ่มต่างๆ (คล้ายกับหลัก)
        for button in buttons:
            self.draw_rounded_rectangle(draw, button['pos'], 30, button['color'], '#FFFFFF', 3)
            
            x1, y1, x2, y2 = button['pos']
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            try:
                font_large = ImageFont.truetype("arial.ttf", 120)
                font_medium = ImageFont.truetype("arial.ttf", 60)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
            
            # วาด emoji
            emoji_bbox = draw.textbbox((0, 0), button['emoji'], font=font_large)
            emoji_width = emoji_bbox[2] - emoji_bbox[0]
            draw.text((center_x - emoji_width//2, center_y - 80), button['emoji'], 
                     fill='#FFFFFF', font=font_large)
            
            # วาดข้อความ
            text_bbox = draw.textbbox((0, 0), button['text'], font=font_medium)
            text_width = text_bbox[2] - text_bbox[0]
            draw.text((center_x - text_width//2, center_y + 50), button['text'], 
                     fill='#FFFFFF', font=font_medium)
        
        # เพิ่มข้อความ "ADMIN MODE" ที่มุมขวาบน
        admin_text = "ADMIN MODE"
        try:
            admin_font = ImageFont.truetype("arial.ttf", 40)
        except:
            admin_font = ImageFont.load_default()
        
        admin_bbox = draw.textbbox((0, 0), admin_text, font=admin_font)
        admin_width = admin_bbox[2] - admin_bbox[0]
        draw.text((self.width - admin_width - 50, 20), admin_text, 
                 fill='#FF6B35', font=admin_font)
        
        # บันทึกรูปภาพ
        image.save(output_path, 'PNG', quality=95)
        print(f"Admin rich menu image created: {output_path}")
    
    def create_all_rich_menu_images(self, output_dir: str = "rich_menu_images"):
        """สร้างรูปภาพ Rich Menu ทั้งหมด"""
        # สร้างโฟลเดอร์ถ้าไม่มี
        os.makedirs(output_dir, exist_ok=True)
        
        # สร้างรูปภาพ Rich Menu หลัก
        main_path = os.path.join(output_dir, "main_rich_menu.png")
        self.create_main_rich_menu_image(main_path)
        
        # สร้างรูปภาพ Rich Menu Admin
        admin_path = os.path.join(output_dir, "admin_rich_menu.png")  
        self.create_admin_rich_menu_image(admin_path)
        
        return {
            'main_menu_image': main_path,
            'admin_menu_image': admin_path
        }

# สร้าง instance สำหรับใช้งาน
rich_menu_creator = RichMenuImageCreator()