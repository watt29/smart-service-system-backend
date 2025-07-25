-- SQL สำหรับสร้างตารางและเพิ่มข้อมูลสินค้าครบชุด (แก้ไข Thai search)
-- ใช้ SQL Editor ใน Supabase Dashboard

-- 1. สร้างตาราง products
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

-- 2. สร้างตาราง product_searches
CREATE TABLE IF NOT EXISTS product_searches (
    id SERIAL PRIMARY KEY,
    search_query VARCHAR(255) NOT NULL,
    product_id INTEGER REFERENCES products(id),
    user_id VARCHAR(255),
    result_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. สร้าง Index สำหรับการค้นหา (แก้ไขให้ใช้ english แทน thai)
CREATE INDEX IF NOT EXISTS idx_products_name ON products USING GIN (to_tsvector('english', product_name));
CREATE INDEX IF NOT EXISTS idx_products_description ON products USING GIN (to_tsvector('english', description));
CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);
CREATE INDEX IF NOT EXISTS idx_products_code ON products (product_code);
CREATE INDEX IF NOT EXISTS idx_searches_query ON product_searches (search_query);

-- 4. สร้างตาราง categories
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. เพิ่มข้อมูลหมวดหมู่เริ่มต้น
INSERT INTO categories (name, description) VALUES
('อิเล็กทรอนิกส์', 'สินค้าอิเล็กทรอนิกส์และเทคโนโลยี'),
('แฟชั่น', 'เสื้อผ้า รองเท้า และเครื่องประดับ'),
('ความงาม', 'เครื่องสำอาง ผลิตภัณฑ์ดูแลผิว'),
('สุขภาพ', 'อาหารเสริม ผลิตภัณฑ์สุขภาพ'),
('บ้านและสวน', 'ของใช้ในบ้าน เครื่องใช้ไฟฟ้า'),
('กีฬา', 'อุปกรณ์กีฬา เสื้อผ้ากีฬา'),
('หนังสือ', 'หนังสือ อีบุ๊ก'),
('เด็กและของเล่น', 'ของเล่น เสื้อผ้าเด็ก'),
('อาหาร', 'อาหารและเครื่องดื่ม'),
('สัตว์เลี้ยง', 'อาหารและอุปกรณ์สัตว์เลี้ยง'),
('อื่นๆ', 'สินค้าอื่นๆ')
ON CONFLICT (name) DO NOTHING;

-- 6. เพิ่มข้อมูลสินค้าสัตว์เลี้ยงจาก CSV
INSERT INTO products (
    product_code, 
    product_name, 
    price, 
    sold_count,
    shop_name, 
    commission_rate, 
    commission_amount,
    product_link, 
    offer_link,
    category,
    description,
    rating
) VALUES
-- สินค้าที่ 1: อาหารกินเล่นของแมว CAT&DOG
('25934548047', 
 '【CAT&DOG】10PCS อาหารกินเล่นของแมว อาหารเสริมแมว อาหารเปียกสำหรับแมว ของกินเล่นแมว อาหารกินเล่นแมว', 
 1.00, 
 10000,
 'CAT&DOG', 
 9.75, 
 0.10,
 'https://shopee.co.th/product/1261216562/25934548047',
 'https://s.shopee.co.th/1LV3QgX09y',
 'สัตว์เลี้ยง',
 'อาหารกินเล่นของแมว อาหารเสริมแมว อาหารเปียกสำหรับแมว ของกินเล่นแมว 10 ชิ้น',
 4.5),

-- สินค้าที่ 2: TUBI แมวอาหารเปียก
('26250504053',
 'TUBI แมวอาหารเปียก อาหารแมวเปียก กระป๋องหลัก 85Gซุบแมว กระป๋อง ซุปแมว อาหารแมว ซุป ซุปแมวอาหารเปียก แมวกระป๋อง',
 12.00,
 10000,
 'TUBI Pet record',
 13.75,
 1.65,
 'https://shopee.co.th/product/1241023619/26250504053',
 'https://s.shopee.co.th/1VoTczWMp1',
 'สัตว์เลี้ยง',
 'แมวอาหารเปียก อาหารแมวเปียก กระป๋องหลัก 85G ซุบแมว กระป๋อง ซุปแมว อาหารแมว ซุป',
 4.6),

-- สินค้าที่ 3: อาหารเปียกแมว Interesting time
('26211374674',
 'อาหารเปียกแมว✨แมวกระป๋อง85g อาหารแมว ซุป ซุบแมว อินทรีย์ เกรวี่แมว ขนมแมวเลีย อาหารเปียกแมว อาหารแมวกระป๋องเปลือย',
 14.00,
 3000,
 'Interesting time',
 10.75,
 1.51,
 'https://shopee.co.th/product/1339653778/26211374674',
 'https://s.shopee.co.th/2LNacWTC8C',
 'สัตว์เลี้ยง',
 'อาหารเปียกแมว แมวกระป๋อง85g อาหารแมว ซุป ซุบแมว อินทรีย์ เกรวี่แมว ขนมแมวเลีย',
 4.4),

-- สินค้าที่ 4: FURRY PET RECORD แมวอาหารเปียก
('25676050898',
 'แมวอาหารเปียก อาหารแมวเปียก กระป๋องหลัก 85Gซุบแมว กระป๋อง ซุปแมว อาหารแมว ซุป ซุปแมวอาหารเปียก แมวกระป๋อง',
 12.00,
 1000,
 'FURRY PET RECORD',
 14.75,
 1.77,
 'https://shopee.co.th/product/1164047573/25676050898',
 'https://s.shopee.co.th/2Vh0opSYnF',
 'สัตว์เลี้ยง',
 'แมวอาหารเปียก อาหารแมวเปียก กระป๋องหลัก 85G ซุบแมว กระป๋อง ซุปแมว อาหารแมว ซุป',
 4.3),

-- สินค้าที่ 5: Pramy อาหารเปียกแมว  
('17798017195',
 '(1ซอง)Pramy อาหารเปียกแมว อาหารเปียกลูกแมว อาหารเปียกแมวโต อาหารเปียกแมวสูงวัย ในมูส เจลลี่ เกรวี่ ขนาด 70g.',
 17.00,
 60000,
 'PET VELAA',
 5.75,
 0.98,
 'https://shopee.co.th/product/831512945/17798017195',
 'https://s.shopee.co.th/40VobaMqkk',
 'สัตว์เลี้ยง',
 'Pramy อาหารเปียกแมว อาหารเปียกลูกแมว อาหารเปียกแมวโต อาหารเปียกแมวสูงวัย ในมูส เจลลี่ เกรวี่ ขนาด 70g',
 4.7),

-- สินค้าที่ 6: Ocean Star ซุปแมวผสมคอลลาเจน
('26237956745',
 '6 แพ็ค ซุปแมวผสมคอลลาเจน Ocean Star ซุปแมวเข้มข้น อาหารเปียกแมว อาหารแมว โปรตีนสูง ขนาด 100 กรัม แมว เด็ก 1 เดือน อาหาร',
 144.00,
 316,
 'PamperCat',
 1.75,
 2.52,
 'https://shopee.co.th/product/936203210/26237956745',
 'https://s.shopee.co.th/4ApEntMDPn',
 'สัตว์เลี้ยง',
 '6 แพ็ค ซุปแมวผสมคอลลาเจน Ocean Star ซุปแมวเข้มข้น อาหารเปียกแมว อาหารแมว โปรตีนสูง ขนาด 100 กรัม แมว เด็ก 1 เดือน',
 4.2)

-- ป้องกันข้อมูลซ้ำ
ON CONFLICT (product_code) DO UPDATE SET
    product_name = EXCLUDED.product_name,
    price = EXCLUDED.price,
    sold_count = EXCLUDED.sold_count,
    shop_name = EXCLUDED.shop_name,
    commission_rate = EXCLUDED.commission_rate,
    commission_amount = EXCLUDED.commission_amount,
    product_link = EXCLUDED.product_link,
    offer_link = EXCLUDED.offer_link,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    rating = EXCLUDED.rating,
    updated_at = NOW();

-- 7. สร้าง RLS (Row Level Security) policies
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_searches ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;

-- Policy สำหรับอ่านข้อมูลสินค้า (ทุกคนอ่านได้)
CREATE POLICY "Allow public read access on products" ON products
    FOR SELECT USING (true);

-- Policy สำหรับเพิ่ม/แก้ไขสินค้า (เฉพาะ authenticated users)
CREATE POLICY "Allow authenticated insert on products" ON products
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated update on products" ON products
    FOR UPDATE USING (auth.role() = 'authenticated');

-- Policy สำหรับ searches
CREATE POLICY "Allow public insert on searches" ON product_searches
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public read on searches" ON product_searches
    FOR SELECT USING (true);

-- Policy สำหรับ categories
CREATE POLICY "Allow public read access on categories" ON categories
    FOR SELECT USING (true);

-- 8. สร้าง Functions สำหรับการค้นหา
CREATE OR REPLACE FUNCTION get_popular_searches(search_limit INTEGER DEFAULT 10)
RETURNS TABLE (
    search_query TEXT,
    search_count BIGINT
) 
LANGUAGE SQL
AS $$
    SELECT 
        ps.search_query,
        COUNT(*) as search_count
    FROM product_searches ps
    WHERE ps.created_at >= NOW() - INTERVAL '30 days'
    GROUP BY ps.search_query
    ORDER BY search_count DESC
    LIMIT search_limit;
$$;

CREATE OR REPLACE FUNCTION get_average_price()
RETURNS DECIMAL(10,2)
LANGUAGE SQL
AS $$
    SELECT COALESCE(AVG(price), 0) FROM products;
$$;

-- 9. ตรวจสอบข้อมูลที่เพิ่มเข้าไป
SELECT 
    'สร้างฐานข้อมูลสำเร็จ!' as status,
    COUNT(*) as total_products
FROM products;

SELECT 
    product_code,
    product_name,
    price,
    sold_count,
    shop_name,
    commission_rate,
    commission_amount,
    rating
FROM products 
WHERE category = 'สัตว์เลี้ยง'
ORDER BY created_at DESC;