"""
Configuration สำหรับ Affiliate Product Review Bot
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
    
    # Supabase Configuration
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    
    # Database Configuration (Fallback to SQLite)
    SQLITE_DATABASE = 'affiliate_products.db'
    USE_SUPABASE = os.environ.get('USE_SUPABASE', 'True').lower() == 'true'
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'affiliate-review-bot-secret-key')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # AI Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    USE_AI_SEARCH = os.environ.get('USE_AI_SEARCH', 'False').lower() == 'true'
    
    # Affiliate Configuration
    DEFAULT_COMMISSION_RATE = float(os.environ.get('DEFAULT_COMMISSION_RATE', '5.0'))
    MAX_RESULTS_PER_SEARCH = int(os.environ.get('MAX_RESULTS_PER_SEARCH', '5'))
    
    # Admin Configuration
    ADMIN_KEYWORDS = ["admin", "แอดมิน", "เมนูแอดมิน", "จัดการสินค้า"]
    CANCEL_KEYWORD = "cancel"
    
    @classmethod
    def validate_config(cls):
        """ตรวจสอบว่าการตั้งค่าที่จำเป็นมีครบหรือไม่"""
        missing_configs = []
        
        # ตรวจสอบ LINE Bot settings
        if not cls.LINE_CHANNEL_ACCESS_TOKEN:
            missing_configs.append('LINE_CHANNEL_ACCESS_TOKEN')
        if not cls.LINE_CHANNEL_SECRET:
            missing_configs.append('LINE_CHANNEL_SECRET')
        
        # ตรวจสอบ Supabase settings (ถ้าเปิดใช้งาน)
        if cls.USE_SUPABASE:
            if not cls.SUPABASE_URL:
                missing_configs.append('SUPABASE_URL')
            if not cls.SUPABASE_KEY:
                missing_configs.append('SUPABASE_KEY')
        
        if missing_configs:
            print(f"[WARNING] ไม่พบการตั้งค่า: {', '.join(missing_configs)}")
            if cls.USE_SUPABASE and any('SUPABASE' in config for config in missing_configs):
                print("[INFO] จะใช้ SQLite แทน Supabase")
                cls.USE_SUPABASE = False
            return False
            
        print("[OK] การตั้งค่าครบถ้วน")
        return True
    
    @classmethod
    def get_database_name(cls):
        """ได้ชื่อฐานข้อมูลที่ใช้"""
        return "Supabase" if cls.USE_SUPABASE else "SQLite"
    
    @classmethod
    def is_production(cls):
        """ตรวจสอบว่าอยู่ใน production mode หรือไม่"""
        return os.environ.get('ENVIRONMENT', 'development').lower() == 'production'

# สร้าง instance สำหรับใช้งาน
config = Config()