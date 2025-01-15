from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
from twilio.rest import Client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Twilio client
twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

# Initialize Redis client
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")), decode_responses=True
)

app = FastAPI()

# Request models
class PhoneRequest(BaseModel):
    phone: str

class OTPRequest(BaseModel):
    phone: str
    otp: str

# Endpoint to send OTP
@app.post("/send-otp")
def send_otp(request: PhoneRequest):
    try:
        verification = twilio_client.verify.services(os.getenv("TWILIO_SERVICE_SID")).verifications.create(
            to=request.phone, channel="sms"
        )
        return {"status": verification.status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to verify OTP
@app.post("/verify-otp")
def verify_otp(request: OTPRequest):
    try:
        verification_check = twilio_client.verify.services(
            os.getenv("TWILIO_SERVICE_SID")
        ).verification_checks.create(to=request.phone, code=request.otp)
        if verification_check.status == "approved":
            redis_client.set(f"session:{request.phone}", "authenticated", ex=3600)
            return {"status": "authenticated"}
        else:
            raise HTTPException(status_code=401, detail="Invalid OTP")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Session status endpoint (optional)
@app.get("/session-status")
def session_status(phone: str):
    if redis_client.exists(f"session:{phone}"):
        return {"status": "authenticated"}
    return {"status": "not authenticated"}
