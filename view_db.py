import sqlite3

DB_FILE = 'knowledge_base.db'

def view_db_content():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items")
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    
    if rows:
        print("--- All Items in Database ---")
        for row in rows:
            item = dict(zip(columns, row))
            for key, value in item.items():
                print(f"{key}: {value}")
            print("-----------------------------")
    else:
        print("No items found in the database.")
    conn.close()

if __name__ == "__main__":
    view_db_content()