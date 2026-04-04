"""
Check all users in database
"""
import sqlite3

# Connect to database
conn = sqlite3.connect('kuraz.db')
cursor = conn.cursor()

# Get all users
cursor.execute('''
    SELECT id, full_name, email, total_bookings, total_spent_etb, loyalty_points
    FROM users
    ORDER BY id
''')

users = cursor.fetchall()
print(f"\n📊 Total Users in Database: {len(users)}\n")

for user in users:
    print(f"ID: {user[0]}")
    print(f"   Name: {user[1]}")
    print(f"   Email: {user[2]}")
    print(f"   Bookings: {user[3]}")
    print(f"   Spent: ETB {user[4]}")
    print(f"   Points: {user[5]}")
    print()

conn.close()
