"""
📁 src/utils/review_generator.py
🎯 สร้างโพสต์รีวิวสินค้าอัตโนมัติสำหรับ Affiliate Marketing
"""

import logging
import random
from typing import Dict, List, Optional
from datetime import datetime

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from ..config import config

class ReviewGenerator:
    """คลาสสำหรับสร้างรีวิวสินค้าอัตโนมัติ"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        
        # เทมเพลตรีวิวแบบต่างๆ
        self.review_templates = {
            'short': [
                "🔥 {product_name}\n💰 ราคา: {price:,.0f}฿\n⭐ คุณภาพดี คุ้มค่าเงิน\n💸 คอมมิชชัน: {commission:,.0f}฿\n🛒 {offer_link}",
                "✨ รีวิว: {product_name}\n🏪 {shop_name}\n💵 {price:,.0f}฿ | 📊 {commission_rate}%\n{offer_link}",
                "🛍️ {product_name}\n🔥 ราคาดี: {price:,.0f}฿\n💎 คุณภาพพรีเมียม\n🎯 {offer_link}"
            ],
            'medium': [
                "🌟 รีวิว: {product_name}\n\n💰 ราคา: {price:,.0f} บาท\n🏪 ร้าน: {shop_name}\n⭐ เรตติ้ง: {rating}/5.0\n\n✨ {description}\n\n💸 คอมมิชชัน: {commission:,.0f}฿ ({commission_rate}%)\n🛒 สั่งซื้อ: {offer_link}\n\n#{category} #รีวิวสินค้า #คุ้มค่า",
                "🔥 ไอเท็มเด็ด: {product_name}\n\n📍 {shop_name}\n💵 ราคา: {price:,.0f}฿\n🔥 ขายแล้ว: {sold_count} ชิ้น\n\n{highlights}\n\n💰 รายได้: {commission:,.0f}฿\n🎯 ลิงก์: {offer_link}",
                "✨ แนะนำสินค้า: {product_name}\n\n🏆 จุดเด่น:\n{features}\n\n💰 ราคา: {price:,.0f}฾ ({commission_rate}% = {commission:,.0f}฿)\n🛒 {offer_link}\n\n#affiliate #{category}"
            ],
            'long': [
                "🌟 รีวิวเต็ม: {product_name}\n\n📋 รายละเอียด:\n• ราคา: {price:,.0f} บาท\n• ร้าน: {shop_name}\n• เรตติ้ง: {rating}⭐\n• ขายแล้ว: {sold_count} ชิ้น\n\n✨ ทำไมต้องเลือกสินค้านี้?\n{detailed_review}\n\n💸 Affiliate Info:\n• คอมมิชชัน: {commission_rate}%\n• รายได้: {commission:,.0f} บาท\n\n🛒 สั่งซื้อได้ที่: {offer_link}\n\n#{category} #รีวิว #affiliate #คุ้มค่า #ของดี"
            ]
        }
        
        # คำคุณศัพท์เชิงบวก
        self.positive_adjectives = [
            "ดีเยี่ยม", "สุดยอด", "คุ้มค่า", "ใช้ดี", "คุณภาพสูง",
            "น่าสนใจ", "แนะนำ", "ปัง", "เด็ด", "ดีมาก"
        ]
        
        # หมวดหมู่และคำอธิบาย
        self.category_descriptions = {
            'อิเล็กทรอนิกส์': 'เทคโนโลยีล้ำสมัย ใช้งานง่าย',
            'แฟชั่น': 'สไตล์เท่ ดีไซน์สวย',
            'ความงาม': 'ผิวสวย เปล่งปลั่ง',
            'สุขภาพ': 'ดูแลสุขภาพ ใส่ใจตัวเอง',
            'บ้านและสวน': 'บ้านสวย ชีวิตดีขึ้น',
            'กีฬา': 'แข็งแรง สุขภาพดี',
            'เด็กและของเล่น': 'ความสุขของลูกรัก',
            'อาหาร': 'อร่อย มีประโยชน์'
        }
        
        # ตั้งค่า OpenAI
        if OPENAI_AVAILABLE and config.OPENAI_API_KEY:
            try:
                openai.api_key = config.OPENAI_API_KEY
                self.client = openai
                self.logger.info("OpenAI client initialized for review generation")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def generate_review(self, product: Dict, style: str = 'medium', use_ai: bool = False) -> str:
        """สร้างรีวิวสินค้า"""
        try:
            if use_ai and self.client and config.USE_AI_SEARCH:
                return self._generate_ai_review(product, style)
            else:
                return self._generate_template_review(product, style)
        except Exception as e:
            self.logger.error(f"Review generation failed: {e}")
            return self._generate_basic_review(product)
    
    def _generate_ai_review(self, product: Dict, style: str) -> str:
        """สร้างรีวิวด้วย AI"""
        try:
            product_info = self._format_product_info(product)
            
            prompt = f"""
            สร้างโพสต์รีวิวสินค้าสำหรับ affiliate marketing:
            
            ข้อมูลสินค้า:
            {product_info}
            
            สไตล์: {style} (short=สั้น, medium=ปานกลาง, long=ยาว)
            
            ข้อกำหนด:
            - ใช้ภาษาไทยที่เป็นกันเอง
            - มีอีโมจิที่เหมาะสม
            - เน้นจุดเด่นของสินค้า
            - ระบุราคาและคอมมิชชัน
            - มีลิงก์ affiliate
            - ใช้แฮชแท็กที่เกี่ยวข้อง
            - ความยาวเหมาะกับสไตล์ที่กำหนด
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "คุณเป็นนักการตลาด affiliate มืออาชีพที่เขียนรีวิวสินค้าได้น่าสนใจ"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400 if style == 'long' else 250,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"AI review generation failed: {e}")
            return self._generate_template_review(product, style)
    
    def _generate_template_review(self, product: Dict, style: str) -> str:
        """สร้างรีวิวจากเทมเพลต"""
        try:
            # เตรียมข้อมูลสำหรับเทมเพลต
            template_data = self._prepare_template_data(product)
            
            # เลือกเทมเพลตแบบสุ่ม
            templates = self.review_templates.get(style, self.review_templates['medium'])
            template = random.choice(templates)
            
            # เพิ่มข้อมูลพิเศษตามสไตล์
            if style == 'medium':
                template_data['highlights'] = self._generate_highlights(product)
            elif style == 'long':
                template_data['detailed_review'] = self._generate_detailed_review(product)
                template_data['features'] = self._generate_features_list(product)
            
            return template.format(**template_data)
            
        except Exception as e:
            self.logger.error(f"Template review generation failed: {e}")
            return self._generate_basic_review(product)
    
    def _prepare_template_data(self, product: Dict) -> Dict:
        """เตรียมข้อมูลสำหรับเทมเพลต"""
        commission = product.get('commission_amount', 0)
        price = product.get('price', 0)
        rating = product.get('rating', 0)
        
        return {
            'product_name': product.get('product_name', 'สินค้า'),
            'price': price,
            'shop_name': product.get('shop_name', 'ร้านค้า'),
            'rating': f"{rating:.1f}" if rating > 0 else "ไม่ระบุ",
            'sold_count': product.get('sold_count', 0),
            'commission': commission,
            'commission_rate': product.get('commission_rate', 0),
            'category': product.get('category', 'สินค้า'),
            'description': product.get('description', '')[:100] + '...' if len(product.get('description', '')) > 100 else product.get('description', ''),
            'offer_link': product.get('offer_link', '#'),
            'product_link': product.get('product_link', '#')
        }
    
    def _generate_highlights(self, product: Dict) -> str:
        """สร้างจุดเด่นของสินค้า"""
        highlights = []
        
        # จุดเด่นจากราคา
        price = product.get('price', 0)
        if price > 10000:
            highlights.append("💎 คุณภาพพรีเมียม")
        elif price < 1000:
            highlights.append("💰 ราคาประหยัด")
        else:
            highlights.append("⚖️ ราคาสมเหตุสมผล")
        
        # จุดเด่นจากยอดขาย
        sold_count = product.get('sold_count', 0)
        if sold_count > 100:
            highlights.append("🔥 ขายดี")
        elif sold_count > 50:
            highlights.append("👍 ได้รับความนิยม")
        
        # จุดเด่นจากเรตติ้ง
        rating = product.get('rating', 0)
        if rating >= 4.5:
            highlights.append("⭐ เรตติ้งสูง")
        elif rating >= 4.0:
            highlights.append("✨ คุณภาพดี")
        
        # จุดเด่นจากหมวดหมู่
        category = product.get('category', '')
        if category in self.category_descriptions:
            highlights.append(f"📱 {self.category_descriptions[category]}")
        
        return " | ".join(highlights) if highlights else "✨ สินค้าคุณภาพ"
    
    def _generate_detailed_review(self, product: Dict) -> str:
        """สร้างรีวิวละเอียด"""
        review_parts = []
        
        # เริ่มต้นด้วยคำชม
        adj = random.choice(self.positive_adjectives)
        review_parts.append(f"สินค้านี้{adj}มากค่ะ!")
        
        # อธิบายจากหมวดหมู่
        category = product.get('category', '')
        if category in self.category_descriptions:
            review_parts.append(f"เป็นสินค้าในหมวด{category} ที่{self.category_descriptions[category]}")
        
        # ข้อมูลจากคำอธิบาย
        description = product.get('description', '')
        if description and len(description) > 20:
            review_parts.append(description[:150] + ('...' if len(description) > 150 else ''))
        
        # ข้อมูลการขาย
        sold_count = product.get('sold_count', 0)
        if sold_count > 0:
            review_parts.append(f"มีคนซื้อไปแล้ว {sold_count} ชิ้น แสดงว่าได้รับความไว้วางใจ")
        
        return " ".join(review_parts)
    
    def _generate_features_list(self, product: Dict) -> str:
        """สร้างรายการคุณสมบัติ"""
        features = []
        
        # คุณสมบัติจากราคา
        price = product.get('price', 0)
        if price > 10000:
            features.append("• คุณภาพระดับพรีเมียม")
        features.append(f"• ราคาเพียง {price:,.0f} บาท")
        
        # คุณสมบัติจากร้าน
        shop_name = product.get('shop_name', '')
        if shop_name:
            features.append(f"• จาก {shop_name} ร้านที่เชื่อถือได้")
        
        # คุณสมบัติจากเรตติ้ง
        rating = product.get('rating', 0)
        if rating > 0:
            features.append(f"• เรตติ้ง {rating:.1f}/5.0 ดาว")
        
        # คุณสมบัติจากการขาย
        sold_count = product.get('sold_count', 0)
        if sold_count > 0:
            features.append(f"• ขายแล้ว {sold_count} ชิ้น")
        
        return "\n".join(features)
    
    def _generate_basic_review(self, product: Dict) -> str:
        """สร้างรีวิวพื้นฐาน (fallback)"""
        name = product.get('product_name', 'สินค้า')
        price = product.get('price', 0)
        commission = product.get('commission_amount', 0)
        link = product.get('offer_link', '#')
        
        return f"""🛍️ {name}
💰 ราคา: {price:,.0f} บาท
💸 คอมมิชชัน: {commission:,.0f} บาท
🛒 {link}

#รีวิวสินค้า #affiliate #คุ้มค่า"""
    
    def _format_product_info(self, product: Dict) -> str:
        """จัดรูปแบบข้อมูลสินค้าสำหรับ AI"""
        return f"""
        ชื่อ: {product.get('product_name', '')}
        ราคา: {product.get('price', 0):,.0f} บาท
        ร้าน: {product.get('shop_name', '')}
        หมวดหมู่: {product.get('category', '')}
        คำอธิบาย: {product.get('description', '')}
        เรตติ้ง: {product.get('rating', 0)}/5.0
        ขายแล้ว: {product.get('sold_count', 0)} ชิ้น
        คอมมิชชัน: {product.get('commission_rate', 0)}% = {product.get('commission_amount', 0):,.0f} บาท
        ลิงก์สินค้า: {product.get('product_link', '')}
        ลิงก์ Affiliate: {product.get('offer_link', '')}
        """
    
    def generate_multiple_reviews(self, product: Dict, count: int = 3) -> List[str]:
        """สร้างรีวิวหลายแบบ"""
        reviews = []
        styles = ['short', 'medium', 'long']
        
        for i in range(count):
            style = styles[i % len(styles)]
            review = self.generate_review(product, style)
            reviews.append(review)
        
        return reviews
    
    def get_review_stats(self, reviews: List[str]) -> Dict:
        """วิเคราะห์สถิติรีวิว"""
        if not reviews:
            return {}
        
        total_chars = sum(len(review) for review in reviews)
        total_lines = sum(review.count('\n') + 1 for review in reviews)
        
        return {
            'total_reviews': len(reviews),
            'avg_length': total_chars / len(reviews),
            'avg_lines': total_lines / len(reviews),
            'total_chars': total_chars,
            'shortest': min(len(review) for review in reviews),
            'longest': max(len(review) for review in reviews)
        }

# สร้าง instance สำหรับใช้งาน
review_generator = ReviewGenerator()