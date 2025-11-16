import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Contact, Alert, Location

app = FastAPI(title="Women's Safety Alert API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers
class ObjectIdStr(str):
    pass


def ensure_objectid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")


@app.get("/")
def read_root():
    return {"message": "Women's Safety Alert API is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# Request models
class RegisterUserRequest(User):
    contacts: Optional[List[Contact]] = None


class CreateAlertRequest(BaseModel):
    user_id: str
    message: Optional[str] = None
    location: Optional[Location] = None


class CancelAlertRequest(BaseModel):
    alert_id: str
    pin: Optional[str] = None


# Endpoints
@app.post("/api/register")
def register_user(payload: RegisterUserRequest):
    # Create user
    user_id = create_document("user", payload)

    # Insert contacts if provided
    if payload.contacts:
        for c in payload.contacts:
            create_document("contact", {**c.model_dump(), "user_id": user_id})

    return {"user_id": user_id}


@app.get("/api/contacts/{user_id}")
def list_contacts(user_id: str):
    ensure_objectid(user_id)  # validate format only
    contacts = get_documents("contact", {"user_id": user_id})
    # Convert ObjectId to str
    for c in contacts:
        c["_id"] = str(c["_id"]) if "_id" in c else None
    return contacts


@app.post("/api/alerts")
def create_alert(payload: CreateAlertRequest):
    # Load user
    ensure_objectid(payload.user_id)
    users = get_documents("user", {"_id": ensure_objectid(payload.user_id)})
    if not users:
        raise HTTPException(status_code=404, detail="User not found")
    user = users[0]

    message = payload.message or user.get(
        "default_message",
        "I need help. This is an emergency. Please check my location and contact me immediately."
    )

    alert_data = {
        "user_id": payload.user_id,
        "message": message,
        "location": payload.location.model_dump() if payload.location else None,
        "status": "active",
        "share_url": None,
    }

    alert_id = create_document("alert", alert_data)
    return {"alert_id": alert_id, "status": "active"}


@app.post("/api/alerts/cancel")
def cancel_alert(payload: CancelAlertRequest):
    ensure_objectid(payload.alert_id)
    # Fetch alert and user to verify pin if set
    alerts = get_documents("alert", {"_id": ensure_objectid(payload.alert_id)})
    if not alerts:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert = alerts[0]

    users = get_documents("user", {"_id": ensure_objectid(alert.get("user_id"))})
    user = users[0] if users else None

    if user and user.get("pin"):
        if not payload.pin or payload.pin != user.get("pin"):
            raise HTTPException(status_code=403, detail="Invalid PIN")

    # Update alert status
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    db["alert"].update_one({"_id": ensure_objectid(payload.alert_id)}, {"$set": {"status": "canceled"}})
    return {"alert_id": payload.alert_id, "status": "canceled"}


@app.get("/api/alerts/{user_id}")
def list_alerts(user_id: str):
    ensure_objectid(user_id)
    alerts = get_documents("alert", {"user_id": user_id})
    for a in alerts:
        a["_id"] = str(a["_id"]) if "_id" in a else None
    return alerts


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
