"""
🚀 Deploy Rich Menu to LINE Bot
สคริปต์สำหรับ deploy Rich Menu ไปยัง LINE Bot
"""

from src.utils.rich_menu_manager import rich_menu_manager

def deploy_rich_menus():
    """Deploy Rich Menus to LINE Bot"""
    print("Deploying Rich Menus to LINE Bot...")
    
    try:
        # Setup Rich Menus (create and upload)
        result = rich_menu_manager.setup_rich_menus()
        
        if result:
            print("Rich Menu deployment successful!")
            print(f"Main Rich Menu ID: {result.get('main_menu_id', 'N/A')}")
            print(f"Admin Rich Menu ID: {result.get('admin_menu_id', 'N/A')}")
            
            # List current Rich Menus
            print("\nCurrent Rich Menus:")
            menus = rich_menu_manager.get_rich_menu_list()
            for menu in menus:
                print(f"  - {menu['name']} (ID: {menu['richMenuId'][:10]}...)")
                
        else:
            print("Rich Menu deployment failed!")
            
    except Exception as e:
        print(f"Error during deployment: {e}")

if __name__ == "__main__":
    deploy_rich_menus()