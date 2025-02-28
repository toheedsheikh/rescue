from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from pydantic import BaseModel
from typing import List
import os
import csv
import shutil

app = FastAPI()

# Folder to save images
IMAGE_FOLDER = "uploaded_images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# CSV file to store reports data
CSV_FILE = "reports.csv"

# Ensure CSV file has headers if not exists
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["image_filename", "latitude", "longitude", "description", "status"])

# User Signup
class SignUpRequest(BaseModel):
    mobile_number: str
    name: str
    email: str
    password: str
    mpin: str

@app.post("/signup1")
async def sign_up_user(request: SignUpRequest):
    try:
        hashed_password = hash_password(request.password)
        new_user = {
            "mobile_number": request.mobile_number,
            "name": request.name,
            "email": request.email,
            "password_hash": hashed_password,
            "mpin": request.mpin,
            "wallet_amount": 0.00,
        }
        return {"message": "User created successfully", "user": new_user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def hash_password(password: str) -> str:
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

# User Login
class LoginRequest(BaseModel):
    mobile_number: str
    mpin: str

@app.post("/login")
async def login_user(request: LoginRequest):
    try:
        return {
            "message": "Login successful",
            "user": {
                "mobile_number": request.mobile_number,
                "name": "Sample User",
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# User report endpoint
@app.post("/user/report/")
async def upload_report(
    image: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    description: str = Form(...)
):
    try:
        # Save image to folder
        image_path = os.path.join(IMAGE_FOLDER, image.filename)
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # Save report to CSV
        with open(CSV_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([image.filename, latitude, longitude, description, "not_resolved"])

        return {
            "message": "Report uploaded successfully",
            "image_filename": image.filename,
            "latitude": latitude,
            "longitude": longitude,
            "description": description,
            "status": "not_resolved"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Fetch all reports
@app.get("/reports/")
async def get_reports():
    try:
        reports = []
        with open(CSV_FILE, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                reports.append(row)
        return reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Fetch image by filename
@app.get("/image/{filename}")
async def get_image(filename: str):
    image_path = os.path.join(IMAGE_FOLDER, filename)
    if os.path.exists(image_path):
        return {"image_url": f"/{IMAGE_FOLDER}/{filename}"}
    else:
        raise HTTPException(status_code=404, detail="Image not found")
