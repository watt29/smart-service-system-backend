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
    
    def search_products(self, query: str, limit: int = 5) -> List[Dict]:
        """ค้นหาสินค้า"""
        if not self.connected:
            return []
        
        try:
            # ค้นหาในชื่อสินค้า, คำอธิบาย, และหมวดหมู่
            response = self.client.table('products')\
                .select('*')\
                .or_(f'product_name.ilike.%{query}%,description.ilike.%{query}%,category.ilike.%{query}%')\
                .limit(limit)\
                .execute()
            
            # บันทึกการค้นหา
            self.log_search(query, len(response.data))
            
            return response.data or []
            
        except Exception as e:
            self.logger.error(f"Error searching products: {e}")
            return []
    
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
    
    def get_stats(self) -> Dict[str, Any]:
        """ดึงสถิติต่างๆ"""
        if not self.connected:
            return {}
        
        try:
            # นับจำนวนสินค้า
            products_count = self.client.table('products').select('count').execute()
            
            # นับจำนวนการค้นหา
            searches_count = self.client.table('product_searches').select('count').execute()
            
            # คำนวณราคาเฉลี่ย
            avg_price = self.client.rpc('get_average_price').execute()
            
            return {
                'total_products': len(products_count.data) if products_count.data else 0,
                'total_searches': len(searches_count.data) if searches_count.data else 0,
                'average_price': avg_price.data[0] if avg_price.data else 0,
                'database_type': 'Supabase'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {'error': str(e)}