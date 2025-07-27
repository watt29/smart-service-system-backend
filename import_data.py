"""
Script for importing CSV data to bypass RLS
Uses service role key instead of anon key
"""

import csv
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def import_csv_data():
    """Import data from CSV using service role"""
    
    # Use service role if available, otherwise anon key
    supabase_url = os.environ.get('SUPABASE_URL')
    service_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')  # service role key
    anon_key = os.environ.get('SUPABASE_KEY')  # anon key
    
    # Try service key first, fallback to anon key
    api_key = service_key if service_key else anon_key
    
    if not supabase_url or not api_key:
        print("ERROR: Missing SUPABASE_URL or API Key")
        return False
    
    try:
        # Create client
        supabase: Client = create_client(supabase_url, api_key)
        key_type = 'service role' if service_key else 'anon key'
        print(f"Connected to Supabase successfully (using {key_type})")
        
        # Read CSV data
        csv_file = 'import_products_fixed.csv'
        if not os.path.exists(csv_file):
            print(f"ERROR: File not found: {csv_file}")
            return False
        
        products_to_insert = []
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for index, row in enumerate(csv_reader, 1):
                try:
                    # Prepare data
                    product_code = f"CSV{index:03d}"
                    price = float(str(row.get('price', 0)).replace(',', ''))
                    rating = float(str(row.get('rating', 0)))
                    sold_count = int(str(row.get('sold_count', 0)).replace(',', ''))
                    commission_rate = 15.0
                    commission_amount = price * (commission_rate / 100)
                    
                    product_data = {
                        'product_code': product_code,
                        'product_name': str(row.get('product_name', '')).strip(),
                        'category': str(row.get('category', '')).strip(),
                        'price': price,
                        'description': str(row.get('description', '')).strip(),
                        'rating': rating,
                        'sold_count': sold_count,
                        'shop_name': str(row.get('shop_name', '')).strip() or 'Not specified',
                        'commission_rate': commission_rate,
                        'commission_amount': commission_amount,
                        'product_link': str(row.get('affiliate_link', '')).strip(),
                        'offer_link': str(row.get('affiliate_link', '')).strip(),
                        'image_url': ''
                    }
                    
                    products_to_insert.append(product_data)
                    
                except Exception as e:
                    print(f"ERROR in row {index}: {e}")
                    continue
        
        if not products_to_insert:
            print("ERROR: No data to import")
            return False
        
        print(f"Importing {len(products_to_insert)} items...")
        
        # Delete old data first (optional)
        print("Deleting old data...")
        try:
            supabase.table('products').delete().neq('product_code', '').execute()
            print("Old data deleted successfully")
        except Exception as e:
            print(f"Warning: Could not delete old data: {e}")
        
        # Import new data in batches
        batch_size = 10
        success_count = 0
        
        for i in range(0, len(products_to_insert), batch_size):
            batch = products_to_insert[i:i + batch_size]
            
            try:
                response = supabase.table('products').insert(batch).execute()
                if response.data:
                    success_count += len(response.data)
                    print(f"SUCCESS batch {i//batch_size + 1}: {len(response.data)} items")
                else:
                    print(f"FAILED batch {i//batch_size + 1}")
                    
            except Exception as e:
                print(f"ERROR batch {i//batch_size + 1}: {e}")
                continue
        
        print(f"\nImport completed!")
        print(f"SUCCESS: {success_count} items")
        print(f"FAILED: {len(products_to_insert) - success_count} items")
        
        # Verify data after import
        result = supabase.table('products').select('*', count='exact').execute()
        print(f"Total products in database: {result.count}")
        
        # Show available categories
        categories_result = supabase.table('products').select('category').execute()
        categories = set([item['category'] for item in categories_result.data if item['category']])
        print(f"Available categories: {len(categories)}")
        for cat in sorted(categories):
            print(f"  - {cat}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Starting CSV data import...")
    success = import_csv_data()
    
    if success:
        print("\nImport completed successfully! System ready to use")
    else:
        print("\nImport failed. Please check errors above")