"""
AI-Enhanced Search สำหรับ Smart Service System
ปรับปรุงการค้นหาด้วยเทคนิค AI
"""

import re
from typing import List, Dict, Tuple
from difflib import SequenceMatcher
from .logger import system_logger, performance_monitor

class AISearchEngine:
    """คลาสสำหรับการค้นหาแบบ AI"""
    
    def __init__(self):
        # คำพ้องความหมายสำหรับการแพทย์ไทย
        self.synonyms = {
            'เลือด': ['blood', 'cbc', 'เม็ดเลือด', 'ตรวจเลือด'],
            'น้ำตาล': ['glucose', 'sugar', 'เบาหวาน', 'ดัชนี'],
            'ปัสสาวะ': ['urine', 'น้ำปัสสาวะ', 'ปัสสาวะ', 'urinalysis'],
            'ไขมัน': ['cholesterol', 'lipid', 'คอเลสเตอรอล'],
            'ฟัน': ['dental', 'ขูด', 'หินปูน', 'ทันตกรรม'],
            'กรด': ['acid', 'uric', 'ยูริก'],
            'โปรตีน': ['protein', 'albumin', 'อัลบูมิน'],
            'ตรวจ': ['test', 'examination', 'check', 'lab'],
            'ค่า': ['rate', 'cost', 'price', 'fee', 'บาท']
        }
        
        # คำย่อและรูปแบบต่างๆ
        self.abbreviations = {
            'cbc': ['complete blood count', 'ตรวจความสมบูรณ์ของเม็ดเลือด'],
            'hba1c': ['glycated hemoglobin', 'น้ำตาลสะสม', 'เฮโมโกลบิน'],
            'fbs': ['fasting blood sugar', 'น้ำตาลในเลือด'],
            'ua': ['uric acid', 'กรดยูริก'],
        }
        
        # รูปแบบรหัสต่างๆ
        self.code_patterns = {
            'medical_code': r'\d{5}',  # รหัส 5 หลัก เช่น 31001
            'cpt_code': r'[A-Z]?\d{4,5}',  # รหัส CPT
            'icd_code': r'[A-Z]\d{2}\.?\d?'  # รหัส ICD-10
        }
    
    def enhanced_search(self, query: str, items: List[Dict], limit: int = 10) -> List[Tuple[float, str, Dict]]:
        """การค้นหาแบบ AI ที่ปรับปรุง"""
        performance_monitor.start_timer("ai_enhanced_search")
        
        query_processed = self._preprocess_query(query)
        results = []
        
        for item in items:
            if isinstance(item, tuple):
                key, data = item
            else:
                key = item.get('key', '')
                data = item
            
            score = self._calculate_relevance_score(query_processed, key, data)
            if score > 0:
                results.append((score, key, data))
        
        # เรียงตามคะแนนจากมากไปน้อย
        results.sort(key=lambda x: x[0], reverse=True)
        
        performance_monitor.end_timer("ai_enhanced_search")
        system_logger.debug(f"AI search for '{query}' found {len(results)} results")
        
        return results[:limit]
    
    def _preprocess_query(self, query: str) -> Dict:
        """ประมวลผลคำค้นหาเบื้องต้น"""
        query_lower = query.lower().strip()
        
        # ขยายคำค้นหาด้วย synonyms
        expanded_terms = [query_lower]
        
        for thai_word, synonyms in self.synonyms.items():
            if thai_word in query_lower:
                expanded_terms.extend(synonyms)
        
        # ตรวจสอบคำย่อ
        if query_lower in self.abbreviations:
            expanded_terms.extend(self.abbreviations[query_lower])
        
        # แยกคำด้วยช่องว่าง
        words = query_lower.split()
        
        return {
            'original': query_lower,
            'expanded_terms': expanded_terms,
            'words': words,
            'has_numbers': bool(re.search(r'\d', query_lower))
        }
    
    def _calculate_relevance_score(self, query_info: Dict, key: str, data: Dict) -> float:
        """คำนวณคะแนนความเกี่ยวข้อง"""
        score = 0.0
        query_original = query_info['original']
        expanded_terms = query_info['expanded_terms']
        
        # 1. Exact match ใน key (คะแนนสูงสุด)
        if query_original == key.lower():
            score += 100
        elif query_original in key.lower():
            score += 80
        
        # 2. Fuzzy match ใน key
        key_similarity = SequenceMatcher(None, query_original, key.lower()).ratio()
        score += key_similarity * 60
        
        # 3. ค้นหาใน name_th
        name_th = data.get('name_th', '').lower()
        if query_original in name_th:
            score += 70
            
        name_th_similarity = SequenceMatcher(None, query_original, name_th).ratio()
        score += name_th_similarity * 50
        
        # 4. ค้นหาใน name_en  
        name_en = data.get('name_en', '').lower()
        if query_original in name_en:
            score += 60
            
        name_en_similarity = SequenceMatcher(None, query_original, name_en).ratio()
        score += name_en_similarity * 40
        
        # 5. ค้นหาใน expanded terms
        for term in expanded_terms[1:]:  # ข้าม original term
            if term in key.lower():
                score += 50
            if term in name_th:
                score += 45
            if term in name_en:
                score += 40
        
        # 6. ค้นหาในรหัสต่างๆ
        codes_to_check = ['cgd_code', 'cpt', 'icd10']
        for code_field in codes_to_check:
            code_value = data.get(code_field, '').lower()
            if query_original in code_value:
                score += 30
        
        # 7. ค้นหาในหมายเหตุ
        notes = data.get('notes', '').lower()
        if query_original in notes:
            score += 20
        
        # 8. Pattern matching สำหรับรหัส
        if query_info['has_numbers']:
            for pattern_name, pattern in self.code_patterns.items():
                if re.match(pattern, query_original):
                    score += 25
        
        # 9. Word-level matching
        query_words = query_info['words']
        if len(query_words) > 1:
            word_matches = 0
            for word in query_words:
                if (word in key.lower() or 
                    word in name_th or 
                    word in name_en):
                    word_matches += 1
            
            word_ratio = word_matches / len(query_words)
            score += word_ratio * 30
        
        return score
    
    def suggest_alternatives(self, query: str, items: List[Dict], limit: int = 5) -> List[str]:
        """แนะนำคำค้นหาทางเลือก"""
        suggestions = set()
        query_lower = query.lower()
        
        # หาคำที่คล้ายกันจาก synonyms
        for thai_word, synonyms in self.synonyms.items():
            if thai_word in query_lower:
                suggestions.update(synonyms[:2])  # เอาแค่ 2 คำแรก
        
        # หาคำที่คล้ายกันจากข้อมูล
        for item in items[:20]:  # ตรวจแค่ 20 รายการแรก
            if isinstance(item, tuple):
                key, data = item
            else:
                key = item.get('key', '')
                data = item
            
            # คำใน name_th ที่คล้ายกัน
            name_words = data.get('name_th', '').split()
            for word in name_words:
                if len(word) > 2 and SequenceMatcher(None, query_lower, word.lower()).ratio() > 0.6:
                    suggestions.add(word)
        
        return list(suggestions)[:limit]
    
    def get_search_insights(self, query: str, results: List) -> Dict:
        """วิเคราะห์ผลการค้นหา"""
        return {
            'query_length': len(query),
            'has_thai': bool(re.search(r'[ก-๙]', query)),
            'has_english': bool(re.search(r'[a-zA-Z]', query)),
            'has_numbers': bool(re.search(r'\d', query)),
            'results_count': len(results),
            'top_score': results[0][0] if results else 0,
            'avg_score': sum(r[0] for r in results) / len(results) if results else 0
        }

# สร้าง instance สำหรับใช้งาน
ai_search = AISearchEngine()