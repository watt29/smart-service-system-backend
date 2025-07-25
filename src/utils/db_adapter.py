"""
Database Adapter สำหรับ Smart Service System
สลับระหว่าง JSON และ SQLite database ได้
"""

from ..config import config
from .logger import system_logger

class DatabaseAdapter:
    """คลาสสำหรับจัดการการสลับระหว่าง database systems"""
    
    def __init__(self):
        self.manager = None
        self._init_manager()
    
    def _init_manager(self):
        """เลือกและสร้าง database manager"""
        if config.USE_SQLITE:
            try:
                # Lazy import เพื่อลด startup time
                import sys
                if 'src.utils.sqlite_database' not in sys.modules:
                    from .sqlite_database import sqlite_db_manager
                else:
                    sqlite_db_manager = sys.modules['src.utils.sqlite_database'].sqlite_db_manager
                
                self.manager = sqlite_db_manager
                system_logger.debug("Using SQLite database")  # เปลี่ยนเป็น debug
            except Exception as e:
                system_logger.error("SQLite init failed, falling back to JSON", e)
                self._use_json()
        else:
            self._use_json()
    
    def _use_json(self):
        """ใช้ JSON database"""
        from .database import db_manager
        self.manager = db_manager
        system_logger.info("Using JSON database")
    
    # Proxy methods - ส่งต่อไปยัง manager ที่เลือก
    
    def fuzzy_search(self, query: str):
        """ค้นหาข้อมูลแบบ fuzzy search"""
        if config.USE_SQLITE:
            # SQLite returns list of dicts
            results = self.manager.fuzzy_search(query)
            # แปลงให้เหมือน JSON format (list of tuples)
            return [(item['key'], item) for item in results]
        else:
            # JSON returns list of tuples
            return self.manager.fuzzy_search(query)
    
    def add_item(self, key: str, item_data: dict) -> bool:
        """เพิ่มรายการใหม่"""
        return self.manager.add_item(key, item_data)
    
    def update_item(self, key: str, field: str, new_value) -> bool:
        """อัปเดตข้อมูลรายการ"""
        return self.manager.update_item(key, field, new_value)
    
    def delete_item(self, key: str) -> bool:
        """ลบรายการ"""
        return self.manager.delete_item(key)
    
    def get_item(self, key: str):
        """ดึงข้อมูลรายการ"""
        return self.manager.get_item(key)
    
    def get_all_items(self):
        """ดึงข้อมูลทั้งหมด"""
        if config.USE_SQLITE:
            # SQLite returns list of full dicts
            items = self.manager.get_all_items()
            # แปลงเป็น dict[key] = item_data format
            return {item['key']: item for item in items}
        else:
            # JSON returns dict[key] = item_data
            return self.manager.get_all_items()
    
    def get_summary(self) -> dict:
        """ดึงสรุปข้อมูลในฐานข้อมูล"""
        return self.manager.get_summary()
    
    def get_search_stats(self, limit: int = 10):
        """ดึงสถิติการค้นหา (SQLite only)"""
        if config.USE_SQLITE and hasattr(self.manager, 'get_search_stats'):
            return self.manager.get_search_stats(limit)
        else:
            return {'popular_queries': [], 'success_rate': 0, 'daily_searches': []}

# สร้าง instance สำหรับใช้งาน
db_adapter = DatabaseAdapter()