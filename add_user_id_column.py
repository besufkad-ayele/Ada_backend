"""
Add user_id column to bookings table
"""
import sqlite3

# Connect to database
conn = sqlite3.connect('kuraz.db')
cursor = conn.cursor()

try:
    # Add user_id column to bookings table
    cursor.execute('''
        ALTER TABLE bookings 
        ADD COLUMN user_id INTEGER
    ''')
    
    print("✅ Successfully added user_id column to bookings table")
    
    # Commit changes
    conn.commit()
    
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("⚠️  Column user_id already exists")
    else:
        print(f"❌ Error: {e}")
        
finally:
    conn.close()

print("✅ Migration complete!")
