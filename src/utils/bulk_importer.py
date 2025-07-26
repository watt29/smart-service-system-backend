"""
📁 Bulk Product Importer
ระบบนำเข้าสินค้าจำนวนมากจาก CSV/Excel
"""

import pandas as pd
import os
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

from .supabase_database import SupabaseDatabase

class BulkProductImporter:
    """คลาสสำหรับนำเข้าสินค้าจำนวนมาก"""
    
    def __init__(self):
        self.db = SupabaseDatabase()
        self.logger = logging.getLogger(__name__)
        
        # คอลัมน์ที่จำเป็นสำหรับการนำเข้า
        self.required_columns = [
            'product_name',
            'category', 
            'price',
            'affiliate_link'
        ]
        
        # คอลัมน์ทั้งหมดที่รองรับ
        self.supported_columns = [
            'product_code',
            'product_name',
            'description', 
            'category',
            'subcategory',
            'price',
            'original_price',
            'discount_percentage',
            'affiliate_link',
            'image_url',
            'brand',
            'rating',
            'review_count',
            'sold_count',
            'stock_quantity',
            'tags',
            'commission_rate',
            'is_featured',
            'is_active'
        ]
    
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """ตรวจสอบไฟล์ก่อนนำเข้า"""
        if not os.path.exists(file_path):
            return False, "ไฟล์ไม่พบ"
        
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension not in ['.csv', '.xlsx', '.xls']:
            return False, "รองรับเฉพาะไฟล์ CSV และ Excel เท่านั้น"
        
        try:
            # อ่านไฟล์ทดสอบ
            if file_extension == '.csv':
                df = pd.read_csv(file_path, nrows=1)
            else:
                df = pd.read_excel(file_path, nrows=1)
            
            # ตรวจสอบคอลัมน์ที่จำเป็น
            missing_columns = []
            for col in self.required_columns:
                if col not in df.columns:
                    missing_columns.append(col)
            
            if missing_columns:
                return False, f"ขาดคอลัมน์ที่จำเป็น: {', '.join(missing_columns)}"
            
            return True, "ไฟล์ถูกต้อง"
            
        except Exception as e:
            return False, f"ไม่สามารถอ่านไฟล์ได้: {str(e)}"
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """ทำความสะอาดข้อมูลก่อนนำเข้า"""
        # สร้าง DataFrame ใหม่
        cleaned_df = df.copy()
        
        # ทำความสะอาดคอลัมน์
        for col in cleaned_df.columns:
            if col in self.supported_columns:
                if col == 'product_name':
                    # ตัดช่องว่างและตรวจสอบความยาว
                    cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
                    cleaned_df = cleaned_df[cleaned_df[col].str.len() > 0]
                
                elif col == 'price':
                    # แปลงราคาเป็นตัวเลข
                    cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
                    cleaned_df = cleaned_df[cleaned_df[col] > 0]
                
                elif col == 'category':
                    # ทำความสะอาดหมวดหมู่
                    cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
                    cleaned_df = cleaned_df[cleaned_df[col].str.len() > 0]
                
                elif col == 'affiliate_link':
                    # ตรวจสอบลิงก์
                    cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
                    url_pattern = re.compile(r'^https?://')
                    cleaned_df = cleaned_df[cleaned_df[col].str.match(url_pattern, na=False)]
                
                elif col in ['rating', 'discount_percentage', 'commission_rate']:
                    # แปลงเป็นตัวเลข
                    cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
                
                elif col in ['review_count', 'sold_count', 'stock_quantity']:
                    # แปลงเป็นจำนวนเต็ม
                    cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce').fillna(0).astype(int)
                
                elif col in ['is_featured', 'is_active']:
                    # แปลงเป็น boolean
                    cleaned_df[col] = cleaned_df[col].fillna(True).astype(bool)
        
        # ลบแถวที่มีข้อมูลสำคัญขาดหาย
        cleaned_df = cleaned_df.dropna(subset=self.required_columns)
        
        return cleaned_df
    
    def generate_product_codes(self, df: pd.DataFrame) -> pd.DataFrame:
        """สร้างรหัสสินค้าอัตโนมัติ"""
        result_df = df.copy()
        
        # หากไม่มีคอลัมน์ product_code หรือมีค่าว่าง
        if 'product_code' not in result_df.columns:
            result_df['product_code'] = ''
        
        # สร้างรหัสใหม่สำหรับรายการที่ไม่มีรหัส
        empty_codes = result_df['product_code'].isna() | (result_df['product_code'] == '')
        
        for idx in result_df[empty_codes].index:
            # สร้างรหัสจากหมวดหมู่และลำดับ
            category = result_df.loc[idx, 'category']
            category_prefix = ''.join([c.upper() for c in category if c.isalpha()])[:3]
            if len(category_prefix) < 3:
                category_prefix = f"{category_prefix}{'X' * (3 - len(category_prefix))}"
            
            # หาลำดับถัดไป
            existing_codes = self.db.get_product_codes_by_prefix(category_prefix)
            next_number = len(existing_codes) + 1
            
            result_df.loc[idx, 'product_code'] = f"{category_prefix}{next_number:04d}"
        
        return result_df
    
    def import_from_file(self, file_path: str, batch_size: int = 100) -> Dict:
        """นำเข้าสินค้าจากไฟล์"""
        result = {
            'success': False,
            'total_rows': 0,
            'processed_rows': 0,
            'successful_imports': 0,
            'failed_imports': 0,
            'errors': [],
            'duplicates': 0,
            'summary': {}
        }
        
        try:
            # ตรวจสอบไฟล์
            is_valid, message = self.validate_file(file_path)
            if not is_valid:
                result['errors'].append(message)
                return result
            
            # อ่านไฟล์
            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension == '.csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            result['total_rows'] = len(df)
            self.logger.info(f"Starting import of {result['total_rows']} products")
            
            # ทำความสะอาดข้อมูล
            cleaned_df = self.clean_data(df)
            result['processed_rows'] = len(cleaned_df)
            
            if len(cleaned_df) == 0:
                result['errors'].append("ไม่มีข้อมูลที่ถูกต้องสำหรับนำเข้า")
                return result
            
            # สร้างรหัสสินค้า
            final_df = self.generate_product_codes(cleaned_df)
            
            # นำเข้าแบบแบตช์
            successful_imports = 0
            failed_imports = 0
            duplicates = 0
            
            for i in range(0, len(final_df), batch_size):
                batch_df = final_df.iloc[i:i+batch_size]
                
                for _, row in batch_df.iterrows():
                    try:
                        product_data = self._prepare_product_data(row)
                        
                        # ตรวจสอบสินค้าซ้ำ
                        if self.db.get_product_by_code(product_data['product_code']):
                            duplicates += 1
                            continue
                        
                        # เพิ่มสินค้า
                        if self.db.add_product(product_data):
                            successful_imports += 1
                        else:
                            failed_imports += 1
                            
                    except Exception as e:
                        failed_imports += 1
                        result['errors'].append(f"Row {i+1}: {str(e)}")
            
            result['successful_imports'] = successful_imports
            result['failed_imports'] = failed_imports
            result['duplicates'] = duplicates
            result['success'] = successful_imports > 0
            
            # สรุปผลลัพธ์
            result['summary'] = {
                'categories': final_df['category'].nunique(),
                'brands': final_df.get('brand', pd.Series()).nunique() if 'brand' in final_df.columns else 0,
                'average_price': float(final_df['price'].mean()),
                'price_range': {
                    'min': float(final_df['price'].min()),
                    'max': float(final_df['price'].max())
                }
            }
            
            self.logger.info(f"Import completed: {successful_imports} success, {failed_imports} failed, {duplicates} duplicates")
            
        except Exception as e:
            result['errors'].append(f"Import error: {str(e)}")
            self.logger.error(f"Import failed: {str(e)}")
        
        return result
    
    def _prepare_product_data(self, row: pd.Series) -> Dict:
        """เตรียมข้อมูลสินค้าสำหรับบันทึก"""
        product_data = {}
        
        # ข้อมูลพื้นฐาน
        for col in self.supported_columns:
            if col in row.index and pd.notna(row[col]):
                if col in ['is_featured', 'is_active']:
                    product_data[col] = bool(row[col])
                elif col in ['price', 'original_price', 'rating', 'discount_percentage', 'commission_rate']:
                    product_data[col] = float(row[col])
                elif col in ['review_count', 'sold_count', 'stock_quantity']:
                    product_data[col] = int(row[col])
                else:
                    product_data[col] = str(row[col]).strip()
        
        # ค่าเริ่มต้น
        if 'is_active' not in product_data:
            product_data['is_active'] = True
        if 'is_featured' not in product_data:
            product_data['is_featured'] = False
        if 'commission_rate' not in product_data:
            product_data['commission_rate'] = 5.0
        
        # เพิ่มวันที่
        product_data['created_at'] = datetime.now().isoformat()
        product_data['updated_at'] = datetime.now().isoformat()
        
        return product_data
    
    def create_sample_csv(self, file_path: str):
        """สร้างไฟล์ตัวอย่างสำหรับการนำเข้า"""
        sample_data = [
            {
                'product_code': 'ELE0001',
                'product_name': 'iPhone 15 Pro Max 256GB',
                'description': 'สมาร์ทโฟนรุ่นล่าสุดจาก Apple พร้อมกล้องระดับมืออาชีพ',
                'category': 'อิเล็กทรอนิกส์',
                'subcategory': 'มือถือ',
                'price': 45900.00,
                'original_price': 47900.00,
                'discount_percentage': 4.18,
                'affiliate_link': 'https://example.com/iphone15promax',
                'image_url': 'https://example.com/images/iphone15.jpg',
                'brand': 'Apple',
                'rating': 4.8,
                'review_count': 1250,
                'sold_count': 850,
                'stock_quantity': 100,
                'tags': 'สมาร์ทโฟน,Apple,iPhone,5G',
                'commission_rate': 3.5,
                'is_featured': True,
                'is_active': True
            },
            {
                'product_code': 'FAB0001', 
                'product_name': 'เสื้อเชิ้ตผ้าคอตตอน',
                'description': 'เสื้อเชิ้ตแฟชั่นผู้ชายแบบเรียบหรู',
                'category': 'แฟชั่น',
                'subcategory': 'เสื้อผ้าผู้ชาย',
                'price': 890.00,
                'original_price': 1290.00,
                'discount_percentage': 31.01,
                'affiliate_link': 'https://example.com/cotton-shirt',
                'image_url': 'https://example.com/images/shirt.jpg',
                'brand': 'BasicWear',
                'rating': 4.2,
                'review_count': 68,
                'sold_count': 245,
                'stock_quantity': 50,
                'tags': 'เสื้อเชิ้ต,แฟชั่น,ผู้ชาย,คอตตอน',
                'commission_rate': 8.0,
                'is_featured': False,
                'is_active': True
            }
        ]
        
        df = pd.DataFrame(sample_data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        return f"สร้างไฟล์ตัวอย่าง: {file_path}"

# สร้าง instance สำหรับใช้งาน
bulk_importer = BulkProductImporter()