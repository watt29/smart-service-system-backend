-- SQL สำหรับสร้างตารางใน Supabase
-- ใช้ SQL Editor ใน Supabase Dashboard

-- สร้างตาราง products
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

-- สร้างตาราง product_searches
CREATE TABLE IF NOT EXISTS product_searches (
    id SERIAL PRIMARY KEY,
    search_query VARCHAR(255) NOT NULL,
    product_id INTEGER REFERENCES products(id),
    user_id VARCHAR(255),
    result_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- สร้าง Index สำหรับการค้นหา
CREATE INDEX IF NOT EXISTS idx_products_name ON products USING GIN (to_tsvector('thai', product_name));
CREATE INDEX IF NOT EXISTS idx_products_description ON products USING GIN (to_tsvector('thai', description));
CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);
CREATE INDEX IF NOT EXISTS idx_products_code ON products (product_code);
CREATE INDEX IF NOT EXISTS idx_searches_query ON product_searches (search_query);

-- สร้าง Function สำหรับการค้นหาที่ได้รับความนิยม
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

-- สร้าง Function สำหรับคำนวณราคาเฉลี่ย
CREATE OR REPLACE FUNCTION get_average_price()
RETURNS DECIMAL(10,2)
LANGUAGE SQL
AS $$
    SELECT COALESCE(AVG(price), 0) FROM products;
$$;

-- สร้างตาราง categories สำหรับจัดหมวดหมู่
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- เพิ่มข้อมูลหมวดหมู่เริ่มต้น
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
('อื่นๆ', 'สินค้าอื่นๆ')
ON CONFLICT (name) DO NOTHING;

-- เพิ่มข้อมูลสินค้าตัวอย่าง
INSERT INTO products (
    product_code, product_name, price, sold_count, shop_name, 
    commission_rate, commission_amount, product_link, offer_link, 
    category, description, rating
) VALUES
('PHONE001', 'iPhone 15 Pro Max 256GB', 45900.00, 150, 'TechShop Thailand', 
 3.0, 1377.00, 'https://example.com/iphone15', 'https://affiliate.link/iphone15',
 'อิเล็กทรอนิกส์', 'สมาร์ทโฟนรุ่นล่าสุดจาก Apple พร้อมกล้อง Pro camera system', 4.8),

('LAPTOP001', 'MacBook Air M3 13" 8GB/256GB', 42900.00, 75, 'Apple Store TH',
 2.5, 1072.50, 'https://example.com/macbook-air', 'https://affiliate.link/macbook',
 'อิเล็กทรอนิกส์', 'แล็ปท็อปที่บางและเบา พร้อมชิป M3 ประสิทธิภาพสูง', 4.7),

('CREAM001', 'SK-II Facial Treatment Essence 230ml', 8900.00, 200, 'Beauty World',
 8.0, 712.00, 'https://example.com/skii', 'https://affiliate.link/skii',
 'ความงาม', 'เอสเซ้นส์บำรุงผิวหน้าสูตรเข้มข้น ช่วยให้ผิวกระจ่างใส', 4.6),

('SUPPLE001', 'Blackmores Bio C 1000mg 150 เม็ด', 890.00, 300, 'Health Plus',
 15.0, 133.50, 'https://example.com/bioc', 'https://affiliate.link/bioc',
 'สุขภาพ', 'วิตามินซีเข้มข้น ช่วยเสริมภูมิคุ้มกัน', 4.4),

('WATCH001', 'Apple Watch Series 9 GPS 45mm', 13900.00, 80, 'iStudio',
 4.0, 556.00, 'https://example.com/watch9', 'https://affiliate.link/applewatch',
 'อิเล็กทรอนิกส์', 'สมาร์ทวอทช์ที่ช่วยติดตามสุขภาพและออกกำลังกาย', 4.5)
ON CONFLICT (product_code) DO NOTHING;

-- สร้าง RLS (Row Level Security) policies
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