from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel


class HCPBase(BaseModel):
    name: str
    specialty: Optional[str] = None
    institution: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class HCPCreate(HCPBase):
    pass


class HCPOut(HCPBase):
    id: int

    class Config:
        from_attributes = True


class InteractionCreate(BaseModel):
    """Payload for the structured form."""
    hcp_id: int
    interaction_type: str
    channel: Optional[str] = None
    interaction_date: Optional[datetime] = None
    raw_notes: Optional[str] = None
    products_discussed: Optional[List[str]] = None
    samples_dropped: Optional[Dict[str, int]] = None
    attendees: Optional[List[str]] = None
    materials_shared: Optional[List[str]] = None
    outcomes: Optional[str] = None
    sentiment: Optional[str] = None
    created_by: Optional[str] = None


class InteractionUpdate(BaseModel):
    interaction_type: Optional[str] = None
    channel: Optional[str] = None
    raw_notes: Optional[str] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    topics_discussed: Optional[List[str]] = None
    products_discussed: Optional[List[str]] = None
    samples_dropped: Optional[Dict[str, int]] = None
    follow_up_actions: Optional[List[Dict[str, Any]]] = None
    attendees: Optional[List[str]] = None
    materials_shared: Optional[List[str]] = None
    outcomes: Optional[str] = None


class InteractionOut(BaseModel):
    id: int
    hcp_id: int
    interaction_type: str
    channel: Optional[str]
    interaction_date: Optional[datetime]
    raw_notes: Optional[str]
    summary: Optional[str]
    sentiment: Optional[str]
    topics_discussed: Optional[List[str]]
    products_discussed: Optional[List[str]]
    samples_dropped: Optional[Dict[str, Any]]
    follow_up_actions: Optional[List[Dict[str, Any]]]
    attendees: Optional[List[str]]
    materials_shared: Optional[List[str]]
    outcomes: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    session_id: str
    message: str
    hcp_id: Optional[int] = None
    created_by: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    tool_calls: List[Dict[str, Any]] = []
    interaction: Optional[InteractionOut] = None
