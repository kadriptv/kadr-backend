import sqlite3
from app.db import _db_path

CODE = "C18C-B86E-9242"
NEW_LIMIT = 10

path = _db_path()
print("DB:", path)

conn = sqlite3.connect(path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT id, code, device_limit FROM users WHERE code=?", (CODE,))
row = cur.fetchone()
if not row:
    raise SystemExit("User with this code not found in users table")

print("BEFORE:", dict(row))

cur.execute("UPDATE users SET device_limit=? WHERE code=?", (NEW_LIMIT, CODE))
conn.commit()

cur.execute("SELECT id, code, device_limit FROM users WHERE code=?", (CODE,))
row2 = cur.fetchone()
print("AFTER:", dict(row2))

conn.close()
print("OK")
