"""
Configuration สำหรับ Smart Service System
จัดการ environment variables และการตั้งค่าต่างๆ
"""

import os
from dotenv import load_dotenv

# โหลด environment variables จากไฟล์ .env
load_dotenv()

class Config:
    """คลาสสำหรับจัดการการตั้งค่าระบบ"""
    
    # LINE Bot Configuration
    LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
    LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
    
    # Database Configuration  
    KNOWLEDGE_BASE_FILE = 'knowledge_base.json'
    SQLITE_DATABASE = 'smart_service.db'
    USE_SQLITE = os.environ.get('USE_SQLITE', 'True').lower() == 'true'
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart-service-system-secret-key')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # External API Configuration
    CGD_BASE_URL = 'https://mbdb.cgd.go.th/wel/searchmed.jsp'
    REQUEST_TIMEOUT = 10  # วินาที
    
    # Admin Configuration
    ADMIN_KEYWORDS = ["admin", "แอดมิน", "เมนูแอดมิน"]
    CANCEL_KEYWORD = "cancel"
    
    @classmethod
    def validate_config(cls):
        """ตรวจสอบว่าการตั้งค่าที่จำเป็นมีครบหรือไม่"""
        missing_configs = []
        
        if not cls.LINE_CHANNEL_ACCESS_TOKEN:
            missing_configs.append('LINE_CHANNEL_ACCESS_TOKEN')
            
        if not cls.LINE_CHANNEL_SECRET:
            missing_configs.append('LINE_CHANNEL_SECRET')
            
        if missing_configs:
            print(f"[WARNING] ไม่พบการตั้งค่า: {', '.join(missing_configs)}")
            print("[INFO] LINE Bot จะทำงานในโหมดจำกัด")
            return False
            
        print("[OK] การตั้งค่าครบถ้วน")
        return True
    
    @classmethod
    def get_database_path(cls):
        """ได้ path ของ knowledge base file"""
        return os.path.abspath(cls.KNOWLEDGE_BASE_FILE)
    
    @classmethod
    def is_production(cls):
        """ตรวจสอบว่าอยู่ใน production mode หรือไม่"""
        return os.environ.get('ENVIRONMENT', 'development').lower() == 'production'

# สร้าง instance สำหรับใช้งาน
config = Config()