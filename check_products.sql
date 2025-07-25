-- ตรวจสอบข้อมูลสินค้าใน Supabase

-- 1. นับจำนวนสินค้าทั้งหมด
SELECT COUNT(*) as total_products FROM products;

-- 2. ดูสินค้าทั้งหมด (ถ้ามี)
SELECT 
    product_code,
    product_name,
    price,
    category,
    shop_name
FROM products;

-- 3. ตรวจสอบว่ามีข้อมูลในตาราง products ไหม
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns 
WHERE table_name = 'products' 
ORDER BY ordinal_position;