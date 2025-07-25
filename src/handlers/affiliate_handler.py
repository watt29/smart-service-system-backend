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
            
            if text.lower() in ["สถิติ", "stats"]:
                self._show_stats(event)
                return
            
            if text.lower() in ["หมวดหมู่", "categories"]:
                self._show_categories(event)
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
    
    def _handle_product_search(self, event, query: str, user_id: str = None):
        """จัดการการค้นหาสินค้า"""
        try:
            print(f"[DEBUG] Searching for: '{query}'")
            products = self.db.search_products(query, config.MAX_RESULTS_PER_SEARCH)
            print(f"[DEBUG] Found {len(products)} products")
            
            if products:
                if len(products) == 1:
                    # แสดงสินค้าเดียวแบบข้อความธรรมดา
                    self._send_product_simple(event, products[0])
                else:
                    # แสดงรายการสินค้าหลายรายการ
                    self._send_products_list(event, products, query)
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
        """ส่งข้อความแสดงสินค้าแบบธรรมดา"""
        # ย่อชื่อสินค้าให้อ่านง่าย
        name = self._shorten_product_name(product['product_name'])
        price = product['price']
        sold_count = product.get('sold_count', 0)
        shop_name = product['shop_name']
        offer_link = product['offer_link']
        rating = product.get('rating', 0)
        
        # แปลงจำนวนขาย
        sold_display = self._format_sold_count(sold_count)
        
        # สร้างข้อความ
        message = f"🔸 {name}\n"
        message += f"💸 ราคาเพียง {price:,.0f} บาท!\n"
        
        if sold_count >= 1000:
            message += f"📦 ขายดีมากกว่า {sold_display} ชิ้น\n"
        elif sold_count > 0:
            message += f"📦 ขายแล้ว {sold_display} ชิ้น\n"
            
        if rating >= 4.0:
            stars = "⭐" * min(int(rating), 5)
            message += f"⭐ คะแนน {rating} {stars}\n"
            
        message += f"🏪 ร้าน {shop_name}\n"
        
        # สร้างลิงก์แบบมืออาชีพ
        short_link = self._create_professional_link_display(offer_link)
        message += f"🛒 {short_link}\n"
        message += f"👉 {offer_link}"
        
        self._reply_text(event, message)
    
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
        products_text = f"🔍 เจอสินค้าดีๆ เกี่ยวกับ '{query}' มาแชร์ให้:\n\n"
        
        for i, product in enumerate(products, 1):
            # ย่อชื่อสินค้า
            name = self._shorten_product_name(product['product_name'])
            price = product['price']
            sold_count = product.get('sold_count', 0)
            shop_name = product['shop_name']
            offer_link = product['offer_link']
            rating = product.get('rating', 0)
            
            # แปลงจำนวนขาย
            sold_display = self._format_sold_count(sold_count)
            
            products_text += f"🔸 {name}\n"
            products_text += f"💸 ราคาเพียง {price:,.0f} บาท!\n"
            
            if sold_count >= 1000:
                products_text += f"📦 ขายดีมากกว่า {sold_display} ชิ้น\n"
            elif sold_count > 0:
                products_text += f"📦 ขายแล้ว {sold_display} ชิ้น\n"
                
            if rating >= 4.0:
                stars = "⭐" * min(int(rating), 5)
                products_text += f"⭐ คะแนน {rating} {stars}\n"
                
            products_text += f"🏪 ร้าน {shop_name}\n"
            
            # สร้างลิงก์แบบมืออาชีพ - ซ่อน URL ที่ยาว
            short_link = self._create_professional_link_display(offer_link)
            products_text += f"🛒 {short_link}\n"
            products_text += f"👉 {offer_link}\n\n"
            products_text += "="*25 + "\n\n"
        
        products_text += "💡 เจอของดี copy ลิงก์ไปสั่งได้เลย!"
        
        self._reply_text(event, products_text)
    
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
        """แสดงหมวดหมู่สินค้า"""
        # ในอนาคตสามารถดึงจาก categories table
        categories = [
            "อิเล็กทรอนิกส์", "แฟชั่น", "ความงาม", "สุขภาพ",
            "บ้านและสวน", "กีฬา", "หนังสือ", "เด็กและของเล่น", 
            "อาหาร", "อื่นๆ"
        ]
        
        categories_text = "📂 หมวดหมู่สินค้า:\n\n" + "\n".join([f"• {cat}" for cat in categories])
        categories_text += "\n\n💡 พิมพ์ชื่อหมวดหมู่เพื่อค้นหาสินค้าในหมวดนั้น"
        
        self._reply_text(event, categories_text)
    
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