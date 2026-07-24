import sqlite3, os
db_path = os.path.expanduser('~/.jobcli/jobcli.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(c.fetchall())
c.execute("DELETE FROM apply_checkpoint")
conn.commit()
print("Checkpoint deleted!")
