import sqlite3, os
db_path = os.path.expanduser('~/.jobcli/jobcli.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("UPDATE jobs SET status = 'PENDING' WHERE url LIKE '%ashbyhq.com%'")
conn.commit()
c.execute("SELECT COUNT(*) FROM jobs WHERE url LIKE '%ashbyhq.com%' AND status = 'PENDING'")
print(f'Total pending Ashby jobs now: {c.fetchone()[0]}')
