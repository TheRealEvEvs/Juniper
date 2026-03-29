"""
Juniper Backend — with in-memory storage
Both the website mic AND the Windows agent push here.
The website polls /todos and /events to get new items.
"""
import json, logging, os
from datetime import datetime
from collections import deque
from typing import List

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("juniper")

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)
gemini = genai.GenerativeModel("gemini-1.5-flash-latest")

_todos: List[dict] = []
_events: List[dict] = []
_context: deque = deque(maxlen=60)
_id_counter = 0

def next_id():
    global _id_counter
    _id_counter += 1
    return _id_counter

app = FastAPI(title="Juniper")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SYSTEM = """You are Juniper, a smart personal assistant. You listen to conversations and detect when the user commits to something.

ONLY act when the user clearly agrees to something — words like "sure", "ok", "yeah", "I will", "I'll", "fine", "sounds good", "got it", "yep".

A question alone is NOT enough. Wait for the user's acceptance.

Respond ONLY with valid JSON, no markdown, no extra text:
{
  "action": "event" | "todo" | "both" | "none",
  "event": {
    "title": "string",
    "location": "string or null",
    "event_time": "ISO8601 datetime",
    "duration_min": 60,
    "notes": "string or null"
  },
  "todo": {
    "title": "string",
    "notes": "string or null",
    "priority": 1
  },
  "reminders": [
    { "offset_min": 30, "message": "string" },
    { "offset_min": 10, "message": "string" },
    { "offset_min": 2, "message": "string" }
  ],
  "reasoning": "one sentence"
}
If action is none just return: {"action":"none"}
Current time: {NOW}
"""

class ProcessRequest(BaseModel):
    context: list

def run_juniper(context: list):
    audio_chunks = [c for c in context if c.get("type") == "audio"]
    if len(audio_chunks) < 2:
        return

    lines = []
    for c in context[-20:]:
        label = {"browser_mic":"[MIC]","phone_mic":"[PHONE]","windows_mic":"[PC]","screen":"[SCREEN]"}.get(c.get("source",""), "[?]")
        ts = c.get("timestamp","")[:16]
        lines.append(f"{ts} {label} {c.get('content','')}")

    now = datetime.utcnow().isoformat(timespec="seconds")
    prompt = SYSTEM.replace("{NOW}", now)
    prompt += f"\n\nRecent context:\n" + "\n".join(lines) + "\n\nShould I take any action?"

    try:
        resp = gemini.generate_content(prompt)
        raw = resp.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
    except Exception as e:
        log.error(f"Gemini error: {e}")
        return

    action = result.get("action", "none")
    log.info(f"🌿 Juniper: {action} — {result.get('reasoning','')}")
    if action == "none":
        return

    now_iso = datetime.utcnow().isoformat(timespec="seconds")

    if action in ("event", "both") and result.get("event"):
        ev = result["event"]
        event = {
            "id": next_id(),
            "title": ev.get("title",""),
            "location": ev.get("location"),
            "event_time": ev.get("event_time",""),
            "duration_min": ev.get("duration_min", 60),
            "notes": ev.get("notes"),
            "reminders": result.get("reminders", []),
            "created_at": now_iso
        }
        _events.append(event)
        log.info(f"📅 Event saved: {event['title']}")

    if action in ("todo", "both") and result.get("todo"):
        td = result["todo"]
        todo = {
            "id": next_id(),
            "title": td.get("title",""),
            "notes": td.get("notes"),
            "priority": td.get("priority", 2),
            "done": False,
            "created_at": now_iso
        }
        _todos.append(todo)
        log.info(f"✅ Todo saved: {todo['title']}")

@app.get("/")
async def root():
    return {"status": "online", "name": "Juniper AI"}

@app.get("/health")
async def health():
    return {"status": "online", "ai": "Juniper (Gemini 1.5 Flash)"}

@app.post("/process")
async def process(req: ProcessRequest, bg: BackgroundTasks):
    for chunk in req.context:
        _context.append(chunk)
    bg.add_task(run_juniper, list(_context))
    return {"status": "queued"}

@app.get("/todos")
async def get_todos():
    return list(reversed(_todos))

@app.patch("/todos/{tid}/done")
async def done_todo(tid: int):
    for t in _todos:
        if t["id"] == tid:
            t["done"] = True
    return {"ok": True}

@app.delete("/todos/{tid}")
async def delete_todo(tid: int):
    global _todos
    _todos = [t for t in _todos if t["id"] != tid]
    return {"ok": True}

@app.get("/events")
async def get_events():
    return list(reversed(_events))

@app.delete("/events/{eid}")
async def delete_event(eid: int):
    global _events
    _events = [e for e in _events if e["id"] != eid]
    return {"ok": True}
