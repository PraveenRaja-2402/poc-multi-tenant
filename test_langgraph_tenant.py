import asyncio
import sys
import selectors
import psycopg
import uuid
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.base import CheckpointMetadata

# Database configuration
DB_BASE_URL = "postgresql://postgres:praveenraja2402@localhost:5432/taskflow"

async def verify_tables_conn(conn, schema_name):
    """Verify that LangGraph tables exist in the specified schema."""
    async with conn.cursor() as cur:
        await cur.execute(f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = '{schema_name}' 
            AND table_name IN ('checkpoints', 'checkpoint_writes', 'checkpoint_blobs', 'checkpoint_migrations');
        """)
        tables = await cur.fetchall()
        return [t[0] for t in tables]

async def run_test():
    print("--- Starting Test 3: LangGraph PostgresSaver isolation ---")
    
    # URLs with search_path set via options
    url_a = f"{DB_BASE_URL}?options=-csearch_path%3Dtenant_poc_a"
    url_b = f"{DB_BASE_URL}?options=-csearch_path%3Dtenant_poc_b"
    
    config_a = {"configurable": {"thread_id": "thread-1", "checkpoint_ns": ""}}
    checkpoint_data = {
        "v": 1,
        "id": str(uuid.uuid4()),
        "ts": "2024-04-15T12:00:00Z",
        "channel_values": {"my_key": "my_value"},
        "channel_versions": {"my_key": 1},
        "versions_seen": {},
        "pending_sends": []
    }
    metadata = {"source": "test"}

    # --- Phase 1: Tenant A Setup and Save ---
    print("\n[Phase 1] Testing Tenant A...")
    async with await psycopg.AsyncConnection.connect(url_a, autocommit=True) as conn_a:
        saver_a = AsyncPostgresSaver(conn_a)
        
        # Step 3: Call setup()
        print("Calling setup() for Tenant A...")
        await saver_a.setup()
        
        # Verify tables
        tables_a = await verify_tables_conn(conn_a, 'tenant_poc_a')
        print(f"Tables created in tenant_poc_a: {tables_a}")
        if not tables_a:
            print("FAILED: No tables found in tenant_poc_a")
            return

        # Step 4: Save a checkpoint
        print("Saving checkpoint in Tenant A...")
        await saver_a.aput(config_a, checkpoint_data, metadata, {})
        
        # Verify it can be loaded
        cp_a = await saver_a.aget(config_a)
        if cp_a:
            print("Successfully saved and loaded checkpoint from Tenant A.")
        else:
            print("FAILED: Could not load checkpoint from Tenant A after saving.")
            return

    # --- Phase 2: Tenant B Setup and Isolation Check ---
    print("\n[Phase 2] Testing Tenant B (Isolation Check)...")
    async with await psycopg.AsyncConnection.connect(url_b, autocommit=True) as conn_b:
        saver_b = AsyncPostgresSaver(conn_b)
        
        # Step 5: Call setup() for B
        print("Calling setup() for Tenant B...")
        await saver_b.setup()
        
        # Verify tables in B
        tables_b = await verify_tables_conn(conn_b, 'tenant_poc_b')
        print(f"Tables created in tenant_poc_b: {tables_b}")
        
        # Step 6: Load checkpoint (should be empty/None)
        print("Attempting to load Tenant A's checkpoint from Tenant B...")
        cp_b = await saver_b.aget(config_a)
        if cp_b is None:
            print("SUCCESS: Checkpoint from Tenant A is NOT visible in Tenant B.")
        else:
            print("FAILED: Checkpoint from Tenant A WAS visible in Tenant B!")

    # --- Phase 3: Idempotency Check ---
    print("\n[Phase 3] Idempotency Check...")
    async with await psycopg.AsyncConnection.connect(url_a, autocommit=True) as conn_a:
        saver_a = AsyncPostgresSaver(conn_a)
        print("Calling setup() again for Tenant A (should not fail)...")
        try:
            await saver_a.setup()
            print("SUCCESS: setup() is idempotent.")
        except Exception as e:
            print(f"FAILED: setup() error on second call: {e}")

    print("\n--- Test 3 Completed ---")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_test())
