# Challenges & Solutions — AI Chief of Staff Build

## Challenge 1: API Proxy Configuration

**Problem:**
- Frontend dev server (port 5173) needs to call backend (port 8000)
- Vite has a proxy feature for development
- Initial config had `rewrite: (path) => path.replace(/^\/api/, '')` which stripped `/api` prefix
- Frontend calls `/api/transcribe` → proxy strips `/api` → backend gets `/transcribe` (404)
- Backend router defined as `APIRouter(prefix="/api", ...)` expected `/api/transcribe`

**Mismatch:**
```
Frontend wants:     /api/agent
Proxy rewrites to:  /agent  (wrong!)
Backend expects:    /api/agent
```

**Solution:**
Removed the `rewrite` rule from vite.config.ts proxy:
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true
    // Don't rewrite — keep /api prefix intact
  }
}
```

Now: `/api/agent` → forwarded as `/api/agent` ✓

**Lesson:** Dev proxies are powerful but require careful configuration. The prefix should be consistent between frontend, proxy, and backend router definitions.

---

## Challenge 2: Backend Configuration Required Fields

**Problem:**
- Backend config.py required all API keys (Supabase, Anthropic, OpenAI, ElevenLabs, Twilio, Stripe)
- No `.env` file in repo (intentional for security)
- Dev couldn't start backend without all keys filled in
- Blocked testing of voice flow without real API credentials

**Initial Error:**
```
pydantic_core._pydantic_core.ValidationError: 15 validation errors for Settings
supabase_url: Field required
anthropic_api_key: Field required
...
```

**Solution:**
Made all fields optional with `Optional[str] = None` defaults:
```python
# Before: required
supabase_url: str

# After: optional, dev-friendly
supabase_url: Optional[str] = None
```

Backend now starts in dev mode without `.env` file. Created lazy database initialization — Supabase client only created if URL + key are provided.

**Lesson:** Dev/prod split needed from day one. Use environment-based config (development mode = permissive, production = strict).

---

## Challenge 3: Authentication Middleware Import Error

**Problem:**
```
ImportError: cannot import name 'HTTPAuthCredentials' from 'fastapi.security'
```

- Middleware tried to import `HTTPAuthCredentials` which doesn't exist in FastAPI
- Should be `HTTPAuthorizationCredentials`
- Typo in auth middleware blocked backend startup

**Solution:**
Changed import:
```python
# Wrong
from fastapi.security import HTTPBearer, HTTPAuthCredentials

# Correct
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
```

**Lesson:** Pin exact versions and validate imports against FastAPI docs. IDE autocomplete can mislead.

---

## Challenge 4: Auth Requirement Blocked Local Testing

**Problem:**
- `/api/agent` endpoint required `verify_token` dependency
- No auth system set up yet (Supabase Auth integration incomplete)
- Couldn't test conversational agent without authentication
- Blocked end-to-end testing of voice flow

**Solution:**
Removed auth requirement for dev testing:
```python
# Dev version (no auth)
@router.post("/agent")
async def agent(req: AgentRequest):
    org_id = "org_getty_group"  # Mock for testing
    user_id = "user_shawn_getty"
```

Once Supabase Auth is wired, will add `current_user = Depends(verify_token)` back.

**Lesson:** Separate dev and prod code paths. Don't let auth block feature testing. Use mock values in dev.

---

## Challenge 5: Vite Dev Server Not Picking Up Config Changes

**Problem:**
- Changed vite.config.ts proxy rules
- Dev server kept using old config
- Frontend still hitting its own port instead of proxying to backend

**Solution:**
Restart dev server after config changes:
```bash
# Stop: Ctrl+C
# Start fresh: npm run dev
```

**Lesson:** Vite (and most bundlers) cache config. Always restart when changing vite.config.ts, not just for code changes.

---

## Summary of Build Order Decisions

1. **Start with auth-optional** → lets you test features before auth is ready
2. **Separate config (dev vs prod)** → dev is permissive, prod is strict
3. **Test endpoint routing early** → proxy + backend router alignment matters
4. **Use mock data + mock org IDs** → removes dependency on live systems
5. **Document import errors** → FastAPI has naming quirks (HTTPAuthorizationCredentials)

---

## Next Challenges Expected

- **Supabase integration** — RLS policies, real org/user auth
- **Tool execution** — wiring calendar, CRM, email APIs
- **Conversation state** — keeping multi-turn context in memory
- **Voice latency** — STT→agent→TTS under 500ms target
