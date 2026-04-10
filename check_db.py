import psycopg2
conn = psycopg2.connect(dbname='taskflow', user='postgres', password='praveenraja2402', host='localhost', port='5433')

cur = conn.cursor()
cur.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema LIKE 'tenant%' OR table_schema = 'public';")
for row in cur.fetchall():
    print(row)
