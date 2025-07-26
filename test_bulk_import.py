"""
🧪 Test Bulk Import System
ทดสอบระบบนำเข้าสินค้าจำนวนมาก
"""

import os
from src.utils.bulk_importer import bulk_importer

def test_bulk_import():
    """ทดสอบระบบ Bulk Import"""
    print("Testing Bulk Import System...")
    
    # ทดสอบการสร้างไฟล์ตัวอย่าง
    print("\n1. Testing Sample CSV Creation...")
    sample_path = "test_sample_products.csv"
    
    try:
        message = bulk_importer.create_sample_csv(sample_path)
        print(f"SUCCESS: {message}")
        
        if os.path.exists(sample_path):
            print(f"File created successfully: {sample_path}")
            
            # อ่านไฟล์เพื่อตรวจสอบ
            with open(sample_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                print(f"File size: {len(content)} characters")
                print("First 200 characters:")
                print(content[:200] + "..." if len(content) > 200 else content)
        else:
            print("ERROR: File not created")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    # ทดสอบการตรวจสอบไฟล์
    print("\n2. Testing File Validation...")
    if os.path.exists(sample_path):
        try:
            is_valid, message = bulk_importer.validate_file(sample_path)
            print(f"Validation result: {is_valid}")
            print(f"Message: {message}")
        except Exception as e:
            print(f"ERROR: {e}")
    
    # ทดสอบการนำเข้าข้อมูล (แบบจำลอง)
    print("\n3. Testing Import Process...")
    if os.path.exists(sample_path):
        try:
            # ใช้ batch_size เล็กเพื่อทดสอบ
            result = bulk_importer.import_from_file(sample_path, batch_size=1)
            
            print("Import Results:")
            print(f"  Success: {result['success']}")
            print(f"  Total rows: {result['total_rows']}")
            print(f"  Processed rows: {result['processed_rows']}")
            print(f"  Successful imports: {result['successful_imports']}")
            print(f"  Failed imports: {result['failed_imports']}")
            print(f"  Duplicates: {result['duplicates']}")
            
            if result['errors']:
                print("Errors:")
                for error in result['errors']:
                    print(f"  - {error}")
            
            if result['summary']:
                print("Summary:")
                for key, value in result['summary'].items():
                    print(f"  {key}: {value}")
                    
        except Exception as e:
            print(f"ERROR during import: {e}")
    
    # ทดสอบการตรวจสอบไฟล์ที่ไม่ถูกต้อง
    print("\n4. Testing Invalid File Validation...")
    try:
        is_valid, message = bulk_importer.validate_file("nonexistent.csv")
        print(f"Non-existent file - Valid: {is_valid}, Message: {message}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # ทำความสะอาด
    print("\n5. Cleanup...")
    try:
        if os.path.exists(sample_path):
            os.remove(sample_path)
            print(f"Removed test file: {sample_path}")
    except Exception as e:
        print(f"Cleanup error: {e}")
    
    print("\nBulk Import test completed!")

if __name__ == "__main__":
    test_bulk_import()