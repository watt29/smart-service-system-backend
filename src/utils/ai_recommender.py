"""
🤖 AI Product Recommender
ระบบแนะนำสินค้าด้วย AI ตามความสนใจและพฤติกรรมผู้ใช้
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import logging

from .supabase_database import SupabaseDatabase

class AIProductRecommender:
    """คลาสสำหรับระบบแนะนำสินค้าด้วย AI"""
    
    def __init__(self):
        self.db = SupabaseDatabase()
        self.logger = logging.getLogger(__name__)
        
        # คำสำคัญสำหรับการจัดกลุ่มความสนใจ
        self.interest_keywords = {
            'technology': ['มือถือ', 'คอมพิวเตอร์', 'แทบเล็ต', 'หูฟัง', 'ลำโพง', 'กล้อง', 'สมาร์ทวอทช์', 'โทรศัพท์', 'smartphone', 'laptop', 'gadget'],
            'fashion': ['เสื้อ', 'กางเกง', 'รองเท้า', 'กระเป๋า', 'เครื่องประดับ', 'แฟชั่น', 'เสื้อผ้า', 'อุปกรณ์แต่งตัว'],
            'beauty': ['เครื่องสำอาง', 'ผลิตภัณฑ์ผิว', 'น้ำหอม', 'ครีม', 'โลชั่น', 'มาส์ก', 'skincare', 'makeup'],
            'home': ['เฟอร์นิเจอร์', 'ของตะแต่งบ้าน', 'เครื่องใช้ไฟฟ้า', 'หม้อ', 'กระทะ', 'ผ้าปู', 'หมอน', 'โซฟา'],
            'sports': ['อุปกรณ์กีฬา', 'รองเท้าวิ่ง', 'เสื้อกีฬา', 'ดัมเบล', 'โยคะ', 'ฟิตเนส', 'exercise'],
            'books': ['หนังสือ', 'นิยาย', 'การ์ตูน', 'วรรณกรรม', 'book', 'novel'],
            'food': ['อาหาร', 'ขนม', 'เครื่องดื่ม', 'อาหารเสริม', 'วิตามิน', 'snack', 'supplement']
        }
        
        # เก็บประวัติการสื่อสารของผู้ใช้
        self.user_history = defaultdict(list)
        self.user_interests = defaultdict(Counter)
        
    def extract_interests_from_text(self, text: str) -> List[str]:
        """สกัดความสนใจจากข้อความที่ผู้ใช้พิมพ์"""
        text_lower = text.lower()
        interests = []
        
        for category, keywords in self.interest_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    interests.append(category)
                    break
        
        return list(set(interests))  # Remove duplicates
    
    def update_user_interests(self, user_id: str, message: str, search_results: List[Dict] = None):
        """อัปเดตความสนใจของผู้ใช้จากการโต้ตอบ"""
        try:
            # สกัดความสนใจจากข้อความ
            interests = self.extract_interests_from_text(message)
            
            # อัปเดตคะแนนความสนใจ
            for interest in interests:
                self.user_interests[user_id][interest] += 1
                
            # วิเคราะห์จากผลการค้นหา
            if search_results:
                for product in search_results:
                    category_interests = self.extract_interests_from_text(
                        f"{product.get('category', '')} {product.get('product_name', '')}"
                    )
                    for interest in category_interests:
                        self.user_interests[user_id][interest] += 0.5  # น้ำหนักน้อยกว่าการพิมพ์โดยตรง
            
            # บันทึกประวัติ
            self.user_history[user_id].append({
                'timestamp': datetime.now().isoformat(),
                'message': message,
                'interests': interests,
                'search_count': len(search_results) if search_results else 0
            })
            
            # จำกัดประวัติไม่เกิน 50 รายการ
            if len(self.user_history[user_id]) > 50:
                self.user_history[user_id] = self.user_history[user_id][-50:]
                
        except Exception as e:
            self.logger.error(f"Error updating user interests: {e}")
    
    def get_user_top_interests(self, user_id: str, limit: int = 3) -> List[Tuple[str, int]]:
        """ดึงความสนใจอันดับต้น ๆ ของผู้ใช้"""
        if user_id not in self.user_interests:
            return []
        
        return self.user_interests[user_id].most_common(limit)
    
    def recommend_by_interest(self, user_id: str, limit: int = 5) -> List[Dict]:
        """แนะนำสินค้าตามความสนใจของผู้ใช้"""
        recommendations = []
        
        try:
            # ดึงความสนใจของผู้ใช้
            top_interests = self.get_user_top_interests(user_id, limit=3)
            
            if not top_interests:
                # หากไม่มีประวัติ ให้แนะนำสินค้าขายดี
                return self.db.get_top_products_by_metric('sold_count', limit)
            
            # สร้างคำค้นหาจากความสนใจ
            for interest, score in top_interests:
                keywords = self.interest_keywords.get(interest, [])
                if keywords:
                    # ค้นหาสินค้าที่เกี่ยวข้อง
                    search_query = ' '.join(keywords[:3])  # ใช้ 3 คำแรก
                    
                    products = self.db.search_products(
                        query=search_query,
                        limit=3,
                        order_by='rating'  # เรียงตามคะแนน
                    )
                    
                    # เพิ่มคะแนนความเกี่ยวข้อง
                    for product in products.get('data', []):
                        product['recommendation_score'] = score
                        product['recommendation_reason'] = f"ตรงกับความสนใจ: {interest}"
                        recommendations.append(product)
            
            # เรียงตามคะแนนและลบรายการซ้ำ
            seen_codes = set()
            unique_recommendations = []
            
            for product in sorted(recommendations, key=lambda x: x.get('recommendation_score', 0), reverse=True):
                code = product.get('product_code')
                if code and code not in seen_codes:
                    seen_codes.add(code)
                    unique_recommendations.append(product)
                    
                if len(unique_recommendations) >= limit:
                    break
            
            return unique_recommendations
            
        except Exception as e:
            self.logger.error(f"Error in recommend_by_interest: {e}")
            return []
    
    def recommend_similar_products(self, product_code: str, limit: int = 5) -> List[Dict]:
        """แนะนำสินค้าที่คล้ายกัน"""
        try:
            # ดึงข้อมูลสินค้าเดิม
            current_product = self.db.get_product_by_code(product_code)
            if not current_product:
                return []
            
            # ค้นหาสินค้าในหมวดเดียวกัน
            similar_products = self.db.search_products(
                query="",
                category=current_product.get('category'),
                limit=limit + 2,  # เพิ่มเผื่อลบสินค้าเดิมออก
                order_by='rating'
            )
            
            # กรองสินค้าเดิมออก
            filtered_products = []
            for product in similar_products.get('data', []):
                if product.get('product_code') != product_code:
                    product['recommendation_reason'] = f"สินค้าใกล้เคียงในหมวด {current_product.get('category', 'ไม่ระบุ')}"
                    filtered_products.append(product)
                    
                if len(filtered_products) >= limit:
                    break
            
            return filtered_products
            
        except Exception as e:
            self.logger.error(f"Error in recommend_similar_products: {e}")
            return []
    
    def recommend_trending_products(self, limit: int = 5) -> List[Dict]:
        """แนะนำสินค้าที่กำลังมาแรง"""
        try:
            # ดึงสินค้าที่มียอดขายดีและคะแนนสูง
            trending = self.db.get_top_products_by_metric('sold_count', limit * 2)
            
            # คำนวณคะแนน trending (ยอดขาย + คะแนน + รีวิว)
            scored_products = []
            for product in trending:
                sold_count = product.get('sold_count', 0)
                rating = product.get('rating', 0)
                review_count = product.get('review_count', 0)
                
                # สูตรคำนวณความนิยม
                trending_score = (sold_count * 0.5) + (rating * 20 * 0.3) + (review_count * 0.2)
                
                product['recommendation_score'] = trending_score
                product['recommendation_reason'] = f"สินค้าขายดี (ขายไป {sold_count:,} ชิ้น)"
                scored_products.append(product)
            
            # เรียงตามคะแนน trending
            sorted_products = sorted(scored_products, key=lambda x: x.get('recommendation_score', 0), reverse=True)
            
            return sorted_products[:limit]
            
        except Exception as e:
            self.logger.error(f"Error in recommend_trending_products: {e}")
            return []
    
    def get_personalized_recommendations(self, user_id: str, context: str = "", limit: int = 8) -> Dict:
        """สร้างคำแนะนำแบบปรับตัว"""
        try:
            # อัปเดตความสนใจจาก context
            if context:
                self.update_user_interests(user_id, context)
            
            recommendations = {
                'personal': [],
                'trending': [],
                'categories': [],
                'total_score': 0
            }
            
            # 1. แนะนำตามความสนใจส่วนตัว (40%)
            personal_recs = self.recommend_by_interest(user_id, limit=4)
            recommendations['personal'] = personal_recs
            
            # 2. แนะนำสินค้าที่กำลังมาแรง (40%)
            trending_recs = self.recommend_trending_products(limit=3)
            recommendations['trending'] = trending_recs
            
            # 3. แนะนำตามหมวดหมู่ยอดนิยม (20%)
            categories_recs = self._get_popular_categories_products(limit=2)
            recommendations['categories'] = categories_recs
            
            # คำนวณคะแนนรวม
            all_products = personal_recs + trending_recs + categories_recs
            recommendations['total_score'] = len(set(p.get('product_code') for p in all_products if p.get('product_code')))
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error in get_personalized_recommendations: {e}")
            return {'personal': [], 'trending': [], 'categories': [], 'total_score': 0}
    
    def _get_popular_categories_products(self, limit: int = 2) -> List[Dict]:
        """ดึงสินค้าจากหมวดหมู่ยอดนิยม"""
        try:
            # ดึงสถิติหมวดหมู่
            categories_stats = self.db.get_categories_with_stats()
            
            if not categories_stats:
                return []
            
            # เรียงตามความนิยม
            popular_categories = sorted(categories_stats, key=lambda x: x.get('popularity_score', 0), reverse=True)
            
            products = []
            for category_stat in popular_categories[:2]:  # เลือก 2 หมวดแรก
                category_name = category_stat.get('category_name')
                if category_name:
                    # ดึงสินค้าในหมวดนั้น
                    category_products = self.db.search_products(
                        query="",
                        category=category_name,
                        limit=1,
                        order_by='rating'
                    )
                    
                    for product in category_products.get('data', []):
                        product['recommendation_reason'] = f"หมวดหมู่ยอดนิยม: {category_name}"
                        products.append(product)
                        
                        if len(products) >= limit:
                            break
                
                if len(products) >= limit:
                    break
            
            return products
            
        except Exception as e:
            self.logger.error(f"Error in _get_popular_categories_products: {e}")
            return []
    
    def get_user_profile_summary(self, user_id: str) -> Dict:
        """สร้างสรุปโปรไฟล์ผู้ใช้"""
        try:
            profile = {
                'user_id': user_id,
                'top_interests': self.get_user_top_interests(user_id, limit=5),
                'interaction_count': len(self.user_history.get(user_id, [])),
                'last_interaction': None,
                'preferences': {}
            }
            
            # ข้อมูลการโต้ตอบล่าสุด
            user_interactions = self.user_history.get(user_id, [])
            if user_interactions:
                profile['last_interaction'] = user_interactions[-1]['timestamp']
                
                # วิเคราะห์รูปแบบการใช้งาน
                recent_interactions = user_interactions[-10:]  # 10 ครั้งล่าสุด
                
                search_counts = [interaction.get('search_count', 0) for interaction in recent_interactions if interaction.get('search_count')]
                if search_counts:
                    profile['preferences']['avg_search_results'] = sum(search_counts) / len(search_counts)
                
                # ช่วงเวลาที่มักใช้งาน
                hours = []
                for interaction in recent_interactions:
                    try:
                        dt = datetime.fromisoformat(interaction['timestamp'].replace('Z', '+00:00'))
                        hours.append(dt.hour)
                    except:
                        continue
                
                if hours:
                    profile['preferences']['preferred_hours'] = Counter(hours).most_common(3)
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Error in get_user_profile_summary: {e}")
            return {'user_id': user_id, 'error': str(e)}

# สร้าง instance สำหรับใช้งาน
ai_recommender = AIProductRecommender()