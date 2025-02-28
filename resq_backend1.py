from fastapi import FastAPI, UploadFile, Form, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import shutil
import csv
import os
import hashlib

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure the uploaded_images folder exists
UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# CSV file setup
CSV_FILE = 'reports.csv'
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['id', 'image_filename', 'latitude', 'longitude', 'location', 'description', 'status'])

# In-memory users array for signup/login
users = []

# Utility function to hash passwords
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Model for user signup
class User(BaseModel):
    mobile_number: str
    name: str
    email: str
    password: str
    mpin: str
    wallet_amount: float = 0.0

# Model for report
class Report(BaseModel):
    id: int
    image_filename: str
    latitude: float
    longitude: float
    location: str
    description: str
    status: str

# Endpoint: POST /user/report/
@app.post("/user/report/")
def upload_report(
    latitude: float = Form(...),
    longitude: float = Form(...),
    location: str = Form(...),
    description: str = Form(...),
    image: UploadFile = File(...)
):
    try:
        image_path = os.path.join(UPLOAD_DIR, f"{int(os.times()[4])}-{image.filename}")
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        with open(CSV_FILE, 'r') as file:
            report_id = sum(1 for line in file)

        new_row = [report_id, image.filename, latitude, longitude, location, description, 'not_resolved']
        with open(CSV_FILE, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(new_row)

        return {"message": "Report uploaded successfully", "report": new_row}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload report: {str(e)}")

# Endpoint: GET /user/reports/
@app.get("/user/reports/", response_model=List[Report])
def get_reports():
    try:
        reports = []
        with open(CSV_FILE, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                reports.append(Report(**row))
        return reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch reports: {str(e)}")

# Endpoint: PUT /admin/report/{report_id}/status
@app.put("/admin/report/{report_id}/status")
def update_report_status(report_id: int, status: str = Form(...)):
    try:
        updated = False
        lines = []
        with open(CSV_FILE, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == str(report_id):
                    row[6] = status
                    updated = True
                lines.append(row)

        if not updated:
            raise HTTPException(status_code=404, detail="Report not found")

        with open(CSV_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(lines)

        return {"message": "Report status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update report status: {str(e)}")

# Endpoint: POST /signup
@app.post("/signup")
def signup(user: User):
    if any(u['mobile_number'] == user.mobile_number for u in users):
        raise HTTPException(status_code=400, detail="Mobile number already exists")
    user.password = hash_password(user.password)
    users.append(user.dict())
    return {"message": "User created successfully", "user": user}

# Endpoint: POST /login
@app.post("/login")
def login(mobile_number: str = Form(...), mpin: str = Form(...)):
    user = next((u for u in users if u['mobile_number'] == mobile_number), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user['mpin'] != mpin:
        raise HTTPException(status_code=401, detail="Invalid MPIN")

    contacts = [{"mobile_number": u['mobile_number'], "name": u['name']} for u in users if u['mobile_number'] != mobile_number]
    return {"message": "Login successful", "user": user, "contacts": contacts}
