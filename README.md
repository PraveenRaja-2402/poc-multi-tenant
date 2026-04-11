# 🌌 Multi-Tenant Vector Database POC

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=chainlink)](https://github.com/langchain-ai/langchain)

A state-of-the-art Proof-of-Concept (POC) demonstrating **Schema-based Multi-Tenant Isolation** using **FastAPI**, **SQLAlchemy Async**, and **LangChain with PGVector**.

---

## 💎 Key Features

-   **🛡️ Hard Isolation**: Physical separation of tenant data via PostgreSQL schemas (`SET LOCAL search_path`).
-   **⚡ Async Performance**: Full asynchronous database access using `SQLAlchemy 2.0` and `asyncpg`.
-   **🧠 Vector Knowledge Bases**: Isolated vector stores per tenant using `PGVector` and `FakeEmbeddings`.
-   **🔄 Dynamic Context Switching**: Middleware-driven tenant context extraction from `x-tenant-slug` headers.
-   **🧪 Robust Validation**: Automated concurrent tests to prove zero-data-leakage across tenants.

---

## 🏗️ Architecture Overview

The system utilizes a **Shared Instance, Separate Schema** strategy:

1.  **Public Schema**: Shared global configuration and user metadata.
2.  **Tenant Schemas**: Each tenant (e.g., `tenant_poc_a`) gets its own isolated table set and vector collections.
3.  **Connection Logic**:
    *   **Relational**: Transactions are scoped using `SET LOCAL search_path`.
    *   **Vector**: Connection strings are dynamically generated with the `?options=-c search_path=` parameter.

---

## 🛠️ Tech Stack

-   **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
-   **ORM**: [SQLAlchemy 2.0](https://docs.sqlalchemy.org/) (Async)
-   **Vector Storage**: [PGVector](https://github.com/pgvector/pgvector)
-   **Framework**: [LangChain](https://python.langchain.com/)
-   **Networking**: [Uvicorn](https://www.uvicorn.org/)

---

## 🚀 Quick Start

### 1. Prerequisites
- Docker (for PostgreSQL + pgvector)
- Python 3.10+

### 2. Environment Setup
```bash
# Create and activate venv
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Initialize the Database
This will create `tenant_poc_a` and `tenant_poc_b` schemas with initial data.
```bash
python init_db.py
```

### 4. Run the API
```bash
python main.py
```

---

## 📡 API Reference

| Method | Endpoint | Description | Header Requirement |
| :--- | :--- | :--- | :--- |
| `GET` | `/tasks` | List tasks for the active tenant | `x-tenant-slug` |
| `POST` | `/vector/ingest` | Add text to tenant's vector store | `x-tenant-slug` |
| `GET` | `/vector/search` | Search tenant's vector knowledge base | `x-tenant-slug` |

---

## 📜 Implementation Deep Dive

The heart of our isolation logic resides in the FastAPI Dependency:

```python
async def get_tenant_session(x_tenant_slug: str = Header(...)):
    async with AsyncSessionLocal() as session:
        # 🔒 Isolate the transaction to the specific tenant schema
        await session.execute(text(f"SET LOCAL search_path TO {x_tenant_slug}, public;"))
        yield session
```

For a detailed technical breakdown, see **[TECHNICAL_GUIDE.md](file:///C:/Users/user/.gemini/antigravity/brain/bb13deda-7b98-46ce-9907-e292bce49f33/technical_guide.md)**.
