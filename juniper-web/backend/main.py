"""
Juniper Backend — FastAPI
Deployed free on Railway.app
"""
import asyncio, json, logging, os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from collections import deque

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import psycopg2
from psycopg2.extras import RealDictCursor
import httpx

loggingdasfadsfasdfasdfasdfasdfasdfasdfasdfasdf.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("juniper")

# ── Config from environment variables (set in Railway dashboard) ──────────────
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
DATABASE_URL   = os.environ["DATABASE_URL"]       # Supabase Postgres URL
NTFY_TOPIC     = os.environ.get("NTFY_TOPIC", "juniper-change-me")
FRONTEND_URL   = os.environ.get("FRONTEND_URL", "*")

genai.configure(api_key=GEMINI_API_KEY)
gemini = genai.GenerativeModel("gemini-1.5-flash")

# Rolling context window per session
_context: deque = deque(maxlen=60)

# ── DB helpers ────────────────────────────────────────────────────────────────
def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS context_log (
                id SERIAL PRIMARY KEY,
                input_type TEXT, source TEXT, content TEXT,
                meta JSONB, created_at TIMESTAMPTZ DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS events (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL, location TEXT,
                event_time TIMESTAMPTZ NOT NULL,
                duration_min INT DEFAULT 60, notes TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS todos (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL, notes TEXT,
                priority INT DEFAULT 2, done BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ
            );
            CREATE TABLE IF NOT EXISTS reminders (
                id SERIAL PRIMARY KEY,
                event_id INT REFERENCES events(id) ON DELETE CASCADE,
                remind_at TIMESTAMPTZ NOT NULL,
                message TEXT NOT NULL, sent BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """)
        conn.commit()
    log.info("✅ Database ready")

# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    asyncio.create_task(reminder_loop())
    log.info("🌿 Juniper online")
    yield

app = FastAPI(title="Juniper", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Request models ────────────────────────────────────────────────────────────
class AudioChunk(BaseModel):
    transcript: str
    source: str = "browser_mic"
    timestamp: str = ""

class ScreenChunk(BaseModel):
    text: str
    app_name: str = ""
    timestamp: str = ""

# ── Gemini brain ──────────────────────────────────────────────────────────────
SYSTEM = """You are Juniper, a smart personal assistant. You monitor conversation transcripts
and screen text to detect when the user makes a commitment or agrees to something.

ONLY create an event/todo when the user clearly accepts something:
words like "sure", "ok", "yeah", "I will", "I'll", "fine", "sounds good", "got it".

Be smart about timing — if travel is involved, add buffer time to reminders.

Respond ONLY with valid JSON, no prose, no markdown fences:
{
  "action": "event" | "todo" | "both" | "none",
  "event": {
    "title": "...", "location": "...",
    "event_time": "ISO8601 datetime",
    "duration_min": 60, "notes": "..."
  },
  "todo": { "title": "...", "notes": "...", "priority": 1 },
  "reminders": [
    { "offset_min": 30, "message": "..." },
    { "offset_min": 10, "message": "..." },
    { "offset_min": 2,  "message": "..." }
  ],
  "reasoning": "one sentence"
}
If action is none: {"action":"none"}
Current time: {NOW}
"""

async def run_juniper(log_id: int):
    if len([c for c in _context if c["type"] == "audio"]) < 2:
        return

    lines = []
    for c in list(_context)[-20:]:
        label = {"browser_mic":"[MIC]","phone_mic":"[PHONE]","windows_mic":"[PC]",
                 "screen":"[SCREEN]"}.get(c["source"], "[?]")
        lines.append(f"{c['timestamp'][:16]} {label} {c['content']}")

    prompt = SYSTEM.replace("{NOW}", datetime.utcnow().isoformat(timespec="seconds"))
    prompt += f"\n\nRecent context:\n" + "\n".join(lines) + "\n\nAction needed?"

    try:
        resp = gemini.generate_content(prompt)
        raw = resp.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(raw)
    except Exception as e:
        log.error(f"Gemini error: {e}")
        return

    action = result.get("action", "none")
    log.info(f"🌿 Juniper: {action} — {result.get('reasoning','')}")
    if action == "none":
        return

    now = datetime.utcnow()
    event_id = None

    if action in ("event", "both") and result.get("event"):
        ev = result["event"]
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO events (title,location,event_time,duration_min,notes) VALUES (%s,%s,%s,%s,%s) RETURNING id",
                    (ev.get("title"), ev.get("location"), ev.get("event_time"), ev.get("duration_min",60), ev.get("notes"))
                )
                event_id = cur.fetchone()["id"]
            conn.commit()
        log.info(f"📅 Event: {ev['title']}")

        if result.get("reminders") and ev.get("event_time"):
            try:
                edt = datetime.fromisoformat(ev["event_time"].replace("Z",""))
                with get_conn() as conn:
                    with conn.cursor() as cur:
                        for r in result["reminders"]:
                            rat = edt - timedelta(minutes=r["offset_min"])
                            cur.execute(
                                "INSERT INTO reminders (event_id,remind_at,message) VALUES (%s,%s,%s)",
                                (event_id, rat.isoformat(), r["message"])
                            )
                    conn.commit()
            except Exception as e:
                log.error(f"Reminder insert error: {e}")

    if action in ("todo", "both") and result.get("todo"):
        td = result["todo"]
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO todos (title,notes,priority) VALUES (%s,%s,%s)",
                    (td.get("title"), td.get("notes"), td.get("priority",2))
                )
            conn.commit()
        log.info(f"✅ Todo: {td['title']}")

# ── Reminder loop ─────────────────────────────────────────────────────────────
async def reminder_loop():
    log.info("⏰ Reminder loop started")
    while True:
        try:
            now = datetime.utcnow()
            soon = now + timedelta(seconds=35)
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT r.id, r.message, e.title FROM reminders r JOIN events e ON r.event_id=e.id WHERE r.sent=FALSE AND r.remind_at <= %s",
                        (soon.isoformat(),)
                    )
                    due = cur.fetchall()
            for row in due:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"https://ntfy.sh/{NTFY_TOPIC}",
                        content=row["message"],
                        headers={"Title": f"⏰ {row['title']}", "Priority": "high", "Tags": "alarm_clock"},
                        timeout=8
                    )
                with get_conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute("UPDATE reminders SET sent=TRUE WHERE id=%s", (row["id"],))
                    conn.commit()
                log.info(f"🔔 Fired: {row['message'][:50]}")
        except Exception as e:
            log.error(f"Reminder loop error: {e}")
        await asyncio.sleep(30)

# ── Ingest endpoints ──────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "online", "ai": "Juniper (Gemini 1.5 Flash)"}

@app.post("/ingest/audio")
async def ingest_audio(chunk: AudioChunk, bg: BackgroundTasks):
    ts = chunk.timestamp or datetime.utcnow().isoformat()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO context_log (input_type,source,content,meta) VALUES (%s,%s,%s,%s) RETURNING id",
                        ("audio", chunk.source, chunk.transcript, json.dumps({})))
            log_id = cur.fetchone()["id"]
        conn.commit()
    _context.append({"type":"audio","source":chunk.source,"content":chunk.transcript,"timestamp":ts})
    bg.add_task(run_juniper, log_id)
    return {"status":"queued"}

@app.post("/ingest/screen")
async def ingest_screen(chunk: ScreenChunk, bg: BackgroundTasks):
    ts = chunk.timestamp or datetime.utcnow().isoformat()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO context_log (input_type,source,content,meta) VALUES (%s,%s,%s,%s) RETURNING id",
                        ("screen","screen",chunk.text,json.dumps({"app":chunk.app_name})))
            log_id = cur.fetchone()["id"]
        conn.commit()
    _context.append({"type":"screen","source":"screen","content":chunk.text[:500],"timestamp":ts})
    bg.add_task(run_juniper, log_id)
    return {"status":"queued"}

# ── Dashboard read endpoints ───────────────────────────────────────────────────
@app.get("/todos")
async def get_todos():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM todos ORDER BY created_at DESC")
            return [dict(r) for r in cur.fetchall()]

@app.patch("/todos/{tid}/done")
async def done_todo(tid: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE todos SET done=TRUE, updated_at=NOW() WHERE id=%s", (tid,))
        conn.commit()
    return {"ok": True}

@app.delete("/todos/{tid}")
async def delete_todo(tid: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM todos WHERE id=%s", (tid,))
        conn.commit()
    return {"ok": True}

@app.get("/events")
async def get_events():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM events ORDER BY event_time ASC")
            return [dict(r) for r in cur.fetchall()]

@app.delete("/events/{eid}")
async def delete_event(eid: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM events WHERE id=%s", (eid,))
        conn.commit()
    return {"ok": True}

@app.get("/reminders")
async def get_reminders():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT r.*,e.title as event_title FROM reminders r JOIN events e ON r.event_id=e.id ORDER BY r.remind_at ASC")
            return [dict(r) for r in cur.fetchall()]

@app.get("/log")
async def get_log():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM context_log ORDER BY created_at DESC LIMIT 100")
            return [dict(r) for r in cur.fetchall()]
