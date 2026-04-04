from fastapi import FastAPI, Request
import requests

app = FastAPI() # Yeh hai entrypoint jo Vercel dhoond raha hai

BASE_URL = "https://100067.connect.garena.com"
APP_ID = "100067"

@app.get("/")
def home():
    return {"status": "Sameer API is Live"}

# STEP 1: OTP Request
@app.get("/api/request")
async def request_otp(token: str, email: str, request: Request):
    headers = {
        "User-Agent": "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "app_id": APP_ID, "access_token": token, "email": email,
        "locale": "en_BD", "region": "BD"
    }
    r = requests.post(f"{BASE_URL}/game/account_security/bind:send_otp", data=payload, headers=headers)
    return r.json()

# STEP 2: Confirm Bind
@app.get("/api/confirm")
async def confirm_bind(token: str, email: str, otp: str, request: Request):
    headers = {
        "User-Agent": "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    # Get Verifier Token
    v_res = requests.post(f"{BASE_URL}/game/account_security/bind:verify_otp", 
                          data={"app_id": APP_ID, "access_token": token, "email": email, "otp": otp}, headers=headers).json()
    v_token = v_res.get("verifier_token")

    if not v_token:
        return {"error": "OTP Invalid", "res": v_res}

    # Final Bind (New Bind API)
    final_payload = {
        "app_id": APP_ID, "access_token": token, "verifier_token": v_token, "email": email
    }
    r = requests.post(f"{BASE_URL}/game/account_security/bind:create_bind_request", data=final_payload, headers=headers)
    return r.json()
