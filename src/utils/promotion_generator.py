"""
Promotion Generator สำหรับสร้างคำโปรโมตสินค้าอัตโนมัติ
ที่ดูเป็นธรรมชาติและน่าเชื่อถือ (ไม่เหมือนขายของ)
"""

import random
from typing import Dict, List
from datetime import datetime

class PromotionGenerator:
    """คลาสสำหรับสร้างคำโปรโมตสินค้าอัตโนมัติ"""
    
    def __init__(self):
        # คำนำหน้าที่เป็นธรรมชาติ
        self.natural_openings = [
            "เพิ่งเจอสินค้าดีๆ มาแชร์",
            "หาซื้อของอยู่เจอเจ้านี้",
            "แนะนำสินค้าที่ใช้ดีจริง",
            "เจอของดีมาบอกต่อ",
            "สินค้าที่หลายคนถาม",
            "มีคนถามเรื่องสินค้านี้บอกกันค่ะ",
            "รีวิวสินค้าที่กำลังฮิต",
            "แชร์ของดีที่เพิ่งค้นพบ"
        ]
        
        # คำบรรยายข้อดี (เฉพาะเจาะจง)
        self.product_benefits = {
            'อาหารแมว': [
                "แมวกินแล้วขนเงางาม",
                "ช่วยให้ระบบย่อยอาหารดีขึ้น", 
                "มีโปรตีนสูง เหมาะกับแมวทุกวัย",
                "ไม่มีสีผสมอาหาร ปลอดภัย",
                "แมวชอบกินไม่เหลือ",
                "ช่วยเสริมภูมิคุ้มกัน"
            ],
            'สุขภาพ': [
                "ช่วยเสริมภูมิคุ้มกันได้ดี",
                "รับประทานง่าย ไม่มีรสขม",
                "เห็นผลชัดเจนภายใน 2 สัปดาห์",
                "ไม่มีผลข้างเคียง",
                "วิตามินครบถ้วน"
            ],
            'ความงาม': [
                "ผิวเนียนใสขึ้นเห็นได้ชัด",
                "ไม่ทำให้ผิวแพ้ แม้ผิวแพ้ง่าย",
                "ซึมซาบเร็ว ไม่เหนียวเหนอะหนะ",
                "กลิ่นหอมอ่อนๆ ไม่ฉุน",
                "ใช้แล้วผิวชุ่มชื้น"
            ],
            'อิเล็กทรอนิกส์': [
                "ใช้งานง่าย ใครๆ ก็ทำได้",
                "คุณภาพดี ใช้ได้นาน",
                "ประหยัดพลังงาน",
                "ตอบสนองเร็ว ไม่ค้าง",
                "การันตีศูนย์ไทย"
            ]
        }
        
        # คำอธิบายราคา (เป็นธรรมชาติ)
        self.price_phrases = [
            "ราคาก็ไม่แพงเกินไป",
            "ราคาคุ้มค่ากับคุณภาพ",
            "เมื่อเทียบกับที่อื่นถือว่าโอเค",
            "ราคานี้ถือว่าสมเหตุสมผล",
            "ในราคาที่เข้าถึงได้",
            "คิดว่าราคาแฟร์พอสมควร"
        ]
        
        # คำอธิบายร้านค้า
        self.shop_credibility = [
            "ร้านนี้ขายดี มีคนรีวิวเยอะ",
            "เจ้าของร้านตอบเร็ว บริการดี",
            "ร้านใหญ่ น่าเชื่อถือ",
            "ส่งของไว มาครบตามที่สั่ง",
            "ร้านมีคนซื้อเยอะ คงไม่ผิดหวัง"
        ]
        
        # คำปิดท้าย (เป็นธรรมชาติ)
        self.natural_endings = [
            "ใครสนใจลองดูนะคะ",
            "แชร์ให้เพื่อนๆ ที่หาซื้ออยู่",
            "หาซื้ออยู่ลองดูเจ้านี้",
            "ใครกำลังหาอยู่แนะนำเลย",
            "มีประโยชน์ก็เอาไปใช้กันนะ",
            "หวังว่าจะช่วยได้นะคะ"
        ]
        
        # Hashtags ธรรมชาติ
        self.natural_hashtags = [
            "#รีวิวของดี", "#แชร์ของดี", "#ของดีบอกต่อ",
            "#ใช้ดีแนะนำ", "#คุณภาพดี", "#ราคาดี",
            "#shopee", "#ช้อปปี้", "#ซื้อของออนไลน์"
        ]

    def generate_promotion(self, product: Dict, style: str = "casual") -> str:
        """สร้างคำโปรโมตสินค้า
        
        Args:
            product: ข้อมูลสินค้า
            style: สไตล์ - casual, enthusiastic, informative
        """
        try:
            product_name = product.get('product_name', '')
            price = float(product.get('price', 0))
            shop_name = product.get('shop_name', '')
            rating = float(product.get('rating', 0))
            sold_count = int(product.get('sold_count', 0))
            category = product.get('category', '')
            
            # เลือกองค์ประกอบตามสไตล์
            if style == "casual":
                return self._generate_casual_promotion(product_name, price, shop_name, rating, sold_count, category)
            elif style == "enthusiastic":
                return self._generate_enthusiastic_promotion(product_name, price, shop_name, rating, sold_count, category)
            else:  # informative
                return self._generate_informative_promotion(product_name, price, shop_name, rating, sold_count, category)
                
        except Exception as e:
            return f"แนะนำ {product.get('product_name', 'สินค้าดีๆ')} \nราคา {product.get('price', 0)} บาท\nใครสนใจลองดูนะคะ"

    def _generate_casual_promotion(self, name: str, price: float, shop: str, rating: float, sold: int, category: str) -> str:
        """สร้างโปรโมตแบบสบายๆ เป็นธรรมชาติ"""
        
        # เลือกคำเปิด
        opening = random.choice(self.natural_openings)
        
        # สร้างชื่อสินค้า (ย่อให้อ่านง่าย)
        short_name = self._shorten_product_name(name)
        
        # เลือกข้อดี
        benefits = self._get_category_benefits(category)
        benefit = random.choice(benefits) if benefits else "คุณภาพดี ใช้ได้จริง"
        
        # คำอธิบายราคา
        price_desc = random.choice(self.price_phrases)
        
        # ข้อมูลร้านค้า (ถ้ามี)
        shop_desc = ""
        if shop:
            shop_desc = f"\nร้าน {shop} " + random.choice(self.shop_credibility)
        
        # สถิติ (ถ้ามี)
        stats = ""
        if sold > 1000:
            stats = f"\nขายไปแล้ว {self._format_sold_count(sold)} "
        if rating >= 4.0:
            stars = "⭐" * int(rating)
            stats += f" {stars} ({rating})"
        
        # คำปิดท้าย
        ending = random.choice(self.natural_endings)
        
        # Hashtags
        hashtags = random.sample(self.natural_hashtags, 3)
        hashtag_str = " ".join(hashtags)
        
        promotion = f"""{opening} 😊

📦 {short_name}
💰 {price:,.0f} บาท - {price_desc}
✨ {benefit}{shop_desc}{stats}

{ending}

{hashtag_str}"""
        
        return promotion

    def _generate_enthusiastic_promotion(self, name: str, price: float, shop: str, rating: float, sold: int, category: str) -> str:
        """สร้างโปรโมตแบบกระตือรือร้น"""
        
        short_name = self._shorten_product_name(name)
        benefits = self._get_category_benefits(category)
        
        promotion = f"""🔥 เจอของดีมาแชร์! 🔥

✨ {short_name} ✨
💸 ราคาเพียง {price:,.0f} บาท!

👍 {random.choice(benefits) if benefits else 'คุณภาพเกินราคา!'}
🏪 ร้าน {shop} มีคนซื้อเยอะมาก!"""

        if sold > 5000:
            promotion += f"\n🔥 ขายดีมาก! ไปแล้วกว่า {self._format_sold_count(sold)}"
        
        if rating >= 4.5:
            promotion += f"\n⭐⭐⭐⭐⭐ คะแนน {rating} ดาว!"

        promotion += f"""

🛒 ใครกำลังหาอยู่ต้องลอง!
💕 รับรองไม่ผิดหวัง!

{' '.join(random.sample(self.natural_hashtags, 4))}"""
        
        return promotion

    def _generate_informative_promotion(self, name: str, price: float, shop: str, rating: float, sold: int, category: str) -> str:
        """สร้างโปรโมตแบบให้ข้อมูล"""
        
        short_name = self._shorten_product_name(name)
        benefits = self._get_category_benefits(category)
        
        promotion = f"""📋 รีวิวสินค้า: {short_name}

📊 ข้อมูลสินค้า:
• ราคา: {price:,.0f} บาท
• ร้านค้า: {shop}"""

        if rating > 0:
            promotion += f"\n• คะแนนรีวิว: {rating}/5.0 ⭐"
        
        if sold > 100:
            promotion += f"\n• ยอดขาย: {self._format_sold_count(sold)} ชิ้น"

        if benefits:
            promotion += f"\n\n✅ จุดเด่น:\n• {random.choice(benefits)}"
            if len(benefits) > 1:
                promotion += f"\n• {random.choice([b for b in benefits if b != benefits[0]])}"

        promotion += f"\n\n📝 สรุป: {random.choice(self.price_phrases)}"
        promotion += f"\n{random.choice(self.natural_endings)}"
        
        return promotion

    def _shorten_product_name(self, name: str) -> str:
        """ย่อชื่อสินค้าให้อ่านง่าย"""
        if len(name) <= 50:
            return name
            
        # ลบข้อความที่ไม่จำเป็น
        name = name.replace('【', '').replace('】', '')
        name = name.replace('✨', '').replace('🔥', '')
        
        # แยกคำและเลือกคำสำคัญ
        words = name.split()
        if len(words) <= 8:
            return name
            
        # เก็บคำสำคัญด้านหน้า
        important_words = words[:6]
        return ' '.join(important_words) + '...'

    def _get_category_benefits(self, category: str) -> List[str]:
        """เลือกข้อดีตามหมวดหมู่"""
        category_map = {
            'สัตว์เลี้ยง': 'อาหารแมว',
            'ความงาม': 'ความงาม',
            'สุขภาพ': 'สุขภาพ',
            'อิเล็กทรอนิกส์': 'อิเล็กทรอนิกส์'
        }
        
        benefit_key = category_map.get(category, 'อาหารแมว')
        return self.product_benefits.get(benefit_key, self.product_benefits['อาหารแมว'])

    def _format_sold_count(self, count: int) -> str:
        """แปลงจำนวนขายให้อ่านง่าย"""
        if count >= 10000:
            return f"{count//1000}k+"
        elif count >= 1000:
            return f"{count//100}00+"
        else:
            return str(count)

    def generate_multiple_promotions(self, product: Dict, count: int = 3) -> List[str]:
        """สร้างคำโปรโมตหลายแบบ"""
        styles = ["casual", "enthusiastic", "informative"]
        promotions = []
        
        for i in range(count):
            style = styles[i % len(styles)]
            promotion = self.generate_promotion(product, style)
            promotions.append(promotion)
            
        return promotions