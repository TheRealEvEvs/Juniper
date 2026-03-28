# 🌿 Juniper — Exact Setup Guide
# Every step spelled out. Takes about 20 minutes.

---

## WHAT YOU'LL CREATE
- A backend server (Railway) that runs Juniper's AI brain — FREE
- A database (Supabase) that stores your todos, events, reminders — FREE
- A website (Vercel) that you open on your phone/PC to listen — FREE
- Push notifications to your phone (ntfy.sh) — FREE

---

## STEP 1 — Upload the code to GitHub

1. Go to github.com → click the green "New" button (top left)
2. Name it: juniper-app
3. Leave everything else default → click "Create repository"
4. On the next page, click "uploading an existing file"
5. Drag the entire `juniper-web` folder contents in
   (drag backend/ and frontend/ folders together)
6. Click "Commit changes"

---

## STEP 2 — Create the database (Supabase)

1. Go to supabase.com → "Start your project" → sign in with GitHub
2. Click "New project"
   - Name: juniper
   - Password: make something up (save it)
   - Region: pick closest to you
3. Wait ~2 min for it to set up
4. Go to Settings (gear icon) → Database
5. Scroll to "Connection string" → select "URI" tab
6. COPY that whole string — looks like:
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxx.supabase.co:5432/postgres
7. Replace [YOUR-PASSWORD] with the password you made in step 2
8. Save this somewhere — you'll need it in Step 3

---

## STEP 3 — Deploy the backend (Railway)

1. Go to railway.app → "Start a New Project" → sign in with GitHub
2. Click "Deploy from GitHub repo" → select "juniper-app"
3. It will ask which folder — type: backend
4. It will try to deploy — WAIT, don't do anything yet
5. Click the "Variables" tab → "Add Variables" and add ALL of these:

   GEMINI_API_KEY    = (your key from aistudio.google.com → Get API Key)
   DATABASE_URL      = (the Supabase connection string from Step 2)
   NTFY_TOPIC        = juniper-abc123  ← make up any random string

6. Click "Deploy" — wait about 2 minutes
7. When done, click "Settings" tab → copy your URL
   It looks like: https://juniper-backend-production.up.railway.app
8. Test it: open that URL + /health in your browser
   You should see: {"status":"online","ai":"Juniper (Gemini 1.5 Flash)"}

---

## STEP 4 — Deploy the frontend (Vercel)

1. Go to vercel.com → "Continue with GitHub"
2. Click "Add New Project" → select "juniper-app"
3. Set ROOT DIRECTORY to: frontend
4. Click "Environment Variables" and add:
   REACT_APP_BACKEND_URL = (your Railway URL from Step 3)
5. Click "Deploy" — takes about 1 minute
6. You'll get a URL like: https://juniper-abc.vercel.app
   THAT is your Juniper website — bookmark it!

---

## STEP 5 — Set up push notifications on your phone

1. Open Play Store → search "ntfy" → install (it's free, by binwiederhier)
2. Open ntfy → tap the + button (bottom right)
3. In "Topic" type the NTFY_TOPIC you picked in Step 3
   (e.g. juniper-abc123)
4. Tap Subscribe
5. Done! Juniper will now push reminders straight to your phone

---

## STEP 6 — Use Juniper!

1. Open your Vercel URL on your phone or PC
2. Go to Settings tab → paste your Railway URL → Save
3. Go to Listen tab → tap the big mic button
4. Start talking! Say something like:
   "Hey can you pick me up at 3pm?" → "Sure!"
5. Watch the Todos and Events tabs fill up automatically

---

## TIPS

- Keep the Listen tab open on your phone while you're out
- The mic uses your browser's built-in speech recognition (free, no API needed)
- Juniper only creates events/todos when it hears you AGREE to something
- Push notifications go to your phone automatically before each event

---

## GETTING YOUR GEMINI API KEY (free)

1. Go to aistudio.google.com
2. Sign in with your Google account
3. Click "Get API Key" (top left)
4. Click "Create API Key"
5. Copy it — paste it as GEMINI_API_KEY in Railway
