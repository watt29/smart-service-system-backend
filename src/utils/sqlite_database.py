"""
SQLite Database Manager สำหรับ Smart Service System
จัดการฐานข้อมูล SQLite แทน JSON
"""

import sqlite3
import json
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from ..config import config
from .logger import system_logger, error_handler, performance_monitor

class SQLiteKnowledgeBaseManager:
    """คลาสสำหรับจัดการ Knowledge Base ด้วย SQLite"""
    
    def __init__(self, db_path: str = "smart_service.db"):
        self.db_path = db_path
        self.connection = None
        self._init_database()
    
    def _init_database(self):
        """สร้างฐานข้อมูลและตารางเริ่มต้น"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # ให้ผลลัพธ์เป็น dict-like
            
            # ปรับแต่ง SQLite เพื่อความเร็ว
            cursor = self.connection.cursor()
            cursor.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
            cursor.execute("PRAGMA synchronous = NORMAL")  # ลดการ sync
            cursor.execute("PRAGMA cache_size = 10000")   # เพิ่ม cache
            cursor.execute("PRAGMA temp_store = MEMORY")  # ใช้ memory สำหรับ temp
            
            # สร้างตาราง knowledge_base
            cursor = self.connection.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    name_th TEXT NOT NULL,
                    name_en TEXT NOT NULL,
                    rate_baht REAL NOT NULL,
                    claimable BOOLEAN DEFAULT TRUE,
                    rights TEXT NOT NULL,  -- JSON array
                    cgd_code TEXT DEFAULT 'N/A',
                    cpt TEXT DEFAULT 'N/A',
                    icd10 TEXT DEFAULT 'N/A',
                    notes TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # สร้างตาราง search_logs สำหรับติดตามการค้นหา  
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    found BOOLEAN NOT NULL,
                    result_key TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source TEXT DEFAULT 'api'  -- api, line, web
                )
            ''')
            
            # สร้าง index สำหรับการค้นหาที่เร็วขึ้น
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_key ON knowledge_base(key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_name_th ON knowledge_base(name_th)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_name_en ON knowledge_base(name_en)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_query ON search_logs(query)')
            
            self.connection.commit()
            system_logger.info(f"SQLite database initialized: {self.db_path}")
            
        except Exception as e:
            error_handler.handle_database_error("init_sqlite", e)
            raise
    
    def migrate_from_json(self, json_file_path: str) -> bool:
        """ย้ายข้อมูลจาก JSON file มาเป็น SQLite"""
        performance_monitor.start_timer("migrate_from_json")
        
        try:
            if not os.path.exists(json_file_path):
                system_logger.warning(f"JSON file not found: {json_file_path}")
                performance_monitor.end_timer("migrate_from_json")
                return False
            
            with open(json_file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            cursor = self.connection.cursor()
            migrated_count = 0
            
            for key, item in json_data.items():
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO knowledge_base 
                        (key, name_th, name_en, rate_baht, claimable, rights, cgd_code, cpt, icd10, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        key,
                        item.get('name_th', ''),
                        item.get('name_en', ''),
                        float(item.get('rate_baht', 0)),
                        bool(item.get('claimable', True)),
                        json.dumps(item.get('rights', []), ensure_ascii=False),
                        item.get('cgd_code', 'N/A'),
                        item.get('cpt', 'N/A'),
                        item.get('icd10', 'N/A'),
                        item.get('notes', '')
                    ))
                    migrated_count += 1
                    
                except Exception as e:
                    system_logger.error(f"Error migrating item {key}: {e}")
            
            self.connection.commit()
            system_logger.info(f"Migrated {migrated_count} items from JSON to SQLite")
            performance_monitor.end_timer("migrate_from_json")
            return True
            
        except Exception as e:
            error_handler.handle_database_error("migrate_from_json", e)
            performance_monitor.end_timer("migrate_from_json")
            return False
    
    def fuzzy_search(self, query: str, limit: int = 10) -> List[Dict]:
        """ค้นหาข้อมูลแบบ fuzzy search - เร็วขึ้น"""
        try:
            cursor = self.connection.cursor()
            query_lower = query.lower().strip()
            
            # ค้นหาแบบง่าย - เร็วกว่า
            search_sql = '''
                SELECT * FROM knowledge_base 
                WHERE LOWER(key) LIKE ? 
                   OR LOWER(name_th) LIKE ? 
                   OR LOWER(name_en) LIKE ?
                ORDER BY 
                    CASE 
                        WHEN LOWER(key) = ? THEN 1
                        WHEN LOWER(name_th) LIKE ? THEN 2
                        ELSE 3
                    END
                LIMIT ?
            '''
            
            like_query = f"%{query_lower}%"
            cursor.execute(search_sql, (
                like_query, like_query, like_query,
                query_lower, f"{query_lower}%",
                limit
            ))
            
            results = cursor.fetchall()
            
            # แปลงผลลัพธ์เป็น list of dict - แบบเร็ว
            items = []
            for row in results:
                item = dict(row)
                try:
                    item['rights'] = json.loads(item['rights'])
                except:
                    item['rights'] = ['กรมบัญชีกลาง']  # fallback
                items.append(item)
            
            # บันทึก search log (async ในอนาคต)
            if items:
                self._log_search_async(query, True, items[0]['key'])
            else:
                self._log_search_async(query, False, None)
            
            return items
            
        except Exception as e:
            print(f"[ERROR] SQLite search error: {e}")
            return []
    
    def _log_search_async(self, query: str, found: bool, result_key: str = None):
        """บันทึก search log แบบไม่บล็อก"""
        try:
            # ใช้ connection แยกเพื่อไม่บล็อก
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO search_logs (query, found, result_key, source)
                VALUES (?, ?, ?, ?)
            ''', (query, found, result_key, "line"))
            self.connection.commit()
        except:
            pass  # ไม่ให้ search log error กระทบการค้นหา
    
    def add_item(self, key: str, item_data: Dict) -> bool:
        """เพิ่มรายการใหม่"""
        performance_monitor.start_timer("sqlite_add_item")
        
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                INSERT INTO knowledge_base 
                (key, name_th, name_en, rate_baht, claimable, rights, cgd_code, cpt, icd10, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                key,
                item_data.get('name_th', ''),
                item_data.get('name_en', ''),
                float(item_data.get('rate_baht', 0)),
                bool(item_data.get('claimable', True)),
                json.dumps(item_data.get('rights', ['กรมบัญชีกลาง', 'ทุกสิทธิ']), ensure_ascii=False),
                item_data.get('cgd_code', 'N/A'),
                item_data.get('cpt', 'N/A'),
                item_data.get('icd10', 'N/A'),
                item_data.get('notes', '')
            ))
            
            self.connection.commit()
            system_logger.info(f"Added new item: {key}")
            performance_monitor.end_timer("sqlite_add_item")
            return True
            
        except sqlite3.IntegrityError:
            system_logger.error(f"Item with key '{key}' already exists")
            performance_monitor.end_timer("sqlite_add_item")
            return False
            
        except Exception as e:
            error_handler.handle_database_error("add_item", e)
            performance_monitor.end_timer("sqlite_add_item")
            return False
    
    def update_item(self, key: str, field: str, new_value) -> bool:
        """อัปเดตข้อมูลรายการ"""
        performance_monitor.start_timer("sqlite_update_item")
        
        try:
            cursor = self.connection.cursor()
            
            # ตรวจสอบว่า item มีอยู่จริง
            cursor.execute('SELECT id FROM knowledge_base WHERE key = ?', (key,))
            if not cursor.fetchone():
                system_logger.error(f"Item not found: {key}")
                performance_monitor.end_timer("sqlite_update_item")
                return False
            
            # แปลงประเภทข้อมูลตามฟิลด์
            if field == 'rate_baht':
                new_value = float(new_value)
            elif field == 'claimable':
                new_value = bool(new_value)
            elif field == 'rights':
                if isinstance(new_value, str):
                    new_value = json.dumps([s.strip() for s in new_value.split(',')], ensure_ascii=False)
                else:
                    new_value = json.dumps(new_value, ensure_ascii=False)
            
            # อัปเดตข้อมูล
            update_sql = f'UPDATE knowledge_base SET {field} = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?'
            cursor.execute(update_sql, (new_value, key))
            
            self.connection.commit()
            system_logger.info(f"Updated item {key}: {field} = {new_value}")
            performance_monitor.end_timer("sqlite_update_item")
            return True
            
        except Exception as e:
            error_handler.handle_database_error("update_item", e)
            performance_monitor.end_timer("sqlite_update_item")
            return False
    
    def delete_item(self, key: str) -> bool:
        """ลบรายการ"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('DELETE FROM knowledge_base WHERE key = ?', (key,))
            
            if cursor.rowcount > 0:
                self.connection.commit()
                system_logger.info(f"Deleted item: {key}")
                return True
            else:
                system_logger.error(f"Item not found for deletion: {key}")
                return False
                
        except Exception as e:
            error_handler.handle_database_error("delete_item", e)
            return False
    
    def get_item(self, key: str) -> Optional[Dict]:
        """ดึงข้อมูลรายการ"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM knowledge_base WHERE key = ?', (key,))
            row = cursor.fetchone()
            
            if row:
                item = dict(row)
                item['rights'] = json.loads(item['rights'])
                return item
            return None
            
        except Exception as e:
            error_handler.handle_database_error("get_item", e)
            return None
    
    def get_all_items(self) -> List[Dict]:
        """ดึงข้อมูลทั้งหมด"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM knowledge_base ORDER BY key')
            rows = cursor.fetchall()
            
            items = []
            for row in rows:
                item = dict(row)
                item['rights'] = json.loads(item['rights'])
                items.append(item)
            
            return items
            
        except Exception as e:
            error_handler.handle_database_error("get_all_items", e)
            return []
    
    def get_summary(self) -> Dict:
        """ดึงสรุปข้อมูลในฐานข้อมูล"""
        try:
            cursor = self.connection.cursor()
            
            # จำนวนรายการทั้งหมด
            cursor.execute('SELECT COUNT(*) as total FROM knowledge_base')
            total_items = cursor.fetchone()['total']
            
            # จำนวนรายการที่เบิกได้
            cursor.execute('SELECT COUNT(*) as claimable FROM knowledge_base WHERE claimable = 1')
            claimable_items = cursor.fetchone()['claimable']
            
            # อัตราเฉลี่ย, สูงสุด, ต่ำสุด
            cursor.execute('SELECT AVG(rate_baht) as avg, MIN(rate_baht) as min, MAX(rate_baht) as max FROM knowledge_base')
            rate_stats = cursor.fetchone()
            
            return {
                'total_items': total_items,
                'claimable_items': claimable_items,
                'average_rate': round(rate_stats['avg'] if rate_stats['avg'] else 0, 2),
                'min_rate': rate_stats['min'] if rate_stats['min'] else 0,
                'max_rate': rate_stats['max'] if rate_stats['max'] else 0
            }
            
        except Exception as e:
            error_handler.handle_database_error("get_summary", e)
            return {
                'total_items': 0,
                'claimable_items': 0,
                'average_rate': 0,
                'min_rate': 0,
                'max_rate': 0
            }
    
    def _log_search(self, query: str, found: bool, result_key: Optional[str] = None, source: str = "api"):
        """บันทึก search log"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO search_logs (query, found, result_key, source)
                VALUES (?, ?, ?, ?)
            ''', (query, found, result_key, source))
            self.connection.commit()
            
        except Exception as e:
            system_logger.error(f"Failed to log search: {e}")
    
    def get_search_stats(self, limit: int = 10) -> Dict:
        """ดึงสถิติการค้นหา"""
        try:
            cursor = self.connection.cursor()
            
            # คำค้นหายอดนิยม
            cursor.execute('''
                SELECT query, COUNT(*) as count 
                FROM search_logs 
                GROUP BY LOWER(query) 
                ORDER BY count DESC 
                LIMIT ?
            ''', (limit,))
            popular_queries = [dict(row) for row in cursor.fetchall()]
            
            # อัตราการพบผลลัพธ์
            cursor.execute('SELECT AVG(CAST(found AS FLOAT)) * 100 as success_rate FROM search_logs')
            success_rate = cursor.fetchone()['success_rate'] or 0
            
            # จำนวนการค้นหาต่อวัน (7 วันล่าสุด)
            cursor.execute('''
                SELECT DATE(timestamp) as date, COUNT(*) as searches
                FROM search_logs 
                WHERE timestamp >= DATE('now', '-7 days')
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            ''')
            daily_searches = [dict(row) for row in cursor.fetchall()]
            
            return {
                'popular_queries': popular_queries,
                'success_rate': round(success_rate, 2),
                'daily_searches': daily_searches
            }
            
        except Exception as e:
            error_handler.handle_database_error("get_search_stats", e)
            return {'popular_queries': [], 'success_rate': 0, 'daily_searches': []}
    
    def close(self):
        """ปิดการเชื่อมต่อฐานข้อมูล"""
        if self.connection:
            self.connection.close()
            system_logger.info("SQLite connection closed")

# สร้าง instance สำหรับใช้งาน
sqlite_db_manager = SQLiteKnowledgeBaseManager()