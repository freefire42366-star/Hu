from fastapi import FastAPI, Request
import requests

app = FastAPI()

# Garena Settings
BASE_URL = "https://100067.connect.garena.com"
APP_ID = "100067"

def get_msdk_headers(request: Request):
    # Asli Mobile Signature simulation
    ua = request.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {
        "User-Agent": ua,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip"
    }

@app.get("/")
def home():
    return {"status": "Sameer New-Bind Engine Live"}

# STEP 1: Request OTP for NEW email
@app.get("/api/request")
async def request_otp(token: str, email: str, request: Request):
    headers = get_msdk_headers(request)
    payload = {
        "app_id": APP_ID,
        "access_token": token,
        "email": email,
        "locale": "en_BD", # BD Server fixed
        "region": "BD"     # BD Server fixed
    }
    # Uthaya gaya: /game/account_security/bind:send_otp
    r = requests.post(f"{BASE_URL}/game/account_security/bind:send_otp", data=payload, headers=headers)
    return r.json()

# STEP 2: Confirm NEW Bind
@app.get("/api/confirm")
async def confirm_new_bind(token: str, email: str, otp: str, request: Request):
    headers = get_msdk_headers(request)
    
    # A. Verify OTP to get Verifier Token
    # Uthaya gaya: /game/account_security/bind:verify_otp
    v_payload = {"app_id": APP_ID, "access_token": token, "email": email, "otp": otp}
    v_res = requests.post(f"{BASE_URL}/game/account_security/bind:verify_otp", data=v_payload, headers=headers).json()
    v_token = v_res.get("verifier_token")

    if not v_token:
        return {"error": "Invalid OTP", "garena_msg": v_res}

    # B. Submit Final Bind Request
    # Uthaya gaya: /game/account_security/bind:create_bind_request
    # NOTE: Isme identity_token nahi dalte (Kyuki ye NEW bind hai)
    final_payload = {
        "app_id": APP_ID,
        "access_token": token,
        "verifier_token": v_token,
        "email": email
    }
    
    # Final Hit to Garena
    r = requests.post(f"{BASE_URL}/game/account_security/bind:create_bind_request", data=final_payload, headers=headers)
    return {
        "action": "NEW_BIND_SUCCESS",
        "garena_response": r.json()
    }                                              }url.py
