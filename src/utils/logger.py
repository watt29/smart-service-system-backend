"""
Logging System สำหรับ Smart Service System
จัดการ logging และ error tracking
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional
from ..config import config

class SystemLogger:
    """คลาสสำหรับจัดการ logging"""
    
    def __init__(self, name: str = "SmartService"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if config.DEBUG else logging.INFO)
        
        # ป้องกันการสร้าง handler ซ้ำ
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """ตั้งค่า logging handlers"""
        
        # สร้างโฟลเดอร์ logs ถ้าไม่มี
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # Format สำหรับ log messages
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console Handler - แสดงใน terminal
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File Handler - บันทึกในไฟล์
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(logs_dir, f'smart_service_{today}.log')
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Error Handler - ไฟล์แยกสำหรับ errors
        error_file = os.path.join(logs_dir, f'errors_{today}.log')
        error_handler = logging.FileHandler(error_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
    
    def info(self, message: str, extra_data: Optional[dict] = None):
        """Log ข้อมูลทั่วไป"""
        if extra_data:
            message = f"{message} | Data: {extra_data}"
        self.logger.info(message)
    
    def debug(self, message: str, extra_data: Optional[dict] = None):
        """Log ข้อมูล debug"""
        if extra_data:
            message = f"{message} | Data: {extra_data}"
        self.logger.debug(message)
    
    def warning(self, message: str, extra_data: Optional[dict] = None):
        """Log คำเตือน"""
        if extra_data:
            message = f"{message} | Data: {extra_data}"
        self.logger.warning(message)
    
    def error(self, message: str, exception: Optional[Exception] = None, extra_data: Optional[dict] = None):
        """Log ข้อผิดพลาด"""
        if extra_data:
            message = f"{message} | Data: {extra_data}"
        
        if exception:
            message = f"{message} | Exception: {str(exception)}"
            self.logger.error(message, exc_info=True)
        else:
            self.logger.error(message)
    
    def critical(self, message: str, exception: Optional[Exception] = None):
        """Log ข้อผิดพลาดร้ายแรง"""
        if exception:
            message = f"{message} | Exception: {str(exception)}"
            self.logger.critical(message, exc_info=True)
        else:
            self.logger.critical(message)

class ErrorHandler:
    """คลาสสำหรับจัดการข้อผิดพลาด"""
    
    def __init__(self, logger: SystemLogger):
        self.logger = logger
    
    def handle_database_error(self, operation: str, exception: Exception) -> dict:
        """จัดการข้อผิดพลาดของฐานข้อมูล"""
        error_msg = f"Database error during {operation}"
        self.logger.error(error_msg, exception)
        
        return {
            "success": False,
            "error": "เกิดข้อผิดพลาดในการเข้าถึงฐานข้อมูล",
            "operation": operation,
            "timestamp": datetime.now().isoformat()
        }
    
    def handle_line_error(self, operation: str, exception: Exception) -> dict:
        """จัดการข้อผิดพลาดของ LINE Bot"""
        error_msg = f"LINE Bot error during {operation}"
        self.logger.error(error_msg, exception)
        
        return {
            "success": False,
            "error": "เกิดข้อผิดพลาดในการส่งข้อความ LINE",
            "operation": operation,
            "timestamp": datetime.now().isoformat()
        }
    
    def handle_api_error(self, endpoint: str, exception: Exception) -> dict:
        """จัดการข้อผิดพลาดของ API"""
        error_msg = f"API error at {endpoint}"
        self.logger.error(error_msg, exception)
        
        return {
            "success": False,
            "error": "เกิดข้อผิดพลาดในการประมวลผล",
            "endpoint": endpoint,
            "timestamp": datetime.now().isoformat()
        }
    
    def handle_validation_error(self, field: str, value: str) -> dict:
        """จัดการข้อผิดพลาดการตรวจสอบข้อมูล"""
        error_msg = f"Validation error for field '{field}' with value '{value}'"
        self.logger.warning(error_msg)
        
        return {
            "success": False,
            "error": f"ข้อมูล '{field}' ไม่ถูกต้อง",
            "field": field,
            "timestamp": datetime.now().isoformat()
        }

# Performance Monitor
class PerformanceMonitor:
    """คลาสสำหรับติดตาม performance"""
    
    def __init__(self, logger: SystemLogger):
        self.logger = logger
        self.start_times = {}
    
    def start_timer(self, operation: str):
        """เริ่มจับเวลา operation"""
        self.start_times[operation] = datetime.now()
        self.logger.debug(f"Started timing: {operation}")
    
    def end_timer(self, operation: str) -> float:
        """จบการจับเวลาและ log ผลลัพธ์"""
        if operation not in self.start_times:
            self.logger.warning(f"No start time found for operation: {operation}")
            return 0.0
        
        start_time = self.start_times.pop(operation)
        duration = (datetime.now() - start_time).total_seconds()
        
        self.logger.info(f"Operation '{operation}' completed in {duration:.3f} seconds")
        
        # แจ้งเตือนถ้าใช้เวลานาน
        if duration > 5.0:
            self.logger.warning(f"Slow operation detected: {operation} took {duration:.3f} seconds")
        
        return duration

# สร้าง instances สำหรับใช้งาน
system_logger = SystemLogger()
error_handler = ErrorHandler(system_logger)
performance_monitor = PerformanceMonitor(system_logger)