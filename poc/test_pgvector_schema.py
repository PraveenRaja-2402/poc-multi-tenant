import pytest
from sqlalchemy import create_engine, text, event
from langchain_community.vectorstores import PGVector
from langchain_community.embeddings import FakeEmbeddings
import time

DATABASE_URL = "postgresql://postgres:praveenraja2402@localhost:5432/taskflow"


def create_tenant_engine(tenant: str):
    # We use a non-pooled engine to ensure the connection event fires reliably for our test isolation
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        # Ensure schema names are safely quoted if they contain dots or hyphen
        cursor.execute(f'SET search_path TO "{tenant}", public')
        cursor.close()
        
    return engine

def test_pgvector_tenant_isolation():
    embeddings = FakeEmbeddings(size=1536)
    collection_name = "test_kb"
    
    # 1. Setup/Cleanup: Ensure tables are gone from both schemas to test creation
    for tenant in ["tenant_poc_a", "tenant_poc_b"]:
        engine = create_tenant_engine(tenant)
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS langchain_pg_embedding CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS langchain_pg_collection CASCADE"))
            conn.commit()
    
    # 2. Add document to Tenant A
    engine_a = create_tenant_engine("tenant_poc_a")
    # We open a connection to pass to PGVector
    conn_a = engine_a.connect()
    try:
        db_info = conn_a.execute(text("SELECT current_database(), current_schema(), current_user")).fetchone()
        print(f"Tenant A Connection Info: {db_info}")
            
        store_a = PGVector(
            connection_string=DATABASE_URL,
            embedding_function=embeddings,
            collection_name=collection_name,
            connection=conn_a,
            use_jsonb=True
        )
        store_a.add_texts(["Document from tenant A"])
        
        # 3. Initialize Tenant B
        engine_b = create_tenant_engine("tenant_poc_b")
        conn_b = engine_b.connect()
        try:
            db_info_b = conn_b.execute(text("SELECT current_database(), current_schema(), current_user, show_search_path FROM (SELECT current_database(), current_schema(), current_user, current_setting('search_path') as show_search_path) as sub")).fetchone()
            print(f"Tenant B Connection Info: {db_info_b}")
            
            store_b = PGVector(
                connection_string=DATABASE_URL,
                embedding_function=embeddings,
                collection_name=collection_name,
                connection=conn_b,
                use_jsonb=True
            )
            store_b.add_texts(["Document from tenant B"])
            
            # 4. Search and Verify Isolation
            results_a = store_a.similarity_search("tenant A")
            results_b = store_b.similarity_search("tenant A")
            results_b_own = store_b.similarity_search("tenant B")
            
            print(f"Results A (Search 'A'): {len(results_a)}")
            print(f"Results B (Search 'A'): {len(results_b)}")
            print(f"Results B (Search 'B'): {len(results_b_own)}")
            
            print(f"Results A (Search 'A') content: {[d.page_content for d in results_a]}")
            print(f"Results B (Search 'A') content: {[d.page_content for d in results_b]}")
            
            assert len(results_a) == 1, "Tenant A should find its document"
            assert all("tenant A" in d.page_content for d in results_a), "A should only find A"
            assert all("tenant A" not in d.page_content for d in results_b), "B should NOT find A"
            assert len(results_b_own) == 1, "Tenant B should find its OWN document"
            
            # 5. Verify physical table existence in schemas
            with engine_a.connect() as check_conn:
                res = check_conn.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'tenant_poc_a' AND table_name = 'langchain_pg_embedding'"))
                assert res.scalar() == 1, "Tables should exist in tenant_poc_a"
                
            with engine_b.connect() as check_conn:
                res = check_conn.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'tenant_poc_b' AND table_name = 'langchain_pg_embedding'"))
                assert res.scalar() == 1, "Tables should exist in tenant_poc_b"
        finally:
            conn_b.close()
    finally:
        conn_a.close()

if __name__ == "__main__":
    try:
        test_pgvector_tenant_isolation()
        print("Test 2 Success: PGVector Tenant Isolation Verified!")
    except Exception as e:
        print(f"Test 2 Failed: {e}")
        import traceback
        traceback.print_exc()
