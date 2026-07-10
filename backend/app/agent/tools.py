"""
Tools available to the LangGraph HCP agent.

Each tool is a plain Python function wrapped with @tool so LangGraph can bind
it to the LLM (Groq's gemma2-9b-it). Tools open their own short-lived DB
session since LangGraph tool nodes are invoked outside the FastAPI
request/response cycle.
"""

import json
from datetime import datetime, timedelta
from typing import Optional

from langchain_core.tools import tool
from langchain_groq import ChatGroq

from app.database import SessionLocal
from app.models import HCP, Interaction
from app.config import settings

# A small, fast model used *inside* tools for sub-tasks like summarization
# and entity extraction (kept separate from the main agent LLM so it can be
# swapped independently).
_extraction_llm = ChatGroq(
    model=settings.GROQ_MODEL,
    groq_api_key=settings.GROQ_API_KEY,
    temperature=0,
)

# Simple keyword list used by the compliance tool. In a production system
# this would be a maintained regulatory term list, not a hardcoded array.
COMPLIANCE_FLAG_TERMS = [
    "off-label", "off label", "guarantee cure", "guaranteed results",
    "adverse event", "side effect not listed", "unapproved use",
]
def _extract_structured_fields(raw_notes: str) -> dict:
    """Use the LLM to turn free-text rep notes into structured fields."""
    prompt = f"""You are a life-sciences CRM assistant. Read the field rep's
raw notes about an interaction with a Healthcare Professional (HCP) and
return ONLY a JSON object (no markdown, no commentary) with these keys:

- "summary": a 1-2 sentence neutral summary of the interaction
- "sentiment": one of "positive", "neutral", "negative"
- "topics_discussed": array of short topic strings (e.g. clinical data, dosing, pricing)
- "products_discussed": array of product/drug names mentioned
- "samples_dropped": object mapping product name to integer quantity, if any were mentioned, else {{}}
- "follow_up_actions": array of objects like {{"action": "...", "due_in_days": 7}}
- "attendees": array of people mentioned as present besides the HCP themself
  (e.g. nurses, other staff, colleagues), else []
- "materials_shared": array of any printed/digital materials mentioned as
  given to the HCP (e.g. "Brochure", "Leave-behind", "Study reprint"), else []
- "outcomes": a short string describing any agreement, decision, or concrete
  outcome from the interaction (e.g. "Agreed to trial the new dosage with
  two patients"), else an empty string ""

Raw notes:
\"\"\"{raw_notes}\"\"\"
"""
    response = _extraction_llm.invoke(prompt)
    text = response.content.strip()
    # Guard against the model wrapping JSON in ```json fences
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fail safe: return a minimal structure rather than crashing the tool
        return {
            "summary": raw_notes[:200],
            "sentiment": "neutral",
            "topics_discussed": [],
            "products_discussed": [],
            "samples_dropped": {},
            "follow_up_actions": [],
            "attendees": [],
            "materials_shared": [],
            "outcomes": "",
        }

@tool
def log_interaction(
    hcp_id: int,
    interaction_type: str,
    raw_notes: str,
    channel: Optional[str] = "in_person",
    created_by: Optional[str] = "rep",
    sentiment: Optional[str] = None,
    attendees: Optional[list] = None,
    materials_shared: Optional[list] = None,
    outcomes: Optional[str] = None,
) -> str:
    """Log a new interaction with an HCP. Captures raw free-text notes about a
    visit, call, email, event, or sample drop, then uses the LLM to
    summarize the notes, detect sentiment, extract topics/products
    discussed, count samples dropped, and pull out follow-up actions.
    If the rep already provided sentiment, attendees, materials_shared, or
    outcomes manually (e.g. via the structured form), those values take
    priority over what the LLM would infer.
    Returns the created interaction as JSON, including the new interaction id.
    """
    db = SessionLocal()
    try:
        hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
        if not hcp:
            return json.dumps({"error": f"No HCP found with id {hcp_id}"})

        extracted = _extract_structured_fields(raw_notes)

        # Manual overrides win over AI-inferred values, when provided
        final_sentiment = sentiment or extracted.get("sentiment")
        final_attendees = attendees if attendees else extracted.get("attendees", [])
        final_materials = materials_shared if materials_shared else extracted.get("materials_shared", [])
        final_outcomes = outcomes if outcomes else extracted.get("outcomes", "")

        interaction = Interaction(
            hcp_id=hcp_id,
            interaction_type=interaction_type,
            channel=channel,
            interaction_date=datetime.utcnow(),
            raw_notes=raw_notes,
            summary=extracted.get("summary"),
            sentiment=final_sentiment,
            topics_discussed=extracted.get("topics_discussed", []),
            products_discussed=extracted.get("products_discussed", []),
            samples_dropped=extracted.get("samples_dropped", {}),
            follow_up_actions=extracted.get("follow_up_actions", []),
            attendees=final_attendees,
            materials_shared=final_materials,
            outcomes=final_outcomes,
            entities_extracted=extracted,
            created_by=created_by,
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        return json.dumps({
            "id": interaction.id,
            "hcp_id": interaction.hcp_id,
            "summary": interaction.summary,
            "sentiment": interaction.sentiment,
            "topics_discussed": interaction.topics_discussed,
            "products_discussed": interaction.products_discussed,
            "samples_dropped": interaction.samples_dropped,
            "follow_up_actions": interaction.follow_up_actions,
            "attendees": interaction.attendees,
            "materials_shared": interaction.materials_shared,
            "outcomes": interaction.outcomes,
        })
    finally:
        db.close()
        
@tool
def edit_interaction(interaction_id: int, updates_json: str) -> str:
    """Edit a previously logged interaction. `updates_json` is a JSON string
    of the fields to change, e.g. '{"raw_notes": "corrected text", "sentiment": "positive"}'.
    If `raw_notes` is updated, the summary/topics/products/samples/follow-ups
    are automatically re-extracted from the new notes via the LLM so the
    record stays consistent. Returns the updated interaction as JSON.
    """
    db = SessionLocal()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({"error": f"No interaction found with id {interaction_id}"})

        try:
            updates = json.loads(updates_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "updates_json was not valid JSON"})

        # Directly editable fields
        for field in ["interaction_type", "channel", "raw_notes", "sentiment"]:
            if field in updates:
                setattr(interaction, field, updates[field])

        # If notes changed, re-run extraction so derived fields stay accurate
        if "raw_notes" in updates:
            extracted = _extract_structured_fields(updates["raw_notes"])
            interaction.summary = extracted.get("summary")
            interaction.sentiment = extracted.get("sentiment")
            interaction.topics_discussed = extracted.get("topics_discussed", [])
            interaction.products_discussed = extracted.get("products_discussed", [])
            interaction.samples_dropped = extracted.get("samples_dropped", {})
            interaction.follow_up_actions = extracted.get("follow_up_actions", [])
            interaction.entities_extracted = extracted

        # Allow direct manual overrides of derived fields too
        for field in ["summary", "topics_discussed", "products_discussed",
                      "samples_dropped", "follow_up_actions"]:
            if field in updates:
                setattr(interaction, field, updates[field])

        interaction.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(interaction)

        return json.dumps({
            "id": interaction.id,
            "summary": interaction.summary,
            "sentiment": interaction.sentiment,
            "topics_discussed": interaction.topics_discussed,
            "products_discussed": interaction.products_discussed,
            "samples_dropped": interaction.samples_dropped,
            "follow_up_actions": interaction.follow_up_actions,
            "updated_at": interaction.updated_at.isoformat(),
        })
    finally:
        db.close()

@tool
def find_hcp_by_name(name: str) -> str:
    """Look up an HCP (Healthcare Professional) by name or partial name
    mentioned by the rep (e.g. "Dr. Kapoor", "Kapoor", "Anita Mehta").
    Use this whenever the rep's message names a specific doctor, even if a
    different hcp_id was provided in context -- the rep's words take
    priority. Returns a JSON list of matching HCPs (id, name, specialty).
    If exactly one match is found, use its id for subsequent tool calls.
    If multiple or zero matches are found, ask the rep to clarify.
    """
    db = SessionLocal()
    try:
        cleaned = name.replace("Dr.", "").replace("Dr", "").strip()
        matches = (
            db.query(HCP)
            .filter(HCP.name.ilike(f"%{cleaned}%"))
            .all()
        )
        return json.dumps([
            {"id": h.id, "name": h.name, "specialty": h.specialty}
            for h in matches
        ])
    finally:
        db.close()        


@tool
def get_hcp_history(hcp_id: int, limit: int = 5) -> str:
    """Retrieve the most recent logged interactions for a given HCP so the
    agent has context (e.g. what was discussed last time, past sentiment,
    open follow-ups) before logging a new interaction or answering a rep's
    question. Returns a JSON list of past interactions, most recent first.
    """
    db = SessionLocal()
    try:
        hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
        if not hcp:
            return json.dumps({"error": f"No HCP found with id {hcp_id}"})

        history = (
            db.query(Interaction)
            .filter(Interaction.hcp_id == hcp_id)
            .order_by(Interaction.interaction_date.desc())
            .limit(limit)
            .all()
        )
        return json.dumps([
            {
                "id": i.id,
                "date": i.interaction_date.isoformat() if i.interaction_date else None,
                "type": i.interaction_type,
                "summary": i.summary,
                "sentiment": i.sentiment,
                "topics_discussed": i.topics_discussed,
                "follow_up_actions": i.follow_up_actions,
            }
            for i in history
        ])
    finally:
        db.close()


@tool
def schedule_follow_up(hcp_id: int, action: str, due_in_days: int = 7) -> str:
    """Schedule a follow-up action/reminder for a rep tied to a specific HCP
    (e.g. 'send updated efficacy data', 'book lunch-and-learn'). Appends the
    follow-up to the most recent interaction for that HCP so it shows up in
    that visit's record. Returns the created follow-up as JSON.
    """
    db = SessionLocal()
    try:
        hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
        if not hcp:
            return json.dumps({"error": f"No HCP found with id {hcp_id}"})

        latest = (
            db.query(Interaction)
            .filter(Interaction.hcp_id == hcp_id)
            .order_by(Interaction.interaction_date.desc())
            .first()
        )
        due_date = (datetime.utcnow() + timedelta(days=due_in_days)).isoformat()
        follow_up = {"action": action, "due_date": due_date, "status": "open"}

        if latest:
            actions = latest.follow_up_actions or []
            actions.append(follow_up)
            latest.follow_up_actions = actions
            db.commit()
            interaction_id = latest.id
        else:
            interaction_id = None

        return json.dumps({
            "hcp_id": hcp_id,
            "interaction_id": interaction_id,
            "follow_up": follow_up,
        })
    finally:
        db.close()


@tool
def check_compliance_flags(raw_notes: str) -> str:
    """Scan interaction notes for phrases that may need compliance review
    before the interaction is finalized -- e.g. off-label discussion claims
    or unlisted adverse events. This does NOT block logging; it returns
    flags so the agent can prompt the rep to review before submitting.
    Returns a JSON object with a boolean 'flagged' and a list of matched terms.
    """
    lowered = raw_notes.lower()
    matches = [term for term in COMPLIANCE_FLAG_TERMS if term in lowered]
    return json.dumps({"flagged": len(matches) > 0, "matched_terms": matches})


ALL_TOOLS = [
    find_hcp_by_name,
    log_interaction,
    edit_interaction,
    get_hcp_history,
    schedule_follow_up,
    check_compliance_flags,
]
