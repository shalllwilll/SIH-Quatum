from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:
    response = client.post("/routing-sessions/compare", json={"seed": 42})
    print(response.status_code)
    print(response.json())
