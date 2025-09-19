from pydantic import BaseModel, ConfigDict
from typing import Optional

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class TrackBase(BaseModel):
    title: str
    artist: str
    album: Optional[str] = None

class TrackResponse(TrackBase):
    id: int
    model_config = ConfigDict(from_attributes=True)