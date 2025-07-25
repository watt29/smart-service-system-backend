"""
LINE Bot Handler สำหรับ Smart Service System
จัดการ LINE Bot logic และ message handling
"""

import re
import requests
import traceback
from typing import Dict, Optional

from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, ReplyMessageRequest, 
    TextMessage, QuickReply, QuickReplyItem, MessageAction
)
from linebot.v3.webhook import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from ..config import config
from ..utils.db_adapter import db_adapter

class LineMessageHandler:
    """คลาสสำหรับจัดการ LINE Bot messages"""
    
    def __init__(self):
        self.admin_state = {}  # เก็บสถานะของแต่ละ user
        
        # ตั้งค่า LINE Bot API
        if config.LINE_CHANNEL_ACCESS_TOKEN and config.LINE_CHANNEL_SECRET:
            configuration = Configuration(access_token=config.LINE_CHANNEL_ACCESS_TOKEN)
            self.line_bot_api = MessagingApi(ApiClient(configuration))
            self.handler = WebhookHandler(config.LINE_CHANNEL_SECRET)
            self._register_handlers()
            print("[OK] LINE Bot API พร้อมใช้งาน")
        else:
            print("[WARNING] LINE Bot ทำงานในโหมดจำกัด (ไม่มี tokens)")
            self.line_bot_api = self._create_dummy_api()
            self.handler = self._create_dummy_handler()
    
    def _create_dummy_api(self):
        """สร้าง dummy API สำหรับกรณีไม่มี LINE tokens"""
        class DummyLineBotApi:
            def reply_message(self, *args, **kwargs):
                print("[DEBUG] Dummy LINE API: reply_message called")
        return DummyLineBotApi()
    
    def _create_dummy_handler(self):
        """สร้าง dummy handler สำหรับกรณีไม่มี LINE tokens"""
        class DummyWebhookHandler:
            def handle(self, *args, **kwargs):
                print("[DEBUG] Dummy Handler: handle called")
            def add(self, *args, **kwargs):
                return lambda f: f
        return DummyWebhookHandler()
    
    def _register_handlers(self):
        """ลงทะเบียน message handlers"""
        @self.handler.add(MessageEvent, message=TextMessageContent)
        def handle_text_message(event):
            self.handle_message(event)
    
    def handle_message(self, event):
        """จัดการข้อความที่ได้รับจาก LINE"""
        user_id = event.source.user_id
        text = event.message.text.lower().strip()
        
        try:
            # ตรวจสอบคำสั่ง Admin
            if text in config.ADMIN_KEYWORDS:
                self._handle_admin_entry(event, user_id)
                return
            
            # ตรวจสอบว่าอยู่ในโหมด Admin หรือไม่
            if user_id in self.admin_state:
                self._handle_admin_flow(event, user_id, text)
                return
            
            # ตรวจสอบคำสั่งพิเศษ
            if text.startswith("fetch "):
                self._handle_fetch_command(event, text)
                return
            
            # ค้นหาข้อมูลปกติ - ใช้การค้นหาแบบเร็ว
            self._handle_search_fast(event, text)
            
        except Exception as e:
            print(f"[ERROR] LINE handler error: {traceback.format_exc()}")
            self._reply_error_message(event)
    
    def _handle_admin_entry(self, event, user_id: str):
        """จัดการการเข้าสู่โหมด Admin"""
        self.admin_state[user_id] = {"mode": "main_menu"}
        
        quick_replies = QuickReply(items=[
            QuickReplyItem(action=MessageAction(label="➕ เพิ่มข้อมูล", text="➕ เพิ่มข้อมูล")),
            QuickReplyItem(action=MessageAction(label="✏️ แก้ไขข้อมูล", text="✏️ แก้ไขข้อมูล")),
            QuickReplyItem(action=MessageAction(label="❌ ลบข้อมูล", text="❌ ลบข้อมูล")),
            QuickReplyItem(action=MessageAction(label="📋 ดูทั้งหมด", text="📋 ดูทั้งหมด")),
            QuickReplyItem(action=MessageAction(label="📊 สถิติ", text="📊 สถิติ")),
        ])
        
        self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="🔧 เมนูแอดมิน - เลือกรายการ:", quick_reply=quick_replies)]
            )
        )
    
    def _handle_admin_flow(self, event, user_id: str, text: str):
        """จัดการ Admin workflow"""
        current_state = self.admin_state[user_id]
        current_mode = current_state.get("mode")
        
        # ตรวจสอบคำสั่งยกเลิก
        if text == config.CANCEL_KEYWORD:
            del self.admin_state[user_id]
            self._reply_text(event, "❌ ยกเลิกการดำเนินการแอดมิน")
            return
        
        # Main Menu
        if current_mode == "main_menu":
            self._handle_admin_menu(event, user_id, text)
        
        # Add Item Flow
        elif current_mode.startswith("add_"):
            self._handle_add_item_flow(event, user_id, text, current_mode)
        
        # Edit Item Flow  
        elif current_mode.startswith("edit_"):
            self._handle_edit_item_flow(event, user_id, text, current_mode)
        
        # Delete Item Flow
        elif current_mode.startswith("delete_"):
            self._handle_delete_item_flow(event, user_id, text, current_mode)
    
    def _handle_admin_menu(self, event, user_id: str, text: str):
        """จัดการเมนูแอดมินหลัก"""
        if text == "➕ เพิ่มข้อมูล":
            self.admin_state[user_id] = {"mode": "add_item_key", "data": {}}
            self._reply_text(event, "➕ เพิ่มรายการใหม่\nกรุณาป้อนรหัสรายการ (เช่น CBC, 31001):")
            
        elif text == "✏️ แก้ไขข้อมูล":
            self.admin_state[user_id] = {"mode": "edit_item_select"}
            self._reply_text(event, "✏️ แก้ไขข้อมูล\nกรุณาป้อนรหัสรายการที่ต้องการแก้ไข:")
            
        elif text == "❌ ลบข้อมูล":
            self.admin_state[user_id] = {"mode": "delete_item_select"}
            self._reply_text(event, "❌ ลบข้อมูล\nกรุณาป้อนรหัสรายการที่ต้องการลบ:")
            
        elif text == "📋 ดูทั้งหมด":
            self._show_all_items(event, user_id)
            
        elif text == "📊 สถิติ":
            self._show_statistics(event, user_id)
            
        else:
            self._reply_text(event, "❓ คำสั่งไม่ถูกต้อง กรุณาเลือกจากเมนู")
    
    def _handle_add_item_flow(self, event, user_id: str, text: str, mode: str):
        """จัดการการเพิ่มรายการใหม่"""
        state = self.admin_state[user_id]
        
        if mode == "add_item_key":
            state["data"]["key"] = text.lower()
            state["mode"] = "add_item_name_th"
            self._reply_text(event, "📝 ป้อนชื่อรายการภาษาไทย:")
            
        elif mode == "add_item_name_th":
            state["data"]["name_th"] = text
            state["mode"] = "add_item_name_en"
            self._reply_text(event, "📝 ป้อนชื่อรายการภาษาอังกฤษ:")
            
        elif mode == "add_item_name_en":
            state["data"]["name_en"] = text
            state["mode"] = "add_item_rate"
            self._reply_text(event, "💰 ป้อนอัตราค่าบริการ (ตัวเลข):")
            
        elif mode == "add_item_rate":
            try:
                rate = float(text)
                state["data"]["rate_baht"] = rate
                
                # เพิ่มข้อมูลลงฐานข้อมูล
                if db_adapter.add_item(state["data"]["key"], state["data"]):
                    summary = (f"✅ เพิ่มรายการสำเร็จ!\n"
                             f"🔑 รหัส: {state['data']['key']}\n"
                             f"📋 ชื่อ: {state['data']['name_th']}\n"
                             f"💰 อัตรา: {rate:.2f} บาท")
                    self._reply_text(event, summary)
                else:
                    self._reply_text(event, "❌ เกิดข้อผิดพลาดในการเพิ่มรายการ")
                
                del self.admin_state[user_id]  # ออกจากโหมดแอดมิน
                
            except ValueError:
                self._reply_text(event, "❌ อัตราค่าบริการต้องเป็นตัวเลข กรุณาป้อนใหม่:")
    
    def _handle_edit_item_flow(self, event, user_id: str, text: str, mode: str):
        """จัดการการแก้ไขรายการ"""
        state = self.admin_state[user_id]
        
        if mode == "edit_item_select":
            item = db_adapter.get_item(text.lower())
            if item:
                state["key"] = text.lower()
                state["mode"] = "edit_item_field"
                
                # แสดงข้อมูลปัจจุบัน
                current_data = "\n".join([f"• {k}: {v}" for k, v in item.items()])
                self._reply_text(event, f"📄 ข้อมูลปัจจุบัน:\n{current_data}\n\n📝 ป้อนชื่อฟิลด์ที่ต้องการแก้ไข:")
            else:
                self._reply_text(event, "❌ ไม่พบรหัสรายการนี้ กรุณาป้อนใหม่:")
        
        elif mode == "edit_item_field":
            field = text.lower()
            item = db_adapter.get_item(state["key"])
            
            if field in item:
                state["field"] = field
                state["mode"] = "edit_item_value"
                self._reply_text(event, f"📝 ป้อนค่าใหม่สำหรับ '{field}':")
            else:
                self._reply_text(event, "❌ ไม่พบฟิลด์นี้ กรุณาป้อนชื่อฟิลด์ที่ถูกต้อง:")
        
        elif mode == "edit_item_value":
            if db_adapter.update_item(state["key"], state["field"], text):
                self._reply_text(event, f"✅ แก้ไขสำเร็จ!\n🔑 รหัส: {state['key']}\n📝 ฟิลด์: {state['field']}\n💾 ค่าใหม่: {text}")
            else:
                self._reply_text(event, "❌ เกิดข้อผิดพลาดในการแก้ไข")
            
            del self.admin_state[user_id]
    
    def _handle_delete_item_flow(self, event, user_id: str, text: str, mode: str):
        """จัดการการลบรายการ"""
        state = self.admin_state[user_id]
        
        if mode == "delete_item_select":
            item = db_adapter.get_item(text.lower())
            if item:
                state["key"] = text.lower()
                state["mode"] = "delete_item_confirm"
                self._reply_text(event, f"⚠️  ต้องการลบรายการ '{item['name_th']}' ใช่หรือไม่?\nพิมพ์ 'confirm' เพื่อยืนยัน หรือ 'cancel' เพื่อยกเลิก")
            else:
                self._reply_text(event, "❌ ไม่พบรหัสรายการนี้ กรุณาป้อนใหม่:")
        
        elif mode == "delete_item_confirm":
            if text == "confirm":
                if db_adapter.delete_item(state["key"]):
                    self._reply_text(event, f"🗑️ ลบรายการ '{state['key']}' สำเร็จ")
                else:
                    self._reply_text(event, "❌ เกิดข้อผิดพลาดในการลบ")
            else:
                self._reply_text(event, "❌ ยกเลิกการลบรายการ")
            
            del self.admin_state[user_id]
    
    def _show_all_items(self, event, user_id: str):
        """แสดงรายการทั้งหมด"""
        all_items = db_adapter.get_all_items()
        
        if all_items:
            items_text = "\n".join([
                f"🔹 {key}: {item['name_th']} ({item['rate_baht']:.2f} บาท)"
                for key, item in list(all_items.items())[:10]  # แสดงแค่ 10 รายการแรก
            ])
            
            if len(all_items) > 10:
                items_text += f"\n... และอีก {len(all_items) - 10} รายการ"
            
            self._reply_text(event, f"📋 รายการทั้งหมด ({len(all_items)} รายการ):\n{items_text}")
        else:
            self._reply_text(event, "📭 ยังไม่มีข้อมูลในระบบ")
        
        del self.admin_state[user_id]
    
    def _show_statistics(self, event, user_id: str):
        """แสดงสถิติ"""
        summary = db_adapter.get_summary()
        
        stats_text = (
            f"📊 สถิติระบบ:\n"
            f"📦 รายการทั้งหมด: {summary['total_items']} รายการ\n"
            f"✅ เบิกได้: {summary['claimable_items']} รายการ\n"
            f"💰 อัตราเฉลี่ย: {summary['average_rate']:.2f} บาท\n"
            f"📈 อัตราสูงสุด: {summary['max_rate']:.2f} บาท\n"
            f"📉 อัตราต่ำสุด: {summary['min_rate']:.2f} บาท"
        )
        
        self._reply_text(event, stats_text)
        del self.admin_state[user_id]
    
    def _handle_fetch_command(self, event, text: str):
        """จัดการคำสั่ง fetch URL"""
        url = text[6:].strip()  # ตัด "fetch " ออก
        
        if url:
            try:
                response = requests.get(url, timeout=config.REQUEST_TIMEOUT)
                response.raise_for_status()
                content = f"🌐 เนื้อหาจาก {url}:\n\n{response.text[:1000]}..."
                self._reply_text(event, content)
            except requests.exceptions.RequestException as e:
                self._reply_text(event, f"❌ ไม่สามารถดึงข้อมูลจาก {url} ได้: {str(e)}")
        else:
            self._reply_text(event, "❓ กรุณาระบุ URL (ตัวอย่าง: fetch https://www.example.com)")
    
    def _handle_search_fast(self, event, text: str):
        """จัดการการค้นหาข้อมูลแบบเร็ว"""
        try:
            # ใช้การค้นหาแบบง่าย limit 1 เพื่อความเร็ว
            if config.USE_SQLITE:
                # SQLite search (faster)
                found_items = db_adapter.fuzzy_search(text)
                if found_items:
                    key, item_data = found_items[0]
                    result = self._format_search_result_short(item_data, text)
                else:
                    result = self._format_not_found_short(text)
            else:
                # JSON fallback
                found_items = db_adapter.fuzzy_search(text)
                if found_items:
                    key, item_data = found_items[0]
                    result = self._format_search_result_short(item_data, text)
                else:
                    result = self._format_not_found_short(text)
            
            self._reply_text(event, result)
            
        except Exception as e:
            print(f"[ERROR] Search error: {e}")
            self._reply_text(event, "เกิดข้อผิดพลาดในการค้นหา กรุณาลองใหม่")
    
    def _format_search_result_short(self, item_data: Dict, query: str) -> str:
        """จัดรูปแบบผลลัพธ์แบบสั้น (เร็ว)"""
        return (
            f"🔍 {item_data['name_th']}\n"
            f"💵 {item_data['rate_baht']:.0f} บาท\n"
            f"✅ {', '.join(item_data['rights'][:2])}\n"  # แสดงแค่ 2 อันแรก
            f"📋 CPT: {item_data.get('cpt', 'N/A')}"
        )
    
    def _format_not_found_short(self, query: str) -> str:
        """ข้อความไม่พบข้อมูลแบบสั้น"""
        return f"❌ ไม่พบ '{query}'\n💡 ลองคำค้นหาอื่น เช่น: CBC, เลือด, 31001"
    
    def _format_search_result(self, item_data: Dict, query: str) -> str:
        """จัดรูปแบบผลลัพธ์การค้นหา"""
        link = self._generate_cgd_link(query)
        
        result = (
            f"🔍 รายการ: {item_data['name_th']} ({item_data['name_en']})\n"
            f"💵 อัตรา: {item_data['rate_baht']:.2f} บาท\n"
            f"✅ เบิกได้ตามสิทธิ: {', '.join(item_data['rights'])}\n"
        )
        
        if item_data.get('notes'):
            result += f"📝 หมายเหตุ: {item_data['notes']}\n"
        
        result += (
            f"🔗 ข้อมูลทางการ: {link}\n"
            f"ℹ️ รหัสมาตรฐาน:\n"
            f"• CPT: {item_data['cpt']}\n"
            f"• ICD-10: {item_data['icd10']}"
        )
        
        return result
    
    def _generate_cgd_link(self, query: str) -> str:
        """สร้างลิงก์ค้นหาใน mbdb.cgd.go.th"""
        encoded_query = re.sub(r'\\s+', '+', query.strip())
        return f"{config.CGD_BASE_URL}?method=search&service_name={encoded_query}"
    
    def _reply_text(self, event, text: str):
        """ส่งข้อความตอบกลับ"""
        self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=text)]
            )
        )
    
    def _reply_error_message(self, event):
        """ส่งข้อความแจ้งข้อผิดพลาด"""
        error_msg = "⚠️ เกิดข้อผิดพลาดภายในระบบ กรุณาลองใหม่อีกครั้ง หรือติดต่อผู้ดูแลระบบ"
        self._reply_text(event, error_msg)

# สร้าง instance สำหรับใช้งาน
line_handler = LineMessageHandler()