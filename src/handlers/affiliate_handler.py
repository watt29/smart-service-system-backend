"""
📁 src/handlers/affiliate_handler.py
🎯 LINE Bot Handler สำหรับ Affiliate Product Review Bot
"""

import re
import traceback
from typing import Dict, List, Optional
from urllib.parse import quote

from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, ReplyMessageRequest, 
    TextMessage, QuickReply, QuickReplyItem, MessageAction,
    FlexMessage, FlexContainer, FlexBox, FlexText, FlexButton,
    URIAction, FlexImage, FlexSeparator
)
from linebot.v3.webhook import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from ..config import config
from ..utils.supabase_database import SupabaseDatabase
from ..utils.promotion_generator import PromotionGenerator
from ..utils.rich_menu_manager import rich_menu_manager
from ..utils.bulk_importer import bulk_importer
from ..utils.ai_recommender import ai_recommender

class AffiliateLineHandler:
    """คลาสสำหรับจัดการ LINE Bot messages สำหรับ Affiliate Products"""
    
    def __init__(self):
        self.admin_state = {}  # เก็บสถานะของแต่ละ user
        self.db = SupabaseDatabase()
        self.promo_generator = PromotionGenerator()
        
        # ตั้งค่า LINE Bot API
        if config.LINE_CHANNEL_ACCESS_TOKEN and config.LINE_CHANNEL_SECRET:
            configuration = Configuration(access_token=config.LINE_CHANNEL_ACCESS_TOKEN)
            self.line_bot_api = MessagingApi(ApiClient(configuration))
            self.handler = WebhookHandler(config.LINE_CHANNEL_SECRET)
            self._register_handlers()
            print("[OK] Affiliate LINE Bot API พร้อมใช้งาน")
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
        text = event.message.text.strip()
        
        print(f"[DEBUG] Received message: '{text}' from user: {user_id}")
        
        try:
            # ตรวจสอบคำสั่ง Admin
            if text.lower() in [word.lower() for word in config.ADMIN_KEYWORDS]:
                self._handle_admin_entry(event, user_id)
                return
            
            # ตรวจสอบว่าอยู่ในโหมด Admin หรือไม่
            if user_id in self.admin_state:
                self._handle_admin_flow(event, user_id, text)
                return
            
            # ตรวจสอบคำสั่งพิเศษ
            if text.lower().startswith("รหัส "):
                product_code = text[4:].strip()
                self._handle_product_code_search(event, product_code)
                return
            
            if text.lower().startswith("โปรโมต "):
                product_code = text[7:].strip()
                self._handle_promotion_generation(event, product_code)
                return
            
            # ตรวจสอบคำสั่ง pagination
            if text.startswith("หน้า") and ":" in text:
                self._handle_pagination_command(event, text, user_id)
                return
            
            # ตรวจสอบคำสั่ง filtering
            if text.lower().startswith("กรอง "):
                self._handle_filter_command(event, text[5:].strip(), user_id)
                return
            
            if text.lower().startswith("เรียง "):
                self._handle_sort_command(event, text[6:].strip(), user_id)
                return
            
            if text.lower() in ["สถิติ", "stats"]:
                self._show_stats(event)
                return
            
            if text.lower() in ["หมวดหมู่", "categories"]:
                self._show_categories(event)
                return
            
            # รองรับข้อความจาก Rich Menu (อังกฤษ)
            if text.upper() in ["SEARCH", "Q"]:
                self._show_search_guide(event)
                return
            
            if text.upper() in ["CATEGORY", "C"]:
                self._show_categories(event)
                return
                
            if text.upper() in ["BESTSELLER", "B"]:
                self._show_bestsellers(event)
                return
            
            if text.upper() in ["PROMOTION", "P"]:
                self._show_promotions(event)
                return
                
            if text.upper() in ["STATS", "S"]:
                self._show_stats(event)
                return
            
            if text.upper() in ["HELP", "H"]:
                self._show_help_menu(event)
                return
            
            # รองรับข้อความภาษาไทยง่าย ๆ
            if text in ["ค้นหา", "หา", "ซื้อ"]:
                self._show_search_guide(event)
                return
                
            if text in ["หมวด", "หมวดหมู่", "ประเภท"]:
                self._show_categories(event)
                return
                
            if text in ["ขายดี", "นิยม", "ฮิต"]:
                self._show_bestsellers(event)
                return
                
            if text in ["โปรโมชั่น", "โปร", "ลด", "ส่วนลด"]:
                self._show_promotions(event)
                return
                
            if text in ["สถิติ", "ข้อมูล", "จำนวน"]:
                self._show_stats(event)
                return
                
            if text in ["ช่วย", "ช่วยเหลือ", "วิธีใช้", "help"]:
                self._show_help_menu(event)
                return
                
            if text in ["หน้าแรก", "กลับ", "เริ่มใหม่", "home"]:
                self._show_home_menu(event)
                return
            
            # คำสั่ง Admin แบบง่าย ๆ (ต้องเป็น Admin เท่านั้น)
            if user_id == config.ADMIN_USER_ID:
                if text.startswith("/"):
                    self._handle_admin_commands(event, text, user_id)
                    return
            
            if text.lower().startswith("แนะนำ") or text.lower() in ["recommendations", "recommend", "แนะนำสินค้า"]:
                # คำสั่งแนะนำสินค้าด้วย AI
                self._show_ai_recommendations(event, user_id, text)
                return
            
            if text.lower().startswith("หมวด "):
                category_name = text[5:].strip()
                self._browse_category(event, category_name, user_id)
                return
            
            # ค้นหาสินค้าปกติ
            self._handle_product_search(event, text, user_id)
            
        except Exception as e:
            print(f"[ERROR] Affiliate LINE handler error: {traceback.format_exc()}")
            self._reply_error_message(event)
    
    def _handle_admin_commands(self, event, text: str, user_id: str):
        """จัดการคำสั่ง Admin แบบง่าย"""
        command = text.lower()
        
        if command == "/help":
            self._show_admin_help(event)
        elif command == "/stats" or command == "/สถิติ":
            self._show_admin_stats(event)
        elif command == "/products" or command == "/สินค้า":
            self._show_admin_products(event)
        elif command == "/users" or command == "/ผู้ใช้":
            self._show_admin_users(event)
        elif command.startswith("/add"):
            self._show_add_product_guide(event)
        elif command.startswith("/import"):
            self._show_import_guide(event)
        else:
            self._show_admin_help(event)
    
    def _show_admin_help(self, event):
        """แสดงคำสั่ง Admin ทั้งหมด"""
        help_text = """🔐 คำสั่ง Admin

📊 /stats - ดูสถิติระบบ
📦 /products - จัดการสินค้า  
👥 /users - ดูข้อมูลผู้ใช้
➕ /add - เพิ่มสินค้าใหม่
📥 /import - นำเข้าสินค้าจำนวนมาก

💡 ใช้คำสั่งง่าย ๆ เท่านั้น!"""
        
        self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=help_text)]
            )
        )

    def _handle_admin_entry(self, event, user_id: str):
        """จัดการการเข้าสู่โหมด Admin"""
        welcome_text = """🔐 ยินดีต้อนรับ Admin!

ใช้คำสั่งง่าย ๆ เหล่านี้:

📊 /stats - ดูสถิติ
📦 /products - จัดการสินค้า
👥 /users - ดูผู้ใช้
➕ /add - เพิ่มสินค้า
📥 /import - นำเข้าสินค้า
❓ /help - ดูคำสั่งทั้งหมด

พิมพ์คำสั่งที่ต้องการได้เลย!"""
        
        quick_replies = QuickReply(items=[
            QuickReplyItem(action=MessageAction(label="📊 สถิติ", text="/stats")),
            QuickReplyItem(action=MessageAction(label="📦 สินค้า", text="/products")),
            QuickReplyItem(action=MessageAction(label="👥 ผู้ใช้", text="/users")),
            QuickReplyItem(action=MessageAction(label="➕ เพิ่มสินค้า", text="/add")),
            QuickReplyItem(action=MessageAction(label="📥 นำเข้า", text="/import")),
            QuickReplyItem(action=MessageAction(label="❓ ช่วยเหลือ", text="/help")),
        ])
        
        self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="🛍️ เมนูจัดการสินค้า Affiliate - เลือกรายการ:", quick_reply=quick_replies)]
            )
        )
    
    def _handle_admin_flow(self, event, user_id: str, text: str):
        """จัดการ Admin workflow"""
        current_state = self.admin_state[user_id]
        current_mode = current_state.get("mode")
        
        # ตรวจสอบคำสั่งยกเลิก
        if text.lower() == config.CANCEL_KEYWORD:
            del self.admin_state[user_id]
            self._reply_text(event, "❌ ยกเลิกการดำเนินการแอดมิน")
            return
        
        # Main Menu
        if current_mode == "main_menu":
            self._handle_admin_menu(event, user_id, text)
        # Add Product Flow
        elif current_mode.startswith("add_"):
            self._handle_add_product_flow(event, user_id, text, current_mode)
        # Edit Product Flow  
        elif current_mode.startswith("edit_"):
            self._handle_edit_product_flow(event, user_id, text, current_mode)
        # Delete Product Flow
        elif current_mode.startswith("delete_"):
            self._handle_delete_product_flow(event, user_id, text, current_mode)
    
    def _handle_admin_menu(self, event, user_id: str, text: str):
        """จัดการเมนูแอดมินหลัก"""
        if text == "➕ เพิ่มสินค้า":
            self.admin_state[user_id] = {"mode": "add_product_code", "data": {}}
            self._reply_text(event, "➕ เพิ่มสินค้าใหม่\n📝 กรุณาป้อนรหัสสินค้า (เช่น PHONE001):")
            
        elif text == "✏️ แก้ไขสินค้า":
            self.admin_state[user_id] = {"mode": "edit_product_select"}
            self._reply_text(event, "✏️ แก้ไขสินค้า\n📝 กรุณาป้อนรหัสสินค้าที่ต้องการแก้ไข:")
            
        elif text == "❌ ลบสินค้า":
            self.admin_state[user_id] = {"mode": "delete_product_select"}
            self._reply_text(event, "❌ ลบสินค้า\n📝 กรุณาป้อนรหัสสินค้าที่ต้องการลบ:")
            
        elif text == "📋 ดูสินค้าทั้งหมด":
            self._show_all_products(event, user_id)
            
        elif text == "📊 สถิติ":
            self._show_admin_stats(event, user_id)
            
        elif text == "🎛️ Dashboard":
            self._show_admin_dashboard(event, user_id)
            
        else:
            self._reply_text(event, "❓ คำสั่งไม่ถูกต้อง กรุณาเลือกจากเมนู")
    
    def _handle_add_product_flow(self, event, user_id: str, text: str, mode: str):
        """จัดการการเพิ่มสินค้าใหม่"""
        state = self.admin_state[user_id]
        
        if mode == "add_product_code":
            state["data"]["product_code"] = text.upper()
            state["mode"] = "add_product_name"
            self._reply_text(event, "📝 ป้อนชื่อสินค้า:")
            
        elif mode == "add_product_name":
            state["data"]["product_name"] = text
            state["mode"] = "add_product_price"
            self._reply_text(event, "💰 ป้อนราคาสินค้า (ตัวเลข):")
            
        elif mode == "add_product_price":
            try:
                price = float(text)
                state["data"]["price"] = price
                state["mode"] = "add_shop_name"
                self._reply_text(event, "🏪 ป้อนชื่อร้านค้า:")
            except ValueError:
                self._reply_text(event, "❌ ราคาต้องเป็นตัวเลข กรุณาป้อนใหม่:")
                
        elif mode == "add_shop_name":
            state["data"]["shop_name"] = text
            state["mode"] = "add_commission_rate"
            self._reply_text(event, f"📊 ป้อนอัตราค่าคอมมิชชัน (%) [ค่าเริ่มต้น: {config.DEFAULT_COMMISSION_RATE}%]:")
            
        elif mode == "add_commission_rate":
            try:
                if text.strip() == "":
                    rate = config.DEFAULT_COMMISSION_RATE
                else:
                    rate = float(text)
                state["data"]["commission_rate"] = rate
                state["mode"] = "add_product_link"
                self._reply_text(event, "🔗 ป้อนลิงก์สินค้า:")
            except ValueError:
                self._reply_text(event, "❌ อัตราค่าคอมมิชชันต้องเป็นตัวเลข กรุณาป้อนใหม่:")
                
        elif mode == "add_product_link":
            state["data"]["product_link"] = text
            state["mode"] = "add_offer_link"
            self._reply_text(event, "🎯 ป้อนลิงก์ข้อเสนอ (Affiliate Link):")
            
        elif mode == "add_offer_link":
            state["data"]["offer_link"] = text
            state["mode"] = "add_category"
            self._reply_text(event, "📂 ป้อนหมวดหมู่สินค้า (ไม่บังคับ):")
            
        elif mode == "add_category":
            state["data"]["category"] = text if text.strip() else "อื่นๆ"
            state["mode"] = "add_description"
            self._reply_text(event, "📋 ป้อนคำอธิบายสินค้า (ไม่บังคับ):")
            
        elif mode == "add_description":
            state["data"]["description"] = text if text.strip() else ""
            
            # เพิ่มสินค้าลงฐานข้อมูล
            result = self.db.add_product(state["data"])
            
            if result:
                commission_amount = (state["data"]["price"] * state["data"]["commission_rate"]) / 100
                summary = (
                    f"✅ เพิ่มสินค้าสำเร็จ!\n"
                    f"🔑 รหัส: {state['data']['product_code']}\n"
                    f"📱 ชื่อ: {state['data']['product_name']}\n"
                    f"💰 ราคา: {state['data']['price']:,.2f} บาท\n"
                    f"🏪 ร้าน: {state['data']['shop_name']}\n"
                    f"📊 คอมมิชชัน: {state['data']['commission_rate']}% = {commission_amount:,.2f} บาท"
                )
                self._reply_text(event, summary)
            else:
                self._reply_text(event, "❌ เกิดข้อผิดพลาดในการเพิ่มสินค้า")
            
            del self.admin_state[user_id]
    
    def _handle_pagination_command(self, event, text: str, user_id: str):
        """จัดการคำสั่ง pagination เช่น 'หน้า2:แมว'"""
        try:
            # แยกข้อมูลจากคำสั่ง
            parts = text.split(":")
            page_part = parts[0]
            page = int(page_part.replace("หน้า", ""))
            query = parts[1] if len(parts) > 1 else ""
            
            # แยกข้อมูล filtering
            category = None
            min_price = None
            max_price = None
            order_by = 'created_at'
            
            for part in parts[2:]:
                if part.startswith("cat:"):
                    category = part[4:]
                elif part.startswith("minp:"):
                    min_price = float(part[5:])
                elif part.startswith("maxp:"):
                    max_price = float(part[5:])
                elif part.startswith("sort:"):
                    order_by = part[5:]
            
            self._handle_product_search(event, query, user_id, page, category, min_price, max_price, order_by)
            
        except (ValueError, IndexError) as e:
            print(f"[ERROR] Invalid pagination command: {text}, error: {e}")
            self._reply_text(event, "❌ คำสั่งไม่ถูกต้อง กรุณาลองใหม่")
    
    def _handle_filter_command(self, event, filter_text: str, user_id: str):
        """จัดการคำสั่งกรอง เช่น 'กรอง แมว หมวดหมู่:สัตว์เลี้ยง ราคา:10-100'"""
        try:
            parts = filter_text.split()
            query = parts[0] if parts else ""
            
            category = None
            min_price = None
            max_price = None
            
            for part in parts[1:]:
                if part.startswith("หมวดหมู่:"):
                    category = part[9:]
                elif part.startswith("ราคา:"):
                    price_range = part[5:]
                    if "-" in price_range:
                        min_str, max_str = price_range.split("-")
                        min_price = float(min_str) if min_str else None
                        max_price = float(max_str) if max_str else None
            
            self._handle_product_search(event, query, user_id, 1, category, min_price, max_price)
            
        except Exception as e:
            print(f"[ERROR] Invalid filter command: {filter_text}, error: {e}")
            self._reply_text(event, "❌ คำสั่งกรองไม่ถูกต้อง\n💡 ตัวอย่าง: 'กรอง แมว หมวดหมู่:สัตว์เลี้ยง ราคา:10-100'")
    
    def _handle_sort_command(self, event, sort_text: str, user_id: str):
        """จัดการคำสั่งเรียง เช่น 'เรียง แมว ราคาถูก'"""
        try:
            parts = sort_text.split()
            query = parts[0] if parts else ""
            sort_option = parts[1] if len(parts) > 1 else "ใหม่"
            
            order_by_map = {
                "ใหม่": "created_at",
                "ราคาถูก": "price_low", 
                "ราคาแพง": "price_high",
                "ขายดี": "popularity",
                "คะแนน": "rating",
                "หมวดหมู่": "category",
                "ชื่อ": "product_name"
            }
            
            order_by = order_by_map.get(sort_option, "created_at")
            
            self._handle_product_search(event, query, user_id, 1, None, None, None, order_by)
            
        except Exception as e:
            print(f"[ERROR] Invalid sort command: {sort_text}, error: {e}")
            self._reply_text(event, "❌ คำสั่งเรียงไม่ถูกต้อง\n💡 ตัวอย่าง: 'เรียง แมว ราคาถูก' (ใหม่/ราคาถูก/ราคาแพง/ขายดี/คะแนน/หมวดหมู่/ชื่อ)")
    
    def _handle_product_search(self, event, query: str, user_id: str = None, 
                             page: int = 1, category: str = None, 
                             min_price: float = None, max_price: float = None, 
                             order_by: str = 'created_at'):
        """จัดการการค้นหาสินค้าพร้อม pagination และ filtering"""
        try:
            print(f"[DEBUG] Searching for: '{query}' (page {page})")
            
            # คำนวณ offset สำหรับ pagination
            limit = config.MAX_RESULTS_PER_SEARCH
            offset = (page - 1) * limit
            
            # ค้นหาสินค้า
            search_result = self.db.search_products(
                query=query, 
                limit=limit, 
                offset=offset,
                category=category,
                min_price=min_price,
                max_price=max_price,
                order_by=order_by
            )
            
            # อัปเดต AI recommendations จากการค้นหา
            if user_id and search_result.get('data'):
                ai_recommender.update_user_interests(user_id, query, search_result['data'])
            
            products = search_result.get('products', [])
            total = search_result.get('total', 0)
            has_more = search_result.get('has_more', False)
            
            print(f"[DEBUG] Found {len(products)} products (total: {total}, has_more: {has_more})")
            
            if products:
                if len(products) == 1 and total == 1:
                    # แสดงสินค้าเดียว
                    self._send_product_simple(event, products[0])
                else:
                    # แสดงรายการสินค้าหลายรายการพร้อม pagination
                    self._send_products_list_with_pagination(
                        event, products, query, page, total, has_more, 
                        category, min_price, max_price, order_by
                    )
            else:
                self._send_not_found_message(event, query)
                
        except Exception as e:
            print(f"[ERROR] Product search error: {e}")
            self._reply_text(event, "❌ เกิดข้อผิดพลาดในการค้นหา กรุณาลองใหม่")
    
    def _handle_product_code_search(self, event, product_code: str):
        """ค้นหาสินค้าด้วยรหัสสินค้า"""
        print(f"[DEBUG] Searching by product code: '{product_code}'")
        product = self.db.get_product_by_code(product_code.upper())
        print(f"[DEBUG] Product found: {product is not None}")
        
        if product:
            self._send_product_simple(event, product)
        else:
            self._reply_text(event, f"❌ ไม่พบสินค้ารหัส '{product_code}'\n💡 ลองค้นหาด้วยชื่อสินค้าแทน")
    
    def _handle_promotion_generation(self, event, product_code: str):
        """สร้างคำโปรโมตสินค้าอัตโนมัติ"""
        print(f"[DEBUG] Generating promotion for product code: '{product_code}'")
        product = self.db.get_product_by_code(product_code.upper())
        
        if product:
            # สร้างโปรโมต 3 แบบ
            promotions = self.promo_generator.generate_multiple_promotions(product, 3)
            
            response = "🎯 คำโปรโมตอัตโนมัติ 3 แบบ:\n\n"
            
            for i, promo in enumerate(promotions, 1):
                response += f"📝 แบบที่ {i}:\n{promo}\n\n" + "="*30 + "\n\n"
            
            response += "💡 Copy ไปใช้ได้เลย! แก้ไขตามใจชอบนะคะ"
            
            self._reply_text(event, response)
        else:
            self._reply_text(event, f"❌ ไม่พบสินค้ารหัส '{product_code}'\n💡 ลองใช้คำสั่ง 'รหัส {product_code}' เพื่อดูสินค้าก่อน")
    
    def _send_product_simple(self, event, product: Dict):
        """ส่งข้อความแสดงสินค้าแบบธรรมดา - ใช้ Flex Message ซ่อนลิงก์"""
        self._send_product_flex_hidden_link(event, product)
    
    def _shorten_product_name(self, name: str) -> str:
        """ย่อชื่อสินค้าให้อ่านง่าย"""
        if len(name) <= 50:
            return name
            
        # ลบข้อความที่ไม่จำเป็น
        name = name.replace('【', '').replace('】', '')
        name = name.replace('✨', '').replace('🔥', '')
        
        # แยกคำและเลือกคำสำคัญ
        words = name.split()
        if len(words) <= 8:
            return name
            
        # เก็บคำสำคัญด้านหน้า
        important_words = words[:6]
        return ' '.join(important_words) + '...'
    
    def _format_sold_count(self, count: int) -> str:
        """แปลงจำนวนขายให้อ่านง่าย"""
        if count >= 10000:
            return f"{count//1000}k+"
        elif count >= 1000:
            return f"{count//100}00+"
        else:
            return str(count)
    
    def _create_professional_link_display(self, offer_link: str) -> str:
        """สร้างการแสดงลิงก์แบบมืออาชีพ ซ่อน URL ยาวๆ"""
        # ตัวเลือกการแสดงลิงก์แบบมืออาชีพ ไม่แสดง URL
        link_styles = [
            "📱 สั่งซื้อทันที",
            "🛍️ ดูสินค้า", 
            "🛒 สั่งเลย",
            "📦 สั่งซื้อ",
            "🎯 ซื้อเลย",
            "✨ สั่งได้ที่นี่",
            "🔥 สั่งทันที",
            "💯 ซื้อตอนนี้",
            "🌟 คลิกเลย",
            "⚡ สั่งด่วน"
        ]
        
        # สุ่มเลือกสไตล์ (ไม่แสดง URL)
        import random
        style = random.choice(link_styles)
        
        return f"{style}"
    
    def _send_product_flex_hidden_link(self, event, product: Dict):
        """ส่ง Flex Message ที่ซ่อนลิงก์ในปุ่ม"""
        name = self._shorten_product_name(product['product_name'])
        price = product['price']
        sold_count = product.get('sold_count', 0)
        shop_name = product['shop_name']
        offer_link = product['offer_link']
        rating = product.get('rating', 0)
        
        sold_display = self._format_sold_count(sold_count)
        short_link = self._create_professional_link_display(offer_link)
        
        # สร้าง content สำหรับ body
        body_contents = [
            {
                "type": "text",
                "text": name,
                "weight": "bold",
                "size": "lg",
                "wrap": True,
                "color": "#333333"
            },
            {
                "type": "text",
                "text": f"💸 ราคาเพียง {price:,.0f} บาท!",
                "size": "md",
                "weight": "bold",
                "color": "#E74C3C",
                "margin": "sm"
            }
        ]
        
        # เพิ่มข้อมูลการขาย
        if sold_count >= 1000:
            body_contents.append({
                "type": "text",
                "text": f"📦 ขายดีมากกว่า {sold_display} ชิ้น",
                "size": "sm",
                "color": "#27AE60",
                "margin": "xs"
            })
        elif sold_count > 0:
            body_contents.append({
                "type": "text",
                "text": f"📦 ขายแล้ว {sold_display} ชิ้น",
                "size": "sm",
                "color": "#27AE60",
                "margin": "xs"
            })
        
        # เพิ่มคะแนน
        if rating >= 4.0:
            stars = "⭐" * min(int(rating), 5)
            body_contents.append({
                "type": "text",
                "text": f"{stars} ({rating})",
                "size": "sm",
                "color": "#F39C12",
                "margin": "xs"
            })
        
        # เพิ่มชื่อร้าน
        body_contents.append({
            "type": "text",
            "text": f"🏪 ร้าน {shop_name}",
            "size": "sm",
            "color": "#666666",
            "margin": "sm"
        })
        
        flex_contents = {
            "type": "bubble",
            "size": "kilo",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": body_contents,
                "spacing": "sm",
                "paddingAll": "18px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": short_link,
                            "uri": offer_link
                        },
                        "style": "primary",
                        "color": "#FF6B35",
                        "height": "sm"
                    }
                ],
                "paddingAll": "18px"
            }
        }
        
        flex_message = FlexMessage(
            alt_text=f"🔸 {name}",
            contents=FlexContainer.from_dict(flex_contents)
        )
        
        self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[flex_message]
            )
        )
    
    def _create_products_carousel(self, products: List[Dict], query: str) -> Dict:
        """สร้าง Flex Carousel สำหรับสินค้าหลายรายการ"""
        bubbles = []
        
        for product in products[:10]:  # จำกัด 10 รายการ
            name = self._shorten_product_name(product['product_name'])
            price = product['price']
            sold_count = product.get('sold_count', 0)
            shop_name = product['shop_name']
            offer_link = product['offer_link']
            rating = product.get('rating', 0)
            
            sold_display = self._format_sold_count(sold_count)
            short_link = self._create_professional_link_display(offer_link)
            
            # สร้าง content สำหรับแต่ละ bubble
            body_contents = [
                {
                    "type": "text",
                    "text": name,
                    "weight": "bold",
                    "size": "md",
                    "wrap": True,
                    "maxLines": 3
                },
                {
                    "type": "text",
                    "text": f"💸 {price:,.0f} บาท",
                    "size": "sm",
                    "weight": "bold",
                    "color": "#E74C3C",
                    "margin": "sm"
                }
            ]
            
            if sold_count >= 1000:
                body_contents.append({
                    "type": "text",
                    "text": f"📦 {sold_display}",
                    "size": "xs",
                    "color": "#27AE60",
                    "margin": "xs"
                })
            
            if rating >= 4.0:
                stars = "⭐" * min(int(rating), 5)
                body_contents.append({
                    "type": "text",
                    "text": f"{stars}",
                    "size": "xs",
                    "color": "#F39C12",
                    "margin": "xs"
                })
            
            bubble = {
                "type": "bubble",
                "size": "nano",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": body_contents,
                    "spacing": "xs",
                    "paddingAll": "12px"
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "uri",
                                "label": short_link,
                                "uri": offer_link
                            },
                            "style": "primary",
                            "color": "#FF6B35",
                            "height": "sm"
                        }
                    ],
                    "paddingAll": "12px"
                }
            }
            
            bubbles.append(bubble)
        
        return {
            "type": "carousel",
            "contents": bubbles
        }
    
    def _send_products_list_with_pagination(self, event, products: List[Dict], query: str, 
                                          page: int, total: int, has_more: bool,
                                          category: str = None, min_price: float = None, 
                                          max_price: float = None, order_by: str = 'created_at'):
        """ส่งรายการสินค้าพร้อม pagination controls"""
        
        # สร้าง Flex Carousel สำหรับสินค้า
        flex_contents = self._create_products_carousel(products, query)
        
        # เพิ่มข้อมูล pagination
        total_pages = (total + config.MAX_RESULTS_PER_SEARCH - 1) // config.MAX_RESULTS_PER_SEARCH
        
        # สร้างปุ่ม pagination
        pagination_buttons = []
        
        # ปุ่มหน้าก่อนหน้า
        if page > 1:
            prev_action = f"หน้า{page-1}:{query}"
            if category:
                prev_action += f":cat:{category}"
            if min_price:
                prev_action += f":minp:{min_price}"
            if max_price:
                prev_action += f":maxp:{max_price}"
            if order_by != 'created_at':
                prev_action += f":sort:{order_by}"
                
            pagination_buttons.append({
                "type": "button",
                "action": {
                    "type": "message",
                    "label": "◀️ หน้าก่อน",
                    "text": prev_action
                },
                "style": "secondary",
                "height": "sm"
            })
        
        # ปุ่มหน้าถัดไป
        if has_more:
            next_action = f"หน้า{page+1}:{query}"
            if category:
                next_action += f":cat:{category}"
            if min_price:
                next_action += f":minp:{min_price}"
            if max_price:
                next_action += f":maxp:{max_price}"
            if order_by != 'created_at':
                next_action += f":sort:{order_by}"
                
            pagination_buttons.append({
                "type": "button",
                "action": {
                    "type": "message",
                    "label": "หน้าถัดไป ▶️",
                    "text": next_action
                },
                "style": "secondary", 
                "height": "sm"
            })
        
        # เพิ่ม footer สำหรับ pagination ถ้ามีมากกว่า 1 หน้า
        if total_pages > 1:
            flex_contents["contents"].append({
                "type": "bubble",
                "size": "nano",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"📄 หน้า {page}/{total_pages}",
                            "size": "sm",
                            "align": "center",
                            "weight": "bold",
                            "color": "#666666"
                        },
                        {
                            "type": "text",
                            "text": f"รวม {total} รายการ",
                            "size": "xs",
                            "align": "center",
                            "color": "#999999",
                            "margin": "xs"
                        }
                    ],
                    "paddingAll": "12px"
                },
                "footer": {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": pagination_buttons,
                    "spacing": "sm",
                    "paddingAll": "8px"
                } if pagination_buttons else None
            })
        
        flex_message = FlexMessage(
            alt_text=f"🔍 เจอสินค้า {len(products)} รายการ (หน้า {page}/{total_pages})",
            contents=FlexContainer.from_dict(flex_contents)
        )
        
        self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[flex_message]
            )
        )
    
    def _send_product_flex(self, event, product: Dict):
        """ส่ง Flex Message แสดงรายละเอียดสินค้า"""
        commission_amount = product.get('commission_amount', 0)
        rating_stars = "⭐" * int(product.get('rating', 0))
        
        flex_contents = {
            "type": "bubble",
            "size": "giga",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": product['product_name'],
                        "weight": "bold",
                        "size": "lg",
                        "wrap": True
                    }
                ],
                "backgroundColor": "#4A90E2",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"💰 ราคา: {product['price']:,.0f} บาท",
                                "size": "md",
                                "weight": "bold",
                                "color": "#E74C3C"
                            },
                            {
                                "type": "text", 
                                "text": f"🏪 ร้าน: {product['shop_name']}",
                                "size": "sm",
                                "color": "#666666"
                            },
                            {
                                "type": "text",
                                "text": f"🔥 ขายแล้ว: {product.get('sold_count', 0)} ชิ้น",
                                "size": "sm",
                                "color": "#666666"
                            }
                        ],
                        "spacing": "sm"
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"💸 คอมมิชชัน: {product['commission_rate']}%",
                                "size": "sm",
                                "color": "#27AE60",
                                "weight": "bold"
                            },
                            {
                                "type": "text",
                                "text": f"= {commission_amount:,.2f} บาท",
                                "size": "sm",
                                "color": "#27AE60",
                                "weight": "bold"
                            }
                        ],
                        "spacing": "xs",
                        "margin": "md"
                    }
                ],
                "spacing": "md",
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "🛒 ดูสินค้า",
                            "uri": product['offer_link']
                        },
                        "style": "primary",
                        "color": "#E74C3C"
                    }
                ],
                "spacing": "sm",
                "paddingAll": "20px"
            }
        }
        
        if product.get('description'):
            flex_contents["body"]["contents"].append({
                "type": "separator",
                "margin": "md"
            })
            flex_contents["body"]["contents"].append({
                "type": "text",
                "text": product['description'][:100] + ("..." if len(product['description']) > 100 else ""),
                "size": "xs",
                "color": "#888888",
                "wrap": True,
                "margin": "md"
            })
        
        if rating_stars:
            flex_contents["body"]["contents"][0]["contents"].append({
                "type": "text",
                "text": f"{rating_stars} ({product.get('rating', 0)})",
                "size": "sm",
                "color": "#F39C12"
            })
        
        flex_message = FlexMessage(
            alt_text=f"รีวิว: {product['product_name']}",
            contents=FlexContainer.from_dict(flex_contents)
        )
        
        self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[flex_message]
            )
        )
    
    def _send_products_list(self, event, products: List[Dict], query: str):
        """ส่งรายการสินค้าหลายรายการแบบโซเชียลมีเดีย"""
        if len(products) == 1:
            # แสดงสินค้าเดียวด้วย Flex Message ที่ซ่อนลิงก์
            self._send_product_flex_hidden_link(event, products[0])
            return
        
        # สำหรับหลายสินค้า ใช้ Flex Carousel
        flex_contents = self._create_products_carousel(products, query)
        
        flex_message = FlexMessage(
            alt_text=f"🔍 เจอสินค้าดีๆ {len(products)} รายการ",
            contents=FlexContainer.from_dict(flex_contents)
        )
        
        self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[flex_message]
            )
        )
    
    def _send_not_found_message(self, event, query: str):
        """ส่งข้อความไม่พบสินค้า"""
        message = (
            f"❌ ไม่พบสินค้า '{query}'\n\n"
            f"💡 ลองค้นหาด้วย:\n"
            f"• ชื่อสินค้า เช่น 'อาหารแมว', 'ครีม'\n"
            f"• หมวดหมู่ เช่น 'สัตว์เลี้ยง', 'ความงาม'\n\n"
            f"พิมพ์ 'หมวดหมู่' เพื่อดูหมวดหมู่สินค้าทั้งหมด"
        )
        self._reply_text(event, message)
    
    def _show_stats(self, event):
        """แสดงสถิติสำหรับผู้ใช้ทั่วไป"""
        stats = self.db.get_stats()
        
        stats_text = (
            f"📊 สถิติระบบ Affiliate:\n"
            f"🛍️ สินค้าทั้งหมด: {stats.get('total_products', 0)} รายการ\n"
            f"🔍 การค้นหาทั้งหมด: {stats.get('total_searches', 0)} ครั้ง\n"
            f"💰 ราคาเฉลี่ย: {stats.get('average_price', 0):,.2f} บาท\n"
            f"💾 ฐานข้อมูล: {stats.get('database_type', 'Unknown')}"
        )
        
        self._reply_text(event, stats_text)
    
    def _show_categories(self, event):
        """แสดงหมวดหมู่สินค้าแบบง่าย"""
        category_text = """📋 หมวดหมู่สินค้า

💬 กดเลือกหมวดที่สนใจ:"""
        
        # Quick Reply แบบง่าย เด็กใช้ได้
        quick_replies = QuickReply(items=[
            QuickReplyItem(action=MessageAction(label="📱 มือถือ", text="มือถือ")),
            QuickReplyItem(action=MessageAction(label="👕 เสื้อผ้า", text="เสื้อผ้า")),
            QuickReplyItem(action=MessageAction(label="👟 รองเท้า", text="รองเท้า")),
            QuickReplyItem(action=MessageAction(label="🎒 กระเป๋า", text="กระเป๋า")),
            QuickReplyItem(action=MessageAction(label="💻 คอมพิวเตอร์", text="คอมพิวเตอร์")),
            QuickReplyItem(action=MessageAction(label="🏠 ของใช้บ้าน", text="ของใช้บ้าน")),
            QuickReplyItem(action=MessageAction(label="🎮 เกมส์", text="เกมส์")),
            QuickReplyItem(action=MessageAction(label="📚 หนังสือ", text="หนังสือ"))
        ])
        
        self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=category_text, quick_reply=quick_replies)]
            )
        )
        except Exception:
            # Fallback หากเกิดข้อผิดพลาด
            category_text = "📋 หมวดหมู่สินค้า

💬 กดเลือกหมวดที่สนใจ:"
            
            quick_replies = QuickReply(items=[
                QuickReplyItem(action=MessageAction(label="📱 มือถือ", text="มือถือ")),
                QuickReplyItem(action=MessageAction(label="👕 เสื้อผ้า", text="เสื้อผ้า")),
                QuickReplyItem(action=MessageAction(label="👟 รองเท้า", text="รองเท้า")),
                QuickReplyItem(action=MessageAction(label="🎒 กระเป๋า", text="กระเป๋า")),
                QuickReplyItem(action=MessageAction(label="💻 คอมพิวเตอร์", text="คอมพิวเตอร์")),
                QuickReplyItem(action=MessageAction(label="🏠 ของใช้บ้าน", text="ของใช้บ้าน")),
                QuickReplyItem(action=MessageAction(label="🎮 เกมส์", text="เกมส์")),
                QuickReplyItem(action=MessageAction(label="📚 หนังสือ", text="หนังสือ"))
            ])
            
            self.line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=category_text, quick_reply=quick_replies)]
                )
            )
            
            # เพิ่มปุ่มพิเศษ
            quick_reply_items.extend([
                QuickReplyItem(action=MessageAction(label="🔥 ขายดีทั้งหมด", text="เรียง ทั้งหมด ขายดี")),
                QuickReplyItem(action=MessageAction(label="💰 ราคาดี", text="เรียง ทั้งหมด ราคาถูก")),
                QuickReplyItem(action=MessageAction(label="⭐ คะแนนสูง", text="เรียง ทั้งหมด คะแนน"))
            ])
            
            quick_replies = QuickReply(items=quick_reply_items)
            
            # สร้างข้อความแสดงผล
            categories_text = "🎯 หมวดหมู่สินค้า (เรียงตามความนิยม):\n\n"
            
            # แสดงหมวดหมู่ฮิต
            if hot_categories:
                categories_text += "🔥 **หมวดหมู่ฮิต**:\n"
                for cat in hot_categories[:5]:
                    categories_text += f"• {cat['name']} ({cat['product_count']} รายการ, คะแนน {cat['popularity_score']})\n"
                categories_text += "\n"
            
            # แสดงหมวดหมู่ยอดนิยม
            if popular_categories:
                categories_text += "⭐ **หมวดหมู่ยอดนิยม**:\n"
                for cat in popular_categories[:3]:
                    categories_text += f"• {cat['name']} ({cat['product_count']} รายการ)\n"
                categories_text += "\n"
            
            categories_text += f"🛍️ รวมทั้งหมด {len(categories_with_stats)} หมวดหมู่\n"
            categories_text += f"💰 ช่วงราคา: {price_range['min_price']:,.0f} - {price_range['max_price']:,.0f} บาท\n\n"
            
            categories_text += "📱 **กดปุ่มด้านล่างเพื่อเลือก** หรือพิมพ์:\n"
            categories_text += "• หมวด [ชื่อหมวดหมู่] เช่น 'หมวด ความงาม'\n"
            categories_text += "• เรียง [คำค้น] หมวดหมู่ เช่น 'เรียง แมว หมวดหมู่'"
            
            self.line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=categories_text, quick_reply=quick_replies)]
                )
            )
            
        except Exception as e:
            print(f"[ERROR] Error showing smart categories: {e}")
            self._reply_text(event, "❌ เกิดข้อผิดพลาดในการแสดงหมวดหมู่")
    
    def _browse_category(self, event, category_name: str, user_id: str):
        """เรียกดูสินค้าในหมวดหมู่เฉพาะ"""
        try:
            print(f"[DEBUG] Browsing category: '{category_name}'")
            
            # ค้นหาสินค้าในหมวดหมู่นั้น เรียงตามยอดขาย
            search_result = self.db.search_products(
                query="",  # ค้นหาทั้งหมด
                limit=config.MAX_RESULTS_PER_SEARCH,
                offset=0,
                category=category_name,
                order_by='popularity'  # เรียงตามความนิยม
            )
            
            products = search_result.get('products', [])
            total = search_result.get('total', 0)
            has_more = search_result.get('has_more', False)
            
            print(f"[DEBUG] Found {len(products)} products in category '{category_name}' (total: {total})")
            
            if products:
                # แสดงผลพร้อม pagination สำหรับหมวดหมู่
                self._send_category_products(event, products, category_name, 1, total, has_more)
            else:
                self._reply_text(event, f"❌ ไม่พบสินค้าในหมวดหมู่ '{category_name}'\n💡 ลองเลือกหมวดหมู่อื่น หรือพิมพ์ 'หมวดหมู่' เพื่อดูทั้งหมด")
                
        except Exception as e:
            print(f"[ERROR] Category browse error: {e}")
            self._reply_text(event, "❌ เกิดข้อผิดพลาดในการเรียกดูหมวดหมู่")
    
    def _send_category_products(self, event, products: List[Dict], category_name: str,
                              page: int, total: int, has_more: bool):
        """ส่งรายการสินค้าในหมวดหมู่พร้อม pagination"""
        
        # สร้าง Flex Carousel สำหรับสินค้า
        flex_contents = self._create_products_carousel(products, f"หมวดหมู่: {category_name}")
        
        # เพิ่มข้อมูล pagination
        total_pages = (total + config.MAX_RESULTS_PER_SEARCH - 1) // config.MAX_RESULTS_PER_SEARCH
        
        # สร้างปุ่ม pagination สำหรับหมวดหมู่
        pagination_buttons = []
        
        # ปุ่มหน้าก่อนหน้า
        if page > 1:
            prev_action = f"หน้า{page-1}::cat:{category_name}:sort:popularity"
            pagination_buttons.append({
                "type": "button",
                "action": {
                    "type": "message",
                    "label": "◀️ หน้าก่อน",
                    "text": prev_action
                },
                "style": "secondary",
                "height": "sm"
            })
        
        # ปุ่มหน้าถัดไป
        if has_more:
            next_action = f"หน้า{page+1}::cat:{category_name}:sort:popularity"
            pagination_buttons.append({
                "type": "button",
                "action": {
                    "type": "message",
                    "label": "หน้าถัดไป ▶️",
                    "text": next_action
                },
                "style": "secondary",
                "height": "sm"
            })
        
        # ปุ่มตัวเลือกการเรียง
        sort_buttons = [
            {
                "type": "button",
                "action": {
                    "type": "message",
                    "label": "🔥 ขายดี",
                    "text": f"เรียง หมวด:{category_name} ขายดี"
                },
                "style": "primary",
                "height": "sm"
            },
            {
                "type": "button", 
                "action": {
                    "type": "message",
                    "label": "💰 ราคาถูก",
                    "text": f"เรียง หมวด:{category_name} ราคาถูก"
                },
                "style": "primary",
                "height": "sm"
            }
        ]
        
        # เพิ่ม footer สำหรับ controls
        if total_pages > 1 or total > 0:
            footer_contents = [
                {
                    "type": "text",
                    "text": f"📂 {category_name}",
                    "size": "md",
                    "align": "center",
                    "weight": "bold",
                    "color": "#333333"
                }
            ]
            
            if total_pages > 1:
                footer_contents.append({
                    "type": "text",
                    "text": f"📄 หน้า {page}/{total_pages} | รวม {total} รายการ",
                    "size": "xs",
                    "align": "center",
                    "color": "#666666",
                    "margin": "xs"
                })
            else:
                footer_contents.append({
                    "type": "text", 
                    "text": f"รวม {total} รายการ",
                    "size": "xs",
                    "align": "center",
                    "color": "#666666",
                    "margin": "xs"
                })
            
            # รวมปุ่มทั้งหมด
            all_buttons = []
            if pagination_buttons:
                all_buttons.extend(pagination_buttons)
            if len(all_buttons) < 4:  # เพิ่มปุ่มเรียงถ้ามีที่ว่าง
                all_buttons.extend(sort_buttons[:4-len(all_buttons)])
                
            flex_contents["contents"].append({
                "type": "bubble",
                "size": "nano",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": footer_contents,
                    "paddingAll": "12px"
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": all_buttons,
                            "spacing": "sm"
                        }
                    ],
                    "paddingAll": "8px"
                } if all_buttons else None
            })
        
        flex_message = FlexMessage(
            alt_text=f"📂 {category_name}: {len(products)} รายการ",
            contents=FlexContainer.from_dict(flex_contents)
        )
        
        self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[flex_message]
            )
        )
    
    def _show_all_products(self, event, user_id: str):
        """แสดงสินค้าทั้งหมด (สำหรับแอดมิน)"""
        products = self.db.get_all_products(20)  # จำกัด 20 รายการ
        
        if products:
            products_text = f"📋 สินค้าทั้งหมด ({len(products)} รายการ):\n\n"
            
            for product in products:
                commission = product.get('commission_amount', 0)
                products_text += (
                    f"🔹 {product['product_code']}: {product['product_name']}\n"
                    f"   💰 {product['price']:,.0f}฿ | 💸 {commission:,.0f}฿\n"
                    f"   🏪 {product['shop_name']}\n\n"
                )
            
            self._reply_text(event, products_text)
        else:
            self._reply_text(event, "📭 ยังไม่มีสินค้าในระบบ")
        
        del self.admin_state[user_id]
    
    def _show_admin_stats(self, event, user_id: str):
        """แสดงสถิติสำหรับแอดมิน"""
        stats = self.db.get_stats()
        
        stats_text = (
            f"📊 สถิติระบบ (Admin):\n"
            f"🛍️ สินค้าทั้งหมด: {stats.get('total_products', 0)} รายการ\n"
            f"🔍 การค้นหาทั้งหมด: {stats.get('total_searches', 0)} ครั้ง\n"
            f"💰 ราคาเฉลี่ย: {stats.get('average_price', 0):,.2f} บาท\n"
            f"💾 ฐานข้อมูล: {stats.get('database_type', 'Unknown')}"
        )
        
        self._reply_text(event, stats_text)
        del self.admin_state[user_id]
    
    def _show_category_stats(self, event):
        """แสดงสถิติหมวดหมู่แบบละเอียด (สำหรับ Admin)"""
        try:
            categories_with_stats = self.db.get_categories_with_stats()
            
            if not categories_with_stats:
                self._reply_text(event, "❌ ไม่มีข้อมูลหมวดหมู่")
                return
            
            stats_text = "📊 **สถิติหมวดหมู่แบบละเอียด**:\n\n"
            
            # จัดกลุ่มตามความนิยม
            hot_categories = [cat for cat in categories_with_stats if cat['popularity_score'] >= 50]
            popular_categories = [cat for cat in categories_with_stats if 20 <= cat['popularity_score'] < 50]
            normal_categories = [cat for cat in categories_with_stats if cat['popularity_score'] < 20]
            
            # แสดงหมวดหมู่ฮิต
            if hot_categories:
                stats_text += "🔥 **หมวดหมู่ฮิต** (คะแนน ≥ 50):\n"
                for i, cat in enumerate(hot_categories[:5], 1):
                    stats_text += (
                        f"{i}. **{cat['name']}**\n"
                        f"   📊 คะแนนความนิยม: {cat['popularity_score']}\n"
                        f"   🛍️ จำนวนสินค้า: {cat['product_count']} รายการ\n"
                        f"   🔥 ยอดขายรวม: {cat['total_sold']:,} ชิ้น\n"
                        f"   💰 ราคาเฉลี่ย: {cat['avg_price']:,.0f} บาท\n"
                        f"   ⭐ คะแนนเฉลี่ย: {cat['avg_rating']:.1f}/5.0\n\n"
                    )
            
            # แสดงหมวดหมู่ยอดนิยม
            if popular_categories:
                stats_text += "⭐ **หมวดหมู่ยอดนิยม** (คะแนน 20-49):\n"
                for i, cat in enumerate(popular_categories[:3], 1):
                    stats_text += (
                        f"{i}. **{cat['name']}**\n"
                        f"   📊 คะแนน: {cat['popularity_score']} | "
                        f"🛍️ {cat['product_count']} รายการ | "
                        f"🔥 {cat['total_sold']:,} ชิ้น\n"
                        f"   💰 {cat['avg_price']:,.0f}฿ | "
                        f"⭐ {cat['avg_rating']:.1f}/5.0\n\n"
                    )
            
            # แสดงสรุป
            total_products = sum(cat['product_count'] for cat in categories_with_stats)
            total_sold = sum(cat['total_sold'] for cat in categories_with_stats)
            
            stats_text += f"📈 **สรุปภาพรวม**:\n"
            stats_text += f"• รวมทั้งหมด: {len(categories_with_stats)} หมวดหมู่\n"
            stats_text += f"• หมวดหมู่ฮิต: {len(hot_categories)} หมวด\n"
            stats_text += f"• หมวดหมู่ยอดนิยม: {len(popular_categories)} หมวด\n"
            stats_text += f"• สินค้าทั้งหมด: {total_products:,} รายการ\n"
            stats_text += f"• ยอดขายรวม: {total_sold:,} ชิ้น\n\n"
            
            stats_text += "💡 **เคล็ดลับ**: หมวดหมู่ฮิตได้รับการแสดงเป็นลำดับแรกใน Quick Reply buttons"
            
            self._reply_text(event, stats_text)
            
        except Exception as e:
            print(f"[ERROR] Error showing category stats: {e}")
            self._reply_text(event, "❌ เกิดข้อผิดพลาดในการแสดงสถิติหมวดหมู่")
    
    def _show_admin_dashboard(self, event, user_id: str):
        """แสดง Admin Dashboard แบบครอบคลุม"""
        try:
            # ดึงข้อมูลสถิติทั้งหมด
            stats = self.db.get_stats()
            categories_stats = self.db.get_categories_with_stats()
            price_range = self.db.get_price_range()
            
            # คำนวณสถิติเพิ่มเติม
            total_products = stats.get('total_products', 0)
            total_searches = stats.get('total_searches', 0)
            avg_price = stats.get('average_price', 0)
            
            # หมวดหมู่ยอดนิยม
            hot_categories = [cat for cat in categories_stats if cat['popularity_score'] >= 50]
            
            # สินค้าที่ขายดีที่สุด (จำลอง - ต้องการ query พิเศษ)
            top_products = self.db.search_products("", limit=3, order_by='popularity')['products']
            
            dashboard_text = "🎛️ **Admin Dashboard - ภาพรวมระบบ**\n\n"
            
            # สถิติหลัก
            dashboard_text += "📊 **สถิติหลัก**:\n"
            dashboard_text += f"• 🛍️ สินค้าทั้งหมด: **{total_products:,}** รายการ\n"
            dashboard_text += f"• 🔍 การค้นหา: **{total_searches:,}** ครั้ง\n"
            dashboard_text += f"• 💰 ราคาเฉลี่ย: **{avg_price:,.0f}** บาท\n"
            dashboard_text += f"• 📂 หมวดหมู่: **{len(categories_stats)}** หมวด\n\n"
            
            # ช่วงราคา
            dashboard_text += "💳 **ช่วงราคาสินค้า**:\n"
            dashboard_text += f"• ราคาต่ำสุด: **{price_range['min_price']:,.0f}** บาท\n"
            dashboard_text += f"• ราคาสูงสุด: **{price_range['max_price']:,.0f}** บาท\n\n"
            
            # หมวดหมู่ฮิต
            if hot_categories:
                dashboard_text += "🔥 **หมวดหมู่ฮิต** (Top 3):\n"
                for i, cat in enumerate(hot_categories[:3], 1):
                    dashboard_text += f"{i}. **{cat['name']}** - คะแนน {cat['popularity_score']}\n"
                    dashboard_text += f"   📦 {cat['product_count']} รายการ | 🔥 {cat['total_sold']:,} ขาย\n"
                dashboard_text += "\n"
            
            # สินค้าขายดี
            if top_products:
                dashboard_text += "⭐ **สินค้าขายดี** (Top 3):\n"
                for i, product in enumerate(top_products[:3], 1):
                    name = product['product_name'][:30] + "..." if len(product['product_name']) > 30 else product['product_name']
                    dashboard_text += f"{i}. {name}\n"
                    dashboard_text += f"   💰 {product['price']:,.0f}฿ | 🔥 {product.get('sold_count', 0):,} ขาย\n"
                dashboard_text += "\n"
            
            # ประสิทธิภาพระบบ
            dashboard_text += "⚡ **ประสิทธิภาพระบบ**:\n"
            
            # คำนวณ search rate
            search_rate = total_searches / max(total_products, 1)
            dashboard_text += f"• อัตราการค้นหา: **{search_rate:.2f}** ครั้ง/สินค้า\n"
            
            # คำนวณ conversion rate (จำลอง)
            conversion_rate = min((total_searches / max(total_products * 10, 1)) * 100, 100)
            dashboard_text += f"• อัตราการใช้งาน: **{conversion_rate:.1f}%**\n\n"
            
            # คำแนะนำ
            dashboard_text += "💡 **คำแนะนำเชิงข้อมูล**:\n"
            
            if len(hot_categories) == 0:
                dashboard_text += "• ⚠️ ไม่มีหมวดหมู่ฮิต - ควรเพิ่มสินค้าในหมวดหมู่ยอดนิยม\n"
            elif len(hot_categories) >= 3:
                dashboard_text += "• ✅ มีหมวดหมู่ฮิตหลากหลาย - ระบบมีความสมดุลดี\n"
            
            if total_products < 100:
                dashboard_text += "• 📈 ควรเพิ่มสินค้าให้ถึง 100+ รายการเพื่อความหนาแน่น\n"
            elif total_products >= 1000:
                dashboard_text += "• 🎉 สินค้าครบ 1000+ รายการ - ระดับ Enterprise!\n"
            
            if search_rate < 0.1:
                dashboard_text += "• 🔍 อัตราการค้นหาต่ำ - ควร optimize SEO ของสินค้า\n"
            elif search_rate > 2.0:
                dashboard_text += "• 🔥 อัตราการค้นหาสูง - ระบบได้รับความนิยมดี!\n"
            
            dashboard_text += "\n---\n"
            dashboard_text += "🎯 **การดำเนินการด่วน**:\n"
            dashboard_text += "• พิมพ์ 'สถิติหมวดหมู่' - ดูสถิติหมวดหมู่ละเอียด\n"
            dashboard_text += "• พิมพ์ 'หมวดหมู่' - ตรวจสอบ Smart Grouping\n"
            dashboard_text += "• พิมพ์ 'สถิติ' - ดูสถิติพื้นฐาน"
            
            self._reply_text(event, dashboard_text)
            del self.admin_state[user_id]
            
        except Exception as e:
            print(f"[ERROR] Error showing admin dashboard: {e}")
            self._reply_text(event, "❌ เกิดข้อผิดพลาดในการแสดง Dashboard")
    
    def _handle_bulk_update(self, event, command: str):
        """จัดการคำสั่ง bulk update - สำหรับ Admin เท่านั้น"""
        try:
            # แยกคำสั่ง: codes field=value
            parts = command.split(' ', 1)
            if len(parts) != 2:
                self._reply_text(event, "❌ รูปแบบคำสั่งไม่ถูกต้อง\n💡 ใช้: bulk-update [codes] [field]=[value]\n🔸 ตัวอย่าง: bulk-update PROD001,PROD002 commission_rate=15")
                return
            
            codes_str = parts[0]
            field_value = parts[1]
            
            # แยก field=value
            if '=' not in field_value:
                self._reply_text(event, "❌ รูปแบบ field=value ไม่ถูกต้อง\n💡 ตัวอย่าง: commission_rate=15 หรือ category=ใหม่")
                return
            
            field, value = field_value.split('=', 1)
            
            # แยก product codes
            product_codes = [code.strip().upper() for code in codes_str.split(',')]
            
            # สร้าง update data
            update_data = {}
            
            # แปลงค่าตามประเภท field
            if field in ['price', 'commission_rate', 'rating']:
                try:
                    update_data[field] = float(value)
                except ValueError:
                    self._reply_text(event, f"❌ ค่า {field} ต้องเป็นตัวเลข")
                    return
            elif field in ['sold_count']:
                try:
                    update_data[field] = int(value)
                except ValueError:
                    self._reply_text(event, f"❌ ค่า {field} ต้องเป็นจำนวนเต็ม")
                    return
            else:
                # String fields
                update_data[field] = value
            
            # ดำเนินการ bulk update
            result = self.db.bulk_update_products(product_codes, update_data)
            
            if result['success']:
                response = f"✅ **Bulk Update สำเร็จ!**\n\n"
                response += f"📊 อัปเดตสำเร็จ: **{result['updated_count']}** รายการ\n"
                response += f"🔧 Field: **{field}** = **{value}**\n\n"
                response += f"📝 รายการที่อัปเดต:\n"
                for code in product_codes[:10]:  # แสดงแค่ 10 รายการแรก
                    response += f"• {code}\n"
                
                if len(product_codes) > 10:
                    response += f"... และอีก {len(product_codes) - 10} รายการ"
                
                self._reply_text(event, response)
            else:
                self._reply_text(event, f"❌ Bulk Update ล้มเหลว: {result['message']}")
                
        except Exception as e:
            print(f"[ERROR] Bulk update error: {e}")
            self._reply_text(event, "❌ เกิดข้อผิดพลาดในการ Bulk Update")
    
    def _handle_bulk_delete(self, event, codes_str: str):
        """จัดการคำสั่ง bulk delete - สำหรับ Admin เท่านั้น"""
        try:
            # แยก product codes
            product_codes = [code.strip().upper() for code in codes_str.split(',')]
            
            if len(product_codes) == 0:
                self._reply_text(event, "❌ กรุณาระบุรหัสสินค้าที่ต้องการลบ\n💡 ตัวอย่าง: bulk-delete PROD001,PROD002")
                return
            
            # ยืนยันการลบ (เพื่อความปลอดภัย)
            if len(product_codes) > 5:
                self._reply_text(event, f"⚠️ **คำเตือน: กำลังลบ {len(product_codes)} รายการ**\n\nเพื่อความปลอดภัย กรุณาลบทีละไม่เกิน 5 รายการ\nหรือใช้คำสั่ง: bulk-delete {','.join(product_codes[:5])}")
                return
            
            # ดำเนินการ bulk delete
            result = self.db.bulk_delete_products(product_codes)
            
            if result['success']:
                response = f"✅ **Bulk Delete สำเร็จ!**\n\n"
                response += f"🗑️ ลบสำเร็จ: **{result['deleted_count']}** รายการ\n\n"
                response += f"📝 รายการที่ลบ:\n"
                for code in product_codes:
                    response += f"• {code}\n"
                
                self._reply_text(event, response)
            else:
                self._reply_text(event, f"❌ Bulk Delete ล้มเหลว: {result['message']}")
                
        except Exception as e:
            print(f"[ERROR] Bulk delete error: {e}")
            self._reply_text(event, "❌ เกิดข้อผิดพลาดในการ Bulk Delete")
    
    def _handle_bulk_import(self, event, command: str):
        """จัดการคำสั่ง bulk import - สำหรับ Admin เท่านั้น"""
        try:
            if command.lower() == 'sample':
                # สร้างไฟล์ตัวอย่าง CSV
                sample_path = "sample_products.csv"
                message = bulk_importer.create_sample_csv(sample_path)
                
                response = f"📁 **ไฟล์ตัวอย่างพร้อมใช้งาน**\n\n"
                response += f"{message}\n\n"
                response += f"📋 **วิธีใช้งาน:**\n"
                response += f"1. ดาวน์โหลดไฟล์ `{sample_path}`\n"
                response += f"2. แก้ไขข้อมูลสินค้าตามต้องการ\n"
                response += f"3. อัปโหลดไฟล์ไปยังเซิร์ฟเวอร์\n"
                response += f"4. ใช้คำสั่ง: `bulk-import [URL]`\n\n"
                response += f"🔧 **คอลัมน์ที่รองรับ:**\n"
                response += f"• product_name, category, price (จำเป็น)\n"
                response += f"• description, brand, rating, tags\n"
                response += f"• affiliate_link, image_url\n"
                response += f"• commission_rate, is_featured"
                
                self._reply_text(event, response)
                return
            
            # ตรวจสอบว่าเป็น URL หรือไม่
            if command.startswith('http'):
                response = f"🚧 **ฟีเจอร์กำลังพัฒนา**\n\n"
                response += f"ขณะนี้ยังไม่รองรับการนำเข้าจาก URL\n"
                response += f"กรุณาใช้คำสั่ง: `bulk-import sample`\n"
                response += f"เพื่อสร้างไฟล์ตัวอย่างก่อน"
            else:
                response = f"❌ **คำสั่งไม่ถูกต้อง**\n\n"
                response += f"💡 **วิธีใช้งาน:**\n"
                response += f"• `bulk-import sample` - สร้างไฟล์ตัวอย่าง\n"
                response += f"• `bulk-import [URL]` - นำเข้าจาก URL (กำลังพัฒนา)"
            
            self._reply_text(event, response)
                
        except Exception as e:
            print(f"[ERROR] Bulk import error: {e}")
            self._reply_text(event, "❌ เกิดข้อผิดพลาดในการนำเข้าข้อมูล")
    
    def _show_ai_recommendations(self, event, user_id: str, context: str = ""):
        """แสดงคำแนะนำสินค้าด้วย AI"""
        try:
            print(f"[DEBUG] AI recommendations for user: {user_id}")
            
            # ดึงคำแนะนำแบบปรับตัว
            recommendations = ai_recommender.get_personalized_recommendations(user_id, context, limit=6)
            
            if not any(recommendations.values()):
                self._reply_text(event, "🤖 ระบบแนะนำยังไม่มีข้อมูลเพียงพอ\nลองค้นหาสินค้าก่อนเพื่อให้ระบบเรียนรู้ความสนใจของคุณ")
                return
            
            # สร้างข้อความแนะนำ
            response = "🤖 **AI แนะนำสินค้าสำหรับคุณ**\n\n"
            
            # แนะนำตามความสนใจส่วนตัว
            if recommendations['personal']:
                response += "💝 **แนะนำตามความสนใจ:**\n"
                for i, product in enumerate(recommendations['personal'][:3], 1):
                    name = product.get('product_name', 'ไม่ระบุชื่อ')[:40]
                    price = f"{product.get('price', 0):,.0f}"
                    reason = product.get('recommendation_reason', '')
                    response += f"{i}. {name}\n   💰 {price} บาท | {reason}\n\n"
            
            # แนะนำสินค้าที่กำลังมาแรง
            if recommendations['trending']:
                response += "🔥 **สินค้าขายดีตอนนี้:**\n"
                for i, product in enumerate(recommendations['trending'][:2], 1):
                    name = product.get('product_name', 'ไม่ระบุชื่อ')[:40]
                    price = f"{product.get('price', 0):,.0f}"
                    sold = product.get('sold_count', 0)
                    response += f"{i}. {name}\n   💰 {price} บาท | ขายไป {sold:,} ชิ้น\n\n"
            
            # เพิ่มข้อมูลโปรไฟล์ผู้ใช้
            user_profile = ai_recommender.get_user_profile_summary(user_id)
            if user_profile.get('top_interests'):
                interests = [interest[0] for interest in user_profile['top_interests'][:3]]
                response += f"📊 **ความสนใจของคุณ:** {', '.join(interests)}\n"
            
            response += f"🎯 **คะแนนการแนะนำ:** {recommendations['total_score']}/10\n\n"
            response += "💡 **ทิป:** ค้นหาสินค้ามากขึ้นเพื่อให้ AI แนะนำได้แม่นยำยิ่งขึ้น!"
            
            # สร้าง Quick Reply สำหรับดูรายละเอียด
            quick_reply_items = []
            all_products = recommendations['personal'] + recommendations['trending']
            
            for product in all_products[:3]:
                code = product.get('product_code')
                if code:
                    quick_reply_items.append({
                        'label': f"ดู {product.get('product_name', '')[:15]}...",
                        'text': f"รหัส {code}"
                    })
            
            # เพิ่มตัวเลือกอื่น ๆ
            quick_reply_items.extend([
                {'label': '🔄 แนะนำใหม่', 'text': 'แนะนำสินค้า'},
                {'label': '📊 โปรไฟล์ของฉัน', 'text': 'โปรไฟล์'},
                {'label': '🏠 หน้าหลัก', 'text': 'หน้าหลัก'}
            ])
            
            quick_replies = self._create_modern_quick_reply(quick_reply_items[:13])  # จำกัด 13 รายการ
            
            self.line_bot_api.reply_message(
                event.reply_token,
                TextMessage(text=response, quick_reply=quick_replies)
            )
                
        except Exception as e:
            print(f"[ERROR] AI recommendations error: {e}")
            self._reply_text(event, "❌ เกิดข้อผิดพลาดในระบบแนะนำ AI")
    
    def _handle_top_products(self, event, command: str):
        """จัดการคำสั่งแสดงสินค้าอันดับสูง - สำหรับ Admin เท่านั้น"""
        try:
            parts = command.split()
            
            # ค่าเริ่มต้น
            metric = 'sold_count'
            limit = 5
            
            if len(parts) >= 1:
                metric = parts[0]
            if len(parts) >= 2:
                try:
                    limit = int(parts[1])
                    limit = min(limit, 20)  # จำกัดไม่เกิน 20
                except ValueError:
                    limit = 5
            
            # ดึงข้อมูล
            top_products = self.db.get_top_products_by_metric(metric, limit)
            
            if not top_products:
                self._reply_text(event, f"❌ ไม่พบข้อมูลสินค้าสำหรับ metric: {metric}")
                return
            
            # สร้างข้อความแสดงผล
            metric_names = {
                'sold_count': 'ยอดขาย',
                'price': 'ราคา',
                'rating': 'คะแนน',
                'commission_amount': 'ค่าคอมมิชชั่น'
            }
            
            metric_display = metric_names.get(metric, metric)
            response = f"🏆 **Top {limit} สินค้า - เรียงตาม{metric_display}**\n\n"
            
            for i, product in enumerate(top_products, 1):
                name = product['product_name'][:25] + "..." if len(product['product_name']) > 25 else product['product_name']
                code = product['product_code']
                
                response += f"{i}. **{name}**\n"
                response += f"   🔑 {code} | 💰 {product['price']:,.0f}฿\n"
                
                if metric == 'sold_count':
                    response += f"   🔥 ขาย: {product.get('sold_count', 0):,} ชิ้น\n"
                elif metric == 'rating':
                    response += f"   ⭐ คะแนน: {product.get('rating', 0):.1f}/5.0\n"
                elif metric == 'commission_amount':
                    response += f"   💸 คอมมิชชั่น: {product.get('commission_amount', 0):,.0f}฿\n"
                
                response += "\n"
            
            response += f"💡 **คำสั่งอื่นๆ**:\n"
            response += f"• top-products sold_count 10 - ขายดี 10 อันดับ\n"
            response += f"• top-products price 5 - ราคาสูง 5 อันดับ\n"
            response += f"• top-products rating 3 - คะแนนสูง 3 อันดับ"
            
            self._reply_text(event, response)
            
        except Exception as e:
            print(f"[ERROR] Top products error: {e}")
            self._reply_text(event, "❌ เกิดข้อผิดพลาดในการแสดงสินค้าอันดับสูง")
    
    def _create_modern_quick_reply(self, items: List[Dict[str, str]]) -> QuickReply:
        """สร้าง Quick Reply แบบทันสมัย"""
        quick_reply_items = []
        
        for item in items[:13]:  # จำกัด 13 รายการตาม LINE limit
            quick_reply_items.append(
                QuickReplyItem(action=MessageAction(
                    label=item['label'], 
                    text=item['text']
                ))
            )
        
        return QuickReply(items=quick_reply_items)
    
    def _show_search_guide(self, event):
        """แสดงวิธีค้นหาสินค้าแบบง่าย"""
        guide_text = """🔍 ค้นหาสินค้า

💬 พิมพ์สิ่งที่ต้องการ:
• "มือถือ" "โทรศัพท์" 
• "เสื้อ" "กางเกง"
• "รองเท้า" "กระเป๋า"

💡 หรือเลือกหมวดด้านล่าง"""
        
        # Quick Reply แบบง่าย เด็กใช้ได้
        quick_replies = QuickReply(items=[
            QuickReplyItem(action=MessageAction(label="📱 มือถือ", text="มือถือ")),
            QuickReplyItem(action=MessageAction(label="👕 เสื้อผ้า", text="เสื้อผ้า")),
            QuickReplyItem(action=MessageAction(label="👟 รองเท้า", text="รองเท้า")),
            QuickReplyItem(action=MessageAction(label="🎒 กระเป๋า", text="กระเป๋า")),
            QuickReplyItem(action=MessageAction(label="💻 คอมพิวเตอร์", text="คอมพิวเตอร์")),
            QuickReplyItem(action=MessageAction(label="🏠 ของใช้บ้าน", text="ของใช้บ้าน")),
            QuickReplyItem(action=MessageAction(label="🔥 ขายดี", text="ขายดี")),
            QuickReplyItem(action=MessageAction(label="💰 โปรโมชั่น", text="โปรโมชั่น"))
        ])
        
        self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=guide_text, quick_reply=quick_replies)]
            )
        )
    
    def _show_bestsellers(self, event):
        """แสดงสินค้าขายดีพร้อม Quick Reply หมวดหมู่"""
        try:
            # ดึงสินค้าขายดี
            bestsellers = self.db.get_top_products_by_metric('sold_count', 5)
            categories = self.db.get_categories()[:8]  # เอาแค่ 8 หมวดหมู่
            
            # สร้าง Quick Reply สำหรับหมวดหมู่ขายดี
            category_options = []
            for cat in categories:
                category_options.append({
                    'label': f'🔥 {cat}', 
                    'text': f'เรียง หมวด:{cat} ขายดี'
                })
            
            # เพิ่มตัวเลือกพิเศษ
            category_options.extend([
                {'label': '🏆 Top 10 ขายดี', 'text': 'top-products sold_count 10'},
                {'label': '💎 Top 5 ราคาแพง', 'text': 'top-products price 5'},
                {'label': '⭐ Top 5 คะแนนสูง', 'text': 'top-products rating 5'},
                {'label': '📊 สถิติครบถ้วน', 'text': 'สถิติ'},
                {'label': '🏠 หน้าหลัก', 'text': '🏠 หน้าหลัก'}
            ])
            
            quick_replies = self._create_modern_quick_reply(category_options)
            
            response_text = "🔥 **สินค้าขายดีอันดับต้นๆ**\n\n"
            
            if bestsellers:
                for i, product in enumerate(bestsellers, 1):
                    name = product['product_name'][:30] + "..." if len(product['product_name']) > 30 else product['product_name']
                    response_text += f"{i}. **{name}**\n"
                    response_text += f"   💰 {product['price']:,.0f}฿ | 🔥 {product.get('sold_count', 0):,} ขาย\n"
                    response_text += f"   🏪 {product['shop_name']}\n\n"
            
            response_text += "🎯 **เลือกหมวดหมู่เพื่อดูสินค้าขายดีเฉพาะหมวด**"
            
            self.line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=response_text, quick_reply=quick_replies)]
                )
            )
            
        except Exception as e:
            print(f"[ERROR] Show bestsellers error: {e}")
            self._reply_text(event, "❌ เกิดข้อผิดพลาดในการแสดงสินค้าขายดี")
    
    def _show_promotions(self, event):
        """แสดงโปรโมชั่นและข้อเสนอพิเศษ"""
        promo_options = [
            {'label': '🔥 สินค้าขายดี', 'text': 'เรียง ทั้งหมด ขายดี'},
            {'label': '💰 ราคาดีที่สุด', 'text': 'เรียง ทั้งหมด ราคาถูก'},
            {'label': '⭐ คะแนนสูงสุด', 'text': 'เรียง ทั้งหมด คะแนน'},
            {'label': '🆕 สินค้าใหม่', 'text': 'เรียง ทั้งหมด ใหม่'},
            {'label': '🎯 สินค้าแนะนำ', 'text': 'แนะนำ'},
            {'label': '🏷️ ค้นหาด้วยรหัส', 'text': 'รหัส'},
            {'label': '📂 เลือกหมวดหมู่', 'text': 'หมวดหมู่'},
            {'label': '📊 ดูสถิติ', 'text': 'สถิติ'}
        ]
        
        quick_replies = self._create_modern_quick_reply(promo_options)
        
        promo_text = """💰 **โปรโมชั่นพิเศษ**

🎉 **ข้อเสนอพิเศษวันนี้**:
• 🔥 สินค้าขายดี - คัดสรรแล้ว!
• 💎 สินค้าคุณภาพ - ราคาดีที่สุด
• ⭐ สินค้าคะแนนสูง - รีวิวดีเยี่ยม
• 🆕 สินค้าใหม่ - อัปเดตล่าสุด

🎯 **วิธีรับโปรโมชั่น**:
1. เลือกหมวดหมู่ที่สนใจ
2. เรียงตามที่ต้องการ (ขายดี/ราคา/คะแนน)
3. คลิกซื้อเพื่อรับส่วนลดพิเศษ!

💡 **เคล็ดลับ**: ใช้การกรองเพื่อหาสินค้าในงบประมาณที่ต้องการ

🎁 กดปุ่มด้านล่างเพื่อเริ่มช้อปปิ้ง!"""
        
        self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=promo_text, quick_reply=quick_replies)]
            )
        )
    
    def _show_help_menu(self, event):
        """แสดงเมนูช่วยเหลือที่ครอบคลุม"""
        help_options = [
            {'label': '🔍 วิธีค้นหา', 'text': '🔍 ค้นหาสินค้า'},
            {'label': '📂 ดูหมวดหมู่', 'text': 'หมวดหมู่'},
            {'label': '🏷️ ค้นหาด้วยรหัส', 'text': 'รหัส EXAMPLE'},
            {'label': '💰 ข้อเสนอพิเศษ', 'text': '💰 โปรโมชั่น'},
            {'label': '📊 ดูสถิติ', 'text': 'สถิติ'},
            {'label': '🎯 ตัวอย่างคำสั่ง', 'text': 'ตัวอย่าง'},
            {'label': '🔥 สินค้าแนะนำ', 'text': '🔥 ขายดี'},
            {'label': '🏠 หน้าหลัก', 'text': '🏠 หน้าหลัก'}
        ]
        
        quick_replies = self._create_modern_quick_reply(help_options)
        
        help_text = """❓ **ศูนย์ช่วยเหลือ - คู่มือการใช้งาน**

🎯 **การค้นหาพื้นฐาน**:
• พิมพ์ชื่อสินค้า: `อาหารแมว`, `ครีม`, `โทรศัพท์`
• ค้นหาด้วยรหัส: `รหัส PROD001`
• เลือกหมวดหมู่: กด `หมวดหมู่`

⚡ **คำสั่งขั้นสูง**:
• `กรอง [สินค้า] ราคา:100-500` - กรองตามราคา
• `เรียง [สินค้า] ขายดี` - เรียงตามยอดขาย
• `หน้า2:[สินค้า]` - ดูหน้าถัดไป

🎨 **ฟีเจอร์พิเศษ**:
• Smart Category Grouping - หมวดหมู่เรียงตามความนิยม
• Enterprise Pagination - ค้นหาในสินค้าหลายพันรายการ
• Professional UI - การแสดงผลแบบโซเชียลมีเดีย

🔧 **Admin Features**:
• Dashboard แบบครอบคลุม
• Bulk Operations จัดการหลายรายการ
• Analytics & Insights ข้อมูลเชิงลึก

💡 **ต้องการความช่วยเหลือเพิ่มเติม?**
กดปุ่มด้านล่างเพื่อดูรายละเอียดเพิ่มเติม!"""
        
        self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=help_text, quick_reply=quick_replies)]
            )
        )
    
    def _show_home_menu(self, event):
        """แสดงเมนูหน้าหลักที่ครอบคลุม"""
        home_options = [
            {'label': '🔍 ค้นหาสินค้า', 'text': '🔍 ค้นหาสินค้า'},
            {'label': '📂 หมวดหมู่', 'text': 'หมวดหมู่'},
            {'label': '🔥 ขายดี', 'text': '🔥 ขายดี'},
            {'label': '💰 โปรโมชั่น', 'text': '💰 โปรโมชั่น'},
            {'label': '📊 สถิติ', 'text': 'สถิติ'},
            {'label': '❓ ช่วยเหลือ', 'text': '❓ ช่วยเหลือ'},
            {'label': '⭐ สินค้าคะแนนสูง', 'text': 'เรียง ทั้งหมด คะแนน'},
            {'label': '🆕 สินค้าใหม่', 'text': 'เรียง ทั้งหมด ใหม่'}
        ]
        
        quick_replies = self._create_modern_quick_reply(home_options)
        
        stats = self.db.get_stats()
        total_products = stats.get('total_products', 0)
        categories_count = stats.get('categories_count', 0)
        
        home_text = f"""🏠 **ยินดีต้อนรับสู่ Affiliate Shopping Assistant**

🛍️ **ภาพรวมระบบ**:
• สินค้าทั้งหมด: **{total_products:,}** รายการ
• หมวดหมู่: **{categories_count}** หมวด
• ระบบค้นหาขั้นสูงพร้อม AI
• รองรับสินค้าหลายพันรายการ

🎯 **ฟีเจอร์เด่น**:
• 🔍 **ค้นหาอัจฉริยะ** - หาสินค้าได้แม่นยำ
• 📂 **Smart Category** - หมวดหมู่เรียงตามความนิยม
• 🔥 **ขายดี Real-time** - อัปเดตตลอดเวลา
• 💰 **โปรโมชั่นพิเศษ** - ข้อเสนอสุดคุ้ม

🚀 **พร้อมเริ่มช้อปปิ้งแล้ว!**
เลือกสิ่งที่ต้องการจากปุ่มด้านล่าง หรือพิมพ์ชื่อสินค้าได้เลย!

💡 **เคล็ดลับ**: ลองพิมพ์ "อาหารแมว" หรือ "โทรศัพท์" เพื่อดูตัวอย่าง!"""
        
        self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=home_text, quick_reply=quick_replies)]
            )
        )
    
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
affiliate_handler = AffiliateLineHandler()