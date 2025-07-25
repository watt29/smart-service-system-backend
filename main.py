"""
Smart Service System - Main Application
ระบบช่วยเหลือข้าราชการไทยเรื่องสิทธิเบิกค่ารักษาพยาบาล
"""

from flask import Flask, request, abort, render_template, jsonify
from linebot.exceptions import InvalidSignatureError

# Import modules ใหม่ที่เราสร้าง
from src.config import config
from src.utils.db_adapter import db_adapter
from src.handlers.line_handler import line_handler
from src.utils.logger import system_logger, error_handler
from src.utils.ai_search import ai_search

# ตั้งค่า Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

def create_app():
    """สร้างและตั้งค่า Flask application"""
    system_logger.info("เริ่มต้น Smart Service System...")
    
    # ตรวจสอบการตั้งค่า
    config_valid = config.validate_config()
    if not config_valid:
        system_logger.warning("การตั้งค่าไม่ครบถ้วน - ระบบจะทำงานในโหมดจำกัด")
    
    # แสดงสถิติฐานข้อมูล
    summary = db_adapter.get_summary()
    db_type = "SQLite" if config.USE_SQLITE else "JSON"
    system_logger.info(f"ฐานข้อมูล ({db_type}): {summary['total_items']} รายการ, อัตราเฉลี่ย {summary['average_rate']:.2f} บาท")
    
    return app

# ===== Flask Routes =====

@app.route('/')
def home():
    """หน้าแรกของเว็บไซต์"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """ตรวจสอบสถานะระบบ"""
    return jsonify({
        "status": "healthy",
        "database_items": len(db_adapter.get_all_items()),
        "database_type": "SQLite" if config.USE_SQLITE else "JSON",
        "line_bot_active": config.LINE_CHANNEL_ACCESS_TOKEN is not None
    })

@app.route('/search', methods=['GET'])
def search_api():
    """API สำหรับค้นหาข้อมูล"""
    try:
        query = request.args.get('query', '').strip()
        system_logger.info(f"API search request: '{query}'")
        
        if not query:
            error_result = error_handler.handle_validation_error("query", "empty")
            return jsonify({"error": "กรุณาระบุคำค้นหา"}), 400
        
        # ค้นหาในฐานข้อมูล
        found_items = db_adapter.fuzzy_search(query)
        
        if found_items:
            key, item_data = found_items[0]
            result_html = format_web_result(item_data, query)
            system_logger.info(f"Search successful: found '{key}' for query '{query}'")
            return jsonify({"success": True, "result": result_html})
        else:
            # สร้างลิงก์สำหรับค้นหาในเว็บทางการ
            cgd_link = f"{config.CGD_BASE_URL}?method=search&service_name={query.replace(' ', '+')}"
            not_found_html = (
                f"❌ ไม่พบข้อมูล '{query}' ในระบบฐานความรู้ภายใน<br><br>"
                f"คุณสามารถค้นหาข้อมูลที่เป็นทางการและล่าสุดได้ที่:<br>"
                f"<a href='{cgd_link}' target='_blank'>คลิกเพื่อค้นหา '{query}' ใน mbdb.cgd.go.th</a>"
            )
            system_logger.info(f"Search not found: '{query}'")
            return jsonify({"success": False, "result": not_found_html})
            
    except Exception as e:
        error_result = error_handler.handle_api_error("/search", e)
        return jsonify(error_result), 500

@app.route("/callback", methods=['POST'])
def line_callback():
    """Webhook สำหรับรับข้อความจาก LINE - เน้นความเร็ว"""
    try:
        signature = request.headers.get('X-Line-Signature', '')
        body = request.get_data(as_text=True)
        
        # ลด logging ใน production เพื่อความเร็ว
        if config.DEBUG:
            system_logger.debug(f"LINE webhook received: signature={signature[:10]}...")
        
        # ประมวลผล webhook - ต้องเร็ว!
        line_handler.handler.handle(body, signature)
        
        if config.DEBUG:
            system_logger.info("LINE webhook processed successfully")
        
        return 'OK'
        
    except InvalidSignatureError:
        if config.DEBUG:
            system_logger.error("Invalid LINE signature")
        abort(400)
        
    except Exception as e:
        system_logger.error(f"LINE webhook error: {str(e)}")
        abort(500)

@app.route('/search/ai', methods=['GET'])
def ai_search_api():
    """API สำหรับค้นหาด้วย AI"""
    try:
        query = request.args.get('query', '').strip()
        system_logger.info(f"AI search request: '{query}'")
        
        if not query:
            return jsonify({"error": "กรุณาระบุคำค้นหา"}), 400
        
        # ดึงข้อมูลทั้งหมด
        all_items = db_adapter.get_all_items()
        items_list = [(k, v) for k, v in all_items.items()]
        
        # ค้นหาด้วย AI
        ai_results = ai_search.enhanced_search(query, items_list, limit=5)
        
        if ai_results:
            results = []
            for score, key, item_data in ai_results:
                result = {
                    "key": key,
                    "score": round(score, 2),
                    "data": format_web_result(item_data, query)
                }
                results.append(result)
            
            # วิเคราะห์ผลการค้นหา
            insights = ai_search.get_search_insights(query, ai_results)
            suggestions = ai_search.suggest_alternatives(query, items_list)
            
            system_logger.info(f"AI search successful: found {len(results)} results with top score {ai_results[0][0]:.2f}")
            
            return jsonify({
                "success": True,
                "results": results,
                "insights": insights,
                "suggestions": suggestions
            })
        else:
            suggestions = ai_search.suggest_alternatives(query, items_list)
            return jsonify({
                "success": False,
                "message": f"ไม่พบข้อมูล '{query}' ด้วย AI search",
                "suggestions": suggestions
            })
            
    except Exception as e:
        error_result = error_handler.handle_api_error("/search/ai", e)
        return jsonify(error_result), 500

@app.route('/stats')
def stats_api():
    """API สำหรับดูสถิติระบบ"""
    try:
        summary = db_adapter.get_summary()
        search_stats = db_adapter.get_search_stats(limit=10)
        
        stats = {
            "database": summary,
            "search": search_stats,
            "system": {
                "database_type": "SQLite" if config.USE_SQLITE else "JSON",
                "debug_mode": config.DEBUG,
                "line_bot_active": config.LINE_CHANNEL_ACCESS_TOKEN is not None
            }
        }
        
        system_logger.info("Stats API accessed")
        return jsonify(stats)
        
    except Exception as e:
        error_result = error_handler.handle_api_error("/stats", e)
        return jsonify(error_result), 500

# ===== Helper Functions =====

def format_web_result(item_data, query):
    """จัดรูปแบบผลลัพธ์สำหรับเว็บ"""
    cgd_link = f"{config.CGD_BASE_URL}?method=search&service_name={query.replace(' ', '+')}"
    
    return f"""
    <div class="card mb-3">
        <div class="card-body text-start">
            <h5 class="card-title">🔍 รายการ: {item_data['name_th']} ({item_data['name_en']})</h5>
            <p class="card-text">
                💵 อัตรา: <strong>{item_data['rate_baht']:.2f} บาท</strong><br>
                ✅ เบิกได้ตามสิทธิ: {', '.join(item_data['rights'])}<br>
                {f"📝 หมายเหตุ: {item_data['notes']}<br>" if item_data.get('notes') else ""}
            </p>
            <p class="card-text">
                ℹ️ รหัสมาตรฐาน:<br>
                - CPT: {item_data['cpt']}<br>
                - ICD-10: {item_data['icd10']}
            </p>
            <a href="{cgd_link}" target="_blank" class="btn btn-sm btn-outline-primary mt-2">
                🔗 ดูข้อมูลทางการใน mbdb.cgd.go.th
            </a>
        </div>
    </div>
    """

# ===== Application Startup =====

if __name__ == '__main__':
    # สร้างแอปพลิเคชัน
    app = create_app()
    
    # รันเซิร์ฟเวอร์
    system_logger.info(f"เริ่มต้นเซิร์ฟเวอร์ที่ {config.HOST}:{config.PORT}")
    system_logger.info(f"โหมด DEBUG: {config.DEBUG}")
    system_logger.info("Smart Service System พร้อมใช้งาน!")
    
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )