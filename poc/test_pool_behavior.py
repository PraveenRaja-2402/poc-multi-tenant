import asyncio
import httpx
import sys

async def run_pool_test():
    base_url = "http://localhost:8000"
    tenants = ["tenant_poc_a", "tenant_poc_b"]
    
    async with httpx.AsyncClient(base_url=base_url) as client:
        print("Starting Test 4: Connection Pool Behavior")
        print("Objective: Verify zero search_path leakage with pool_size=2")
        
        tasks = []
        for i in range(100):
            tenant = tenants[i % 2]
            tasks.append(client.get("/debug/search-path", headers={"X-Tenant-Slug": tenant}))
        
        results = await asyncio.gather(*tasks)
        
        passed = 0
        failed = 0
        
        for i, r in enumerate(results):
            expected_tenant = tenants[i % 2]
            if r.status_code != 200:
                print(f"Request {i} failed with status {r.status_code}")
                failed += 1
                continue
                
            data = r.json()
            actual_path = data["search_path"]
            
            # The search_path we set is "{tenant}, public"
            if expected_tenant in actual_path:
                passed += 1
            else:
                print(f"Leak detected in request {i}! Expected {expected_tenant}, got {actual_path}")
                failed += 1
        
        print("-" * 30)
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        
        if failed == 0:
            print("\nSUCCESS: No connection pool leakage detected!")
        else:
            print("\nFAILURE: Data leakage detected!")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_pool_test())
