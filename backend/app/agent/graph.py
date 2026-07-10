"""
The LangGraph agent that powers the conversational "Log Interaction" chat
interface.

Role of the agent:
    The rep chats naturally, e.g. "Just left Dr. Mehta's clinic, discussed
    Drug A efficacy data, dropped 10 samples, she wants updated pediatric
    dosing info by next week." The agent (backed by Groq's gemma2-9b-it)
    decides which tool(s) to call -- pulling HCP history for context,
    checking compliance flags, logging the interaction, editing a prior
    entry, or scheduling a follow-up -- and replies conversationally,
    confirming what was captured. This removes the need for the rep to fill
    out a structured form field-by-field: the agent does the structuring.
"""

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from app.config import settings
from app.agent.tools import ALL_TOOLS

SYSTEM_PROMPT = """You are the AI agent inside a pharma CRM's HCP (Healthcare
Professional) module. Field reps talk to you to log their interactions with
doctors instead of filling out a form.

Behavior rules:
1. If the rep's message names a specific HCP (e.g. "Dr. Kapoor"), ALWAYS
   call `find_hcp_by_name` first to resolve the correct hcp_id -- even if a
   different hcp_id was passed in context. The name in the rep's message
   always takes priority over the context hcp_id, since the rep may be
   switching to a different doctor than whichever is currently selected in
   the UI. Only fall back to the context hcp_id if no name is mentioned.
2. Once you have the correct hcp_id, call `get_hcp_history` if it would
   help you understand context before logging.
3. Always run `check_compliance_flags` on the raw notes before logging.
   If flagged, mention the flag to the rep in your reply, but still log the
   interaction (the flag is informational for compliance review, not a
   blocker).
4. Use `log_interaction` to persist a new interaction, using the resolved
   hcp_id from step 1. Never invent an hcp_id -- if `find_hcp_by_name`
   returns zero or multiple matches, ask the rep to clarify which HCP.
5. If the rep wants to correct/change something already logged, use
   `edit_interaction`.
6. If the rep mentions something to do later (send data, schedule a lunch
   and learn, etc.), use `schedule_follow_up`.
7. Keep replies short, professional, and confirm exactly what was captured
   (summary, sentiment, products, samples, follow-ups) so the rep can
   correct you if anything is wrong.
"""


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def build_agent_graph():
    llm = ChatGroq(
        model=settings.GROQ_MODEL,
        groq_api_key=settings.GROQ_API_KEY,
        temperature=0.2,
    )
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    def agent_node(state: AgentState):
        messages = state["messages"]
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(ALL_TOOLS))

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


# Compiled once at import time and reused across requests.
agent_executor = build_agent_graph()
