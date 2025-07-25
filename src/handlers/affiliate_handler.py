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
            
            if text.lower() in ["สถิติหมวดหมู่", "category-stats"] and user_id == config.ADMIN_USER_ID:
                self._show_category_stats(event)
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
    
    def _handle_admin_entry(self, event, user_id: str):
        """จัดการการเข้าสู่โหมด Admin"""
        self.admin_state[user_id] = {"mode": "main_menu"}
        
        quick_replies = QuickReply(items=[
            QuickReplyItem(action=MessageAction(label="➕ เพิ่มสินค้า", text="➕ เพิ่มสินค้า")),
            QuickReplyItem(action=MessageAction(label="✏️ แก้ไขสินค้า", text="✏️ แก้ไขสินค้า")),
            QuickReplyItem(action=MessageAction(label="❌ ลบสินค้า", text="❌ ลบสินค้า")),
            QuickReplyItem(action=MessageAction(label="📋 ดูสินค้าทั้งหมด", text="📋 ดูสินค้าทั้งหมด")),
            QuickReplyItem(action=MessageAction(label="📊 สถิติ", text="📊 สถิติ")),
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
        """แสดงหมวดหมู่สินค้าด้วย Smart Category Grouping และ Quick Reply buttons"""
        try:
            # ดึงหมวดหมู่พร้อมสถิติความนิยม
            categories_with_stats = self.db.get_categories_with_stats()
            price_range = self.db.get_price_range()
            
            if not categories_with_stats:
                # Fallback หากไม่มีข้อมูล
                categories = ["อิเล็กทรอนิกส์", "แฟชั่น", "ความงาม", "สุขภาพ", "บ้านและสวน", "กีฬา", "หนังสือ", "เด็กและของเล่น", "อาหาร", "สัตว์เลี้ยง"]
                categories_with_stats = [{'name': cat, 'product_count': 0, 'popularity_score': 0} for cat in categories]
            
            # จัดกลุ่มหมวดหมู่ตามความนิยม
            hot_categories = []  # คะแนน >= 50
            popular_categories = []  # คะแนน 20-49
            normal_categories = []  # คะแนน < 20
            
            for cat in categories_with_stats:
                if cat['popularity_score'] >= 50:
                    hot_categories.append(cat)
                elif cat['popularity_score'] >= 20:
                    popular_categories.append(cat)
                else:
                    normal_categories.append(cat)
            
            # สร้าง Quick Reply buttons แบบ Smart grouping
            quick_reply_items = []
            
            # หมวดหมู่ฮิต (ใส่ emoji พิเศษ)
            for cat in hot_categories[:4]:  # จำกัด 4 หมวดหมู่ฮิต
                emoji = "🔥" if cat['popularity_score'] >= 80 else "⭐"
                quick_reply_items.append(
                    QuickReplyItem(action=MessageAction(
                        label=f"{emoji} {cat['name']}", 
                        text=f"หมวด {cat['name']}"
                    ))
                )
            
            # หมวดหมู่ยอดนิยม
            for cat in popular_categories[:4]:  # จำกัด 4 หมวดหมู่
                quick_reply_items.append(
                    QuickReplyItem(action=MessageAction(
                        label=f"📂 {cat['name']}", 
                        text=f"หมวด {cat['name']}"
                    ))
                )
            
            # หมวดหมู่ปกติ (เติมเต็มให้ครบ)
            remaining_slots = 10 - len(quick_reply_items)
            for cat in normal_categories[:remaining_slots]:
                quick_reply_items.append(
                    QuickReplyItem(action=MessageAction(
                        label=f"📁 {cat['name']}", 
                        text=f"หมวด {cat['name']}"
                    ))
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