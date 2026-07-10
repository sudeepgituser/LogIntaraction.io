# AI-First CRM &mdash; HCP Module: Log Interaction Screen

An AI-first Customer Relationship Management module for pharma/life-science
field representatives, focused on the **Log Interaction** screen. Reps can
log a visit, call, email, event, or sample drop with a Healthcare
Professional (HCP) either through a **structured form** or a **natural-language
chat interface**, both backed by the same LangGraph agent.

## Why AI-first

Instead of reps manually filling in a dozen form fields after every visit,
they type or say what happened in their own words. A **LangGraph agent**
(using Groq's `gemma2-9b-it`) reads that free text and automatically derives:
a short summary, sentiment, topics discussed, products discussed, samples
dropped, and follow-up actions &mdash; then persists a structured record.
Reps can also just *talk* to the agent conversationally, and it decides which
tool(s) to call.

## Architecture

```
┌──────────────────────┐        ┌───────────────────────────┐        ┌──────────────┐
│   React + Redux UI    │  HTTP  │        FastAPI backend      │        │  Postgres /   │
│  (Structured Form OR   │──────▶│  /api/interactions          │───────▶│  MySQL DB     │
│   Chat Interface)      │◀──────│  /api/chat  (LangGraph agent)│◀──────│               │
└──────────────────────┘        └──────────────┬──────────────┘        └──────────────┘
                                                │
                                                ▼
                                     Groq LLM (gemma2-9b-it)
                                     via langchain-groq
```

- **Frontend**: React + Redux Toolkit. `LogInteractionScreen` toggles between
  `StructuredForm` and `ChatInterface`. Both write into the same Redux
  `interactions` slice and hit the same backend record shape.
- **Backend**: FastAPI exposes REST endpoints for HCPs/interactions and a
  `/api/chat` endpoint that drives the conversational flow through a compiled
  LangGraph graph.
- **AI Agent**: A LangGraph `StateGraph` with one `agent` node (Groq LLM bound
  to tools) and one `tools` node (LangGraph's prebuilt `ToolNode`), looping
  until the LLM stops requesting tool calls.
- **Database**: SQLAlchemy models work against either Postgres or MySQL
  (switch via the `DATABASE_URL` env var / driver).

## The LangGraph Agent & Its 5 Tools

The agent's job is to sit between the rep's natural language and the CRM's
structured data model: understanding intent, pulling context, flagging
compliance concerns, and keeping records accurate and current.

| Tool | Purpose |
|---|---|
| **`log_interaction`** | Takes raw free-text notes + an `hcp_id`, calls the LLM to extract `summary`, `sentiment`, `topics_discussed`, `products_discussed`, `samples_dropped`, and `follow_up_actions` as structured JSON, then writes a new `Interaction` row. This is the core "form-free logging" tool. |
| **`edit_interaction`** | Takes an `interaction_id` and a JSON patch of fields to change. If `raw_notes` changes, it **re-runs the LLM extraction** so summary/sentiment/topics/products/follow-ups stay consistent with the corrected text; also supports direct manual overrides of any derived field. |
| **`get_hcp_history`** | Returns the N most recent interactions for an HCP so the agent has context (what was discussed last time, open follow-ups) before logging something new or answering a rep's question. |
| **`schedule_follow_up`** | Appends a follow-up action + due date to an HCP's latest interaction record (e.g. "send updated pediatric dosing data in 7 days"). |
| **`check_compliance_flags`** | Scans raw notes for phrases that may need compliance review (off-label claims, unlisted adverse events, guaranteed-outcome language) and returns flags. Informational only &mdash; it does not block logging, but the agent surfaces the flag to the rep. |

All 5 tools are plain Python functions decorated with `@tool` in
`backend/app/agent/tools.py`, bound to the Groq LLM via `llm.bind_tools(...)`
in `backend/app/agent/graph.py`.

## Project structure

```
hcp-crm/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, routers
│   │   ├── config.py          # env-based settings (DB url, Groq key/model)
│   │   ├── database.py        # SQLAlchemy engine/session
│   │   ├── models.py          # HCP, Interaction, ChatSession ORM models
│   │   ├── schemas.py         # Pydantic request/response schemas
│   │   ├── seed.py            # seeds 3 sample HCPs
│   │   ├── agent/
│   │   │   ├── tools.py       # the 5 LangGraph tools
│   │   │   └── graph.py       # LangGraph StateGraph wiring + system prompt
│   │   └── routers/
│   │       ├── interactions.py # REST endpoints for structured form path
│   │       └── chat.py         # /api/chat endpoint for conversational path
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── package.json
    ├── public/index.html       # loads Google "Inter" font
    └── src/
        ├── App.js
        ├── store/               # Redux Toolkit slices (hcps, interactions, chat)
        ├── api/api.js            # axios client
        └── components/
            ├── LogInteractionScreen.jsx  # HCP picker + form/chat toggle + history
            ├── StructuredForm.jsx        # structured logging form
            └── ChatInterface.jsx         # conversational logging UI w/ tool trace
```

## Running it locally

### 1. Database
Create a Postgres or MySQL database, e.g. Postgres:
```bash
createdb hcp_crm
```

### 2. Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: set DATABASE_URL and GROQ_API_KEY
#   Get a free Groq API key at https://console.groq.com/keys

python -m app.seed          # creates tables + 3 sample HCPs
uvicorn app.main:app --reload --port 8000
```
Backend runs at `http://localhost:8000` (`/api/health` for a quick check,
`/docs` for interactive Swagger UI).

### 3. Frontend
```bash
cd frontend
npm install
npm start
```
Runs at `http://localhost:3000` and proxies `/api/*` to the backend.

## Using the app

1. Pick an HCP from the dropdown at the top of the Log Interaction screen.
2. **Structured Form tab**: choose interaction type/channel, type free-text
   notes, click "Log Interaction" &mdash; the AI-extracted summary, sentiment,
   products, samples, and follow-ups appear immediately below the form.
3. **Conversational Log tab**: just describe what happened in plain
   English. The agent may call `get_hcp_history` and `check_compliance_flags`
   before calling `log_interaction`; each tool call the agent made is shown
   as a small chip under its reply so you can see exactly what happened
   (useful for the demo video and for compliance auditing).
4. Recent interactions for the selected HCP are listed below both tabs.

## Notes on the tech choices

- **Groq `gemma2-9b-it`** is used as the primary/extraction model for speed
  and cost; `llama-3.3-70b-versatile` is referenced in config as a drop-in
  swap (`GROQ_MODEL_LARGE`) for cases needing stronger reasoning.
- **LangGraph** (not a plain LangChain chain) is used so the agent can loop
  between reasoning and tool calls an arbitrary number of times per turn
  (e.g. check history → check compliance → log interaction → schedule
  follow-up), which a single-shot chain can't do cleanly.
- Tables are auto-created on backend startup via
  `Base.metadata.create_all(...)` for simplicity; a production build would
  use Alembic migrations instead.
