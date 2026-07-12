import httpx

BASE = "https://boleta-saas-production.up.railway.app"

# Test super-login
r = httpx.post(f"{BASE}/api/auth/super-login", json={
    "email": "admin@sistema.com",
    "password": "123456",
}, timeout=15)
print(f"super-login: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    token = data.get("access_token", "")
    print(f"  Token: {token[:50]}...")
    print(f"  Type: {data.get('token_type')}")
    print(f"  Role: {data.get('role')}")
else:
    print(f"  Error: {r.json()}")

# Test CORS preflight
headers = {
    "Origin": "https://boleta-saas.vercel.app",
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type",
}
r = httpx.options(f"{BASE}/api/auth/super-login", headers=headers, timeout=15)
print(f"\nCORS preflight: {r.status_code}")
print(f"  Allow-Origin: {r.headers.get('access-control-allow-origin')}")
print(f"  Allow-Methods: {r.headers.get('access-control-allow-methods')}")

# Test actual CORS request
r = httpx.post(
    f"{BASE}/api/auth/super-login",
    json={"email": "admin@sistema.com", "password": "123456"},
    headers={"Origin": "https://boleta-saas.vercel.app"},
    timeout=15,
)
print(f"\nCORS actual: {r.status_code}")
print(f"  Allow-Origin: {r.headers.get('access-control-allow-origin')}")
