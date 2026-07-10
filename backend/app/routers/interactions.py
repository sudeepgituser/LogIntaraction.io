from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.agent.tools import log_interaction as log_interaction_tool
from app.agent.tools import edit_interaction as edit_interaction_tool

router = APIRouter()


# ---------- HCPs ----------

@router.get("/hcps", response_model=list[schemas.HCPOut])
def list_hcps(db: Session = Depends(get_db)):
    return db.query(models.HCP).all()


@router.post("/hcps", response_model=schemas.HCPOut)
def create_hcp(hcp: schemas.HCPCreate, db: Session = Depends(get_db)):
    db_hcp = models.HCP(**hcp.model_dump())
    db.add(db_hcp)
    db.commit()
    db.refresh(db_hcp)
    return db_hcp


# ---------- Interactions (structured form path) ----------

@router.get("/interactions", response_model=list[schemas.InteractionOut])
def list_interactions(hcp_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Interaction)
    if hcp_id is not None:
        query = query.filter(models.Interaction.hcp_id == hcp_id)
    return query.order_by(models.Interaction.interaction_date.desc()).all()


@router.post("/interactions", response_model=schemas.InteractionOut)
def create_interaction(payload: schemas.InteractionCreate, db: Session = Depends(get_db)):
    """
    The structured form calls this endpoint directly. Under the hood it
    reuses the same `log_interaction` LangGraph tool used by the chat agent,
    so both entry points produce identically-shaped, LLM-enriched records.
    """
    hcp = db.query(models.HCP).filter(models.HCP.id == payload.hcp_id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")
    result_json = log_interaction_tool.invoke({
        "hcp_id": payload.hcp_id,
        "interaction_type": payload.interaction_type,
        "raw_notes": payload.raw_notes or "",
        "channel": payload.channel or "in_person",
        "created_by": payload.created_by or "rep",
        "attendees": payload.attendees,
        "materials_shared": payload.materials_shared,
        "outcomes": payload.outcomes,
        "sentiment": payload.sentiment,
    })
    import json
    result = json.loads(result_json)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    interaction = db.query(models.Interaction).filter(models.Interaction.id == result["id"]).first()
    return interaction


@router.put("/interactions/{interaction_id}", response_model=schemas.InteractionOut)
def update_interaction(interaction_id: int, payload: schemas.InteractionUpdate, db: Session = Depends(get_db)):
    import json
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    result_json = edit_interaction_tool.invoke({
        "interaction_id": interaction_id,
        "updates_json": json.dumps(updates),
    })
    result = json.loads(result_json)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    return interaction
