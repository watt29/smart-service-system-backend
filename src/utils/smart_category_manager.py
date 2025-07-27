"""
📁 Smart Category Manager
ระบบจัดการหมวดหมู่อัจฉริยะ สำหรับการแสดงโปรโมต และการค้นหา
"""

import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

class SmartCategoryManager:
    """คลาสจัดการหมวดหมู่อัจฉริยะ"""
    
    def __init__(self, db_instance=None):
        self.logger = logging.getLogger(__name__)
        self.db = db_instance
        
        # กำหนดหมวดหมู่และไอคอน
        self.categories = {
            'โทรศัพท์มือถือ': {
                'icon': '📱',
                'keywords': ['มือถือ', 'โทรศัพท์', 'smartphone', 'iphone', 'samsung', 'android'],
                'priority': 1,  # ความสำคัญสูง
                'promo_style': 'tech',
                'color': '#007AFF'
            },
            'ความงาม': {
                'icon': '💄',
                'keywords': ['ความงาม', 'เซรั่ม', 'ครีม', 'ลิป', 'แต่งหน้า', 'beauty', 'skincare'],
                'priority': 1,
                'promo_style': 'beauty',
                'color': '#FF69B4'
            },
            'แฟชั่น': {
                'icon': '👕',
                'keywords': ['แฟชั่น', 'เสื้อผ้า', 'เสื้อ', 'กางเกง', 'fashion', 'clothes'],
                'priority': 1,
                'promo_style': 'fashion',
                'color': '#8B4513'
            },
            'สัตว์เลี้ยง': {
                'icon': '🐾',
                'keywords': ['สัตว์เลี้ยง', 'แมว', 'หมา', 'อาหารแมว', 'อาหารหมา', 'pet'],
                'priority': 2,
                'promo_style': 'pet',
                'color': '#FF6347'
            },
            'กระเป๋า': {
                'icon': '🎒',
                'keywords': ['กระเป๋า', 'เป้', 'สะพาย', 'bag', 'backpack'],
                'priority': 2,
                'promo_style': 'accessories',
                'color': '#8B4513'
            },
            'เกมมิ่ง': {
                'icon': '🎮',
                'keywords': ['เกมมิ่ง', 'เกม', 'หูฟัง', 'คีย์บอร์ด', 'gaming', 'game'],
                'priority': 1,
                'promo_style': 'gaming',
                'color': '#9932CC'
            },
            'รองเท้า': {
                'icon': '👟',
                'keywords': ['รองเท้า', 'ผ้าใบ', 'ส้นสูง', 'shoes', 'sneaker'],
                'priority': 2,
                'promo_style': 'fashion',
                'color': '#2E8B57'
            },
            'นาฬิกาแว่นตา': {
                'icon': '⌚',
                'keywords': ['นาฬิกา', 'แว่นตา', 'สมาร์ทวอทช์', 'watch', 'glasses'],
                'priority': 2,
                'promo_style': 'accessories',
                'color': '#4682B4'
            },
            'กล้อง': {
                'icon': '📷',
                'keywords': ['กล้อง', 'เลนส์', 'camera', 'lens', 'photography'],
                'priority': 2,
                'promo_style': 'tech',
                'color': '#FF4500'
            },
            'คอมพิวเตอร์': {
                'icon': '💻',
                'keywords': ['คอมพิวเตอร์', 'โน๊ตบุ๊ค', 'เมาส์', 'laptop', 'computer'],
                'priority': 1,
                'promo_style': 'tech',
                'color': '#4169E1'
            },
            'สุขภาพ': {
                'icon': '💊',
                'keywords': ['สุขภาพ', 'วิตามิน', 'อาหารเสริม', 'health', 'vitamin'],
                'priority': 2,
                'promo_style': 'health',
                'color': '#32CD32'
            },
            'อาหารเครื่องดื่ม': {
                'icon': '🍽️',
                'keywords': ['อาหาร', 'เครื่องดื่ม', 'กาแฟ', 'food', 'drink', 'coffee'],
                'priority': 3,
                'promo_style': 'food',
                'color': '#FF8C00'
            },
            'เครื่องใช้ไฟฟ้า': {
                'icon': '🔌',
                'keywords': ['เครื่องใช้ไฟฟ้า', 'เครื่องปั่น', 'เครื่องทำกาแฟ', 'appliance'],
                'priority': 2,
                'promo_style': 'appliance',
                'color': '#DC143C'
            },
            'กีฬา': {
                'icon': '⚽',
                'keywords': ['กีฬา', 'ฟุตบอล', 'ออกกำลังกาย', 'sport', 'fitness'],
                'priority': 3,
                'promo_style': 'sport',
                'color': '#228B22'
            },
            'เด็กและของเล่น': {
                'icon': '🧸',
                'keywords': ['เด็ก', 'ของเล่น', 'baby', 'toys', 'kids'],
                'priority': 3,
                'promo_style': 'kids',
                'color': '#FFB6C1'
            }
        }
        
        # รูปแบบโปรโมชั่นตามสไตล์
        self.promo_templates = {
            'tech': [
                "🚀 เทคโนโลยีล้ำสมัย {product} ราคาพิเศษ {price:,} บาท!",
                "⚡ อัปเกรดชีวิตด้วย {product} ลดเหลือ {price:,} บาท",
                "🔥 Hot Deal! {product} เทคโนโลยีล่าสุดในราคาสุดคุ้ม!"
            ],
            'beauty': [
                "✨ สวยใสเปล่งปลั่งด้วย {product} เพียง {price:,} บาท",
                "💖 ความงามที่คุณสมควรได้! {product} ราคาพิเศษ",
                "🌟 เปลี่ยนแปลงผิวให้สวยกว่าเดิมด้วย {product}"
            ],
            'fashion': [
                "👗 แฟชั่นเทรนด์ใหม่! {product} สไตล์เก๋ ราคา {price:,} บาท",
                "🔥 สวยใส่ได้ทุกโอกาส {product} ลดราคาพิเศษ!",
                "💫 อัปเดตลุคใหม่กับ {product} ราคาคุ้มค่า"
            ],
            'pet': [
                "🐱 รักน้องเมี่ยวด้วย {product} คุณภาพดี ราคา {price:,} บาท",
                "🐶 เพื่อน 4 ขาของคุณสมควรได้ดีที่สุด! {product}",
                "❤️ ดูแลสัตว์เลี้ยงด้วยใจ {product} ราคาพิเศษ"
            ]
        }
        
        # อัปเดตหมวดหมู่จากฐานข้อมูล
        if self.db:
            self._initialize_from_database()
    
    def get_category_info(self, category_name: str) -> Optional[Dict]:
        """ดึงข้อมูลหมวดหมู่"""
        return self.categories.get(category_name)
    
    def detect_category_from_query(self, query: str) -> List[str]:
        """ตรวจจับหมวดหมู่จากคำค้นหา"""
        query_lower = query.lower()
        detected_categories = []
        
        for category, info in self.categories.items():
            for keyword in info['keywords']:
                if keyword.lower() in query_lower:
                    detected_categories.append(category)
                    break
        
        return detected_categories
    
    def get_smart_categories_display(self) -> List[Dict]:
        """สร้างการแสดงหมวดหมู่แบบอัจฉริยะ"""
        categories_list = []
        
        # ดึงหมวดหมู่จากฐานข้อมูลก่อน
        db_categories = self.get_categories_from_database()
        
        # สร้างรายการแสดง โดยให้หมวดหมู่ที่มีในฐานข้อมูลมาก่อน
        for category in db_categories:
            info = self.categories.get(category, {
                'icon': '📦',
                'priority': 3,
                'color': '#6B7280'
            })
            
            categories_list.append({
                'name': category,
                'display': f"{info['icon']} {category}",
                'priority': info['priority'],
                'color': info['color']
            })
        
        # จัดเรียงตาม priority
        categories_list.sort(key=lambda x: x['priority'])
        
        return categories_list
    
    def generate_promo_message(self, product_data: Dict, style: str = None) -> str:
        """สร้างข้อความโปรโมชั่น"""
        if not style:
            category = product_data.get('category', '')
            category_info = self.get_category_info(category)
            style = category_info.get('promo_style', 'general') if category_info else 'general'
        
        templates = self.promo_templates.get(style, self.promo_templates['tech'])
        template = random.choice(templates)
        
        return template.format(
            product=product_data.get('product_name', 'สินค้าพิเศษ'),
            price=product_data.get('price', 0)
        )
    
    def get_category_based_quick_reply(self, detected_categories: List[str] = None) -> List[Dict]:
        """สร้าง Quick Reply ตามหมวดหมู่ที่ตรวจจับได้"""
        if not detected_categories:
            # แสดงหมวดหมู่ยอดนิยม
            popular_categories = ['โทรศัพท์มือถือ', 'ความงาม', 'แฟชั่น', 'เกมมิ่ง', 'สัตว์เลี้ยง']
        else:
            popular_categories = detected_categories[:5]
        
        quick_replies = []
        for category in popular_categories:
            info = self.get_category_info(category)
            if info:
                quick_replies.append({
                    'label': f"{info['icon']} {category}",
                    'text': category
                })
        
        # เพิ่มตัวเลือกเพิ่มเติม
        quick_replies.extend([
            {'label': '🔥 ขายดี', 'text': 'ขายดี'},
            {'label': '💰 โปรโมชั่น', 'text': 'โปรโมชั่น'},
            {'label': '📋 หมวดหมู่', 'text': 'หมวดหมู่'}
        ])
        
        return quick_replies[:8]  # จำกัดไม่เกิน 8 ปุ่ม
    
    def get_smart_search_suggestions(self, query: str) -> Dict:
        """สร้างคำแนะนำการค้นหาอัจฉริยะ"""
        detected_categories = self.detect_category_from_query(query)
        
        suggestions = {
            'detected_categories': detected_categories,
            'alternative_searches': [],
            'related_categories': []
        }
        
        if detected_categories:
            # แนะนำการค้นหาในหมวดหมู่ที่ตรวจจับได้
            for category in detected_categories:
                info = self.get_category_info(category)
                if info:
                    # แนะนำคำค้นหาอื่นในหมวดเดียวกัน
                    other_keywords = [kw for kw in info['keywords'] if kw != query.lower()]
                    suggestions['alternative_searches'].extend(other_keywords[:3])
            
            # หาหมวดหมู่ที่เกี่ยวข้อง
            for category in detected_categories:
                related = self._find_related_categories(category)
                suggestions['related_categories'].extend(related)
        else:
            # ถ้าไม่เจอหมวดหมู่ แนะนำหมวดหมู่ยอดนิยม
            suggestions['related_categories'] = ['โทรศัพท์มือถือ', 'ความงาม', 'แฟชั่น', 'เกมมิ่ง']
        
        return suggestions
    
    def _find_related_categories(self, category: str) -> List[str]:
        """หาหมวดหมู่ที่เกี่ยวข้อง"""
        category_info = self.get_category_info(category)
        if not category_info:
            return []
        
        style = category_info['promo_style']
        priority = category_info['priority']
        
        related = []
        for cat_name, cat_info in self.categories.items():
            if (cat_name != category and 
                (cat_info['promo_style'] == style or cat_info['priority'] == priority)):
                related.append(cat_name)
        
        return related[:3]
    
    def create_category_carousel_data(self, categories: List[str]) -> List[Dict]:
        """สร้างข้อมูลสำหรับ Carousel แสดงหมวดหมู่"""
        carousel_items = []
        
        for category in categories:
            info = self.get_category_info(category)
            if info:
                carousel_items.append({
                    'title': f"{info['icon']} {category}",
                    'subtitle': f"สินค้า{category}คุณภาพดี ราคาเป็นมิตร",
                    'action_text': f"ดู{category}",
                    'action_data': category,
                    'color': info['color']
                })
        
        return carousel_items
    
    def update_categories_from_database(self, db_categories: List[str]):
        """อัปเดตหมวดหมู่จากฐานข้อมูลจริง"""
        try:
            # เพิ่มหมวดหมู่ใหม่ที่ไม่มีในระบบ
            for category in db_categories:
                if category not in self.categories:
                    # สร้างข้อมูลหมวดหมู่ใหม่
                    icon_map = {
                        'โทรศัพท์มือถือ': '📱',
                        'ความงาม': '💄',
                        'เสื้อผ้าผู้ชาย': '👔',
                        'เสื้อผ้าผู้หญิง': '👗',
                        'รองเท้าผู้ชาย': '👞',
                        'รองเท้าผู้หญิง': '👠',
                        'นาฬิกาแว่นตา': '⌚',
                        'กล้อง': '📷',
                        'คอมพิวเตอร์': '💻',
                        'สุขภาพ': '💊',
                        'อาหารเครื่องดื่ม': '🍽️',
                        'เครื่องใช้ไฟฟ้า': '🔌',
                        'กีฬา': '⚽'
                    }
                    
                    self.categories[category] = {
                        'icon': icon_map.get(category, '📦'),
                        'keywords': [category.lower()],
                        'priority': 2,  # ค่าเริ่มต้น
                        'promo_style': 'general',
                        'color': '#6B7280'  # สีเทา
                    }
            
            self.logger.info(f"อัปเดตหมวดหมู่แล้ว: {len(db_categories)} หมวดหมู่")
            
        except Exception as e:
            self.logger.error(f"Error updating categories from database: {e}")
    
    def get_available_categories(self) -> List[str]:
        """ดึงรายการหมวดหมู่ที่มีอยู่ในระบบ"""
        return list(self.categories.keys())
    
    def _initialize_from_database(self):
        """เริ่มต้นระบบหมวดหมู่จากฐานข้อมูล"""
        try:
            if not self.db:
                return
                
            # ดึงหมวดหมู่จากฐานข้อมูล
            db_categories = self.db.get_categories()
            
            if db_categories:
                self.update_categories_from_database(db_categories)
                self.logger.info(f"โหลดหมวดหมู่จากฐานข้อมูล: {len(db_categories)} หมวดหมู่")
            else:
                self.logger.warning("ไม่พบหมวดหมู่ในฐานข้อมูล ใช้หมวดหมู่เริ่มต้น")
                
        except Exception as e:
            self.logger.error(f"ไม่สามารถโหลดหมวดหมู่จากฐานข้อมูล: {e}")
    
    def get_categories_from_database(self) -> List[str]:
        """ดึงหมวดหมู่จากฐานข้อมูลแบบ real-time"""
        try:
            if not self.db:
                return list(self.categories.keys())
                
            db_categories = self.db.get_categories()
            
            # รวมหมวดหมู่จากฐานข้อมูลและหมวดหมู่เริ่มต้น
            all_categories = set(db_categories)
            all_categories.update(self.categories.keys())
            
            return sorted(list(all_categories))
            
        except Exception as e:
            self.logger.error(f"Error getting categories from database: {e}")
            return list(self.categories.keys())