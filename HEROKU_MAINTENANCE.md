# 🚀 คู่มือการดูแลเซิร์ฟเวอร์ Heroku 

## 🔄 ปัญหาเซิร์ฟเวอร์หยุดทำงาน

### สาเหตุหลัก:
1. **Heroku Free Tier Sleep** - แอปฟรีจะหยุดหลังไม่ใช้งาน 30 นาที
2. **Memory Limit** - ใช้ RAM เกิน 512MB
3. **Database Connection Timeout** - Supabase connection หมดอายุ
4. **Build/Deploy Error** - Code มี bug ทำให้ crash

## 🛠️ วิธีแก้ไขเฉพาะหน้า

### 1. ตรวจสอบสถานะ
```bash
# ตรวจสอบว่าแอปทำงานหรือไม่
curl -I https://appreciate-1234-335b96804c19.herokuapp.com/

# ดู process status
heroku ps --app appreciate-1234

# ดู logs
heroku logs --tail --app appreciate-1234
```

### 2. Restart แอป
```bash
heroku restart --app appreciate-1234
```

### 3. ถ้ายังไม่ทำงาน - Deploy ใหม่
```bash
git add -A
git commit -m "🔧 Fix server issue"
git push heroku master
```

## 🛡️ วิธีป้องกันเซิร์ฟเวอร์หยุด

### 1. ใช้ Keep-Alive Script (วิธีฟรี):
```bash
# รันในเครื่องคอมพิวเตอร์ที่เปิดตลอด
python keep_alive.py
```

### 2. ใช้ UptimeRobot (วิธีแนะนำ):
- ไป https://uptimerobot.com/
- สร้าง monitor สำหรับ `https://appreciate-1234-335b96804c19.herokuapp.com/ping`
- ตั้งให้ ping ทุก 5 นาที

### 3. Upgrade Heroku Plan (วิธีที่ดีที่สุด):
```bash
# อัพเกรดเป็น Basic ($7/เดือน)
heroku ps:scale web=1:basic --app appreciate-1234
```

## 📊 Monitoring Endpoints

### Health Check:
```bash
curl https://appreciate-1234-335b96804c19.herokuapp.com/health
```

### Simple Ping:
```bash
curl https://appreciate-1234-335b96804c19.herokuapp.com/ping
```

### Main Status:
```bash
curl https://appreciate-1234-335b96804c19.herokuapp.com/
```

## 🔧 การแก้ไขปัญหาเฉพาะ

### ปัญหา: Bot ไม่ตอบใน LINE
1. ตรวจสอบ webhook URL ใน LINE Console
2. ตรวจสอบ environment variables:
   ```bash
   heroku config --app appreciate-1234
   ```

### ปัญหา: Database ไม่เชื่อมต่อ
1. ตรวจสอบ Supabase credentials
2. ทดสอบการเชื่อมต่อ:
   ```bash
   curl https://appreciate-1234-335b96804c19.herokuapp.com/health
   ```

### ปัญหา: Memory เกิน
1. ดู memory usage:
   ```bash
   heroku logs --source app --app appreciate-1234 | grep memory
   ```
2. Restart แอป:
   ```bash
   heroku restart --app appreciate-1234
   ```

## 📈 Best Practices

1. **Monitor แบบ Real-time**: ใช้ UptimeRobot หรือ Pingdom
2. **Backup Database**: Export ข้อมูล Supabase เป็นประจำ
3. **Update Dependencies**: Update Python packages เป็นประจำ
4. **Log Monitoring**: ดู Heroku logs เป็นประจำ
5. **Performance Testing**: ทดสอบ load และ response time

## 🆘 Emergency Contacts

- **Heroku Support**: https://help.heroku.com/
- **Supabase Support**: https://supabase.com/support  
- **LINE Developers**: https://developers.line.biz/

---

**📱 LINE Bot URL:** https://appreciate-1234-335b96804c19.herokuapp.com/
**🔗 Admin Dashboard:** พิมพ์ `/admin` ใน LINE Bot