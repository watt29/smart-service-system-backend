"""
Affiliate Product Review Bot - Main Application
ระบบ LINE Bot สำหรับรีวิวสินค้าและ Affiliate Marketing
"""

from flask import Flask, request, abort, render_template, jsonify
from linebot.exceptions import InvalidSignatureError

# Import modules ใหม่ที่เราสร้าง
from src.config import config
from src.utils.supabase_database import SupabaseDatabase
from src.handlers.affiliate_handler import affiliate_handler
from src.utils.ai_search import ai_search
from src.utils.review_generator import review_generator
import logging

# ตั้งค่า logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# ตั้งค่า Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

# สร้าง database instance
db = SupabaseDatabase()

def create_app():
    """สร้างและตั้งค่า Flask application"""
    logger.info("เริ่มต้น Affiliate Product Review Bot...")
    
    # ตรวจสอบการตั้งค่า
    config_valid = config.validate_config()
    if not config_valid:
        logger.warning("การตั้งค่าไม่ครบถ้วน - ระบบจะทำงานในโหมดจำกัด")
    
    # แสดงสถิติฐานข้อมูล
    stats = db.get_stats()
    db_type = config.get_database_name()
    logger.info(f"ฐานข้อมูล ({db_type}): {stats.get('total_products', 0)} สินค้า, ราคาเฉลี่ย {stats.get('average_price', 0):,.2f} บาท")
    
    return app

# ===== Flask Routes =====

@app.route('/')
def home():
    """หน้าแรกของเว็บไซต์"""
    return jsonify({
        "message": "🛍️ Affiliate Product Review Bot",
        "description": "LINE Bot สำหรับรีวิวสินค้าและ Affiliate Marketing",
        "endpoints": {
            "/health": "ตรวจสอบสถานะระบบ",
            "/callback": "LINE Bot Webhook",
            "/api/products": "จัดการสินค้า",
            "/api/search": "ค้นหาสินค้า",
            "/api/stats": "สถิติระบบ",
            "/api/review": "สร้างรีวิว"
        }
    })

@app.route('/health')
def health_check():
    """ตรวจสอบสถานะระบบ"""
    stats = db.get_stats()
    return jsonify({
        "status": "healthy",
        "products_count": stats.get('total_products', 0),
        "database_type": config.get_database_name(),
        "database_connected": db.connected if hasattr(db, 'connected') else True,
        "line_bot_active": config.LINE_CHANNEL_ACCESS_TOKEN is not None,
        "ai_search_enabled": config.USE_AI_SEARCH,
        "supabase_enabled": config.USE_SUPABASE
    })

@app.route('/ping')
def ping():
    """Simple ping endpoint เพื่อป้องกันเซิร์ฟเวอร์หยุด"""
    return "pong", 200

@app.route('/api/search', methods=['GET'])
def search_products_api():
    """API สำหรับค้นหาสินค้า"""
    try:
        query = request.args.get('query', '').strip()
        limit = int(request.args.get('limit', config.MAX_RESULTS_PER_SEARCH))
        use_ai = request.args.get('ai', 'false').lower() == 'true'
        
        logger.info(f"Product search API: '{query}' (limit={limit}, ai={use_ai})")
        
        if not query:
            return jsonify({"error": "กรุณาระบุคำค้นหา"}), 400
        
        # ค้นหาสินค้า
        products = db.search_products(query, limit)
        
        # ใช้ AI search หากเปิดใช้งาน
        if use_ai and products:
            products = ai_search.enhanced_product_search(query, products, limit)
        
        if products:
            logger.info(f"Search successful: found {len(products)} products for '{query}'")
            return jsonify({
                "success": True,
                "query": query,
                "count": len(products),
                "products": products
            })
        else:
            logger.info(f"Search not found: '{query}'")
            suggestions = ["อิเล็กทรอนิกส์", "แฟชั่น", "ความงาม", "สุขภาพ"]
            return jsonify({
                "success": False,
                "message": f"ไม่พบสินค้า '{query}'",
                "suggestions": suggestions
            })
            
    except Exception as e:
        logger.error(f"Search API error: {e}")
        return jsonify({"error": "เกิดข้อผิดพลาดในการค้นหา"}), 500

@app.route("/callback", methods=['POST'])
def line_callback():
    """Webhook สำหรับรับข้อความจาก LINE - Affiliate Bot"""
    try:
        signature = request.headers.get('X-Line-Signature', '')
        body = request.get_data(as_text=True)
        
        # ลด logging ใน production เพื่อความเร็ว
        if config.DEBUG:
            logger.debug(f"LINE webhook received: signature={signature[:10]}...")
        
        # ประมวลผล webhook - ใช้ affiliate handler
        affiliate_handler.handler.handle(body, signature)
        
        if config.DEBUG:
            logger.info("LINE webhook processed successfully")
        
        return 'OK'
        
    except InvalidSignatureError:
        if config.DEBUG:
            logger.error("Invalid LINE signature")
        abort(400)
        
    except Exception as e:
        logger.error(f"LINE webhook error: {str(e)}")
        abort(500)

@app.route('/api/products', methods=['GET', 'POST', 'PUT', 'DELETE'])
def products_api():
    """API สำหรับจัดการสินค้า"""
    try:
        if request.method == 'GET':
            # ดึงสินค้าทั้งหมดหรือตามเงื่อนไข
            category = request.args.get('category')
            limit = int(request.args.get('limit', 50))
            
            if category:
                products = db.get_products_by_category(category)
            else:
                products = db.get_all_products(limit)
            
            return jsonify({
                "success": True,
                "count": len(products),
                "products": products
            })
        
        elif request.method == 'POST':
            # เพิ่มสินค้าใหม่
            data = request.get_json()
            if not data:
                return jsonify({"error": "ไม่พบข้อมูลสินค้า"}), 400
            
            result = db.add_product(data)
            if result:
                logger.info(f"Product added: {data.get('product_name')}")
                return jsonify({
                    "success": True,
                    "message": "เพิ่มสินค้าสำเร็จ",
                    "product": result
                })
            else:
                return jsonify({"error": "ไม่สามารถเพิ่มสินค้าได้"}), 500
        
        elif request.method == 'PUT':
            # อัปเดตสินค้า
            product_code = request.args.get('code')
            data = request.get_json()
            
            if not product_code or not data:
                return jsonify({"error": "ไม่พบรหัสสินค้าหรือข้อมูล"}), 400
            
            success = db.update_product(product_code, data)
            if success:
                return jsonify({
                    "success": True,
                    "message": "อัปเดตสินค้าสำเร็จ"
                })
            else:
                return jsonify({"error": "ไม่สามารถอัปเดตสินค้าได้"}), 500
        
        elif request.method == 'DELETE':
            # ลบสินค้า
            product_code = request.args.get('code')
            if not product_code:
                return jsonify({"error": "ไม่พบรหัสสินค้า"}), 400
            
            success = db.delete_product(product_code)
            if success:
                return jsonify({
                    "success": True,
                    "message": "ลบสินค้าสำเร็จ"
                })
            else:
                return jsonify({"error": "ไม่สามารถลบสินค้าได้"}), 500
                
    except Exception as e:
        logger.error(f"Products API error: {e}")
        return jsonify({"error": "เกิดข้อผิดพลาดในการจัดการสินค้า"}), 500

@app.route('/api/stats')
def stats_api():
    """API สำหรับดูสถิติระบบ"""
    try:
        stats = db.get_stats()
        popular_searches = db.get_popular_searches(10)
        
        result = {
            "system": {
                "database_type": config.get_database_name(),
                "debug_mode": config.DEBUG,
                "line_bot_active": config.LINE_CHANNEL_ACCESS_TOKEN is not None,
                "ai_search_enabled": config.USE_AI_SEARCH,
                "supabase_enabled": config.USE_SUPABASE
            },
            "database": stats,
            "popular_searches": popular_searches
        }
        
        logger.info("Stats API accessed")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Stats API error: {e}")
        return jsonify({"error": "เกิดข้อผิดพลาดในการดึงสถิติ"}), 500

@app.route('/api/review', methods=['POST'])
def generate_review_api():
    """API สำหรับสร้างรีวิวสินค้า"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "ไม่พบข้อมูลสินค้า"}), 400
        
        product_code = data.get('product_code')
        style = data.get('style', 'medium')  # short, medium, long
        use_ai = data.get('ai', False)
        count = int(data.get('count', 1))
        
        # ดึงข้อมูลสินค้า
        if product_code:
            product = db.get_product_by_code(product_code)
            if not product:
                return jsonify({"error": "ไม่พบสินค้า"}), 404
        else:
            product = data  # ใช้ข้อมูลที่ส่งมา
        
        # สร้างรีวิว
        if count > 1:
            reviews = review_generator.generate_multiple_reviews(product, count)
            review_stats = review_generator.get_review_stats(reviews)
        else:
            review = review_generator.generate_review(product, style, use_ai)
            reviews = [review]
            review_stats = review_generator.get_review_stats(reviews)
        
        logger.info(f"Generated {len(reviews)} review(s) for {product.get('product_name', 'product')}")
        
        return jsonify({
            "success": True,
            "product": {
                "name": product.get('product_name'),
                "code": product.get('product_code'),
                "price": product.get('price')
            },
            "reviews": reviews,
            "stats": review_stats
        })
        
    except Exception as e:
        logger.error(f"Review API error: {e}")
        return jsonify({"error": "เกิดข้อผิดพลาดในการสร้างรีวิว"}), 500

# ===== Error Handlers =====

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "ไม่พบ endpoint ที่ระบุ"}), 404

@app.errorhandler(405)
def method_not_allowed_error(error):
    return jsonify({"error": "Method ไม่ถูกต้อง"}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "เกิดข้อผิดพลาดภายในระบบ"}), 500

# ===== Application Startup =====

if __name__ == '__main__':
    # สร้างแอปพลิเคชัน
    app = create_app()
    
    # รันเซิร์ฟเวอร์
    logger.info(f"เริ่มต้นเซิร์ฟเวอร์ที่ {config.HOST}:{config.PORT}")
    logger.info(f"โหมด DEBUG: {config.DEBUG}")
    logger.info("🛍️ Affiliate Product Review Bot พร้อมใช้งาน!")
    
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )