import asyncio
import httpx
import pytest

@pytest.mark.asyncio
async def test_concurrent_tenant_isolation():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        tasks = []
        for i in range(50):
            tenant = "tenant_poc_a" if i % 2 == 0 else "tenant_poc_b"
            tasks.append(client.get("/tasks", headers={"X-Tenant-Slug": tenant}))
        
        results = await asyncio.gather(*tasks)
        
        for i, r in enumerate(results):
            # Check successful response
            assert r.status_code == 200, f"Request failed with {r.status_code}: {r.text}"
            
            expected_tenant = "tenant_poc_a" if i % 2 == 0 else "tenant_poc_b"
            data = r.json()
            
            # Ensure we got tasks back
            assert len(data) > 0, f"No tasks returned for {expected_tenant}"
            
            # Check all tasks belong to the expected tenant (and thus the correct schema)
            assert all(t["tenant"] == expected_tenant for t in data), f"Cross-contamination detected in request {i}"
