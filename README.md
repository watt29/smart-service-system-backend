# 🛍️ Affiliate Product Review Bot

LINE Bot สำหรับรีวิวสินค้าและ Affiliate Marketing ที่มีระบบ AI ช่วยในการค้นหาและสร้างเนื้อหา

## ✨ คุณสมบัติหลัก

### 📱 LINE Bot Features
- **ค้นหาสินค้า**: ค้นหาสินค้าด้วยชื่อ, หมวดหมู่, รหัสสินค้า
- **รีวิวสินค้า**: แสดงรายละเอียดสินค้าแบบ Flex Message
- **จัดการสินค้า**: เพิ่ม/แก้ไข/ลบสินค้า (สำหรับแอดมิน)
- **AI Search**: ค้นหาอัจฉริยะด้วย AI
- **สถิติการใช้งาน**: ดูสถิติและคำค้นหายอดนิยม

### 🗃️ Database Schema
**ตาราง `products`:**
```
| Field             | Type         | Description               |
|-------------------|--------------|---------------------------|
| id                | SERIAL       | Primary Key               |
| product_code      | VARCHAR(50)  | รหัสสินค้า (Unique)        |
| product_name      | VARCHAR(255) | ชื่อสินค้า                 |
| price             | DECIMAL      | ราคา                      |
| sold_count        | INTEGER      | จำนวนที่ขายแล้ว            |
| shop_name         | VARCHAR(255) | ชื่อร้านค้า                |
| commission_rate   | DECIMAL(5,2) | อัตราค่าคอมมิชชัน (%)      |
| commission_amount | DECIMAL      | จำนวนเงินคอมมิชชัน         |
| product_link      | TEXT         | ลิงก์สินค้า                |
| offer_link        | TEXT         | ลิงก์ Affiliate           |
| category          | VARCHAR(100) | หมวดหมู่                  |
| description       | TEXT         | คำอธิบายสินค้า             |
| image_url         | TEXT         | URL รูปภาพ               |
| rating            | DECIMAL(3,2) | คะแนนรีวิว (1-5)          |
```

### 🚀 API Endpoints

#### Authentication
- `GET /` - หน้าแรก + ข้อมูล API
- `GET /health` - ตรวจสอบสถานะระบบ

#### Products Management
- `GET /api/products` - ดึงสินค้าทั้งหมด
- `POST /api/products` - เพิ่มสินค้าใหม่
- `PUT /api/products?code={product_code}` - อัปเดตสินค้า
- `DELETE /api/products?code={product_code}` - ลบสินค้า

#### Search & Analytics
- `GET /api/search?query={query}&limit={limit}&ai={true/false}` - ค้นหาสินค้า
- `GET /api/stats` - ดูสถิติระบบ

#### Review Generation
- `POST /api/review` - สร้างรีวิวสินค้า

#### LINE Bot
- `POST /callback` - LINE Bot Webhook

## 🛠️ การติดตั้ง

### 1. Clone Repository
```bash
git clone <repository-url>
cd affiliate-product-review-bot
```

### 2. ติดตั้ง Dependencies
```bash
pip install -r requirements.txt
```

### 3. ตั้งค่า Environment Variables
สร้างไฟล์ `.env`:
```env
# LINE Bot Configuration
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret

# Supabase Configuration (แนะนำ)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
USE_SUPABASE=true

# AI Configuration (ไม่บังคับ)
OPENAI_API_KEY=your_openai_api_key
USE_AI_SEARCH=false

# Application Settings
DEBUG=false
PORT=5000
HOST=0.0.0.0
SECRET_KEY=your-secret-key

# Affiliate Settings
DEFAULT_COMMISSION_RATE=5.0
MAX_RESULTS_PER_SEARCH=5
```

### 4. ตั้งค่าฐานข้อมูล Supabase
1. สร้างโปรเจค Supabase ใหม่
2. รันคำสั่ง SQL ใน `create_supabase_tables.sql`
3. ตั้งค่า RLS policies ตามที่ระบุในไฟل์

### 5. รันแอปพลิเคชัน
```bash
python main.py
```

## 🎯 การใช้งาน LINE Bot

### สำหรับผู้ใช้ทั่วไป:
- **ค้นหาสินค้า**: พิมพ์ชื่อสินค้าหรือหมวดหมู่
- **ค้นหาด้วยรหัส**: พิมพ์ `รหัส PHONE001`
- **ดูหมวดหมู่**: พิมพ์ `หมวดหมู่`
- **ดูสถิติ**: พิมพ์ `สถิติ`

### สำหรับแอดมิน:
- **เข้าสู่โหมดแอดมิน**: พิมพ์ `แอดมิน` หรือ `admin`
- **เพิ่มสินค้า**: เลือก "➕ เพิ่มสินค้า"
- **จัดการสินค้า**: เลือกเมนูที่ต้องการ

## 🤖 AI Features

### AI Search
- ขยายคำค้นหาด้วยคำพ้องความหมาย
- จัดอันดับผลลัพธ์แบบอัจฉริยะ
- วิเคราะห์เจตนาการค้นหา
- แนะนำคำค้นหาทางเลือก

### Review Generation
- สร้างรีวิวอัตโนมัติ 3 รูปแบบ (สั้น/กลาง/ยาว)
- รองรับการสร้างด้วย AI (OpenAI)
- เทมเพลตที่หลากหลาย
- วิเคราะห์สถิติรีวิว

## 📊 ตัวอย่างการใช้งาน API

### ค้นหาสินค้า
```bash
curl "http://localhost:5000/api/search?query=iPhone&limit=5&ai=true"
```

### เพิ่มสินค้าใหม่
```bash
curl -X POST http://localhost:5000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "product_code": "PHONE002",
    "product_name": "Samsung Galaxy S24",
    "price": 35900,
    "shop_name": "Samsung Store",
    "commission_rate": 4.0,
    "product_link": "https://example.com/galaxy-s24",
    "offer_link": "https://affiliate.link/galaxy-s24",
    "category": "อิเล็กทรอนิกส์",
    "description": "สมาร์ทโฟนรุ่นล่าสุดจาก Samsung"
  }'
```

### สร้างรีวิวสินค้า
```bash
curl -X POST http://localhost:5000/api/review \
  -H "Content-Type: application/json" \
  -d '{
    "product_code": "PHONE002",
    "style": "medium",
    "ai": false,
    "count": 1
  }'
```

## 📁 โครงสร้างโปรเจค

```
📦 Affiliate Product Review Bot
├── 📂 src/
│   ├── 📂 config/
│   │   └── 📜 config.py           # การตั้งค่าระบบ
│   ├── 📂 handlers/
│   │   └── 📜 affiliate_handler.py # LINE Bot Handler
│   └── 📂 utils/
│       ├── 📜 supabase_database.py # Supabase Database
│       ├── 📜 ai_search.py         # AI Search Engine
│       └── 📜 review_generator.py  # Review Generator
├── 📜 main.py                      # Flask Application
├── 📜 requirements.txt             # Dependencies
├── 📜 create_supabase_tables.sql   # Database Schema
├── 📜 Procfile                     # Heroku Config
└── 📜 README.md                    # คู่มือนี้
```

## 🚀 Deployment

### Heroku
1. สร้าง Heroku App
2. ตั้งค่า Environment Variables
3. Deploy:
```bash
git add .
git commit -m "Deploy affiliate bot"
git push heroku main
```

### อื่นๆ
แอปพลิเคชันรองรับ Docker และ cloud platforms อื่นๆ

## 🔧 การปรับแต่ง

### เพิ่มหมวดหมู่สินค้าใหม่
แก้ไขไฟล์ `src/utils/ai_search.py`:
```python
self.categories = {
    'หมวดหมู่ใหม่': ['คำค้นหาที่เกี่ยวข้อง', 'keyword2'],
    # ...
}
```

### เพิ่มเทมเพลตรีวิว
แก้ไขไฟล์ `src/utils/review_generator.py`:
```python
self.review_templates = {
    'custom': [
        "เทมเพลตใหม่: {product_name}..."
    ]
}
```

## 🤝 Contributing

1. Fork โปรเจค
2. สร้าง Feature Branch
3. Commit การเปลี่ยนแปลง
4. Push ไปยัง Branch
5. สร้าง Pull Request

## 📄 License

MIT License - ดูรายละเอียดในไฟล์ LICENSE

## 🆘 Support

หากมีปัญหาหรือข้อสงสัย:
1. เปิด Issue ใน GitHub
2. ติดต่อผู้พัฒนา
3. ดูเอกสาร API ที่ `/` endpoint

---

**🛍️ Happy Affiliate Marketing!** 
สร้างรายได้จากการรีวิวสินค้าด้วย AI Bot ที่ทรงพลัง
