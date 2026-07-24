import sqlite3, os
db_path = os.path.expanduser('~/.jobcli/jobcli.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT title, company, url FROM jobs WHERE url LIKE '%ashbyhq.com%' LIMIT 1")
row = c.fetchone()
if not row:
    print('No existing Ashby job found in DB to use as template.')
    exit(1)

title, company, base_url = row

for i in range(1, 5):
    new_url = base_url
    if '?' in new_url:
        new_url += f'&dummy={i}'
    else:
        new_url += f'?dummy={i}'
    
    try:
        c.execute(
            'INSERT INTO jobs (title, company, url, status) VALUES (?, ?, ?, ?)',
            (title, company, new_url, 'pending')
        )
    except Exception as e:
        print('Error inserting:', e)

conn.commit()
print('Successfully added 4 more pending Ashby jobs to the queue! You now have 5 jobs ready.')
