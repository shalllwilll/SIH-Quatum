import requests
import time

print("Seeding scenario...")
r1 = requests.post("http://localhost:8000/demo/seed-scenario", json={"preset": "Balanced", "parcels_count": 56})
print(r1.status_code, r1.json())

print("Running routing session...")
r2 = requests.post("http://localhost:8000/routing-sessions/run", json={"preset": "Balanced"})
print(r2.status_code)
session_id = r2.json()["session_id"]
print("Session ID:", session_id)

print("Assigning session...")
r3 = requests.post(f"http://localhost:8000/routing-sessions/{session_id}/assign")
print(r3.status_code, r3.json())
