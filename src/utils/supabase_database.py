"""
📁 src/utils/supabase_database.py
🎯 จัดการฐานข้อมูล Supabase สำหรับ Affiliate Product Review Bot
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import json

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

from ..config import config

class SupabaseDatabase:
    """คลาสสำหรับจัดการฐานข้อมูล Supabase"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.logger = logging.getLogger(__name__)
        self.connected = False
        
        if not SUPABASE_AVAILABLE:
            self.logger.warning("Supabase library not installed. Please install: pip install supabase")
            return
            
        try:
            self.connect()
        except Exception as e:
            self.logger.error(f"Failed to connect to Supabase: {e}")
    
    def connect(self) -> bool:
        """เชื่อมต่อกับ Supabase"""
        try:
            if not config.SUPABASE_URL or not config.SUPABASE_KEY:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
            
            self.client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
            
            # ทดสอบการเชื่อมต่อ
            response = self.client.table('products').select('count').execute()
            self.connected = True
            self.logger.info("Successfully connected to Supabase")
            return True
            
        except Exception as e:
            self.logger.error(f"Supabase connection failed: {e}")
            self.connected = False
            return False
    
    def create_tables(self) -> bool:
        """สร้างตารางในฐานข้อมูล (ใช้ SQL Editor ใน Supabase Dashboard)"""
        create_products_table = """
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            product_code VARCHAR(50) UNIQUE NOT NULL,
            product_name VARCHAR(255) NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            sold_count INTEGER DEFAULT 0,
            shop_name VARCHAR(255) NOT NULL,
            commission_rate DECIMAL(5,2) NOT NULL,
            commission_amount DECIMAL(10,2) NOT NULL,
            product_link TEXT NOT NULL,
            offer_link TEXT NOT NULL,
            category VARCHAR(100),
            description TEXT,
            image_url TEXT,
            rating DECIMAL(3,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """
        
        create_searches_table = """
        CREATE TABLE IF NOT EXISTS product_searches (
            id SERIAL PRIMARY KEY,
            search_query VARCHAR(255) NOT NULL,
            product_id INTEGER REFERENCES products(id),
            user_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
        
        self.logger.info("Tables should be created using Supabase SQL Editor:")
        self.logger.info(create_products_table)
        self.logger.info(create_searches_table)
        return True
    
    def add_product(self, product_data: Dict[str, Any]) -> Optional[Dict]:
        """เพิ่มสินค้าใหม่"""
        if not self.connected:
            return None
        
        try:
            # คำนวณ commission_amount
            commission_amount = (product_data['price'] * product_data['commission_rate']) / 100
            
            data = {
                'product_code': product_data['product_code'],
                'product_name': product_data['product_name'],
                'price': float(product_data['price']),
                'sold_count': int(product_data.get('sold_count', 0)),
                'shop_name': product_data['shop_name'],
                'commission_rate': float(product_data['commission_rate']),
                'commission_amount': commission_amount,
                'product_link': product_data['product_link'],
                'offer_link': product_data['offer_link'],
                'category': product_data.get('category', ''),
                'description': product_data.get('description', ''),
                'image_url': product_data.get('image_url', ''),
                'rating': float(product_data.get('rating', 0))
            }
            
            response = self.client.table('products').insert(data).execute()
            
            if response.data:
                self.logger.info(f"Added product: {product_data['product_name']}")
                return response.data[0]
            return None
            
        except Exception as e:
            self.logger.error(f"Error adding product: {e}")
            return None
    
    def search_products(self, query: str, limit: int = 5, offset: int = 0, 
                       category: str = None, min_price: float = None, 
                       max_price: float = None, order_by: str = 'created_at') -> Dict:
        """ค้นหาสินค้าพร้อม pagination และ filtering"""
        if not self.connected:
            return {"products": [], "total": 0, "has_more": False}
        
        try:
            # สร้าง query พื้นฐาน
            query_builder = self.client.table('products').select('*')
            count_builder = self.client.table('products').select('*', count='exact')
            
            # เพิ่มเงื่อนไขการค้นหา
            search_condition = f'product_name.ilike.%{query}%,description.ilike.%{query}%,category.ilike.%{query}%'
            query_builder = query_builder.or_(search_condition)
            count_builder = count_builder.or_(search_condition)
            
            # เพิ่มตัวกรองหมวดหมู่
            if category:
                query_builder = query_builder.eq('category', category)
                count_builder = count_builder.eq('category', category)
            
            # เพิ่มตัวกรองราคา
            if min_price is not None:
                query_builder = query_builder.gte('price', min_price)
                count_builder = count_builder.gte('price', min_price)
            
            if max_price is not None:
                query_builder = query_builder.lte('price', max_price)
                count_builder = count_builder.lte('price', max_price)
            
            # เรียงลำดับ
            sort_column = order_by
            desc_order = True
            
            if order_by == 'popularity':
                sort_column = 'sold_count'
            elif order_by == 'price_low':
                sort_column = 'price'
                desc_order = False
            elif order_by == 'price_high':
                sort_column = 'price'
                desc_order = True
            elif order_by == 'rating':
                sort_column = 'rating'
                desc_order = True
            elif order_by == 'category':
                sort_column = 'category'
                desc_order = False
                # เรียงตามหมวดหมู่ แล้วตามยอดขาย
                query_builder = query_builder.order('category', desc=False).order('sold_count', desc=True)
            elif order_by == 'product_name':
                sort_column = 'product_name'
                desc_order = False
            else:  # created_at และอื่นๆ
                sort_column = 'created_at'
                desc_order = True
            
            # ใช้การเรียงลำดับ (ยกเว้น category ที่เรียงแล้ว)
            if order_by != 'category':
                query_builder = query_builder.order(sort_column, desc=desc_order)
            
            # เพิ่ม pagination
            query_builder = query_builder.range(offset, offset + limit - 1)
            
            # ดำเนินการ query
            response = query_builder.execute()
            count_response = count_builder.execute()
            
            products = response.data or []
            total = count_response.count or 0
            has_more = (offset + limit) < total
            
            # บันทึกการค้นหา
            self.log_search(query, len(products))
            
            return {
                "products": products,
                "total": total,
                "has_more": has_more,
                "current_offset": offset,
                "limit": limit
            }
            
        except Exception as e:
            self.logger.error(f"Error searching products: {e}")
            return {"products": [], "total": 0, "has_more": False}
    
    def get_product_by_code(self, product_code: str) -> Optional[Dict]:
        """ค้นหาสินค้าด้วยรหัสสินค้า"""
        if not self.connected:
            return None
        
        try:
            response = self.client.table('products')\
                .select('*')\
                .eq('product_code', product_code)\
                .single()\
                .execute()
            
            return response.data
            
        except Exception as e:
            self.logger.error(f"Error getting product by code: {e}")
            return None
    
    def update_product(self, product_code: str, update_data: Dict) -> bool:
        """อัปเดตข้อมูลสินค้า"""
        if not self.connected:
            return False
        
        try:
            # คำนวณ commission_amount ใหม่ถ้ามีการเปลี่ยน price หรือ commission_rate
            if 'price' in update_data or 'commission_rate' in update_data:
                product = self.get_product_by_code(product_code)
                if product:
                    price = update_data.get('price', product['price'])
                    rate = update_data.get('commission_rate', product['commission_rate'])
                    update_data['commission_amount'] = (float(price) * float(rate)) / 100
            
            update_data['updated_at'] = datetime.now().isoformat()
            
            response = self.client.table('products')\
                .update(update_data)\
                .eq('product_code', product_code)\
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            self.logger.error(f"Error updating product: {e}")
            return False
    
    def delete_product(self, product_code: str) -> bool:
        """ลบสินค้า"""
        if not self.connected:
            return False
        
        try:
            response = self.client.table('products')\
                .delete()\
                .eq('product_code', product_code)\
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting product: {e}")
            return False
    
    def get_all_products(self, limit: int = 100) -> List[Dict]:
        """ดึงสินค้าทั้งหมด"""
        if not self.connected:
            return []
        
        try:
            response = self.client.table('products')\
                .select('*')\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            self.logger.error(f"Error getting all products: {e}")
            return []
    
    def get_products_by_category(self, category: str) -> List[Dict]:
        """ดึงสินค้าตามหมวดหมู่"""
        if not self.connected:
            return []
        
        try:
            response = self.client.table('products')\
                .select('*')\
                .eq('category', category)\
                .order('rating', desc=True)\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            self.logger.error(f"Error getting products by category: {e}")
            return []
    
    def log_search(self, query: str, result_count: int, user_id: str = None) -> bool:
        """บันทึกการค้นหา"""
        if not self.connected:
            return False
        
        try:
            data = {
                'search_query': query,
                'user_id': user_id,
                'result_count': result_count
            }
            
            response = self.client.table('product_searches').insert(data).execute()
            return len(response.data) > 0
            
        except Exception as e:
            self.logger.error(f"Error logging search: {e}")
            return False
    
    def get_popular_searches(self, limit: int = 10) -> List[Dict]:
        """ดึงคำค้นหาที่ได้รับความนิยม"""
        if not self.connected:
            return []
        
        try:
            # สร้าง query ที่นับจำนวนการค้นหาแต่ละคำ
            response = self.client.rpc('get_popular_searches', {'search_limit': limit}).execute()
            return response.data or []
            
        except Exception as e:
            self.logger.error(f"Error getting popular searches: {e}")
            return []
    
    def get_categories(self) -> List[str]:
        """ดึงรายการหมวดหมู่ทั้งหมด"""
        if not self.connected:
            return []
        
        try:
            response = self.client.table('products')\
                .select('category')\
                .execute()
            
            categories = set()
            for item in response.data or []:
                if item.get('category'):
                    categories.add(item['category'])
            
            return sorted(list(categories))
            
        except Exception as e:
            self.logger.error(f"Error getting categories: {e}")
            return []
    
    def get_categories_with_stats(self) -> List[Dict[str, Any]]:
        """ดึงหมวดหมู่พร้อมสถิติความนิยม สำหรับ Smart grouping"""
        if not self.connected:
            return []
        
        try:
            response = self.client.table('products')\
                .select('category, price, sold_count, rating')\
                .execute()
            
            # คำนวณสถิติแต่ละหมวดหมู่
            category_stats = {}
            
            for item in response.data or []:
                category = item.get('category', 'อื่นๆ')
                if not category:
                    category = 'อื่นๆ'
                
                if category not in category_stats:
                    category_stats[category] = {
                        'name': category,
                        'product_count': 0,
                        'total_sold': 0,
                        'avg_price': 0,
                        'avg_rating': 0,
                        'popularity_score': 0,
                        'prices': [],
                        'ratings': []
                    }
                
                stats = category_stats[category]
                stats['product_count'] += 1
                stats['total_sold'] += int(item.get('sold_count', 0))
                stats['prices'].append(float(item.get('price', 0)))
                
                rating = float(item.get('rating', 0))
                if rating > 0:
                    stats['ratings'].append(rating)
            
            # คำนวณค่าเฉลี่ยและคะแนนความนิยม
            categories_with_stats = []
            for category, stats in category_stats.items():
                # คำนวณราคาเฉลี่ย
                if stats['prices']:
                    stats['avg_price'] = sum(stats['prices']) / len(stats['prices'])
                
                # คำนวณคะแนนเฉลี่ย
                if stats['ratings']:
                    stats['avg_rating'] = sum(stats['ratings']) / len(stats['ratings'])
                
                # คำนวณคะแนนความนิยม (น้อมหนัก: จำนวนสินค้า 40%, ยอดขาย 40%, คะแนน 20%)
                popularity_score = (
                    (stats['product_count'] * 0.4) +
                    (min(stats['total_sold'] / 100, 100) * 0.4) +  # normalize ยอดขายต่อ 100
                    (stats['avg_rating'] * 20 * 0.2)  # normalize คะแนนต่อ 100
                )
                stats['popularity_score'] = round(popularity_score, 2)
                
                # ลบ arrays ที่ไม่ต้องการ
                del stats['prices']
                del stats['ratings']
                
                categories_with_stats.append(stats)
            
            # เรียงตามคะแนนความนิยม
            categories_with_stats.sort(key=lambda x: x['popularity_score'], reverse=True)
            
            return categories_with_stats
            
        except Exception as e:
            self.logger.error(f"Error getting categories with stats: {e}")
            return []
    
    def get_price_range(self) -> Dict[str, float]:
        """ดึงช่วงราคาของสินค้าทั้งหมด"""
        if not self.connected:
            return {"min_price": 0, "max_price": 0}
        
        try:
            # ดึงราคาต่ำสุดและสูงสุด
            min_response = self.client.table('products')\
                .select('price')\
                .order('price', desc=False)\
                .limit(1)\
                .execute()
            
            max_response = self.client.table('products')\
                .select('price')\
                .order('price', desc=True)\
                .limit(1)\
                .execute()
            
            min_price = min_response.data[0]['price'] if min_response.data else 0
            max_price = max_response.data[0]['price'] if max_response.data else 0
            
            return {
                "min_price": float(min_price),
                "max_price": float(max_price)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting price range: {e}")
            return {"min_price": 0, "max_price": 0}

    def get_stats(self) -> Dict[str, Any]:
        """ดึงสถิติต่างๆ"""
        if not self.connected:
            return {}
        
        try:
            # นับจำนวนสินค้า
            products_count = self.client.table('products').select('*', count='exact').execute()
            
            # นับจำนวนการค้นหา
            searches_count = self.client.table('product_searches').select('*', count='exact').execute()
            
            # คำนวณราคาเฉลี่ย
            avg_price = self.client.rpc('get_average_price').execute()
            
            # เพิ่มข้อมูลหมวดหมู่และช่วงราคา
            categories = self.get_categories()
            price_range = self.get_price_range()
            
            return {
                'total_products': products_count.count if products_count.count else 0,
                'total_searches': searches_count.count if searches_count.count else 0,
                'average_price': avg_price.data if avg_price.data else 0,
                'database_type': 'Supabase',
                'categories_count': len(categories),
                'categories': categories[:10],  # แสดงแค่ 10 หมวดหมู่แรก
                'price_range': price_range
            }
            
        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {'error': str(e)}