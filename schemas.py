"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

# App-specific schemas for Women's Safety Alert App

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    phone: str = Field(..., description="Primary phone number in E.164 or local format")
    email: Optional[EmailStr] = Field(None, description="Email address")
    default_message: str = Field(
        "I need help. This is an emergency. Please check my location and contact me immediately.",
        description="Default SOS message used when an alert is created"
    )
    pin: Optional[str] = Field(None, description="Optional 4-6 digit PIN for canceling false alerts")

class Contact(BaseModel):
    """
    Trusted Contacts collection schema
    Collection name: "contact"
    """
    user_id: str = Field(..., description="ID of the owning user (string ObjectId)")
    name: str = Field(..., description="Contact name")
    phone: Optional[str] = Field(None, description="Contact phone number")
    email: Optional[EmailStr] = Field(None, description="Contact email address")

class Location(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lng: float = Field(..., ge=-180, le=180, description="Longitude")
    accuracy: Optional[float] = Field(None, ge=0, description="Accuracy in meters")

class Alert(BaseModel):
    """
    Safety Alerts collection schema
    Collection name: "alert"
    """
    user_id: str = Field(..., description="ID of the user who triggered the alert (string ObjectId)")
    message: str = Field(..., description="Message sent with the alert")
    location: Optional[Location] = Field(None, description="Location at the time of alert")
    status: str = Field("active", description="Status of alert: active, canceled, resolved")
    share_url: Optional[str] = Field(None, description="Public URL that can be shared with contacts")

# Example schemas kept for reference (not used by the app directly)
class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
