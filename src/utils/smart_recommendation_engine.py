"""
📁 Smart Recommendation Engine
ระบบแนะนำสินค้าอัจฉริยะตามความสนใจและพฤติกรรม
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import logging

class SmartRecommendationEngine:
    """เครื่องมือแนะนำสินค้าอัจฉริยะ"""
    
    def __init__(self, db_instance=None):
        self.db = db_instance
        self.logger = logging.getLogger(__name__)
        
        # เก็บประวัติการค้นหาของผู้ใช้
        self.user_interests = {}
        
        # กำหนดน้ำหนักความสนใจ
        self.interest_weights = {
            'search_count': 3,      # ค้นหาหลายครั้ง
            'category_view': 2,     # ดูหมวดหมู่
            'product_click': 4,     # คลิกดูสินค้า
            'recent_activity': 2    # กิจกรรมล่าสุด
        }
        
        # หมวดหมู่และคำสำคัญที่เกี่ยวข้อง
        self.category_keywords = {
            'โทรศัพท์มือถือ': ['เทคโนโลยี', 'ไฮเทค', 'การสื่อสาร', 'สมาร์ท'],
            'ความงาม': ['สกินแคร์', 'แต่งหน้า', 'ผิวสวย', 'ความมั่นใจ'],
            'แฟชั่น': ['สไตล์', 'เทรนด์', 'แต่งตัว', 'ลุค'],
            'เกมมิ่ง': ['เกม', 'บันเทิง', 'เทคโนโลยี', 'ความสนุก'],
            'สัตว์เลี้ยง': ['ดูแลสัตว์', 'ความรัก', 'สุขภาพสัตว์'],
            'สุขภาพ': ['ดูแลสุขภาพ', 'วิตามิน', 'ออกกำลังกาย', 'สุขภาพดี'],
            'กีฬา': ['ออกกำลังกาย', 'ฟิตเนส', 'สุขภาพ', 'ความแข็งแรง']
        }
    
    def track_user_interest(self, user_id: str, action: str, category: str = None, product_id: str = None):
        """บันทึกความสนใจของผู้ใช้"""
        if user_id not in self.user_interests:
            self.user_interests[user_id] = {
                'categories': {},
                'last_activity': datetime.now(),
                'total_searches': 0
            }
        
        user_data = self.user_interests[user_id]
        user_data['last_activity'] = datetime.now()
        
        if category:
            if category not in user_data['categories']:
                user_data['categories'][category] = {
                    'search_count': 0,
                    'view_count': 0,
                    'click_count': 0,
                    'last_seen': datetime.now()
                }
            
            cat_data = user_data['categories'][category]
            cat_data['last_seen'] = datetime.now()
            
            if action == 'search':
                cat_data['search_count'] += 1
                user_data['total_searches'] += 1
            elif action == 'view':
                cat_data['view_count'] += 1
            elif action == 'click':
                cat_data['click_count'] += 1
    
    def get_user_interest_score(self, user_id: str, category: str) -> float:
        """คำนวณคะแนนความสนใจของผู้ใช้ในหมวดหมู่"""
        if user_id not in self.user_interests:
            return 0.0
        
        user_data = self.user_interests[user_id]
        if category not in user_data['categories']:
            return 0.0
        
        cat_data = user_data['categories'][category]
        
        # คำนวณคะแนนจากการกระทำต่างๆ
        score = (
            cat_data['search_count'] * self.interest_weights['search_count'] +
            cat_data['view_count'] * self.interest_weights['category_view'] +
            cat_data['click_count'] * self.interest_weights['product_click']
        )
        
        # เพิ่มคะแนนสำหรับกิจกรรมล่าสุด (ใน 7 วันที่ผ่านมา)
        days_ago = (datetime.now() - cat_data['last_seen']).days
        if days_ago <= 7:
            recent_bonus = self.interest_weights['recent_activity'] * (8 - days_ago) / 7
            score += recent_bonus
        
        return score
    
    def get_personalized_recommendations(self, user_id: str, limit: int = 5) -> List[Dict]:
        """แนะนำสินค้าตามความสนใจส่วนบุคคล"""
        if not self.db:
            return []
        
        try:
            # หาหมวดหมู่ที่ผู้ใช้สนใจ
            interest_scores = {}
            for category in self.category_keywords.keys():
                score = self.get_user_interest_score(user_id, category)
                if score > 0:
                    interest_scores[category] = score
            
            if not interest_scores:
                # ถ้าไม่มีประวัติ แนะนำสินค้าขายดี
                return self._get_trending_products(limit)
            
            # เรียงตามคะแนนความสนใจ
            sorted_interests = sorted(interest_scores.items(), key=lambda x: x[1], reverse=True)
            
            recommendations = []
            products_per_category = max(1, limit // len(sorted_interests))
            
            for category, score in sorted_interests:
                # ค้นหาสินค้าในหมวดหมู่ที่สนใจ
                category_products = self.db.search_products(
                    query="", 
                    category=category, 
                    limit=products_per_category,
                    order_by='rating'
                )
                
                products = category_products.get('products', [])
                for product in products:
                    product['recommendation_score'] = score
                    product['recommendation_reason'] = f"ตามความสนใจใน{category}"
                    recommendations.append(product)
                
                if len(recommendations) >= limit:
                    break
            
            return recommendations[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting personalized recommendations: {e}")
            return self._get_trending_products(limit)
    
    def get_similar_products(self, product_id: str, limit: int = 3) -> List[Dict]:
        """แนะนำสินค้าที่คล้ายกัน"""
        if not self.db:
            return []
        
        try:
            # ดึงข้อมูลสินค้าต้นฉบับ
            product = self.db.get_product_by_code(product_id)
            if not product:
                return []
            
            category = product.get('category', '')
            price = product.get('price', 0)
            
            # หาสินค้าในหมวดเดียวกันที่ราคาใกล้เคียง
            price_range_min = price * 0.7  # -30%
            price_range_max = price * 1.3  # +30%
            
            similar_products = self.db.search_products(
                query="",
                category=category,
                min_price=price_range_min,
                max_price=price_range_max,
                limit=limit + 1,  # +1 เพื่อไม่รวมสินค้าตัวเอง
                order_by='rating'
            )
            
            products = similar_products.get('products', [])
            # กรองสินค้าตัวเองออก
            filtered_products = [p for p in products if p.get('product_code') != product_id]
            
            for product in filtered_products:
                product['recommendation_reason'] = "สินค้าที่คล้ายกัน"
            
            return filtered_products[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting similar products: {e}")
            return []
    
    def get_trending_products(self, limit: int = 5) -> List[Dict]:
        """แนะนำสินค้าที่กำลังมาแรง"""
        return self._get_trending_products(limit)
    
    def _get_trending_products(self, limit: int) -> List[Dict]:
        """ดึงสินค้าที่กำลังมาแรง (ขายดี + คะแนนสูง)"""
        if not self.db:
            return []
        
        try:
            # ดึงสินค้าขายดีที่มีคะแนนสูง
            trending = self.db.search_products(
                query="",
                limit=limit,
                order_by='sold_count'  # เรียงตามยอดขาย
            )
            
            products = trending.get('products', [])
            
            # คำนวณคะแนน trending (ยอดขาย + คะแนนรีวิว)
            for product in products:
                sold_count = product.get('sold_count', 0)
                rating = product.get('rating', 0)
                trending_score = (sold_count * 0.7) + (rating * 100 * 0.3)
                product['trending_score'] = trending_score
                product['recommendation_reason'] = "สินค้าที่กำลังมาแรง"
            
            # เรียงใหม่ตามคะแนน trending
            products.sort(key=lambda x: x.get('trending_score', 0), reverse=True)
            
            return products[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting trending products: {e}")
            return []
    
    def get_category_recommendations(self, category: str, limit: int = 5) -> List[Dict]:
        """แนะนำสินค้าในหมวดหมู่เฉพาะ"""
        if not self.db:
            return []
        
        try:
            # ดึงสินค้าในหมวดหมู่ เรียงตามคะแนนรีวิว
            category_products = self.db.search_products(
                query="",
                category=category,
                limit=limit,
                order_by='rating'
            )
            
            products = category_products.get('products', [])
            
            for product in products:
                product['recommendation_reason'] = f"แนะนำใน{category}"
            
            return products
            
        except Exception as e:
            self.logger.error(f"Error getting category recommendations: {e}")
            return []
    
    def generate_recommendation_message(self, recommendations: List[Dict], user_id: str = None) -> str:
        """สร้างข้อความแนะนำสินค้า"""
        if not recommendations:
            return "🤖 ขออภัย ไม่มีสินค้าแนะนำในขณะนี้"
        
        # ข้อความต้อนรับ
        headers = [
            "🎯 สินค้าแนะนำสำหรับคุณ",
            "⭐ สินค้าที่น่าสนใจ",
            "🔥 Hot Items ที่คุณไม่ควรพลาด"
        ]
        
        message = f"{headers[len(recommendations) % len(headers)]}\\n\\n"
        
        # แสดงรายการสินค้า
        for i, product in enumerate(recommendations, 1):
            name = product.get('product_name', 'N/A')
            price = product.get('price', 0)
            rating = product.get('rating', 0)
            reason = product.get('recommendation_reason', '')
            
            message += f"{i}. {name}\\n"
            message += f"   💰 {price:,.0f} บาท"
            if rating > 0:
                message += f" | ⭐ {rating:.1f}"
            if reason:
                message += f"\\n   🎯 {reason}"
            message += "\\n\\n"
        
        return message