from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class HCP(Base):
    """A Healthcare Professional the field rep engages with."""

    __tablename__ = "hcps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    specialty = Column(String(255), nullable=True)
    institution = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="hcp")


class Interaction(Base):
    """A single logged interaction (visit, call, email, sample drop, event) with an HCP."""

    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey("hcps.id"), nullable=False)

    interaction_type = Column(String(50), nullable=False)  # visit, call, email, event, sample_drop
    channel = Column(String(50), nullable=True)  # in_person, virtual, phone, email
    interaction_date = Column(DateTime, default=datetime.utcnow)

    # Raw free-text captured from the rep, either typed into the form's notes
    # field or spoken/typed into the chat interface.
    raw_notes = Column(Text, nullable=True)

    # LLM-derived fields (populated by the Log Interaction tool)
    summary = Column(Text, nullable=True)
    sentiment = Column(String(50), nullable=True)  # positive, neutral, negative
    topics_discussed = Column(JSON, nullable=True)  # e.g. ["Drug A efficacy", "dosing"]
    products_discussed = Column(JSON, nullable=True)
    samples_dropped = Column(JSON, nullable=True)  # e.g. {"Drug A": 10}
    follow_up_actions = Column(JSON, nullable=True)  # list of {action, due_date}
    entities_extracted = Column(JSON, nullable=True)  # raw NER output for auditing
    attendees = Column(JSON, nullable=True)  # e.g. ["Dr. Kapoor", "Nurse Singh"]
    materials_shared = Column(JSON, nullable=True)  # e.g. ["Brochures", "Sample kit"]
    outcomes = Column(Text, nullable=True)  # key outcomes/agreements from the visit
   
    created_by = Column(String(100), nullable=True)  # rep name/id
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")


class ChatSession(Base):
    """Stores conversational chat turns for the conversational logging interface."""

    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True, nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, tool
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
