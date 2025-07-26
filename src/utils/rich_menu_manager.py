"""
📱 Rich Menu Manager สำหรับ LINE Bot Affiliate
🎯 จัดการ Rich Menu ที่ทันสมัยและมีประโยชน์
"""

import json
import requests
from typing import Dict, List, Optional
from ..config import config

class RichMenuManager:
    """คลาสสำหรับจัดการ Rich Menu ที่ทันสมัย"""
    
    def __init__(self):
        self.channel_access_token = config.LINE_CHANNEL_ACCESS_TOKEN
        self.headers = {
            'Authorization': f'Bearer {self.channel_access_token}',
            'Content-Type': 'application/json'
        }
        self.base_url = 'https://api.line.me/v2/bot'
    
    def create_main_rich_menu(self) -> Dict:
        """สร้าง Rich Menu หลักที่ทันสมัยและมีประโยชน์"""
        rich_menu_data = {
            "size": {
                "width": 2500,
                "height": 1686
            },
            "selected": True,
            "name": "Affiliate Shopping Assistant",
            "chatBarText": "เมนูช้อปปิ้ง",
            "areas": [
                # ปุ่มค้นหาสินค้า (ซ้ายบน)
                {
                    "bounds": {
                        "x": 0,
                        "y": 0,
                        "width": 833,
                        "height": 843
                    },
                    "action": {
                        "type": "message",
                        "text": "ค้นหาสินค้า"
                    }
                },
                # ปุ่มหมวดหมู่ (กลางบน)
                {
                    "bounds": {
                        "x": 833,
                        "y": 0,
                        "width": 834,
                        "height": 843
                    },
                    "action": {
                        "type": "message",
                        "text": "หมวดหมู่"
                    }
                },
                # ปุ่มขายดี (ขวาบน)
                {
                    "bounds": {
                        "x": 1667,
                        "y": 0,
                        "width": 833,
                        "height": 843
                    },
                    "action": {
                        "type": "message",
                        "text": "ขายดี"
                    }
                },
                # ปุ่มโปรโมชั่น (ซ้ายล่าง)
                {
                    "bounds": {
                        "x": 0,
                        "y": 843,
                        "width": 833,
                        "height": 843
                    },
                    "action": {
                        "type": "message",
                        "text": "โปรโมชั่น"
                    }
                },
                # ปุ่มสถิติ (กลางล่าง)
                {
                    "bounds": {
                        "x": 833,
                        "y": 843,
                        "width": 834,
                        "height": 843
                    },
                    "action": {
                        "type": "message",
                        "text": "สถิติ"
                    }
                },
                # ปุ่มช่วยเหลือ (ขวาล่าง)
                {
                    "bounds": {
                        "x": 1667,
                        "y": 843,
                        "width": 833,
                        "height": 843
                    },
                    "action": {
                        "type": "message",
                        "text": "ช่วยเหลือ"
                    }
                }
            ]
        }
        
        return rich_menu_data
    
    def create_admin_rich_menu(self) -> Dict:
        """สร้าง Rich Menu สำหรับ Admin"""
        rich_menu_data = {
            "size": {
                "width": 2500,
                "height": 1686
            },
            "selected": False,
            "name": "Admin Control Panel",
            "chatBarText": "จัดการระบบ",
            "areas": [
                # Dashboard (ซ้ายบน)
                {
                    "bounds": {
                        "x": 0,
                        "y": 0,
                        "width": 833,
                        "height": 843
                    },
                    "action": {
                        "type": "message",
                        "text": "Dashboard"
                    }
                },
                # เพิ่มสินค้า (กลางบน)
                {
                    "bounds": {
                        "x": 833,
                        "y": 0,
                        "width": 834,
                        "height": 843
                    },
                    "action": {
                        "type": "message",
                        "text": "admin"
                    }
                },
                # สถิติหมวดหมู่ (ขวาบน)
                {
                    "bounds": {
                        "x": 1667,
                        "y": 0,
                        "width": 833,
                        "height": 843
                    },
                    "action": {
                        "type": "message",
                        "text": "สถิติหมวดหมู่"
                    }
                },
                # สินค้าขายดี (ซ้ายล่าง)
                {
                    "bounds": {
                        "x": 0,
                        "y": 843,
                        "width": 833,
                        "height": 843
                    },
                    "action": {
                        "type": "message",
                        "text": "top-products sold_count 10"
                    }
                },
                # หมวดหมู่ (กลางล่าง)
                {
                    "bounds": {
                        "x": 833,
                        "y": 843,
                        "width": 834,
                        "height": 843
                    },
                    "action": {
                        "type": "message",
                        "text": "หมวดหมู่"
                    }
                },
                # กลับเมนูหลัก (ขวาล่าง)
                {
                    "bounds": {
                        "x": 1667,
                        "y": 843,
                        "width": 833,
                        "height": 843
                    },
                    "action": {
                        "type": "message",
                        "text": "หน้าหลัก"
                    }
                }
            ]
        }
        
        return rich_menu_data
    
    def upload_rich_menu(self, rich_menu_data: Dict) -> Optional[str]:
        """อัปโหลด Rich Menu ไปยัง LINE"""
        try:
            response = requests.post(
                f'{self.base_url}/richmenu',
                headers=self.headers,
                data=json.dumps(rich_menu_data)
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('richMenuId')
            else:
                print(f"Error creating rich menu: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Exception creating rich menu: {e}")
            return None
    
    def upload_rich_menu_image(self, rich_menu_id: str, image_path: str) -> bool:
        """อัปโหลดรูปภาพสำหรับ Rich Menu"""
        try:
            headers = {
                'Authorization': f'Bearer {self.channel_access_token}',
                'Content-Type': 'image/png'
            }
            
            with open(image_path, 'rb') as image_file:
                response = requests.post(
                    f'{self.base_url}/richmenu/{rich_menu_id}/content',
                    headers=headers,
                    data=image_file.read()
                )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Exception uploading rich menu image: {e}")
            return False
    
    def set_default_rich_menu(self, rich_menu_id: str) -> bool:
        """ตั้งค่า Rich Menu เป็นค่าเริ่มต้น"""
        try:
            response = requests.post(
                f'{self.base_url}/user/all/richmenu/{rich_menu_id}',
                headers=self.headers
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Exception setting default rich menu: {e}")
            return False
    
    def set_user_rich_menu(self, user_id: str, rich_menu_id: str) -> bool:
        """ตั้งค่า Rich Menu สำหรับผู้ใช้เฉพาะ"""
        try:
            response = requests.post(
                f'{self.base_url}/user/{user_id}/richmenu/{rich_menu_id}',
                headers=self.headers
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Exception setting user rich menu: {e}")
            return False
    
    def get_rich_menu_list(self) -> List[Dict]:
        """ดึงรายการ Rich Menu ทั้งหมด"""
        try:
            response = requests.get(
                f'{self.base_url}/richmenu/list',
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json().get('richmenus', [])
            else:
                return []
                
        except Exception as e:
            print(f"Exception getting rich menu list: {e}")
            return []
    
    def delete_rich_menu(self, rich_menu_id: str) -> bool:
        """ลบ Rich Menu"""
        try:
            response = requests.delete(
                f'{self.base_url}/richmenu/{rich_menu_id}',
                headers=self.headers
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Exception deleting rich menu: {e}")
            return False
    
    def setup_rich_menus(self) -> Dict[str, str]:
        """ตั้งค่า Rich Menu ทั้งหมด"""
        results = {}
        
        try:
            # ลบ Rich Menu เก่าทั้งหมด
            old_menus = self.get_rich_menu_list()
            for menu in old_menus:
                self.delete_rich_menu(menu['richMenuId'])
                print(f"Deleted old rich menu: {menu['name']}")
            
            # สร้าง Rich Menu หลัก
            main_menu_data = self.create_main_rich_menu()
            main_menu_id = self.upload_rich_menu(main_menu_data)
            
            if main_menu_id:
                results['main_menu_id'] = main_menu_id
                print(f"Created main rich menu: {main_menu_id}")
                
                # ตั้งเป็น default
                if self.set_default_rich_menu(main_menu_id):
                    print("Set main rich menu as default")
            
            # สร้าง Rich Menu สำหรับ Admin
            admin_menu_data = self.create_admin_rich_menu()
            admin_menu_id = self.upload_rich_menu(admin_menu_data)
            
            if admin_menu_id:
                results['admin_menu_id'] = admin_menu_id
                print(f"Created admin rich menu: {admin_menu_id}")
                
                # ตั้งค่าสำหรับ Admin user
                if config.ADMIN_USER_ID:
                    if self.set_user_rich_menu(config.ADMIN_USER_ID, admin_menu_id):
                        print("Set admin rich menu for admin user")
            
            return results
            
        except Exception as e:
            print(f"Exception setting up rich menus: {e}")
            return {}

# สร้าง instance สำหรับใช้งาน
rich_menu_manager = RichMenuManager()