from database import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(tasks)")
for row in cursor.fetchall():
    print(row)

conn.close()