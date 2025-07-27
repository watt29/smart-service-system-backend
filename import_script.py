"""
🚀 Script สำหรับ import ข้อมูลจาก CSV โดย bypass RLS
ใช้ service role key แทน anon key
"""

import csv
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def import_csv_data():
    """นำเข้าข้อมูลจาก CSV โดยใช้ service role"""
    
    # ใช้ service role ถ้ามี หรือ anon key
    supabase_url = os.environ.get('SUPABASE_URL')
    service_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')  # service role key
    anon_key = os.environ.get('SUPABASE_KEY')  # anon key
    
    # ลองใช้ service key ก่อน ถ้าไม่มีใช้ anon key
    api_key = service_key if service_key else anon_key
    
    if not supabase_url or not api_key:
        print("❌ ไม่พบ SUPABASE_URL หรือ API Key")
        return False
    
    try:
        # สร้าง client
        supabase: Client = create_client(supabase_url, api_key)
        print(f"✅ เชื่อมต่อ Supabase สำเร็จ (ใช้ {'service role' if service_key else 'anon key'})")
        
        # อ่านข้อมูลจาก CSV
        csv_file = 'import_products_fixed.csv'
        if not os.path.exists(csv_file):
            print(f"❌ ไม่พบไฟล์: {csv_file}")
            return False
        
        products_to_insert = []
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for index, row in enumerate(csv_reader, 1):
                try:
                    # เตรียมข้อมูล
                    product_code = f"CSV{index:03d}"
                    price = float(str(row.get('price', 0)).replace(',', ''))
                    rating = float(str(row.get('rating', 0)))
                    sold_count = int(str(row.get('sold_count', 0)).replace(',', ''))
                    commission_rate = 15.0
                    commission_amount = price * (commission_rate / 100)
                    
                    product_data = {
                        'product_code': product_code,
                        'product_name': str(row.get('product_name', '')).strip(),
                        'category': str(row.get('category', '')).strip(),
                        'price': price,
                        'description': str(row.get('description', '')).strip(),
                        'rating': rating,
                        'sold_count': sold_count,
                        'shop_name': str(row.get('shop_name', '')).strip() or 'ไม่ระบุ',
                        'commission_rate': commission_rate,
                        'commission_amount': commission_amount,
                        'product_link': str(row.get('affiliate_link', '')).strip(),
                        'offer_link': str(row.get('affiliate_link', '')).strip(),
                        'image_url': ''
                    }
                    
                    products_to_insert.append(product_data)
                    
                except Exception as e:
                    print(f"❌ ข้อผิดพลาดแถว {index}: {e}")
                    continue
        
        if not products_to_insert:
            print("❌ ไม่มีข้อมูลที่จะนำเข้า")
            return False
        
        print(f"📦 กำลังนำเข้า {len(products_to_insert)} รายการ...")
        
        # ลบข้อมูลเก่าทั้งหมดก่อน (optional)
        print("🗑️ ลบข้อมูลเก่า...")
        supabase.table('products').delete().neq('product_code', '').execute()
        
        # นำเข้าข้อมูลใหม่ทีละ batch
        batch_size = 10
        success_count = 0
        
        for i in range(0, len(products_to_insert), batch_size):
            batch = products_to_insert[i:i + batch_size]
            
            try:
                response = supabase.table('products').insert(batch).execute()
                if response.data:
                    success_count += len(response.data)
                    print(f"✅ นำเข้าสำเร็จ batch {i//batch_size + 1}: {len(response.data)} รายการ")
                else:
                    print(f"❌ ล้มเหลว batch {i//batch_size + 1}")
                    
            except Exception as e:
                print(f"❌ ข้อผิดพลาด batch {i//batch_size + 1}: {e}")
                continue
        
        print(f"\n🎉 นำเข้าข้อมูลเสร็จสิ้น!")
        print(f"✅ สำเร็จ: {success_count} รายการ")
        print(f"❌ ล้มเหลว: {len(products_to_insert) - success_count} รายการ")
        
        # ตรวจสอบข้อมูลหลังนำเข้า
        result = supabase.table('products').select('*', count='exact').execute()
        print(f"📊 รวมสินค้าในฐานข้อมูล: {result.count} รายการ")
        
        # แสดงหมวดหมู่ที่มี
        categories_result = supabase.table('products').select('category').execute()
        categories = set([item['category'] for item in categories_result.data if item['category']])
        print(f"📋 หมวดหมู่ที่มี: {len(categories)} หมวดหมู่")
        for cat in sorted(categories):
            print(f"  - {cat}")
        
        return True
        
    except Exception as e:
        print(f"❌ ข้อผิดพลาด: {e}")
        return False

if __name__ == "__main__":
    print("🚀 เริ่มต้นการนำเข้าข้อมูล CSV...")
    success = import_csv_data()
    
    if success:
        print("\n🎯 การนำเข้าเสร็จสมบูรณ์! ระบบพร้อมใช้งาน")
    else:
        print("\n💥 การนำเข้าล้มเหลว กรุณาตรวจสอบข้อผิดพลาด")