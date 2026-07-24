import sqlite3, os
db_path = os.path.expanduser('~/.jobcli/jobcli.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT id, url, status FROM jobs")
for row in c.fetchall():
    print(row)
