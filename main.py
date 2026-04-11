from fastapi import FastAPI, Header, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from typing import AsyncGenerator
import urllib.parse
from pydantic import BaseModel

# --- NEW: Langchain imports for Test 2 ---
from langchain_community.vectorstores import PGVector
from langchain_core.documents import Document
from langchain_community.embeddings import FakeEmbeddings

DATABASE_URL = "postgresql+asyncpg://postgres:praveenraja2402@localhost:5433/taskflow"
# Langchain's PGVector works best with synchronous psycopg2 connections
SYNC_DATABASE_URL = "postgresql://postgres:praveenraja2402@localhost:5433/taskflow"

engine = create_async_engine(DATABASE_URL, pool_size=2, max_overflow=0, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# TEST 1: Basic SQLAlchemy Tenant Isolation (Your Original Code)
# ---------------------------------------------------------
async def get_tenant_session(x_tenant_slug: str = Header(...)) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            # SET LOCAL sets the search_path only for the current transaction.
            await session.execute(text(f"SET LOCAL search_path TO {x_tenant_slug}, public;"))
            yield session
        finally:
            # Reset search_path to public to prevent pool leakage
            await session.execute(text("RESET search_path;"))

@app.get("/tasks")
async def get_tasks(
    x_tenant_slug: str = Header(...),
    session: AsyncSession = Depends(get_tenant_session)
):
    result = await session.execute(text("SELECT * FROM tasks;"))
    rows = result.fetchall()

    return [
        {
            "id": row.id,
            "name": row.name,
            "tenant": x_tenant_slug
        }
        for row in rows
    ]

@app.get("/debug/search-path")
async def get_search_path(
    session: AsyncSession = Depends(get_tenant_session)
):
    # This query directly checks what Postgres thinks the current search_path is
    result = await session.execute(text("SHOW search_path;"))
    search_path = result.scalar()
    return {"search_path": search_path}


# ---------------------------------------------------------
# TEST 2: LangChain PGVector Tenant Isolation (New Additions)
# ---------------------------------------------------------
class IngestData(BaseModel):
    text: str

def get_tenant_connection_string(tenant: str) -> str:
    # URL-encode the search_path option so LangChain uses it immediately on connection
    search_path_val = f"{tenant},public"
    encoded_option = urllib.parse.quote(f"-c search_path={search_path_val}")
    # The URL will look like: postgresql://...?options=-c%20search_path%3Dtenant_a%2Cpublic
    return f"{SYNC_DATABASE_URL}?options={encoded_option}"

@app.post("/vector/ingest")
async def ingest_vector(
    data: IngestData, 
    x_tenant_slug: str = Header(...)
):
    try:
        conn_string = get_tenant_connection_string(x_tenant_slug)
        embeddings = FakeEmbeddings(size=1536)
        
        # Langchain PGVector automatically creates tables in the tenant's schema!
        store = PGVector(
            connection_string=conn_string,
            embedding_function=embeddings,
            collection_name="tenant_knowledge_base",
        )
        
        doc = Document(page_content=data.text, metadata={"source": "api"})
        store.add_documents([doc])
        
        return {"status": "success", "message": f"Added '{data.text}' safely to schema '{x_tenant_slug}'"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vector/search")
async def search_vector(
    query: str, 
    x_tenant_slug: str = Header(...)
):
    try:
        conn_string = get_tenant_connection_string(x_tenant_slug)
        embeddings = FakeEmbeddings(size=1536)
        
        store = PGVector(
            connection_string=conn_string,
            embedding_function=embeddings,
            collection_name="tenant_knowledge_base",
        )
        
        # Search the database and get the top 2 matches
        results = store.similarity_search(query, k=2)
        
        return {
            "tenant": x_tenant_slug,
            "results": [doc.page_content for doc in results]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)