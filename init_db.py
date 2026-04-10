import psycopg2

def init_db():
    try:
        conn = psycopg2.connect(
            dbname="taskflow",
            user="postgres",
            password="praveenraja2402",
            host="localhost",
            port="5433"
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Create schema and table for tenant_poc_a
        cur.execute("CREATE SCHEMA IF NOT EXISTS tenant_poc_a;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tenant_poc_a.tasks (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL
            );
        """)
        
        # Insert demo data if empty
        cur.execute("SELECT COUNT(*) FROM tenant_poc_a.tasks;")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO tenant_poc_a.tasks (name) VALUES ('Setup database'), ('Configure multi-tenancy');")
        print("Initialized schema 'tenant_poc_a' with dummy tasks.")

        # Create schema and table for tenant_poc_b (for testing switching)
        cur.execute("CREATE SCHEMA IF NOT EXISTS tenant_poc_b;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tenant_poc_b.tasks (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL
            );
        """)
        
        # Insert demo data if empty
        cur.execute("SELECT COUNT(*) FROM tenant_poc_b.tasks;")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO tenant_poc_b.tasks (name) VALUES ('Learn FastAPI'), ('Write blog post');")
        print("Initialized schema 'tenant_poc_b' with dummy tasks.")

        # Create global users table in public schema
        cur.execute("CREATE TABLE IF NOT EXISTS public.users (id SERIAL PRIMARY KEY, username VARCHAR(255) UNIQUE);")
        cur.execute("SELECT COUNT(*) FROM public.users;")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO public.users (username) VALUES ('admin'), ('global_user');")
        print("Initialized global 'users' table in public schema.")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error initializing DB: {e}")

if __name__ == "__main__":
    init_db()
