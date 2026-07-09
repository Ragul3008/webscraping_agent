import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app

def test_root_endpoint():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"
    print("API root endpoint test passed.")

def test_register_and_login():
    client = TestClient(app)
    # 1. Register User
    reg_response = client.post("/api/v1/auth/register", json={
        "email": "testuser@aura.com",
        "password": "securepassword123"
    })
    if reg_response.status_code == 400:
        print("Test user already exists, proceeding to login...")
    else:
        assert reg_response.status_code == 200
        assert reg_response.json()["email"] == "testuser@aura.com"
        print("Registration test passed.")

    # 2. Login User
    login_response = client.post("/api/v1/auth/login", data={
        "username": "testuser@aura.com",
        "password": "securepassword123"
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    assert token is not None
    print("Login test passed.")

    # 3. Fetch User Profile
    me_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "testuser@aura.com"
    print("Fetch profile test passed.")

if __name__ == "__main__":
    test_root_endpoint()
    test_register_and_login()
    print("\nAll core backend endpoint tests completed successfully!")
