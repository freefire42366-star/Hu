from fastapi import FastAPI, Query
import requests

app = FastAPI()

# --- Configuration ---
# Jo JWT aapne di thi, wo yaha as a Bearer Token use hogi
API_KEY = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE4MDY4MTUxMTEsImlhdCI6MTc3NTI3OTExMSwicmF5IjoiYzAzMmE4NDY5ZmIxNjQ4NDBmYjRiZGZiMzRhZDVjOTgiLCJzdWIiOjM5Mzc2NzJ9.ht2w7toffecDHaxtKOsb8jRuzJgKGzFLeyzty1c6VQrTztD4mDbZkBOVrC4ZdEAoecHnhFffTYvrjq_ZwpNLRoNy9FihaDo1Ij3y3YMrszFhL83olx61STbA4EYKsqkdfgZ9wYMxyjK6WYNnML4cLDQHs-tHC1gah4NGoOhv6Sd_HdjS57qnVNZtT8aG6C_ioDTqvjjOYuWSs4ER3D4atxngp-nZpMrzBeVyDGOf6q_9K-DeVpkKwNRbZbEzCc6QVhvRMhuaZFXg0E7GT663iAae9S-X73c1KGDy5iwCq0xtYB32EZ8u8qUR6yiq4Ub5bAQOuAp1gtgJYx3oe6A7jg"

BASE_URL = "https://api.sms-service.com/v1" # Example Private API Base

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

@app.get("/api/get-number")
def buy_number(country: str, operator: str):
    # Nepal/India ke liye specific routing
    payload = {
        "country": country, 
        "operator": operator,
        "service": "garena" # Specifically for Free Fire/Garena
    }
    # Yeh aapke private provider se number mangega
    r = requests.post(f"{BASE_URL}/buy", json=payload, headers=HEADERS)
    return r.json()

@app.get("/api/get-otp")
def get_otp(order_id: str):
    # Live OTP check karne ke liye
    r = requests.get(f"{BASE_URL}/status/{order_id}", headers=HEADERS)
    return r.json()
