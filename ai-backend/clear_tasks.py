from database import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("DELETE FROM tasks")
cursor.execute("DELETE FROM sqlite_sequence WHERE name='tasks'")

conn.commit()
conn.close()

print("Tasks deleted and IDs reset.")