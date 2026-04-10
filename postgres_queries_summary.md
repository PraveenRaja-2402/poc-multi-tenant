# Complete Summary of PostgreSQL Queries

Here is a complete summary of all the PostgreSQL queries executed behind the scenes during our setup and application runtime:

## 1. Database Initialization Queries (`init_db.py`)
These are the queries that created the two separate tenant schemas, their respective tables, and populated them with dummy data.

**For Tenant A (`tenant_poc_a`):**
```sql
CREATE SCHEMA IF NOT EXISTS tenant_poc_a;

CREATE TABLE IF NOT EXISTS tenant_poc_a.tasks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

SELECT COUNT(*) FROM tenant_poc_a.tasks;

-- Only runs if the table is empty
INSERT INTO tenant_poc_a.tasks (name) 
VALUES ('Setup database'), ('Configure multi-tenancy');
```

**For Tenant B (`tenant_poc_b`):**
```sql
CREATE SCHEMA IF NOT EXISTS tenant_poc_b;

CREATE TABLE IF NOT EXISTS tenant_poc_b.tasks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

SELECT COUNT(*) FROM tenant_poc_b.tasks;

-- Only runs if the table is empty
INSERT INTO tenant_poc_b.tasks (name) 
VALUES ('Learn FastAPI'), ('Write blog post');
```

## 2. Live Request Execution Queries (`main.py`)
Whenever an HTTP request hits the FastAPI `/tasks` endpoint, SQLAlchemy executes these queries in Postgres to isolate and fetch the data. 

```sql
-- 1. SQLAlchemy implicitly starts a transaction
BEGIN;

-- 2. We dynamically bind the request to the specific tenant schema 
-- (The `LOCAL` keyword ensures this setting drops automatically once the query completes)
SET LOCAL search_path TO {tenant_slug}, public;

-- 3. We fetch data. Because we set the search_path above, Postgres inherently knows 
-- it should only grab tasks out of the specific tenant's schema!
SELECT * FROM tasks;

-- 4. SQLAlchemy implicitly closes out the transaction, clearing the environment
COMMIT;  -- (Or ROLLBACK if there was an exception)
```

## 3. Debugging / Checking Queries (`check_schemas.py`)
You also had these specific introspection queries to ensure the databases had properly formed:

```sql
-- To list out all available logical schemas
SELECT schema_name FROM information_schema.schemata;

-- To list all physical tables and which schemas they reside within
SELECT table_schema, table_name FROM information_schema.tables;
```
