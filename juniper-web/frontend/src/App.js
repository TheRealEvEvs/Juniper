import React, { useState, useEffect, useRef, useCallback } from 'react';

// ── Config ──────────────────────────────────────────────────────────────────
// Replace this with your Railway backend URL after deploying
const BACKEND = process.env.REACT_APP_BACKEND_URL || 'https://your-juniper-backend.railway.app';

// ── Styles ───────────────────────────────────────────────────────────────────
const css = `
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0f1117; color: #e8e8e8; font-family: 'Inter', sans-serif; min-height: 100vh; }
  ::-webkit-scrollbar { width: 6px; } ::-webkit-scrollbar-track { background: #1a1d27; }
  ::-webkit-scrollbar-thumb { background: #2d6a4f; border-radius: 3px; }

  .app { max-width: 900px; margin: 0 auto; padding: 20px 16px 80px; }
  .header { display: flex; align-items: center; gap: 12px; margin-bottom: 28px; padding-bottom: 20px; border-bottom: 1px solid #1e2130; }
  .logo { font-size: 28px; }
  .header h1 { font-size: 22px; font-weight: 600; color: #a8e6cf; }
  .header p { font-size: 13px; color: #666; margin-top: 2px; }

  .mic-card { background: #1a1d27; border: 1px solid #1e2130; border-radius: 16px; padding: 24px; margin-bottom: 24px; text-align: center; }
  .mic-btn { width: 80px; height: 80px; border-radius: 50%; border: none; cursor: pointer; font-size: 32px; margin: 0 auto 16px; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
  .mic-btn.off { background: #1e2130; box-shadow: 0 0 0 0 transparent; }
  .mic-btn.on  { background: #2d6a4f; animation: pulse 2s infinite; }
  .mic-btn.on:hover { background: #1b4332; }
  @keyframes pulse { 0%,100%{box-shadow:0 0 0 0 rgba(45,106,79,0.5)} 50%{box-shadow:0 0 0 16px rgba(45,106,79,0)} }
  .mic-status { font-size: 14px; color: #888; margin-bottom: 8px; }
  .mic-transcript { font-size: 13px; color: #a8e6cf; min-height: 40px; font-style: italic; padding: 8px 16px; background: #0f1117; border-radius: 8px; }

  .tabs { display: flex; gap: 4px; margin-bottom: 20px; background: #1a1d27; border-radius: 12px; padding: 4px; }
  .tab { flex: 1; padding: 10px; border: none; background: transparent; color: #888; font-size: 13px; font-weight: 500; cursor: pointer; border-radius: 9px; transition: all 0.15s; font-family: inherit; }
  .tab.active { background: #2d6a4f; color: #fff; }

  .section { display: flex; flex-direction: column; gap: 10px; }
  .card { background: #1a1d27; border: 1px solid #1e2130; border-radius: 12px; padding: 16px; }
  .card.done { opacity: 0.45; }
  .card-title { font-size: 15px; font-weight: 500; color: #e8e8e8; margin-bottom: 4px; }
  .card-title.done { text-decoration: line-through; }
  .card-meta { font-size: 12px; color: #555; display: flex; flex-wrap: wrap; gap: 8px; }
  .card-meta span { display: flex; align-items: center; gap: 4px; }
  .badge { padding: 2px 8px; border-radius: 20px; font-size: 11px; font-weight: 500; }
  .badge.p1 { background: #3d1515; color: #ff6b6b; }
  .badge.p2 { background: #2d2a15; color: #ffd93d; }
  .badge.p3 { background: #152d1e; color: #6bcb77; }
  .row { display: flex; align-items: flex-start; gap: 12px; }
  .row .card { flex: 1; }
  .check-btn { width: 24px; height: 24px; border-radius: 50%; border: 2px solid #2d6a4f; background: transparent; cursor: pointer; flex-shrink: 0; margin-top: 4px; color: #2d6a4f; font-size: 14px; display: flex; align-items: center; justify-content: center; transition: all 0.15s; }
  .check-btn:hover { background: #2d6a4f; color: #fff; }
  .del-btn { width: 28px; height: 28px; border: none; background: transparent; cursor: pointer; color: #333; font-size: 16px; flex-shrink: 0; border-radius: 6px; transition: all 0.15s; display: flex; align-items: center; justify-content: center; margin-top: 2px; }
  .del-btn:hover { background: #2a1515; color: #ff6b6b; }

  .empty { text-align: center; padding: 48px 24px; color: #444; font-size: 14px; }
  .empty .icon { font-size: 36px; margin-bottom: 12px; }

  .settings-card { background: #1a1d27; border: 1px solid #1e2130; border-radius: 12px; padding: 20px; margin-bottom: 16px; }
  .settings-card h3 { font-size: 14px; font-weight: 600; color: #a8e6cf; margin-bottom: 12px; }
  .input { width: 100%; padding: 10px 12px; background: #0f1117; border: 1px solid #1e2130; border-radius: 8px; color: #e8e8e8; font-size: 14px; font-family: inherit; outline: none; }
  .input:focus { border-color: #2d6a4f; }
  .btn { padding: 10px 20px; border: none; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; font-family: inherit; transition: all 0.15s; }
  .btn-green { background: #2d6a4f; color: #fff; }
  .btn-green:hover { background: #1b4332; }
  .btn-gray { background: #1e2130; color: #888; }
  .label { font-size: 12px; color: #666; margin-bottom: 6px; margin-top: 12px; }
  .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }
  .dot-green { background: #2d6a4f; }
  .dot-red { background: #8b1a1a; }
  .dot-yellow { background: #8b6914; }
  .connect-status { font-size: 13px; color: #666; display: flex; align-items: center; margin-top: 10px; }

  .log-item { font-size: 12px; font-family: monospace; color: #555; padding: 6px 10px; background: #0f1117; border-radius: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .log-item .src { color: #2d6a4f; margin-right: 6px; }

  .ntfy-steps { font-size: 13px; color: #888; line-height: 1.8; }
  .ntfy-steps b { color: #a8e6cf; }
  .ntfy-topic { font-family: monospace; background: #0f1117; padding: 8px 12px; border-radius: 6px; color: #a8e6cf; font-size: 13px; margin: 8px 0; word-break: break-all; }

  @media (max-width: 600px) { .app { padding: 12px 12px 80px; } .mic-btn { width: 70px; height: 70px; } }
`;

// ── Helpers ──────────────────────────────────────────────────────────────────
const api = async (path, opts = {}) => {
  const r = await fetch(BACKEND + path, { headers: { 'Content-Type': 'application/json' }, ...opts });
  if (!r.ok) throw new Error(`${r.status}`);
  return r.json();
};

const fmtDate = iso => {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('en-CA', { weekday:'short', month:'short', day:'numeric', hour:'2-digit', minute:'2-digit' });
};

const priorityLabel = p => ({ 1: ['p1','🔴 High'], 2: ['p2','🟡 Medium'], 3: ['p3','🟢 Low'] }[p] || ['p2','Medium']);

// ── Mic hook using Web Speech API (free, browser-native) ─────────────────────
function useMic(onTranscript) {
  const [listening, setListening] = useState(false);
  const [liveText, setLiveText] = useState('');
  const recognitionRef = useRef(null);
  const restartRef = useRef(null);
  const activeRef = useRef(false);

  const start = useCallback(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { alert('Your browser does not support speech recognition. Use Chrome or Edge.'); return; }

    activeRef.current = true;
    setListening(true);

    const startRecognition = () => {
      if (!activeRef.current) return;
      const r = new SR();
      recognitionRef.current = r;
      r.continuous = true;
      r.interimResults = true;
      r.lang = 'en-US';

      r.onresult = e => {
        let interim = '', final = '';
        for (let i = e.resultIndex; i < e.results.length; i++) {
          const t = e.results[i][0].transcript;
          if (e.results[i].isFinal) final += t;
          else interim += t;
        }
        setLiveText(interim || final);
        if (final.trim()) {
          onTranscript(final.trim());
          setLiveText('');
        }
      };

      r.onerror = e => { if (e.error !== 'no-speech') console.warn('Speech error:', e.error); };
      r.onend = () => {
        if (activeRef.current) {
          restartRef.current = setTimeout(startRecognition, 300);
        }
      };
      r.start();
    };

    startRecognition();
  }, [onTranscript]);

  const stop = useCallback(() => {
    activeRef.current = false;
    setListening(false);
    setLiveText('');
    clearTimeout(restartRef.current);
    recognitionRef.current?.stop();
  }, []);

  return { listening, liveText, start, stop };
}

// ── Components ───────────────────────────────────────────────────────────────
function TodoCard({ todo, onDone, onDelete }) {
  const [cls, label] = priorityLabel(todo.priority);
  return (
    <div className="row">
      <button className="check-btn" onClick={() => onDone(todo.id)} title="Mark done">
        {todo.done ? '✓' : ''}
      </button>
      <div className={`card ${todo.done ? 'done' : ''}`}>
        <div className={`card-title ${todo.done ? 'done' : ''}`}>{todo.title}</div>
        {todo.notes && <div style={{fontSize:13,color:'#666',marginTop:4}}>{todo.notes}</div>}
        <div className="card-meta" style={{marginTop:8}}>
          <span><span className={`badge ${cls}`}>{label}</span></span>
          <span>📅 {fmtDate(todo.created_at)}</span>
        </div>
      </div>
      <button className="del-btn" onClick={() => onDelete(todo.id)} title="Delete">✕</button>
    </div>
  );
}

function EventCard({ event, onDelete }) {
  return (
    <div className="row">
      <div className="card">
        <div className="card-title">📅 {event.title}</div>
        {event.location && <div style={{fontSize:13,color:'#666',marginTop:4}}>📍 {event.location}</div>}
        {event.notes && <div style={{fontSize:13,color:'#555',marginTop:4}}>{event.notes}</div>}
        <div className="card-meta" style={{marginTop:8}}>
          <span>🕐 {fmtDate(event.event_time)}</span>
          {event.duration_min && <span>⏱ {event.duration_min}min</span>}
        </div>
      </div>
      <button className="del-btn" onClick={() => onDelete(event.id)} title="Delete">✕</button>
    </div>
  );
}

// ── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab] = useState('listen');
  const [todos, setTodos] = useState([]);
  const [events, setEvents] = useState([]);
  const [log, setLog] = useState([]);
  const [backendStatus, setBackendStatus] = useState('checking');
  const [backendUrl, setBackendUrl] = useState(
    localStorage.getItem('juniper_backend') || BACKEND
  );
  const [ntfyTopic, setNtfyTopic] = useState(
    localStorage.getItem('juniper_ntfy') || ''
  );
  const [lastAction, setLastAction] = useState('');

  // Send transcript to backend
  const handleTranscript = useCallback(async (text) => {
    try {
      await fetch(backendUrl + '/ingest/audio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript: text, source: 'browser_mic', timestamp: new Date().toISOString() })
      });
      setLastAction(`Heard: "${text.slice(0, 60)}${text.length > 60 ? '…' : ''}"`);
    } catch (e) {
      console.warn('Could not send to backend:', e);
    }
  }, [backendUrl]);

  const { listening, liveText, start, stop } = useMic(handleTranscript);

  // Load data
  const refresh = useCallback(async () => {
    try {
      const [t, e, l] = await Promise.all([
        fetch(backendUrl + '/todos').then(r => r.json()),
        fetch(backendUrl + '/events').then(r => r.json()),
        fetch(backendUrl + '/log').then(r => r.json()),
      ]);
      setTodos(Array.isArray(t) ? t : []);
      setEvents(Array.isArray(e) ? e : []);
      setLog(Array.isArray(l) ? l.slice(0, 30) : []);
      setBackendStatus('online');
    } catch { setBackendStatus('offline'); }
  }, [backendUrl]);

  useEffect(() => { refresh(); const id = setInterval(refresh, 8000); return () => clearInterval(id); }, [refresh]);

  // Check backend
  useEffect(() => {
    fetch(backendUrl + '/health').then(() => setBackendStatus('online')).catch(() => setBackendStatus('offline'));
  }, [backendUrl]);

  const doneTodo = async id => {
    await fetch(backendUrl + `/todos/${id}/done`, { method: 'PATCH' });
    refresh();
  };
  const deleteTodo = async id => {
    await fetch(backendUrl + `/todos/${id}`, { method: 'DELETE' });
    refresh();
  };
  const deleteEvent = async id => {
    await fetch(backendUrl + `/events/${id}`, { method: 'DELETE' });
    refresh();
  };

  const saveSettings = () => {
    localStorage.setItem('juniper_backend', backendUrl);
    localStorage.setItem('juniper_ntfy', ntfyTopic);
    refresh();
  };

  const activeTodos = todos.filter(t => !t.done);
  const doneTodos = todos.filter(t => t.done);

  return (
    <>
      <style>{css}</style>
      <div className="app">

        {/* Header */}
        <div className="header">
          <div className="logo">🌿</div>
          <div>
            <h1>Juniper</h1>
            <p>Your always-on AI life assistant</p>
          </div>
          <div style={{marginLeft:'auto',display:'flex',alignItems:'center',gap:6,fontSize:13}}>
            <span className={`status-dot ${backendStatus==='online'?'dot-green':backendStatus==='checking'?'dot-yellow':'dot-red'}`}/>
            <span style={{color:'#555'}}>{backendStatus}</span>
          </div>
        </div>

        {/* Tabs */}
        <div className="tabs">
          {[['listen','🎙 Listen'],['todos','✅ Todos'+(activeTodos.length?` (${activeTodos.length})`:'')],
            ['events','📅 Events'+(events.length?` (${events.length})`:'')],['settings','⚙️ Setup']].map(([id,label]) => (
            <button key={id} className={`tab ${tab===id?'active':''}`} onClick={() => setTab(id)}>{label}</button>
          ))}
        </div>

        {/* ── Listen tab ─────────────────────────────────────────────────── */}
        {tab === 'listen' && (
          <>
            <div className="mic-card">
              <button className={`mic-btn ${listening?'on':'off'}`} onClick={listening?stop:start}>
                {listening ? '🎙' : '🎤'}
              </button>
              <div className="mic-status">
                {listening ? '🟢 Juniper is listening...' : '⚫ Tap to start listening'}
              </div>
              <div className="mic-transcript">
                {liveText || lastAction || (listening ? 'Waiting for speech...' : 'Press the mic button above')}
              </div>
            </div>

            {backendStatus === 'offline' && (
              <div style={{background:'#2a1515',border:'1px solid #4a2020',borderRadius:12,padding:16,marginBottom:20,fontSize:13,color:'#ff8080'}}>
                ⚠️ Can't reach Juniper backend. Go to <b>Setup</b> tab and enter your Railway URL.
              </div>
            )}

            <div style={{marginBottom:12,fontSize:12,color:'#444',fontWeight:500,textTransform:'uppercase',letterSpacing:1}}>
              Recent activity
            </div>
            <div className="section">
              {log.length === 0 && (
                <div className="empty"><div className="icon">👂</div>Nothing heard yet. Start listening!</div>
              )}
              {log.map(l => (
                <div key={l.id} className="log-item">
                  <span className="src">[{l.source}]</span>
                  {l.content?.slice(0, 120)}
                </div>
              ))}
            </div>
          </>
        )}

        {/* ── Todos tab ─────────────────────────────────────────────────── */}
        {tab === 'todos' && (
          <div className="section">
            {activeTodos.length === 0 && doneTodos.length === 0 && (
              <div className="empty">
                <div className="icon">✅</div>
                No todos yet. Juniper will add them automatically<br/>when it hears you commit to something.
              </div>
            )}
            {activeTodos.map(t => <TodoCard key={t.id} todo={t} onDone={doneTodo} onDelete={deleteTodo}/>)}
            {doneTodos.length > 0 && (
              <>
                <div style={{fontSize:12,color:'#333',marginTop:8,fontWeight:500}}>COMPLETED</div>
                {doneTodos.map(t => <TodoCard key={t.id} todo={t} onDone={doneTodo} onDelete={deleteTodo}/>)}
              </>
            )}
          </div>
        )}

        {/* ── Events tab ─────────────────────────────────────────────────── */}
        {tab === 'events' && (
          <div className="section">
            {events.length === 0 && (
              <div className="empty">
                <div className="icon">📅</div>
                No events yet. Juniper will create them<br/>when it hears you agree to an appointment.
              </div>
            )}
            {events.map(e => <EventCard key={e.id} event={e} onDelete={deleteEvent}/>)}
          </div>
        )}

        {/* ── Settings tab ─────────────────────────────────────────────────── */}
        {tab === 'settings' && (
          <>
            <div className="settings-card">
              <h3>🔌 Backend Connection</h3>
              <div className="label">Railway backend URL</div>
              <input className="input" value={backendUrl}
                onChange={e => setBackendUrl(e.target.value)}
                placeholder="https://your-app.railway.app" />
              <div className="connect-status">
                <span className={`status-dot ${backendStatus==='online'?'dot-green':'dot-red'}`}/>
                {backendStatus === 'online' ? 'Connected ✓' : 'Not connected — enter your Railway URL above'}
              </div>
            </div>

            <div className="settings-card">
              <h3>🔔 Push Notifications (ntfy.sh)</h3>
              <div className="ntfy-steps">
                <b>1.</b> Install the free <b>ntfy</b> app on your phone (Play Store / App Store)<br/>
                <b>2.</b> Open ntfy → tap + → subscribe to this topic:
                <div className="ntfy-topic">{ntfyTopic || '(enter your topic below first)'}</div>
                <b>3.</b> Juniper will push reminders directly to your phone
              </div>
              <div className="label" style={{marginTop:12}}>Your ntfy topic (set this in Railway env vars too)</div>
              <input className="input" value={ntfyTopic}
                onChange={e => setNtfyTopic(e.target.value)}
                placeholder="juniper-your-secret-topic-here" />
            </div>

            <div className="settings-card">
              <h3>📋 How to deploy the backend (one-time setup)</h3>
              <div className="ntfy-steps">
                <b>1.</b> Go to <b>railway.app</b> → sign in with GitHub<br/>
                <b>2.</b> Click <b>New Project → Deploy from GitHub repo</b><br/>
                <b>3.</b> Select your repo → pick the <b>backend</b> folder<br/>
                <b>4.</b> Go to <b>Variables</b> tab and add:<br/>
                &nbsp;&nbsp;• <b>GEMINI_API_KEY</b> = your key from aistudio.google.com<br/>
                &nbsp;&nbsp;• <b>DATABASE_URL</b> = your Supabase connection string<br/>
                &nbsp;&nbsp;• <b>NTFY_TOPIC</b> = your secret topic name<br/>
                <b>5.</b> Copy the Railway URL and paste it above<br/>
                <b>6.</b> Deploy this frontend folder to <b>vercel.com</b> → set REACT_APP_BACKEND_URL
              </div>
            </div>

            <button className="btn btn-green" style={{width:'100%'}} onClick={saveSettings}>
              Save Settings
            </button>
          </>
        )}

      </div>
    </>
  );
}
