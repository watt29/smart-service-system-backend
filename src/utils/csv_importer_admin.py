"""
🔧 CSV Import System ที่ใช้ Admin API
แก้ไขปัญหา RLS โดยใช้ Admin API ของ Supabase
"""

import csv
import logging
from typing import Dict, List, Optional
import re

class AdminCSVImporter:
    """นำเข้า CSV ผ่าน Admin API แทนการใช้ RLS"""
    
    def __init__(self, db_instance=None):
        self.db = db_instance
        self.logger = logging.getLogger(__name__)
        
        # หมวดหมู่ที่รองรับ
        self.valid_categories = {
            'โทรศัพท์มือถือ', 'ความงาม', 'สัตว์เลี้ยง', 'กระเป๋า', 'เกมมิ่ง',
            'เสื้อผ้าผู้ชาย', 'เสื้อผ้าผู้หญิง', 'รองเท้าผู้ชาย', 'รองเท้าผู้หญิง',
            'นาฬิกาแว่นตา', 'กล้อง', 'คอมพิวเตอร์', 'สุขภาพ', 'อาหารเครื่องดื่ม',
            'เครื่องใช้ไฟฟ้า', 'กีฬา'
        }
    
    def generate_product_code(self, category: str, index: int) -> str:
        """สร้างรหัสสินค้าอัตโนมัติ"""
        category_codes = {
            'โทรศัพท์มือถือ': 'PHN',
            'ความงาม': 'BTY',
            'สัตว์เลี้ยง': 'PET',
            'กระเป๋า': 'BAG',
            'เกมมิ่ง': 'GAM',
            'เสื้อผ้าผู้ชาย': 'MFH',
            'เสื้อผ้าผู้หญิง': 'WFH',
            'รองเท้าผู้ชาย': 'MSH',
            'รองเท้าผู้หญิง': 'WSH',
            'นาฬิกาแว่นตา': 'WAT',
            'กล้อง': 'CAM',
            'คอมพิวเตอร์': 'CMP',
            'สุขภาพ': 'HTH',
            'อาหารเครื่องดื่ม': 'FDR',
            'เครื่องใช้ไฟฟ้า': 'ELC',
            'กีฬา': 'SPT'
        }
        
        code_prefix = category_codes.get(category, 'GEN')
        return f"{code_prefix}{index:03d}"
    
    def validate_row(self, row: Dict) -> Dict:
        """ตรวจสอบความถูกต้องของข้อมูล"""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # ตรวจสอบฟิลด์จำเป็น
        required_fields = ['product_name', 'category', 'price', 'description', 'affiliate_link']
        for field in required_fields:
            if not row.get(field) or str(row[field]).strip() == '':
                result['valid'] = False
                result['errors'].append(f"ฟิลด์ {field} จำเป็นต้องมีข้อมูล")
        
        # ตรวจสอบหมวดหมู่
        category = row.get('category', '').strip()
        if category not in self.valid_categories:
            result['warnings'].append(f"หมวดหมู่ '{category}' ไม่อยู่ในรายการมาตรฐาน")
        
        # ตรวจสอบราคา
        try:
            price = float(str(row.get('price', 0)).replace(',', ''))
            if price <= 0:
                result['valid'] = False
                result['errors'].append("ราคาต้องมากกว่า 0")
        except (ValueError, TypeError):
            result['valid'] = False
            result['errors'].append("ราคาต้องเป็นตัวเลข")
        
        # ตรวจสอบ rating
        try:
            rating = float(str(row.get('rating', 0)))
            if rating < 0 or rating > 5:
                result['warnings'].append("คะแนนรีวิวควรอยู่ระหว่าง 0-5")
        except (ValueError, TypeError):
            result['warnings'].append("คะแนนรีวิวต้องเป็นตัวเลข")
        
        # ตรวจสอบลิงก์
        affiliate_link = row.get('affiliate_link', '').strip()
        if not affiliate_link.startswith('http'):
            result['valid'] = False
            result['errors'].append("ลิงก์ affiliate ต้องเป็น URL ที่ถูกต้อง")
        
        return result
    
    def prepare_product_data(self, row: Dict, product_code: str) -> Dict:
        """เตรียมข้อมูลสินค้าสำหรับนำเข้า"""
        # ทำความสะอาดข้อมูล
        product_name = str(row.get('product_name', '')).strip()
        category = str(row.get('category', '')).strip()
        
        try:
            price = float(str(row.get('price', 0)).replace(',', ''))
        except (ValueError, TypeError):
            price = 0
        
        try:
            rating = float(str(row.get('rating', 0)))
        except (ValueError, TypeError):
            rating = 0
        
        try:
            sold_count = int(str(row.get('sold_count', 0)).replace(',', ''))
        except (ValueError, TypeError):
            sold_count = 0
        
        description = str(row.get('description', '')).strip()
        brand = str(row.get('brand', '')).strip() or 'ไม่ระบุ'
        tags = str(row.get('tags', '')).strip()
        affiliate_link = str(row.get('affiliate_link', '')).strip()
        shop_name = str(row.get('shop_name', '')).strip() or 'ไม่ระบุ'
        
        # คำนวณคอมมิชชั่น (15% ของราคา)
        commission_rate = 15.0
        commission = price * (commission_rate / 100)
        
        return {
            'product_code': product_code,
            'product_name': product_name,
            'category': category,
            'price': price,
            'description': description,
            'rating': rating,
            'sold_count': sold_count,
            'shop_name': shop_name,
            'commission_rate': commission_rate,
            'product_link': affiliate_link,  # ต้องใช้ product_link แทน affiliate_link
            'offer_link': affiliate_link,    # ใช้ link เดียวกันสำหรับ offer
            'image_url': ''  # ไม่มีข้อมูลรูปภาพใน CSV
        }
    
    def import_csv_file(self, csv_file_path: str, skip_duplicates: bool = True) -> Dict:
        """นำเข้าข้อมูลจากไฟล์ CSV"""
        results = {
            'success': 0,
            'errors': 0,
            'warnings': 0,
            'total_rows': 0,
            'details': []
        }
        
        if not self.db:
            results['details'].append("ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
            return results
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                for index, row in enumerate(csv_reader, 1):
                    results['total_rows'] += 1
                    
                    # ตรวจสอบข้อมูล
                    validation = self.validate_row(row)
                    
                    if not validation['valid']:
                        results['errors'] += 1
                        error_msg = f"แถว {index}: {', '.join(validation['errors'])}"
                        results['details'].append(error_msg)
                        self.logger.error(error_msg)
                        continue
                    
                    if validation['warnings']:
                        results['warnings'] += 1
                        warning_msg = f"แถว {index}: {', '.join(validation['warnings'])}"
                        results['details'].append(warning_msg)
                        self.logger.warning(warning_msg)
                    
                    # สร้างรหัสสินค้า
                    product_code = self.generate_product_code(row['category'], index)
                    
                    # ตรวจสอบว่ามีสินค้านี้อยู่แล้วหรือไม่
                    if skip_duplicates:
                        existing = self.db.get_product_by_code(product_code)
                        if existing:
                            results['details'].append(f"แถว {index}: ข้ามสินค้าที่มีอยู่แล้ว - {product_code}")
                            continue
                    
                    # เตรียมข้อมูล
                    product_data = self.prepare_product_data(row, product_code)
                    
                    # นำเข้าข้อมูล (ใช้ Admin API)
                    success = self._insert_product_admin(product_data)
                    
                    if success:
                        results['success'] += 1
                        results['details'].append(f"แถว {index}: นำเข้าสำเร็จ - {product_data['product_name']}")
                        self.logger.info(f"นำเข้าสินค้าสำเร็จ: {product_code}")
                    else:
                        results['errors'] += 1
                        results['details'].append(f"แถว {index}: ล้มเหลวในการนำเข้า - {product_data['product_name']}")
                        self.logger.error(f"ล้มเหลวในการนำเข้าสินค้า: {product_code}")
        
        except FileNotFoundError:
            results['details'].append(f"ไม่พบไฟล์: {csv_file_path}")
        except Exception as e:
            results['details'].append(f"เกิดข้อผิดพลาด: {str(e)}")
            self.logger.error(f"Error importing CSV: {e}")
        
        return results
    
    def _insert_product_admin(self, product_data: Dict) -> bool:
        """นำเข้าสินค้าผ่าน Admin API"""
        try:
            # ใช้ database method แทน direct supabase access
            return self.db.add_product(product_data)
                
        except Exception as e:
            self.logger.error(f"Error inserting product {product_data['product_code']}: {e}")
            return False
    
    def create_sample_csv(self, output_path: str) -> bool:
        """สร้างไฟล์ CSV ตัวอย่าง"""
        sample_data = [
            {
                'product_name': 'iPhone 15 Pro Max 256GB',
                'category': 'โทรศัพท์มือถือ',
                'price': '45900',
                'description': 'iPhone 15 Pro Max ล่าสุด กล้อง 48MP Pro',
                'brand': 'Apple',
                'rating': '4.8',
                'sold_count': '1250',
                'tags': 'iPhone,Apple,smartphone,5G',
                'affiliate_link': 'https://s.shopee.co.th/9ADyJMhFF0',
                'shop_name': 'Apple Store Official'
            },
            {
                'product_name': 'เซรั่มวิตามินซี 30ml',
                'category': 'ความงาม',
                'price': '890',
                'description': 'เซรั่มวิตามินซีเข้มข้น ลดจุดด่างดำ',
                'brand': 'Beauty Plus',
                'rating': '4.6',
                'sold_count': '850',
                'tags': 'เซรั่ม,วิตามินซี,ความงาม',
                'affiliate_link': 'https://s.shopee.co.th/5VKfwcvCgS',
                'shop_name': 'Beauty House'
            }
        ]
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as file:
                fieldnames = [
                    'product_name', 'category', 'price', 'description', 'brand',
                    'rating', 'sold_count', 'tags', 'affiliate_link', 'shop_name'
                ]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(sample_data)
            
            return True
        except Exception as e:
            self.logger.error(f"Error creating sample CSV: {e}")
            return False
    
    def get_import_summary(self, results: Dict) -> str:
        """สร้างสรุปผลการนำเข้า"""
        summary = f"📊 สรุปการนำเข้าข้อมูล\n\n"
        summary += f"✅ สำเร็จ: {results['success']} รายการ\n"
        summary += f"❌ ล้มเหลว: {results['errors']} รายการ\n"
        summary += f"⚠️ คำเตือน: {results['warnings']} รายการ\n"
        summary += f"📝 รวมทั้งหมด: {results['total_rows']} รายการ\n\n"
        
        if results['details']:
            summary += "📋 รายละเอียด:\n"
            # แสดงเฉพาะ 10 รายการแรก
            for detail in results['details'][:10]:
                summary += f"• {detail}\n"
            
            if len(results['details']) > 10:
                summary += f"... และอีก {len(results['details']) - 10} รายการ\n"
        
        return summary