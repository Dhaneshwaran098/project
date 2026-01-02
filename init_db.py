import sqlite3
import os

# Create uploads folder if not exists
os.makedirs("uploads/permissions", exist_ok=True)

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# Create users table
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

# Create leave_requests table
cur.execute("""
CREATE TABLE IF NOT EXISTS leave_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT,
    reason TEXT,
    permission_file TEXT,
    attendance INTEGER,
    instructor_status TEXT DEFAULT 'Pending',
    hod_status TEXT DEFAULT 'Pending'
)
""")

# Insert demo users
cur.executemany("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", [
    ("student1", "1234", "student"),
    ("inst1", "1234", "instructor"),
    ("hod1", "1234", "hod")
])

conn.commit()
conn.close()

print("Database created and ready to use!")
