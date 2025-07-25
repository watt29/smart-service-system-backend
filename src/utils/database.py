"""
Database Manager สำหรับ Smart Service System
จัดการ Knowledge Base และการค้นหาข้อมูล
"""

import json
import os
import re
from typing import Dict, List, Tuple, Optional
from ..config import config
from .logger import system_logger, error_handler, performance_monitor

class KnowledgeBaseManager:
    """คลาสสำหรับจัดการ Knowledge Base"""
    
    def __init__(self):
        self.knowledge_base = {}
        self.file_path = config.get_database_path()
        self.load_knowledge_base()
    
    def load_knowledge_base(self) -> bool:
        """โหลดข้อมูลจาก JSON file"""
        performance_monitor.start_timer("load_knowledge_base")
        
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.knowledge_base = json.load(f)
                
                system_logger.info(f"โหลดข้อมูล {len(self.knowledge_base)} รายการจาก {self.file_path}")
                performance_monitor.end_timer("load_knowledge_base")
                return True
            else:
                system_logger.info(f"ไม่พบไฟล์ {self.file_path} สร้างฐานข้อมูลเปล่า")
                self.knowledge_base = {}
                performance_monitor.end_timer("load_knowledge_base")
                return False
                
        except json.JSONDecodeError as e:
            error_result = error_handler.handle_database_error("load_json", e)
            system_logger.error("ไฟล์ JSON เสียหาย", e)
            self.knowledge_base = {}
            performance_monitor.end_timer("load_knowledge_base")
            return False
            
        except Exception as e:
            error_result = error_handler.handle_database_error("load_knowledge_base", e)
            self.knowledge_base = {}
            performance_monitor.end_timer("load_knowledge_base")
            return False
    
    def save_knowledge_base(self) -> bool:
        """บันทึกข้อมูลลง JSON file"""
        performance_monitor.start_timer("save_knowledge_base")
        
        try:
            # สร้าง backup ก่อนบันทึก
            if os.path.exists(self.file_path):
                backup_path = f"{self.file_path}.backup"
                os.rename(self.file_path, backup_path)
                system_logger.debug(f"สร้าง backup: {backup_path}")
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_base, f, ensure_ascii=False, indent=4)
            
            system_logger.info(f"บันทึกข้อมูล {len(self.knowledge_base)} รายการลง {self.file_path}")
            performance_monitor.end_timer("save_knowledge_base")
            return True
            
        except Exception as e:
            error_result = error_handler.handle_database_error("save_knowledge_base", e)
            performance_monitor.end_timer("save_knowledge_base")
            return False
    
    def fuzzy_search(self, query: str) -> List[Tuple[str, Dict]]:
        """ค้นหาข้อมูลแบบ fuzzy search"""
        query_lower = query.lower().strip()
        found_items = []
        
        for key, item in self.knowledge_base.items():
            # ค้นหาใน key
            if query_lower in key.lower():
                found_items.append((key, item))
                continue
                
            # ค้นหาในชื่อภาษาไทย
            if query_lower in item.get('name_th', '').lower():
                found_items.append((key, item))
                continue
                
            # ค้นหาในชื่อภาษาอังกฤษ
            if query_lower in item.get('name_en', '').lower():
                found_items.append((key, item))
                continue
                
            # ค้นหาในรหัส CGD
            if query_lower in item.get('cgd_code', '').lower():
                found_items.append((key, item))
                continue
                
            # ค้นหาในรหัส CPT
            if query_lower in item.get('cpt', '').lower():
                found_items.append((key, item))
                continue
                
            # ค้นหาในรหัส ICD-10
            if query_lower in item.get('icd10', '').lower():
                found_items.append((key, item))
                continue
        
        return found_items
    
    def add_item(self, key: str, item_data: Dict) -> bool:
        """เพิ่มรายการใหม่"""
        try:
            # ตรวจสอบว่า key ไม่ซ้ำ
            if key.lower() in [k.lower() for k in self.knowledge_base.keys()]:
                print(f"[ERROR] รหัส '{key}' มีอยู่แล้ว")
                return False
            
            # ตรวจสอบข้อมูลที่จำเป็น
            required_fields = ['name_th', 'name_en', 'rate_baht']
            for field in required_fields:
                if field not in item_data:
                    print(f"[ERROR] ข้อมูล '{field}' จำเป็นต้องระบุ")
                    return False
            
            # ตั้งค่าเริ่มต้นสำหรับข้อมูลที่ไม่ได้ระบุ
            default_data = {
                'claimable': True,
                'rights': ['กรมบัญชีกลาง', 'ทุกสิทธิ'],
                'cgd_code': 'N/A',
                'cpt': 'N/A',
                'icd10': 'N/A',
                'notes': ''
            }
            
            # รวมข้อมูลเริ่มต้นกับข้อมูลที่ได้รับ
            final_data = {**default_data, **item_data}
            
            self.knowledge_base[key] = final_data
            return self.save_knowledge_base()
            
        except Exception as e:
            print(f"[ERROR] เกิดข้อผิดพลาดในการเพิ่มรายการ: {e}")
            return False
    
    def update_item(self, key: str, field: str, new_value) -> bool:
        """อัปเดตข้อมูลรายการ"""
        try:
            if key not in self.knowledge_base:
                print(f"[ERROR] ไม่พบรหัส '{key}'")
                return False
            
            if field not in self.knowledge_base[key]:
                print(f"[ERROR] ไม่พบฟิลด์ '{field}'")
                return False
            
            # แปลงประเภทข้อมูลตามฟิลด์
            if field == 'rate_baht':
                new_value = float(new_value)
            elif field == 'claimable':
                new_value = str(new_value).lower() == 'true'
            elif field == 'rights':
                if isinstance(new_value, str):
                    new_value = [s.strip() for s in new_value.split(',')]
            
            self.knowledge_base[key][field] = new_value
            return self.save_knowledge_base()
            
        except Exception as e:
            print(f"[ERROR] เกิดข้อผิดพลาดในการอัปเดต: {e}")
            return False
    
    def delete_item(self, key: str) -> bool:
        """ลบรายการ"""
        try:
            if key not in self.knowledge_base:
                print(f"[ERROR] ไม่พบรหัส '{key}'")
                return False
            
            del self.knowledge_base[key]
            return self.save_knowledge_base()
            
        except Exception as e:
            print(f"[ERROR] เกิดข้อผิดพลาดในการลบ: {e}")
            return False
    
    def get_item(self, key: str) -> Optional[Dict]:
        """ดึงข้อมูลรายการ"""
        return self.knowledge_base.get(key)
    
    def get_all_items(self) -> Dict:
        """ดึงข้อมูลทั้งหมด"""
        return self.knowledge_base.copy()
    
    def get_summary(self) -> Dict:
        """ดึงสรุปข้อมูลในฐานข้อมูล"""
        total_items = len(self.knowledge_base)
        claimable_items = sum(1 for item in self.knowledge_base.values() 
                            if item.get('claimable', False))
        
        # หาอัตราเฉลี่ย
        rates = [item.get('rate_baht', 0) for item in self.knowledge_base.values()]
        avg_rate = sum(rates) / len(rates) if rates else 0
        
        return {
            'total_items': total_items,
            'claimable_items': claimable_items,
            'average_rate': round(avg_rate, 2),
            'min_rate': min(rates) if rates else 0,
            'max_rate': max(rates) if rates else 0
        }

# สร้าง instance สำหรับใช้งาน
db_manager = KnowledgeBaseManager()