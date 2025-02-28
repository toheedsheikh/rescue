from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import hashlib

app = FastAPI(title="Crowdsourced Disaster Mapping Platform")

# In-memory storage for reports and users
reports = []
users = []

# Pydantic models
class ReportResponse(BaseModel):
    id: int
    image_filename: str
    latitude: float
    longitude: float
    description: str
    status: str

class StatusUpdate(BaseModel):
    status: str

class SignUpRequest(BaseModel):
    mobile_number: str
    name: str
    email: str
    password: str
    mpin: str

class LoginRequest(BaseModel):
    mobile_number: str
    mpin: str

# Utility functions
def hash_password(password: str) -> str:
    """Hash the password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

# User Endpoints
@app.post("/user/report/", response_model=ReportResponse)
def upload_report(
    image: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    description: str = Form(...)
):
    report_id = len(reports) + 1
    new_report = {
        "id": report_id,
        "image_filename": image.filename,
        "latitude": latitude,
        "longitude": longitude,
        "description": description,
        "status": "not_resolved"
    }
    reports.append(new_report)
    return new_report

@app.get("/user/reports/", response_model=List[ReportResponse])
def get_reports():
    return reports

@app.post("/signup")
async def sign_up_user(request: SignUpRequest):
    try:
        # Check if the mobile number already exists
        existing_user = next((user for user in users if user["mobile_number"] == request.mobile_number), None)
        if existing_user:
            raise HTTPException(status_code=400, detail="Mobile number already exists")

        # Hash the password before saving
        hashed_password = hash_password(request.password)

        # Prepare new user data
        new_user = {
            "mobile_number": request.mobile_number,
            "name": request.name,
            "email": request.email,
            "password_hash": hashed_password,
            "mpin": request.mpin,
            "wallet_amount": 0.00,
        }

        users.append(new_user)

        return {"message": "User created successfully", "user": new_user}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
async def login_user(request: LoginRequest):
    try:
        # Check if the user exists and the MPIN matches
        user = next((user for user in users if user["mobile_number"] == request.mobile_number), None)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user["mpin"] != request.mpin:
            raise HTTPException(status_code=401, detail="Invalid MPIN")

        # Fetch all contacts except the user's own number
        all_contacts = [
            {"mobile_number": contact["mobile_number"], "name": contact["name"]}
            for contact in users if contact["mobile_number"] != request.mobile_number
        ]

        return {
            "message": "Login successful",
            "user": {
                "mobile_number": user["mobile_number"],
                "name": user["name"],
            },
            "contacts": all_contacts
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Admin Endpoints
@app.put("/admin/report/{report_id}/status", response_model=ReportResponse)
def change_status(report_id: int, status_update: StatusUpdate):
    for report in reports:
        if report["id"] == report_id:
            report["status"] = status_update.status
            return report
    raise HTTPException(status_code=404, detail="Report not found")

# Run with: uvicorn <filename>:app --reload
