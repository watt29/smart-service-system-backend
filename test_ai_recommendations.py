"""
🧪 Test AI Recommendations System
ทดสอบระบบแนะนำสินค้าด้วย AI
"""

from src.utils.ai_recommender import ai_recommender

def test_ai_recommendations():
    """ทดสอบระบบ AI Recommendations"""
    print("Testing AI Recommendations System...")
    
    # ทดสอบการสกัดความสนใจจากข้อความ
    print("\n1. Testing Interest Extraction...")
    test_messages = [
        "หามือถือ iPhone ใหม่",
        "อยากได้เสื้อผ้าแฟชั่น",
        "ครีมบำรุงผิวดี ๆ",
        "อุปกรณ์กีฬาออกกำลังกาย",
        "laptop gaming สเปคดี"
    ]
    
    for message in test_messages:
        interests = ai_recommender.extract_interests_from_text(message)
        print(f"Message: '{message}' -> Interests: {interests}")
    
    # ทดสอบการอัปเดตความสนใจของผู้ใช้
    print("\n2. Testing User Interest Updates...")
    test_user_id = "test_user_123"
    
    # จำลองการโต้ตอบของผู้ใช้
    interactions = [
        ("มือถือ Samsung", []),
        ("iPhone 15 ราคา", []),
        ("เสื้อเชิ้ตผู้ชาย", []),
        ("รองเท้าวิ่ง Nike", []),
        ("laptop gaming", [])
    ]
    
    for message, search_results in interactions:
        ai_recommender.update_user_interests(test_user_id, message, search_results)
        print(f"Updated interests for: '{message}'")
    
    # ดูความสนใจของผู้ใช้
    print("\n3. Testing User Interest Analysis...")
    top_interests = ai_recommender.get_user_top_interests(test_user_id)
    print(f"Top interests: {top_interests}")
    
    # ทดสอบการแนะนำตามความสนใจ
    print("\n4. Testing Interest-based Recommendations...")
    try:
        interest_recs = ai_recommender.recommend_by_interest(test_user_id, limit=3)
        print(f"Interest-based recommendations: {len(interest_recs)} products")
        for i, product in enumerate(interest_recs, 1):
            name = product.get('product_name', 'N/A')
            reason = product.get('recommendation_reason', 'N/A')
            print(f"  {i}. {name} - {reason}")
    except Exception as e:
        print(f"Interest recommendations error: {e}")
    
    # ทดสอบการแนะนำสินค้าที่กำลังมาแรง
    print("\n5. Testing Trending Recommendations...")
    try:
        trending_recs = ai_recommender.recommend_trending_products(limit=3)
        print(f"Trending recommendations: {len(trending_recs)} products")
        for i, product in enumerate(trending_recs, 1):
            name = product.get('product_name', 'N/A')
            score = product.get('recommendation_score', 0)
            print(f"  {i}. {name} - Score: {score:.2f}")
    except Exception as e:
        print(f"Trending recommendations error: {e}")
    
    # ทดสอบการแนะนำแบบปรับตัว
    print("\n6. Testing Personalized Recommendations...")
    try:
        personalized = ai_recommender.get_personalized_recommendations(
            test_user_id, 
            context="ต้องการซื้อของใหม่", 
            limit=5
        )
        
        print(f"Personalized recommendations:")
        print(f"  Personal: {len(personalized['personal'])} products")
        print(f"  Trending: {len(personalized['trending'])} products")
        print(f"  Categories: {len(personalized['categories'])} products")
        print(f"  Total Score: {personalized['total_score']}")
        
    except Exception as e:
        print(f"Personalized recommendations error: {e}")
    
    # ทดสอบการสร้างโปรไฟล์ผู้ใช้
    print("\n7. Testing User Profile Summary...")
    try:
        profile = ai_recommender.get_user_profile_summary(test_user_id)
        print(f"User Profile:")
        print(f"  User ID: {profile.get('user_id')}")
        print(f"  Top Interests: {profile.get('top_interests', [])}")
        print(f"  Interaction Count: {profile.get('interaction_count', 0)}")
        print(f"  Last Interaction: {profile.get('last_interaction', 'None')}")
        
        preferences = profile.get('preferences', {})
        if preferences:
            print(f"  Preferences: {preferences}")
            
    except Exception as e:
        print(f"User profile error: {e}")
    
    # ทดสอบการแนะนำสินค้าที่คล้ายกัน
    print("\n8. Testing Similar Product Recommendations...")
    try:
        # ใช้รหัสสินค้าจำลอง
        similar_recs = ai_recommender.recommend_similar_products("TEST001", limit=3)
        print(f"Similar product recommendations: {len(similar_recs)} products")
        for i, product in enumerate(similar_recs, 1):
            name = product.get('product_name', 'N/A')
            reason = product.get('recommendation_reason', 'N/A')
            print(f"  {i}. {name} - {reason}")
    except Exception as e:
        print(f"Similar products error: {e}")
    
    print("\nAI Recommendations test completed!")

if __name__ == "__main__":
    test_ai_recommendations()