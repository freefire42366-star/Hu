from fastapi import FastAPI, Request
import requests
import hashlib

app = FastAPI()

# --- Full URLs (BD Server Stack) ---
URL_SEND_OTP   = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
URL_VERIFY_OTP = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
URL_BIND_REQ   = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
URL_VERIFY_ID  = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
URL_REBIND_REQ = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"

APP_ID = "100067"
SEC_CODE = "123456" # Default Security Code

def sha256_hash(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

def get_msdk_headers(request: Request):
    ua = request.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {
        "User-Agent": ua,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip"
    }

@app.get("/")
def home():
    return {"msg": "Sameer Anti-Error Engine Active"}

# [STEP 1: SEND OTP]
@app.get("/api/request")
async def send_otp(token: str, email: str, request: Request):
    headers = get_msdk_headers(request)
    payload = {
        "app_id": APP_ID, "access_token": token, "email": email,
        "locale": "en_PK", "region": "PK" # en_PK mandatory for Garena
    }
    r = requests.post(URL_SEND_OTP, data=payload, headers=headers)
    return r.json()

# [STEP 2: CONFIRM & AUTO-FIX]
@app.get("/api/confirm")
async def confirm(token: str, email: str, otp: str, request: Request):
    headers = get_msdk_headers(request)
    
    # 1. OTP Verify karke Verifier Token lo
    v_data = {"app_id": APP_ID, "access_token": token, "email": email, "otp": otp}
    v_res = requests.post(URL_VERIFY_OTP, data=v_data, headers=headers).json()
    v_token = v_res.get("verifier_token")

    if not v_token:
        return {"result": 2106, "error": "OTP_INVALID", "garena_res": v_res}

    # 2. TRY NEW BIND (First Attempt)
    # Payload for fresh account
    bind_payload = {
        "app_id": APP_ID,
        "access_token": token,
        "verifier_token": v_token,
        "email": email
    }
    
    r1 = requests.post(URL_BIND_REQ, data=bind_payload, headers=headers).json()

    # 3. THE FIX: Agar Garena ne 'error_params' bola, toh turant Rebind try karo
    if r1.get("error") == "error_params" or r1.get("result") != 0:
        # Matlab Garena ko Identity Token chahiye!
        # Background mein 123456 ka identity token nikalo
        pw_hash = sha256_hash(SEC_CODE)
        id_data = {
            "app_id": APP_ID, 
            "access_token": token, 
            "secondary_password": pw_hash
        }
        id_res = requests.post(URL_VERIFY_ID, data=id_data, headers=headers).json()
        id_token = id_res.get("identity_token")

        if not id_token:
            # Agar security code 123456 nahi hai, tabhi fail hoga
            return {"status": "Failed", "msg": "error_params detect hua, par 123456 code bhi work nahi kiya.", "raw": id_res}

        # Ab REBIND endpoint use karo (Dono tokens ke saath)
        rebind_payload = {
            "app_id": APP_ID,
            "access_token": token,
            "identity_token": id_token,
            "verifier_token": v_token,
            "email": email
        }
        r2 = requests.post(URL_REBIND_REQ, data=rebind_payload, headers=headers).json()
        
        return {
            "action": "AUTO_SWITCH_TO_REBIND",
            "msg": "Fixed error_params by injecting Identity Token",
            "result": r2
        }

    # Agar pehla attempt hi bina error ke success ho gaya
    return {
        "action": "NEW_BIND_SUCCESS",
        "result": r1
    }
