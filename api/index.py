from fastapi import FastAPI, Query, Request
import requests
import hashlib

app = FastAPI()

# Garena Official Config
BASE_URL = "https://100067.connect.garena.com"
APP_ID = "100067"
DEFAULT_SEC_CODE = "123456"

def sha256_hash(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

def get_garena_headers(user_agent: str):
    return {
        "User-Agent": user_agent if "Garena" in user_agent else "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip",
        "Connection": "keep-alive"
    }

@app.get("/")
def check():
    return {"status": "Sameer API Final Version Ready", "region": "BD Optimized"}

# STEP 1: Send OTP
@app.get("/api/request")
def send_otp(token: str, email: str, request: Request):
    headers = get_garena_headers(request.headers.get("user-agent", ""))
    payload = {
        "app_id": APP_ID,
        "access_token": token,
        "email": email,
        "locale": "en_BD",
        "region": "BD"
    }
    r = requests.post(f"{BASE_URL}/game/account_security/bind:send_otp", data=payload, headers=headers)
    return r.json()

# STEP 2: The Logic (Automated Bind/Rebind)
@app.get("/api/confirm")
def confirm(token: str, email: str, otp: str, request: Request):
    headers = get_garena_headers(request.headers.get("user-agent", ""))
    
    # A. Check if account is already bound (Important for deciding endpoint)
    info = requests.get(f"{BASE_URL}/game/account_security/bind:get_bind_info", 
                        params={"app_id": APP_ID, "access_token": token}, headers=headers).json()
    is_rebind = True if info.get("email") else False

    # B. Get Verifier Token (Always needed)
    v_data = {"app_id": APP_ID, "access_token": token, "email": email, "otp": otp}
    v_res = requests.post(f"{BASE_URL}/game/account_security/bind:verify_otp", data=v_data, headers=headers).json()
    v_token = v_res.get("verifier_token")

    if not v_token:
        return {"status": "failed", "msg": "OTP Incorrect", "garena_res": v_res}

    # C. Execute based on account status
    if is_rebind:
        # Rebind logic (Requires Identity Token)
        id_data = {
            "app_id": APP_ID, "access_token": token, 
            "secondary_password": sha256_hash(DEFAULT_SEC_CODE)
        }
        id_res = requests.post(f"{BASE_URL}/game/account_security/bind:verify_identity", data=id_data, headers=headers).json()
        id_token = id_res.get("identity_token")
        
        if not id_token:
            return {"status": "failed", "msg": "Identity Token Failed (Check Sec Code)", "res": id_res}
            
        final_payload = {
            "app_id": APP_ID, "access_token": token, "identity_token": id_token,
            "verifier_token": v_token, "email": email
        }
        final_url = f"{BASE_URL}/game/account_security/bind:create_rebind_request"
    else:
        # New Bind logic (Identity Token NOT required)
        final_payload = {
            "app_id": APP_ID, "access_token": token, "verifier_token": v_token, "email": email
        }
        final_url = f"{BASE_URL}/game/account_security/bind:create_bind_request"

    # D. Final Hit
    r = requests.post(final_url, data=final_payload, headers=headers)
    return {"type": "REBIND" if is_rebind else "NEW_BIND", "result": r.json()}
