import sqlite3, os
db_path = os.path.expanduser('~/.jobcli/jobcli.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("DELETE FROM config WHERE key='apply_checkpoint'")
conn.commit()
print("Checkpoint deleted from config table!")
