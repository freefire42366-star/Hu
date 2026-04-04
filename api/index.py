from fastapi import FastAPI, Request
import requests
import hashlib

app = FastAPI()

BASE_URL = "https://100067.connect.garena.com"
APP_ID = "100067"
SEC_CODE = "123456"

def sha256_hash(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

def get_msdk_headers(request: Request):
    ua = request.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {
        "User-Agent": ua,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip",
        "Connection": "keep-alive"
    }

@app.get("/")
def home():
    return {"msg": "Sameer Real Verification Engine Live"}

# ================= STEP 1: SEND OTP =================
@app.get("/api/request")
async def send_otp(token: str, email: str, request: Request):
    headers = get_msdk_headers(request)
    payload = {
        "app_id": APP_ID, "access_token": token, "email": email,
        "locale": "en_BD", "region": "BD"
    }
    # API: /game/account_security/bind:send_otp
    r = requests.post(f"{BASE_URL}/game/account_security/bind:send_otp", data=payload, headers=headers)
    return r.json()

# ================= STEP 2: VERIFY & CONFIRM BIND =================
@app.get("/api/confirm")
async def confirm_bind(token: str, email: str, otp: str, request: Request):
    headers = get_msdk_headers(request)

    # --- PART 1: VERIFY OTP (Asli Verification) ---
    # API: /game/account_security/bind:verify_otp
    v_data = {"app_id": APP_ID, "access_token": token, "email": email, "otp": otp}
    v_res = requests.post(f"{BASE_URL}/game/account_security/bind:verify_otp", data=v_data, headers=headers).json()
    verifier_token = v_res.get("verifier_token")

    if not verifier_token:
        return {"status": "Failed", "msg": "OTP Verification Failed", "garena_res": v_res}

    # --- PART 2: CHECK BIND STATUS ---
    # API: /game/account_security/bind:get_bind_info
    info = requests.get(f"{BASE_URL}/game/account_security/bind:get_bind_info", 
                        params={"app_id": APP_ID, "access_token": token}, headers=headers).json()
    is_rebind = True if info.get("email") else False

    # --- PART 3: THE ACTION ---
    if is_rebind:
        # REBIND FLOW: Identity Token mangna padega
        id_data = {"app_id": APP_ID, "access_token": token, "secondary_password": sha256_hash(SEC_CODE)}
        id_res = requests.post(f"{BASE_URL}/game/account_security/bind:verify_identity", data=id_data, headers=headers).json()
        identity_token = id_res.get("identity_token")

        if not identity_token:
            return {"status": "Failed", "msg": "Rebind requires correct Sec Code 123456", "id_res": id_res}

        # Final Rebind Call
        final_payload = {
            "app_id": APP_ID, "access_token": token, "identity_token": identity_token,
            "verifier_token": verifier_token, "email": email
        }
        endpoint = "/game/account_security/bind:create_rebind_request"
    else:
        # NEW BIND FLOW: Direct Bind
        final_payload = {
            "app_id": APP_ID, "access_token": token, 
            "verifier_token": verifier_token, "email": email
        }
        endpoint = "/game/account_security/bind:create_bind_request"

    # --- FINAL HIT TO GARENA ---
    r = requests.post(f"{BASE_URL}{endpoint}", data=final_payload, headers=headers)
    return {
        "action": "REBIND" if is_rebind else "NEW_BIND",
        "garena_response": r.json()
    }
