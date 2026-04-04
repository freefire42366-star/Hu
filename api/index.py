from fastapi import FastAPI, Request, HTTPException
import requests
import hashlib

app = FastAPI()

# Garena Configuration
BASE_URL = "https://100067.connect.garena.com"
APP_ID = "100067"
SEC_CODE = "123456" # Fixed per your request

def sha256_hash(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

def get_headers(request: Request):
    # Jo mobile link kholi hai uska real user-agent uthayega
    ua = request.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {
        "User-Agent": ua,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip",
        "Connection": "keep-alive"
    }

@app.get("/")
def home():
    return {"msg": "Sameer Auto-Identity API Active (BD Server)"}

# --- STEP 1: SEND OTP ---
@app.get("/api/request")
async def send_otp(token: str, email: str, request: Request):
    headers = get_headers(request)
    payload = {
        "app_id": APP_ID,
        "access_token": token,
        "email": email,
        "locale": "en_BD",
        "region": "BD"
    }
    r = requests.post(f"{BASE_URL}/game/account_security/bind:send_otp", data=payload, headers=headers)
    return r.json()

# --- STEP 2: CONFIRM (AUTO-IDENTITY) ---
@app.get("/api/confirm")
async def confirm(token: str, email: str, otp: str, request: Request):
    headers = get_headers(request)
    
    # 1. Sabse pehle check karo account par mail hai ya nahi
    info_res = requests.get(f"{BASE_URL}/game/account_security/bind:get_bind_info", 
                            params={"app_id": APP_ID, "access_token": token}, headers=headers).json()
    has_mail = True if info_res.get("email") else False

    # 2. OTP Verify karke Verifier Token lo
    v_payload = {"app_id": APP_ID, "access_token": token, "email": email, "otp": otp}
    v_res = requests.post(f"{BASE_URL}/game/account_security/bind:verify_otp", data=v_payload, headers=headers).json()
    verifier_token = v_res.get("verifier_token")

    if not verifier_token:
        return {"status": "error", "msg": "OTP Galat hai", "garena_res": v_res}

    # 3. AUTO IDENTITY: Garena se Identity Token maango (Identity verification)
    # Yeh background mein khud Identity Token mangwayega
    id_payload = {
        "app_id": APP_ID,
        "access_token": token,
        "secondary_password": sha256_hash(SEC_CODE)
    }
    id_res = requests.post(f"{BASE_URL}/game/account_security/bind:verify_identity", data=id_payload, headers=headers).json()
    identity_token = id_res.get("identity_token")

    # 4. Final Binding
    if has_mail:
        # REBIND FLOW (Identity Token must be sent)
        if not identity_token:
            return {"status": "error", "msg": "Auto Identity Token Failed", "details": id_res}
        
        final_payload = {
            "app_id": APP_ID,
            "access_token": token,
            "identity_token": identity_token,
            "verifier_token": verifier_token,
            "email": email
        }
        endpoint = "/game/account_security/bind:create_rebind_request"
    else:
        # NEW BIND FLOW (Identity Token NOT sent to avoid error_params)
        final_payload = {
            "app_id": APP_ID,
            "access_token": token,
            "verifier_token": verifier_token,
            "email": email
        }
        endpoint = "/game/account_security/bind:create_bind_request"

    # Garena ko final request bhejo
    r = requests.post(f"{BASE_URL}{endpoint}", data=final_payload, headers=headers)
    return {
        "action": "REBIND" if has_mail else "NEW_BIND",
        "identity_token_used": True if identity_token else False,
        "garena_response": r.json()
    }
