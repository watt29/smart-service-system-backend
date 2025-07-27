"""
Script เพิ่มสินค้าผ่าน LINE Bot admin interface
"""

from src.handlers.affiliate_handler import AffiliateLineHandler
import csv

def add_products_via_admin():
    """เพิ่มสินค้าผ่าน admin interface"""
    
    handler = AffiliateLineHandler()
    
    # อ่านข้อมูลจาก CSV
    csv_file = 'import_products_fixed.csv'
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            success_count = 0
            error_count = 0
            
            for index, row in enumerate(csv_reader, 1):
                try:
                    # เตรียมข้อมูล
                    product_code = f"MAN{index:03d}"
                    price = float(str(row.get('price', 0)).replace(',', ''))
                    rating = float(str(row.get('rating', 0)))
                    sold_count = int(str(row.get('sold_count', 0)).replace(',', ''))
                    commission_rate = 15.0
                    
                    product_data = {
                        'product_code': product_code,
                        'product_name': str(row.get('product_name', '')).strip(),
                        'price': price,
                        'shop_name': str(row.get('shop_name', '')).strip() or 'Not specified',
                        'commission_rate': commission_rate,
                        'product_link': str(row.get('affiliate_link', '')).strip(),
                        'offer_link': str(row.get('affiliate_link', '')).strip(),
                        'category': str(row.get('category', '')).strip(),
                        'description': str(row.get('description', '')).strip(),
                        'image_url': '',
                        'rating': rating
                    }
                    
                    # ใช้ database add_product method
                    result = handler.db.add_product(product_data)
                    
                    if result:
                        success_count += 1
                        print(f"SUCCESS {index}: {product_data['product_name']}")
                    else:
                        error_count += 1
                        print(f"FAILED {index}: {product_data['product_name']}")
                    
                except Exception as e:
                    error_count += 1
                    print(f"ERROR {index}: {e}")
                    continue
            
            print(f"\nCompleted!")
            print(f"SUCCESS: {success_count}")
            print(f"FAILED: {error_count}")
            
            # ตรวจสอบผลลัพธ์
            print("\nChecking database...")
            results = handler.db.search_products('', limit=50)
            print(f"Total products: {results['total']}")
            
            # แสดงหมวดหมู่
            categories = handler.db.get_categories()
            print(f"Categories: {len(categories)}")
            for cat in categories:
                print(f"  - {cat}")
            
            return success_count > 0
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Adding products via admin interface...")
    success = add_products_via_admin()
    
    if success:
        print("\nProducts added successfully!")
    else:
        print("\nFailed to add products")