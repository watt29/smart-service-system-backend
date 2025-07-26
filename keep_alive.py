#!/usr/bin/env python3
"""
Keep-Alive Script สำหรับ Heroku Free Tier
ป้องกันเซิร์ฟเวอร์หยุดทำงานหลังจาก 30 นาที
"""

import requests
import time
import logging
from datetime import datetime

# ตั้งค่า logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# URL ของแอป Heroku
APP_URL = "https://appreciate-1234-335b96804c19.herokuapp.com"
PING_INTERVAL = 25 * 60  # 25 นาที (ก่อนที่ Heroku จะหยุด 30 นาทีครับ)

def ping_server():
    """Ping เซิร์ฟเวอร์เพื่อให้ทำงานต่อ"""
    try:
        # Ping endpoint หลัก
        response = requests.get(f"{APP_URL}/ping", timeout=30)
        
        if response.status_code == 200:
            logger.info(f"✅ Ping สำเร็จ - Status: {response.status_code}")
            
            # ตรวจสอบ health
            health_response = requests.get(f"{APP_URL}/health", timeout=30)
            if health_response.status_code == 200:
                health_data = health_response.json()
                logger.info(f"📊 Health: {health_data.get('status')} - Products: {health_data.get('products_count', 0)}")
            
            return True
        else:
            logger.warning(f"⚠️ Ping ไม่สำเร็จ - Status: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ping error: {e}")
        return False

def keep_alive():
    """Keep-alive main loop"""
    logger.info("🚀 เริ่มต้น Keep-Alive Service")
    logger.info(f"📍 Target: {APP_URL}")
    logger.info(f"⏰ Interval: {PING_INTERVAL // 60} นาที")
    
    while True:
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"🔄 Pinging at {current_time}")
            
            success = ping_server()
            
            if success:
                logger.info("😴 Sleeping for next ping...")
            else:
                logger.warning("⚠️ Ping failed, retrying in 5 minutes...")
                time.sleep(5 * 60)  # รอ 5 นาทีถ้า ping ไม่สำเร็จ
                continue
                
            time.sleep(PING_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("⏹️ Keep-Alive หยุดทำงานโดยผู้ใช้")
            break
        except Exception as e:
            logger.error(f"💥 Unexpected error: {e}")
            time.sleep(60)  # รอ 1 นาทีแล้วลองใหม่

if __name__ == "__main__":
    keep_alive()