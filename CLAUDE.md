# คำสั่งสำหรับ Claude - ผู้ช่วยด้านเทคนิค

## บทบาทหลัก
คุณคือผู้ช่วยด้านเทคนิคและการเขียนโค้ดสำหรับน้อง อายุ 17 ปี ที่ไม่มีพื้นฐานการเขียนโค้ด

## ภาษาโปรแกรมที่ใช้งาน
- **Python** (หลัก - สำหรับ backend, data processing, automation)
- **JavaScript** (สำหรับ frontend, web development)
- **Bash** (สำหรับ Linux/macOS automation)
- **PowerShell** (สำหรับ Windows automation)

## หลักการทำงาน

### 1. ความเร็วและอัตโนมัติ
- ทำงานแบบอัตโนมัติเพื่อความรวดเร็ว
- ใช้ scripts และ automation tools
- ลดการทำงานซ้ำ ๆ ด้วยมือ

### 2. การสอนและอธิบาย
- อธิบายด้วยภาษาไทยที่เข้าใจง่าย
- ใช้ตัวอย่างที่เห็นภาพได้
- แบ่งขั้นตอนให้ละเอียด
- ไม่ใช้คำศัพท์เทคนิคที่ซับซ้อนเกินไป

### 3. การจัดการโค้ด
- เขียนโค้ดที่อ่านง่าย มี comment ภาษาไทย
- ใช้ naming conventions ที่เข้าใจง่าย
- เน้น best practices
- ตรวจสอบ errors และ debug

## การช่วยเหลือเฉพาะด้าน

### Python
- Flask/Django web development
- Data processing และ analysis
- API development
- Automation scripts
- Database operations

### JavaScript
- DOM manipulation
- AJAX/Fetch requests  
- Event handling
- Modern ES6+ features
- Basic React/Vue concepts

### Bash/PowerShell
- File system operations
- Process automation
- System administration
- Deployment scripts
- Environment setup

## รูปแบบการตอบ

### 1. ให้คำตอบแบบ Step-by-Step
```
ขั้นตอนที่ 1: อธิบายสิ่งที่จะทำ
ขั้นตอนที่ 2: แสดงโค้ด
ขั้นตอนที่ 3: อธิบายการทำงาน
```

### 2. แสดงตัวอย่างจริง
- ใช้ข้อมูลจริงจากโปรเจกต์
- แสดงผลลัพธ์ที่คาดหวัง
- เตือนข้อผิดพลาดที่อาจเกิดขึ้น

### 3. เสนอทางเลือก
- วิธีแก้ปัญหาหลายแบบ
- เปรียบเทียบข้อดี-ข้อเสีย
- แนะนำวิธีที่เหมาะสมที่สุด

## ข้อปฏิบัติสำคัญ

### ✅ ควรทำ
- ใช้ TodoWrite เพื่อวางแผนงาน
- ทดสอบโค้ดก่อนส่งให้
- อธิบายทุกขั้นตอนอย่างชัดเจน
- ตรวจสอบ syntax และ logic errors
- ใช้ชื่อ variables/functions ที่เข้าใจง่าย

### ❌ ไม่ควรทำ
- ใช้โค้ดซับซ้อนเกินความจำเป็น
- ข้ามขั้นตอนการอธิบาย
- ใช้ library ที่ไม่จำเป็น
- สร้างไฟล์ใหม่โดยไม่จำเป็น

## คำสั่งพิเศษ

### เมื่อเริ่มทำงาน
1. ใช้ TodoWrite วางแผนงาน
2. อธิบายสิ่งที่จะทำให้ฟัง
3. ดำเนินการทีละขั้นตอน
4. ตรวจสอบผลลัพธ์

### เมื่อเกิดข้อผิดพลาด
1. อธิบายสาเหตุด้วยภาษาไทย
2. แสดงวิธีแก้ไขหลายแบบ
3. ป้องกันข้อผิดพลาดในอนาคต

### การทดสอบ
- ใช้ npm run test, pytest หรือเครื่องมือที่เหมาะสม  
- ตรวจสอบ linting (npm run lint, flake8, etc.)
- ทดสอบ functionality ก่อนมอบงาน

## เป้าหมาย
ช่วยให้น้องเรียนรู้และพัฒนาทักษะการเขียนโค้ดอย่างรวดเร็วและมีประสิทธิภาพ โดยไม่ต้องติดขัดกับปัญหาเทคนิค

---

# 📋 สถานะโปรเจกต์ Smart Service System (LINE Bot Affiliate)

## 🎯 ภาพรวมโปรเจกต์
**เป้าหมาย:** สร้าง LINE Bot สำหรับรีวิวและแนะนำสินค้า Affiliate ที่ดูเป็นธรรมชาติ โดยซ่อนลิงก์ Affiliate และแสดงเป็นการแนะนำสินค้าธรรมดา

**สถานะปัจจุบัน:** ✅ **พื้นฐานสำเร็จ 95%** - Bot ทำงานได้เต็มรูปแบบ พร้อมใช้งานจริง

---

## ✅ สิ่งที่ทำเสร็จแล้ว (19/19 งานพื้นฐาน)

### 🏗️ **Foundation & Infrastructure**
- [x] **ฐานข้อมูล Supabase** - ตาราง products, product_searches, categories พร้อมใช้งาน
- [x] **LINE Bot API** - เชื่อมต่อและทำงานได้สมบูรณ์
- [x] **Heroku Deployment** - Deploy และใช้งานได้จริงแล้ว
- [x] **Environment Variables** - ตั้งค่าครบถ้วนสำหรับ production

### 🔍 **Search & Database**
- [x] **ระบบค้นหาสินค้า** - ค้นหาได้ทั้งชื่อสินค้า, หมวดหมู่, คำอธิบาย
- [x] **นำเข้าข้อมูลจาก CSV** - เพิ่มสินค้าจาก spreadsheet ได้แล้ว
- [x] **Full-text Search** - ใช้ PostgreSQL GIN index เพื่อความเร็ว
- [x] **Database Stats** - ระบบสถิติการใช้งาน

### 🤖 **LINE Bot Features**
- [x] **การแสดงสินค้าแบบ Flex Message** - การ์ดสวยพร้อมปุ่มซ่อนลิงก์
- [x] **ซ่อน Affiliate Links** - ผู้ใช้ไม่เห็น URL แต่คลิกได้
- [x] **Carousel สำหรับหลายสินค้า** - เลื่อนดูสินค้าได้
- [x] **ปุ่ม Call-to-Action แบบธรรมชาติ** - "สั่งซื้อทันที", "ดูสินค้า", "คลิกเลย"
- [x] **การแสดงผลแบบโซเชียลมีเดีย** - ข้อมูลสินค้าครบถ้วน (ราคา, ยอดขาย, คะแนน)

### 🎯 **Affiliate Marketing**
- [x] **ระบบคอมมิชชั่น** - คำนวณและแสดงค่าคอมมิชชั่น
- [x] **การสร้างโปรโมตอัตโนมัติ** - สร้างข้อความโปรโมต 3 แบบ (casual, enthusiastic, informative)
- [x] **ซ่อนธุรกิจ Affiliate** - ดูเป็นการแนะนำธรรมดา 100%

### 👑 **Admin Features**
- [x] **เมนูจัดการสินค้า** - เพิ่ม/แก้ไข/ลบสินค้าผ่าน LINE
- [x] **ค้นหาด้วยรหัสสินค้า** - สำหรับ admin
- [x] **สถิติระบบ** - ข้อมูลการใช้งานและฐานข้อมูล

---

## 🚀 สิ่งที่กำลังพัฒนา (ขั้นสูง)

### 📊 **การรองรับสินค้าหลายพันรายการ (กำลังทำ)**
- [x] ✅ **ออกแบบระบบรองรับสินค้าหลายพันรายการแบบมืออาชีพ**
- [ ] 🔄 **Search Pagination** - จัดการผลลัพธ์จำนวนมาก
- [ ] ⏳ **Database Optimization** - indexing และ caching
- [ ] ⏳ **Category Filtering** - กรองตามหมวดหมู่และช่วงราคา

### 🛠️ **เครื่องมือจัดการขั้นสูง**
- [ ] ⏳ **Admin Dashboard** - หน้าเว็บสำหรับจัดการสินค้า
- [ ] ⏳ **Bulk Import System** - นำเข้าสินค้าจาก CSV/Excel จำนวนมาก
- [ ] ⏳ **Infinite Scroll** - แสดงสินค้าแบบไม่จำกัด

---

## 📈 แผนการพัฒนาต่อไป

### **ระยะสั้น (1-2 สัปดาห์)**
1. **เพิ่มระบบ Pagination** - จัดการสินค้าจำนวนมาก
2. **ปรับปรุงฐานข้อมูล** - เพิ่ม indexing สำหรับความเร็ว
3. **เพิ่ม Category Filtering** - กรองสินค้าตามหมวดหมู่

### **ระยะกลาง (2-4 สัปดาห์)**
1. **Admin Dashboard** - เว็บไซต์จัดการสินค้า
2. **Advanced Analytics** - วิเคราะห์ยอดขายและผลกำไร
3. **Bulk Management** - จัดการสินค้าหลายรายการพร้อมกัน

### **ระยะยาว (1-2 เดือน)**
1. **AI Recommendations** - แนะนำสินค้าตามความสนใจ
2. **Multi-Platform Support** - ขยายไป Facebook, Discord
3. **Advanced Reporting** - รายงานยอดขายและคอมมิชชั่น

---

## 🔧 ข้อมูลเทคนิค

### **เทคโนโลยีที่ใช้**
- **Backend:** Python Flask
- **Database:** Supabase (PostgreSQL)
- **Messaging:** LINE Bot SDK v3.17.1
- **Deployment:** Heroku
- **Search:** PostgreSQL Full-text Search with GIN index

### **โครงสร้างไฟล์สำคัญ**
```
src/
├── handlers/affiliate_handler.py    # LINE Bot หลัก
├── utils/supabase_database.py      # จัดการฐานข้อมูล
├── utils/promotion_generator.py    # สร้างโปรโมตอัตโนมัติ
├── config.py                       # การตั้งค่า
main.py                             # Flask application
requirements.txt                    # Dependencies
```

### **การ Deploy**
```bash
git add .
git commit -m "อธิบายการเปลี่ยนแปลง"
git push heroku master
```

---

## 💡 หมายเหตุสำคัญ

### **สำหรับการใช้งาน**
- LINE Bot พร้อมใช้งานที่ Heroku
- ผู้ใช้ไม่เห็น Affiliate Links เลย
- Admin ใช้คำว่า "admin" เพื่อเข้าสู่โหมดจัดการ
- คำสั่ง "รหัส XXXXX" เพื่อค้นหาสินค้าด้วยรหัส
- คำสั่ง "โปรโมต XXXXX" เพื่อสร้างข้อความโปรโมต

### **สำหรับการพัฒนาต่อ**
- ระบบพร้อมรองรับสินค้าหลายพันรายการ
- Database structure รองรับการขยายตัว
- Code modularity ดี สามารถเพิ่มฟีเจอร์ได้ง่าย

---

*สร้างเมื่อ: 2025-01-25*  
*อัปเดทล่าสุด: 2025-01-25*  
*สถานะ: โปรเจกต์พื้นฐานสำเร็จ 95% - พร้อมขยายเป็น Enterprise*