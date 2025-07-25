"""
📁 src/utils/ai_search.py
🎯 AI-Enhanced Search สำหรับ Affiliate Product Review Bot
ปรับปรุงการค้นหาสินค้าด้วยเทคนิค AI
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from difflib import SequenceMatcher

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from ..config import config

class AISearchEngine:
    """คลาสสำหรับการค้นหาสินค้าแบบ AI"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        
        # คำพ้องความหมายสำหรับสินค้า
        self.synonyms = {
            'โทรศัพท์': ['phone', 'มือถือ', 'smartphone', 'iphone', 'android'],
            'คอมพิวเตอร์': ['computer', 'pc', 'laptop', 'แล็ปท็อป', 'macbook'],
            'เสื้อผ้า': ['fashion', 'แฟชั่น', 'เสื้อ', 'กางเกง', 'ชุด'],
            'ความงาม': ['beauty', 'cosmetic', 'เครื่องสำอาง', 'ครีม', 'ลิปสติก'],
            'สุขภาพ': ['health', 'อาหารเสริม', 'วิตามิน', 'ยา', 'supple'],
            'รองเท้า': ['shoes', 'sneaker', 'รองเท้าผ้าใบ', 'รองเท้าแฟชั่น'],
            'กระเป๋า': ['bag', 'handbag', 'backpack', 'เป้', 'clutch'],
            'นาฬิกา': ['watch', 'clock', 'smartwatch', 'apple watch'],
            'หูฟัง': ['headphone', 'earphone', 'airpods', 'wireless'],
            'อาหาร': ['food', 'snack', 'ขนม', 'อาหารเสริม']
        }
        
        # แบรนด์ที่รู้จัก
        self.brands = {
            'apple': ['iphone', 'ipad', 'macbook', 'apple watch', 'airpods'],
            'samsung': ['galaxy', 'note', 'samsung'],
            'nike': ['nike', 'air', 'jordan'],
            'adidas': ['adidas', 'three stripes'],
            'uniqlo': ['uniqlo', 'ยูนิโคล่']
        }
        
        # หมวดหมู่และคำเกี่ยวข้อง
        self.categories = {
            'อิเล็กทรอนิกส์': ['electronics', 'gadget', 'tech', 'device'],
            'แฟชั่น': ['fashion', 'style', 'clothing', 'wear'],
            'ความงาม': ['beauty', 'cosmetic', 'skincare', 'makeup'],
            'สุขภาพ': ['health', 'wellness', 'supplement', 'vitamin'],
            'บ้านและสวน': ['home', 'garden', 'furniture', 'decoration'],
            'กีฬา': ['sport', 'fitness', 'exercise', 'gym'],
            'หนังสือ': ['book', 'ebook', 'novel', 'education'],
            'เด็กและของเล่น': ['kids', 'toys', 'children', 'baby'],
            'อาหาร': ['food', 'snack', 'beverage', 'organic']
        }
        
        # ตั้งค่า OpenAI client
        if OPENAI_AVAILABLE and config.OPENAI_API_KEY:
            try:
                openai.api_key = config.OPENAI_API_KEY
                self.client = openai
                self.logger.info("OpenAI client initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")
        else:
            self.logger.warning("OpenAI not available - using fallback search")
    
    def enhanced_product_search(self, query: str, products: List[Dict], limit: int = 10) -> List[Dict]:
        """การค้นหาสินค้าแบบ AI ที่ปรับปรุง"""
        try:
            self.logger.debug(f"AI enhanced search for: '{query}'")
            
            query_processed = self._preprocess_query(query)
            scored_products = []
            
            for product in products:
                score = self._calculate_product_relevance_score(query_processed, product)
                if score > 0:
                    scored_products.append((score, product))
            
            # เรียงตามคะแนนจากมากไปน้อย
            scored_products.sort(key=lambda x: x[0], reverse=True)
            
            self.logger.debug(f"AI search found {len(scored_products)} relevant products")
            
            return [product for score, product in scored_products[:limit]]
            
        except Exception as e:
            self.logger.error(f"Enhanced search failed: {e}")
            return products[:limit]  # Fallback to original list
    
    def _preprocess_query(self, query: str) -> Dict:
        """ประมวลผลคำค้นหาเบื้องต้น"""
        query_lower = query.lower().strip()
        
        # ขยายคำค้นหาด้วย synonyms
        expanded_terms = [query_lower]
        
        for thai_word, synonyms in self.synonyms.items():
            if thai_word in query_lower:
                expanded_terms.extend(synonyms)
        
        # ตรวจสอบแบรนด์
        detected_brands = []
        for brand, keywords in self.brands.items():
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    detected_brands.append(brand)
                    expanded_terms.extend(keywords)
                    break
        
        # ตรวจสอบหมวดหมู่
        detected_categories = []
        for category, keywords in self.categories.items():
            if category in query_lower:
                detected_categories.append(category)
                expanded_terms.extend(keywords)
            else:
                for keyword in keywords:
                    if keyword.lower() in query_lower:
                        detected_categories.append(category)
                        expanded_terms.extend([category])
                        break
        
        # แยกคำด้วยช่องว่าง
        words = query_lower.split()
        
        # ตรวจสอบช่วงราคา
        price_range = self._extract_price_range(query_lower)
        
        return {
            'original': query_lower,
            'expanded_terms': list(set(expanded_terms)),  # ลบคำซ้ำ
            'words': words,
            'brands': detected_brands,
            'categories': detected_categories,
            'price_range': price_range,
            'has_numbers': bool(re.search(r'\d', query_lower))
        }
    
    def _extract_price_range(self, query: str) -> Optional[Dict]:
        """แยกช่วงราคาจากคำค้นหา"""
        # รูปแบบต่างๆ ของการระบุราคา
        patterns = [
            (r'ราคา.*?(\d+).*?(\d+)', 'range'),
            (r'ไม่เกิน.*?(\d+)', 'max'),
            (r'มากกว่า.*?(\d+)', 'min'),
            (r'ประมาณ.*?(\d+)', 'around'),
            (r'(\d+).*?บาท', 'around')
        ]
        
        for pattern, price_type in patterns:
            match = re.search(pattern, query)
            if match:
                if price_type == 'range':
                    return {
                        'min': int(match.group(1)),
                        'max': int(match.group(2))
                    }
                elif price_type == 'max':
                    return {'max': int(match.group(1))}
                elif price_type == 'min':
                    return {'min': int(match.group(1))}
                elif price_type == 'around':
                    price = int(match.group(1))
                    return {
                        'min': price * 0.8,
                        'max': price * 1.2
                    }
        
        return None
    
    def _calculate_product_relevance_score(self, query_info: Dict, product: Dict) -> float:
        """คำนวณคะแนนความเกี่ยวข้องสำหรับสินค้า"""
        score = 0.0
        query_original = query_info['original']
        expanded_terms = query_info['expanded_terms']
        
        # ข้อมูลของสินค้า
        product_name = product.get('product_name', '').lower()
        product_code = product.get('product_code', '').lower()
        description = product.get('description', '').lower()
        category = product.get('category', '').lower()
        shop_name = product.get('shop_name', '').lower()
        
        # 1. Exact match ในชื่อสินค้า (คะแนนสูงสุด)
        if query_original == product_name:
            score += 100
        elif query_original in product_name:
            score += 80
        
        # 2. Fuzzy match ในชื่อสินค้า
        name_similarity = SequenceMatcher(None, query_original, product_name).ratio()
        score += name_similarity * 70
        
        # 3. ค้นหาในรหัสสินค้า
        if query_original == product_code:
            score += 90
        elif query_original in product_code:
            score += 60
        
        # 4. ค้นหาในคำอธิบาย
        if query_original in description:
            score += 50
        
        desc_similarity = SequenceMatcher(None, query_original, description).ratio()
        score += desc_similarity * 30
        
        # 5. ค้นหาในหมวดหมู่
        if query_original in category:
            score += 70
        
        # 6. ค้นหาในชื่อร้าน
        if query_original in shop_name:
            score += 40
        
        # 7. ค้นหาใน expanded terms
        for term in expanded_terms[1:]:  # ข้าม original term
            term_lower = term.lower()
            if term_lower in product_name:
                score += 45
            if term_lower in description:
                score += 35
            if term_lower in category:
                score += 40
        
        # 8. Brand matching
        if query_info['brands']:
            for brand in query_info['brands']:
                if brand.lower() in product_name or brand.lower() in description:
                    score += 60
        
        # 9. Category matching
        if query_info['categories']:
            for cat in query_info['categories']:
                if cat.lower() in category:
                    score += 50
        
        # 10. Price range matching
        if query_info['price_range']:
            product_price = product.get('price', 0)
            price_range = query_info['price_range']
            
            if 'min' in price_range and 'max' in price_range:
                if price_range['min'] <= product_price <= price_range['max']:
                    score += 30
            elif 'max' in price_range:
                if product_price <= price_range['max']:
                    score += 25
            elif 'min' in price_range:
                if product_price >= price_range['min']:
                    score += 25
        
        # 11. Word-level matching
        query_words = query_info['words']
        if len(query_words) > 1:
            word_matches = 0
            total_text = f"{product_name} {description} {category}".lower()
            
            for word in query_words:
                if word in total_text:
                    word_matches += 1
            
            word_ratio = word_matches / len(query_words)
            score += word_ratio * 25
        
        # 12. Bonus สำหรับคุณภาพสินค้า
        rating = product.get('rating', 0)
        if rating >= 4.5:
            score += 10
        elif rating >= 4.0:
            score += 5
        
        sold_count = product.get('sold_count', 0)
        if sold_count > 100:
            score += 8
        elif sold_count > 50:
            score += 4
        elif sold_count > 10:
            score += 2
        
        return score
    
    def suggest_product_alternatives(self, query: str, products: List[Dict], limit: int = 5) -> List[str]:
        """แนะนำคำค้นหาทางเลือกสำหรับสินค้า"""
        suggestions = set()
        query_lower = query.lower()
        
        # หาคำที่คล้ายกันจาก synonyms
        for thai_word, synonyms in self.synonyms.items():
            if thai_word in query_lower:
                suggestions.update(synonyms[:2])  # เอาแค่ 2 คำแรก
        
        # หาคำที่คล้ายกันจากข้อมูลสินค้า
        for product in products[:20]:  # ตรวจแค่ 20 รายการแรก
            # คำในชื่อสินค้าที่คล้ายกัน
            product_words = product.get('product_name', '').split()
            for word in product_words:
                if len(word) > 2 and SequenceMatcher(None, query_lower, word.lower()).ratio() > 0.6:
                    suggestions.add(word)
            
            # หมวดหมู่ที่เกี่ยวข้อง
            category = product.get('category', '')
            if category and len(category) > 1:
                suggestions.add(category)
        
        # เพิ่มหมวดหมู่ยอดนิยม
        popular_categories = ['อิเล็กทรอนิกส์', 'แฟชั่น', 'ความงาม', 'สุขภาพ']
        suggestions.update(popular_categories)
        
        return list(suggestions)[:limit]
    
    def get_search_insights(self, query: str, products: List[Dict]) -> Dict:
        """วิเคราะห์ผลการค้นหาสินค้า"""
        query_info = self._preprocess_query(query)
        
        return {
            'query_length': len(query),
            'has_thai': bool(re.search(r'[ก-๙]', query)),
            'has_english': bool(re.search(r'[a-zA-Z]', query)),
            'has_numbers': query_info['has_numbers'],
            'detected_brands': query_info['brands'],
            'detected_categories': query_info['categories'],
            'price_range': query_info['price_range'],
            'results_count': len(products),
            'expanded_terms_count': len(query_info['expanded_terms'])
        }

# สร้าง instance สำหรับใช้งาน
ai_search = AISearchEngine()