"""
Migration Script - ย้ายข้อมูลจาก JSON เป็น SQLite
สำหรับ Smart Service System
"""

import os
import sys
from src.utils.sqlite_database import sqlite_db_manager
from src.utils.logger import system_logger

def main():
    """ย้ายข้อมูลจาก JSON เป็น SQLite"""
    
    print("=" * 50)
    print("[MIGRATE] Smart Service System - Database Migration")
    print("=" * 50)
    
    json_file = "knowledge_base.json"
    
    # ตรวจสอบไฟล์ JSON
    if not os.path.exists(json_file):
        print(f"[ERROR] ไม่พบไฟล์ {json_file}")
        return False
    
    print(f"[INFO] พบไฟล์ JSON: {json_file}")
    
    # ทำการ migrate
    print("[START] เริ่มย้ายข้อมูล...")
    
    try:
        success = sqlite_db_manager.migrate_from_json(json_file)
        
        if success:
            print("[OK] ย้ายข้อมูลสำเร็จ!")
            
            # แสดงสถิติ
            summary = sqlite_db_manager.get_summary()
            print("\n[STATS] สรุปข้อมูลใน SQLite:")
            print(f"   รายการทั้งหมด: {summary['total_items']}")
            print(f"   เบิกได้: {summary['claimable_items']}")
            print(f"   อัตราเฉลี่ย: {summary['average_rate']:.2f} บาท")
            print(f"   อัตราสูงสุด: {summary['max_rate']:.2f} บาท")
            print(f"   อัตราต่ำสุด: {summary['min_rate']:.2f} บาท")
            
            # สำรองไฟล์ JSON
            backup_file = f"{json_file}.backup"
            os.rename(json_file, backup_file)
            print(f"\n[BACKUP] สำรองไฟล์เดิมเป็น: {backup_file}")
            
            print("\n[COMPLETE] Migration เสร็จสิ้น!")
            print("ตอนนี้ระบบจะใช้ SQLite database แทน JSON")
            
            return True
            
        else:
            print("[ERROR] ย้ายข้อมูลไม่สำเร็จ")
            return False
            
    except Exception as e:
        print(f"[ERROR] เกิดข้อผิดพลาด: {e}")
        system_logger.error("Migration failed", e)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)