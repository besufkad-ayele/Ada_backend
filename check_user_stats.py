"""
Check user stats in database
"""
import sqlite3

# Connect to database
conn = sqlite3.connect('kuraz.db')
cursor = conn.cursor()

# Get user with id 3 (Egnuma Gelana)
cursor.execute('''
    SELECT id, full_name, email, total_bookings, total_spent_etb, loyalty_points
    FROM users
    WHERE id = 3
''')

user = cursor.fetchone()
if user:
    print(f"\n📊 User Stats for ID {user[0]}:")
    print(f"   Name: {user[1]}")
    print(f"   Email: {user[2]}")
    print(f"   Total Bookings: {user[3]}")
    print(f"   Total Spent: ETB {user[4]}")
    print(f"   Loyalty Points: {user[5]}")
else:
    print("❌ User not found")

# Get bookings for this user
cursor.execute('''
    SELECT booking_ref, total_revenue_etb, status, user_id
    FROM bookings
    WHERE user_id = 3
''')

bookings = cursor.fetchall()
print(f"\n📋 Bookings for User ID 3: {len(bookings)} found")
for booking in bookings:
    print(f"   - {booking[0]}: ETB {booking[1]} ({booking[2]})")

conn.close()
