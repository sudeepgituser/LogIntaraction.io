import sqlite3, os
print("Working from:", os.getcwd())
print("Full DB path:", os.path.abspath('hcp_crm.db'))
print("File size:", os.path.getsize('hcp_crm.db'), "bytes")
conn = sqlite3.connect('hcp_crm.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", c.fetchall())
conn.close()