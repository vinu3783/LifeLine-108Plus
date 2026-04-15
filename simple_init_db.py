"""
Simplified database initialization script.
"""

import sqlite3

# Create a connection to the SQLite database
conn = sqlite3.connect('emergency_response.db')
cursor = conn.cursor()

# Create ambulances table
cursor.execute('''
CREATE TABLE IF NOT EXISTS ambulances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ambulance_id TEXT UNIQUE NOT NULL,
    driver_name TEXT NOT NULL,
    driver_phone TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    is_available INTEGER DEFAULT 1,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Create emergency_calls table
cursor.execute('''
CREATE TABLE IF NOT EXISTS emergency_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caller_phone TEXT NOT NULL,
    call_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'initiated',
    location_link_id TEXT UNIQUE,
    latitude REAL,
    longitude REAL,
    address TEXT,
    assigned_ambulance_id INTEGER,
    assigned_time TIMESTAMP,
    location_shared_time TIMESTAMP,
    pickup_time TIMESTAMP,
    completion_time TIMESTAMP,
    FOREIGN KEY (assigned_ambulance_id) REFERENCES ambulances (id)
)
''')

# Add test ambulances
test_ambulances = [
    ("DVG-AMB-001", "Rajesh Kumar", "+919876543210", 14.4732, 75.9260),
    ("DVG-AMB-002", "Suresh Gowda", "+919876543211", 14.4510, 75.9190)
]

cursor.executemany(
    "INSERT OR IGNORE INTO ambulances (ambulance_id, driver_name, driver_phone, latitude, longitude) VALUES (?, ?, ?, ?, ?)",
    test_ambulances
)

# Commit changes and close connection
conn.commit()

# Count ambulances
cursor.execute("SELECT COUNT(*) FROM ambulances")
ambulance_count = cursor.fetchone()[0]

# Count emergency calls
cursor.execute("SELECT COUNT(*) FROM emergency_calls")
call_count = cursor.fetchone()[0]

print(f"\nDatabase initialized with:")
print(f"- {ambulance_count} ambulances")
print(f"- {call_count} emergency calls")

conn.close()