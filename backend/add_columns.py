import sqlite3
conn = sqlite3.connect('hcp_crm.db')
c = conn.cursor()
c.execute("ALTER TABLE interactions ADD COLUMN attendees JSON")
c.execute("ALTER TABLE interactions ADD COLUMN materials_shared JSON")
c.execute("ALTER TABLE interactions ADD COLUMN outcomes TEXT")
conn.commit()
print("Columns added successfully")
conn.close()