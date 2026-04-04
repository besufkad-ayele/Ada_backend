import sqlite3

conn = sqlite3.connect('kuraz.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables in database:", tables)

if 'users' in tables:
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    print("\nUsers table columns:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
else:
    print("\nWARNING: users table does not exist!")

conn.close()
