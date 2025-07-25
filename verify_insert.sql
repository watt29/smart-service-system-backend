-- ตรวจสอบหลังจาก INSERT สินค้า

-- 1. นับจำนวนสินค้า
SELECT COUNT(*) as total_products FROM products;

-- 2. ดูสินค้าที่เพิ่มเข้าไป
SELECT 
    product_code,
    product_name,
    price,
    category,
    shop_name
FROM products 
ORDER BY created_at DESC;

-- 3. ทดสอบค้นหา "แมว"
SELECT 
    product_code,
    product_name
FROM products 
WHERE 
    product_name ILIKE '%แมว%' 
    OR description ILIKE '%แมว%' 
    OR category ILIKE '%แมว%';