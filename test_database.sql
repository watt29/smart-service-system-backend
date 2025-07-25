-- ตรวจสอบข้อมูลในฐานข้อมูล Supabase

-- 1. ดูข้อมูลสินค้าทั้งหมด
SELECT 
    product_code,
    product_name,
    category,
    price,
    shop_name
FROM products 
ORDER BY created_at DESC;

-- 2. นับจำนวนสินค้าในแต่ละหมวดหมู่
SELECT 
    category,
    COUNT(*) as product_count
FROM products 
GROUP BY category
ORDER BY product_count DESC;

-- 3. ทดสอบการค้นหาคำว่า 'แมว'
SELECT 
    product_code,
    product_name,
    category
FROM products 
WHERE 
    product_name ILIKE '%แมว%' 
    OR description ILIKE '%แมว%' 
    OR category ILIKE '%แมว%';

-- 4. ทดสอบการค้นหาคำว่า 'อาหาร'
SELECT 
    product_code,
    product_name,
    category
FROM products 
WHERE 
    product_name ILIKE '%อาหาร%' 
    OR description ILIKE '%อาหาร%' 
    OR category ILIKE '%อาหาร%';

-- 5. ดูข้อมูลหมวดหมู่ทั้งหมด
SELECT * FROM categories ORDER BY name;