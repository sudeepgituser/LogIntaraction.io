from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from app.database import get_db
from app import models, schemas
from app.agent.graph import agent_executor

router = APIRouter()

# In-memory per-session message history for this demo. Swap for Redis/DB
# backed persistence for production use.
_session_histories: dict[str, list] = {}


@router.post("/chat", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatRequest, db: Session = Depends(get_db)):
    history = _session_histories.setdefault(payload.session_id, [])

    user_context = payload.message
    if payload.hcp_id:
        user_context = f"[Context: hcp_id={payload.hcp_id}] {payload.message}"

    history.append(HumanMessage(content=user_context))

    result = agent_executor.invoke({"messages": history})
    new_messages = result["messages"]
    _session_histories[payload.session_id] = new_messages

    # Persist chat turns for audit trail
    db.add(models.ChatSession(session_id=payload.session_id, role="user", content=payload.message))

    tool_calls_made = []
    interaction_out = None
    reply_text = ""

    for m in new_messages:
        if isinstance(m, AIMessage) and m.content:
            reply_text = m.content
        if isinstance(m, ToolMessage):
            tool_calls_made.append({"tool": m.name, "output": m.content})
            if m.name == "log_interaction":
                import json
                try:
                    parsed = json.loads(m.content)
                    if "id" in parsed:
                        interaction = db.query(models.Interaction).filter(
                            models.Interaction.id == parsed["id"]
                        ).first()
                        if interaction:
                            interaction_out = interaction
                except json.JSONDecodeError:
                    pass

    db.add(models.ChatSession(session_id=payload.session_id, role="assistant", content=reply_text))
    db.commit()

    return schemas.ChatResponse(
        session_id=payload.session_id,
        reply=reply_text,
        tool_calls=tool_calls_made,
        interaction=interaction_out,
    )
