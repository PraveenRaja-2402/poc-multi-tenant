# Multi-Tenant Vector Database POC

A professional Proof-of-Concept (POC) demonstrating multi-tenant isolation using **FastAPI**, **SQLAlchemy** (Asynchronous), and **LangChain with PGVector**.

This project implements **Schema-based Isolation** in PostgreSQL, ensuring that each tenant's data (both relational and vector) is physically separated and strictly isolated during runtime.

## 🚀 Key Features

- **Dynamic Schema Switching**: Uses PostgreSQL `search_path` to isolate tenants at the database level.
- **Async Relational Access**: FastAPI handles tenant-scoped requests using SQLAlchemy `AsyncSession`.
- **Vector Isolation**: Integrates LangChain's `PGVector` to store and search embeddings within tenant-specific schemas.
- **Automated Validation**: Includes concurrent testing to prove that data never leaks between tenants.
- **RESTful API**: Clean endpoints for task management and vector knowledge base ingestion/search.

## 🏗️ Architecture

The application uses a **Shared Database, Separate Schema** strategy:
1. **Public Schema**: Stores global data (e.g., users).
2. **Tenant Schemas** (`tenant_poc_a`, `tenant_poc_b`, etc.): Store tenant-specific tables and vector collections.
3. **Middleware/Dependencies**: Extract `x-tenant-slug` from headers to set the session's `search_path`.

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.14+)
- **ORM**: SQLAlchemy 2.0 (Async)
- **Vector DB**: PGVector (PostgreSQL extension)
- **Orchestration**: LangChain
- **Database**: PostgreSQL 16+

## 📥 Installation

### 1. Prerequisites
- Docker (for PostgreSQL with pgvector) or a local PostgreSQL instance.
- Python 3.10+

### 2. Setup Database
Ensure the `pgvector` extension is installed. You can run the following in your database:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 3. Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies (ensure you have psycopg2, asyncpg, fastapi, uvicorn, langchain)
pip install -r requirements.txt
```

### 4. Initialize Database
Run the initialization script to create tenant schemas and demo data:
```bash
python init_db.py
```

## 🚦 Usage

### Start the Server
```bash
python main.py
```
The server will be available at `http://127.0.0.1:8000`.

### API Endpoints

| Method | Endpoint | Description | Header Required |
| --- | --- | --- | --- |
| **GET** | `/tasks` | List tasks for the tenant | `x-tenant-slug` |
| **POST** | `/vector/ingest` | Add text to vector store | `x-tenant-slug` |
| **GET** | `/vector/search` | Search vector store | `x-tenant-slug` |

### Testing Isolation
You can run the provided test scripts to verify strict isolation:
```bash
# Run concurrent SQLAlchemy isolation test
pytest poc/test_sqlalchemy_schema.py

# Run PGVector isolation test
python poc/test_pgvector_schema.py
```

## 📜 Professional Implementation details
The core of the tenant isolation lies in the `get_tenant_session` dependency in `main.py`:
```python
async def get_tenant_session(x_tenant_slug: str = Header(...)):
    async with AsyncSessionLocal() as session:
        await session.execute(text(f"SET LOCAL search_path TO {x_tenant_slug}, public;"))
        yield session
```
This ensures every query executed during the request lifecycle is automatically scoped to the correct schema.
