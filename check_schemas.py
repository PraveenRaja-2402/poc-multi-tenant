import psycopg2
try:
    conn = psycopg2.connect(dbname='taskflow', user='postgres', password='praveenraja2402', host='localhost', port='5433')
    cur = conn.cursor()
    cur.execute("SELECT schema_name FROM information_schema.schemata;")
    print("Schemas:", [row[0] for row in cur.fetchall()])
    
    cur.execute("SELECT table_schema, table_name FROM information_schema.tables;")
    print("All Tables:", [f"{row[0]}.{row[1]}" for row in cur.fetchall() if row[0] not in ('pg_catalog', 'information_schema')])
except Exception as e:
    print("Error:", e)
