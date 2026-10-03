# AI Chief of Staff — React + TypeScript Frontend

A ring-first voice interface for real estate agent operations, featuring:

- **Home** — Interactive voice ring (idle/listening/speaking states) with morning briefs & metrics
- **Business Health** — Deal pipeline and status overview
- **Today** — Daily briefing and agenda
- **Approvals** — Pending approvals with approve/deny workflow
- **Agents** — AI agent status and activity

## Quick Start

### Install dependencies
```bash
cd frontend
npm install
```

### Run dev server
```bash
npm run dev
```
Opens at `http://localhost:5173`

### Type checking
```bash
npm run type-check
```

### Build for production
```bash
npm run build
```
Output in `frontend/dist/`

## Architecture

### Mock Data → Real API
- **Now:** All data in `src/mocks/mockData.ts`, served by `src/services/api.ts`
- **Later:** Update `useMockData = false` in `api.ts` to swap to real FastAPI endpoints

API endpoints to build:
- `GET /api/briefs` — Morning briefs
- `GET /api/agents` — Agent list and status
- `GET /api/approvals` — Pending approvals
- `POST /api/approvals/{id}/approve` — Approve
- `POST /api/approvals/{id}/deny` — Deny
- `GET /api/deals` — Deal pipeline

### File Structure

```
src/
  components/          # Reusable components
    Ring.tsx          # Voice state ring (idle/listening/speaking)
    Nav.tsx           # Bottom navigation bar
  pages/              # Full pages
    Home.tsx          # Ring + briefs + metrics
    BusinessHealth.tsx
    Today.tsx
    Approvals.tsx
    Agents.tsx
  services/
    api.ts            # Typed API functions, currently mock
  mocks/
    mockData.ts       # Getty Group demo data
  types/
    index.ts          # TypeScript types (Brief, Agent, Approval, Deal, etc)
  App.tsx             # Main router & layout
  main.tsx            # React entry point
```

### Styling

- **Theme:** Dark cyan (#00d4ff accent) matching CLAUDE.md theme
- **Colors:** 
  - Background: `#0a0a1a`
  - Panels: `#0d1117`
  - Accent: `#00d4ff` (cyan)
  - Status: green (#44c98f), red (#e74c3c), orange (#ff6b35)
- **Responsive:** CSS Grid, mobile-first (cards stack on narrow viewports)

### Ring Component

The `<Ring>` component drives voice interaction:

```tsx
<Ring state="idle|listening|speaking" onClick={handleClick} />
```

States:
- **idle** — Static ring with subtle glow, ready for input
- **listening** — Pulsing ring + expanding waves
- **speaking** — Animated waveform + inner glow, AI responding

Canvas-based rendering for smooth animations. Prop-driven so voice layer can control state later.

## Getty Group Demo Data

All mock data reflects Getty Group's real estate business:
- 3 active deals (Chen family, Lopez, Mitchell)
- 5 AI agents (Lead Qualifier, Follow-up Master, Email Composer, Calendar Manager, Market Analyst)
- 3 pending approvals (email, message, action)
- Morning briefs with market updates and follow-up reminders

## Next Steps

1. **Wire FastAPI backend** — Update `api.ts` to hit real endpoints
2. **Add voice integration** — Wire ring state to STT/TTS (Layer 5)
3. **Approval persistence** — Save approved/denied decisions to database
4. **Agent details** — Add agent conversation history & logs
5. **Analytics** — Add charts/metrics to Business Health page

---

Built with React 18 + TypeScript 5 + Vite 5. Configured for zero-data-retention with LLM providers via CLAUDE.md.
