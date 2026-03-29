"""
Juniper Backend — No database needed!
Just the AI brain. All data stored in user's browser.
Deploy free on Render.com
"""
import json, logging, os
from datetime import datetime
from collections import deque

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("juniper")

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)
gemini = genai.GenerativeModel("gemini-1.5-flash")

_context: deque = deque(maxlen=60)

app = FastAPI(title="Juniper")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SYSTEM = """You are Juniper, a smart personal assistant. You listen to conversations and detect when the user commits to something.

ONLY act when the user clearly agrees to something — words like "sure", "ok", "yeah", "I will", "I'll", "fine", "sounds good", "got it", "yep".

A question alone is NOT enough. Wait for the user's acceptance.

Be smart about timing — if travel is involved, add buffer time to reminders.

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

class AudioChunk(BaseModel):
    transcript: str
    source: str = "browser_mic"
    timestamp: str = ""

class ProcessRequest(BaseModel):
    context: list

@app.get("/")
async def root():
    return {"status": "online", "name": "Juniper AI"}

@app.get("/health")
async def health():
    return {"status": "online", "ai": "Juniper (Gemini 1.5 Flash)"}

@app.post("/process")
async def process(req: ProcessRequest):
    """
    Receives recent context from the browser,
    asks Gemini if action is needed,
    returns structured data for browser to save locally.
    """
    if len([c for c in req.context if c.get("type") == "audio"]) < 2:
        return {"action": "none"}

    lines = []
    for c in req.context[-20:]:
        label = {"browser_mic":"[MIC]","phone_mic":"[PHONE]","screen":"[SCREEN]"}.get(c.get("source",""), "[?]")
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
        log.info(f"🌿 Juniper: {result.get('action','none')} — {result.get('reasoning','')}")
        return result
    except Exception as e:
        log.error(f"Gemini error: {e}")
        return {"action": "none"}
