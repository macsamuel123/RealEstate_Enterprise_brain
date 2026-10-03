# Setup Guide — AI Chief of Staff

Complete step-by-step guide to get the project running locally.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- Git
- A Supabase account
- API keys from: Anthropic, OpenAI, Google Cloud, Twilio, ElevenLabs, Stripe

---

## Step 1: Clone & Install Dependencies

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

---

## Step 2: Set Up Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Note your **Project URL** and **Anon Key**
3. Go to **SQL Editor** → paste contents of `supabase/migrations/001_init_schema.sql` and run
4. Verify tables are created: check the **Table Editor** view

**For local development**, you can optionally use Supabase local development:
```bash
# Install Supabase CLI
brew install supabase/tap/supabase  # macOS
# or download from https://github.com/supabase/cli

# Initialize local database
supabase start

# Get your local connection details
supabase status
```

---

## Step 3: Get API Keys

### Anthropic
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an API key
3. **Request zero-data-retention (ZDR) agreement** — critical for IP protection

### OpenAI
1. Go to [platform.openai.com](https://platform.openai.com)
2. Create an API key
3. **Request ZDR agreement** as well

### Google Cloud (Gmail + Google Calendar)
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project
3. Enable **Gmail API** and **Google Calendar API**
4. Create an OAuth 2.0 credential (type: Web Application)
5. Set redirect URL to `http://localhost:8000/api/auth/google/callback` (adjust for your env)
6. Download credentials → note **Client ID** and **Client Secret**

### Twilio
1. Go to [twilio.com](https://twilio.com)
2. Create an account
3. In Console, note **Account SID** and **Auth Token**
4. Provision a phone number for testing

### ElevenLabs
1. Go to [elevenlabs.io](https://elevenlabs.io)
2. Create an account and get API key
3. Choose a voice ID (e.g., "Adam" or "Aria")

### Stripe (Optional for now — Phase 1 doesn't need payments)
1. Go to [stripe.com](https://stripe.com)
2. Create account and get **Secret Key** and **Publishable Key**

---

## Step 4: Configure Environment

```bash
# Copy example to .env
cp .env.example .env

# Edit .env and fill in all keys
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_ANON_KEY=your_anon_key
# ANTHROPIC_API_KEY=sk-ant-...
# ... etc
```

**Never commit `.env` to git** — it's in `.gitignore` for safety.

---

## Step 5: Run Backend

```bash
cd backend
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Start FastAPI server
python -m uvicorn app.main:app --reload

# Server runs on http://localhost:8000
# Docs available at http://localhost:8000/docs
```

---

## Step 6: Run Frontend

```bash
cd frontend
npm run dev

# Dev server runs on http://localhost:5173
# Automatically proxies /api calls to http://localhost:8000
```

---

## Step 7: Verify Everything Works

1. Open [http://localhost:5173](http://localhost:5173)
2. Should show "Backend online - development"
3. Check [http://localhost:8000/health](http://localhost:8000/health) — should return status=ok

If you see "Backend offline", check:
- Is the backend running? (`python -m uvicorn app.main:app --reload`)
- Are all API keys in `.env` filled in?
- Are there errors in the backend console?

---

## Step 8: Test Database Connection

```bash
# From backend directory with venv active
python
>>> from app.database import get_supabase
>>> supabase = get_supabase()
>>> response = supabase.table("org").select("*").execute()
>>> print(response)
```

Should return a response (empty if no orgs exist yet).

---

## Step 9: Create First Org & User (for testing)

```python
# In Python shell (from previous step)

# Create org
org_response = supabase.table("org").insert({
    "name": "Test Real Estate",
    "slug": "test-realty",
    "subscription_tier": "saas"
}).execute()

org_id = org_response.data[0]["id"]
print(f"Created org: {org_id}")

# Create user
user_response = supabase.table("users").insert({
    "org_id": org_id,
    "auth_user_id": "test-user-123",  # Temporary ID
    "email": "test@example.com",
    "full_name": "Test User",
    "role": "owner"
}).execute()

print(f"Created user: {user_response.data[0]['id']}")
```

---

## Running in Production

### Backend (Railway / Render / Similar)

```bash
# Set environment to production
export ENVIRONMENT=production
export LOG_LEVEL=warn

# Run with gunicorn for production
pip install gunicorn
gunicorn "app.main:app" --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### Frontend (Vercel)

```bash
# Build for production
npm run build

# Output goes to dist/
# Deploy to Vercel: `vercel`
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"
Make sure you're in the `backend/` directory when running the server.

### "Supabase connection failed"
- Check `.env` has correct `SUPABASE_URL` and keys
- Verify project is active in Supabase dashboard
- Check Network tab in browser for CORS issues

### "CORS error on frontend"
Backend CORS middleware allows `localhost:3000`, `localhost:5173`. If you're running on a different port, update `app/main.py`.

### "LLM API key invalid"
- Double-check the key in `.env` — no extra spaces
- Verify key has necessary permissions in provider console
- For Anthropic: ZDR agreement may take 24h to activate

### "Gmail OAuth not working"
- Verify redirect URL is correct in Google Cloud console
- Check `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correct
- If developing locally, OAuth redirect must be to `localhost` (not IP address)

---

## Next Steps

Once everything is running:

1. **Layer 2**: Implement embeddings and memory system
2. **Layer 3**: Build the morning brief scheduler
3. **Layer 4**: Complete agent routers and tool execution
4. **Layer 5**: Add voice loop (STT/TTS)

See [02-TRD.md](02-TRD.md) §8 for the full build order.

---

## Getting Help

- Check logs in terminal where server is running
- See [README.md](README.md) for architecture overview
- See [02-TRD.md](02-TRD.md) for technical decisions and stack rationale
- See [01-BRD-PRD.md](01-BRD-PRD.md) for the business context
