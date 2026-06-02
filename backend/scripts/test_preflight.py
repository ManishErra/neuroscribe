from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

app = FastAPI()

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dummy Auth Dependency
def get_current_user():
    print("Dependency get_current_user executed!")
    raise HTTPException(status_code=401, detail="Unauthorized")

# Guarded Router
router = APIRouter(
    prefix="/protected",
    dependencies=[Depends(get_current_user)]
)

@router.get("/")
def read_data():
    return {"data": "secure"}

app.include_router(router)
client = TestClient(app)

def run_preflight_test():
    print("\n--- Running FastAPI CORS Preflight Test ---")
    
    # 1. Test normal protected route (No headers)
    print("\n1. Request GET /protected/ without token:")
    res = client.get("/protected/")
    print(f"   Status: {res.status_code} | Details: {res.json()}")
    assert res.status_code == 401
    
    # 2. Test preflight OPTIONS request
    print("\n2. CORS Preflight: Request OPTIONS /protected/ with preflight headers:")
    preflight_headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization"
    }
    res = client.options("/protected/", headers=preflight_headers)
    print(f"   Status: {res.status_code}")
    print(f"   Response Headers: {dict(res.headers)}")
    assert res.status_code == 200
    assert "access-control-allow-origin" in res.headers
    print("   PASS: CORS preflight bypasses dependency check successfully!")

if __name__ == "__main__":
    run_preflight_test()
