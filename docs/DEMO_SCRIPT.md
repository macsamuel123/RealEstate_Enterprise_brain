# AI Chief of Staff Demo Script for Shawn Getty

**Pilot Org:** Getty Group (eXp Realty, Calgary)
**Duration:** 15-20 minutes
**Goal:** Show agent orchestration, voice interaction, approval flow

---

## Setup

```bash
# Reset to clean demo state
python backend/scripts/reset_demo.py

# Start backend + frontend
cd backend && python -m uvicorn app.main:app --reload
cd frontend && npm run dev
```

**Expected state after reset:**
- Org: Getty Group (Calgary)
- 20 fictional agent-recruit prospects
- 30 leads in pipeline
- 10+ past conversations with memories
- 3 recruits silent 10+ days (anomaly detected)
- Response time drifted (target 60 min, actual 85 min)
- 2 PM recruiting call scheduled (rich history available)

---

## 7 Demo Scenes

### Scene 1: Morning Brief (2 min)
**"Here's what happened overnight, Shawn"**

Visit dashboard → Morning Brief widget shows:
- 🎯 Personal: "Your Stampeders play Calgary at 7pm tonight"
- 💼 Business:
  - **Market Alert:** "BoC cut rates 50bps; expect ~3% more motivated sellers in SE Calgary next quarter"
  - **Competitor:** "Davids Group hired 2 new agents this week (vs 0 last month)"
  - **Anomaly:** "3 recruits silent 10+ days (Marcus, Jen, Chris) — follow-up overdue"
  - **Health:** "Response time +25min this week (now 85 min); leads waiting"

**Agent orchestration behind the scenes:**
- Memory Scribe recalled personal interests (Stampeders fan)
- Research Agent did live web_search (Calgary real estate + BoC news)
- Heartbeat Agent detected response time drift
- Orchestrator synthesized into brief

**What to say:** "This is what the AI learned about you and your market overnight. All this from agents working together silently."

---

### Scene 2: Voice Command (3 min)
**"Talk to the Chief of Staff"**

Click Voice Command widget → Speak:
> "What's the status with my recruiting pipeline?"

**Expected orchestration:**
1. STT (Whisper) → "What's the status with my recruiting pipeline?"
2. Orchestrator (Haiku) → "User wants pipeline status → delegate to Pipeline Agent"
3. Pipeline Agent:
   - crm_read → get all deals with stage="lead" (30 results)
   - memory_search → recruits, hiring goals, hiring history
   - crm_read filtered → 3 stalled recruits (Marcus, Jen, Chris, silent 10+ days)
4. Synthesizer (Sonnet) → "You have 30 leads in pipeline. Good news: 12 qualified this week. Concern: 3 recruits went silent — they were interested but you haven't touched base in 10 days. Recommend: quick personal call today."
5. TTS (ElevenLabs) → Audio response

**Dashboard updates:**
- Waveform animates during listening
- Transcript appears in real-time
- Response audio plays back
- Agent Squad shows "Pipeline Agent" active, then "Communications Agent" drafting

**What to say:** "Every word Shawn speaks gets routed through agents. No CRM clicking — just voice."

---

### Scene 3: Approval Queue (2 min)
**"Here's what needs your sign-off"**

Show Approval Queue widget with 3 pending items:
1. **Email Draft** (from Scene 2)
   - To: marcus@example.com
   - Subject: "Quick catch-up?"
   - Body: "Hey Marcus, we've been meaning to connect. Free for a 15-min call this week? —Shawn"
   - Status: "Draft ready for approval"

2. **CRM Update**
   - Contact: Marcus Chen
   - Field: last_contact_date → today
   - Status: "Will be logged after email approval"

3. **Calendar Event** (from pre-call setup)
   - Title: "Call with Marcus Chen (Recruiting)"
   - Time: "Today 3 PM"
   - Duration: 15 min

**Interaction:**
- Tap "Approve" on email
- System: "Sending..." (1 sec)
- Email sent, CRM updated, calendar blocked
- New notification: "Email sent + logged to actions_log"

**What to say:** "Every write is gated. You stay in control. Each action gets audited for compliance."

---

### Scene 4: Web Lead Form (2 min)
**"Watch a lead come in and get qualified in <10 seconds"**

**Setup:** Open browser side-by-side
- Left: Lead form (demo-form.html)
- Right: Dashboard → Recent Activity log

**Action:** Fill out lead form:
```
Name: "Sarah Johnson"
Email: sarah@example.com
Phone: 403-555-0123
Interest: "3-bed home, SW Calgary, $450-500k, 60 days"
Message: "Moving for work, need quick closing"
```

**Hit Submit** → Watch the orchestration:

1. **Webhook received** (0s)
   - Pipeline Agent dispatched
   - Recent Activity: "New lead: Sarah Johnson"

2. **Lead qualified** (2s)
   - Pipeline Agent runs:
     - web_search: "SW Calgary market, $450-500k range"
     - crm_read: Shawn's recent sales in that area
     - memory_search: "Moving for work" sentiment
   - Score: 8/10 (urgent timeline, motivated)
   - Recent Activity: "Lead qualified (8/10)"

3. **Draft reply** (4s)
   - Communications Agent:
     - email_draft: Personalized response using memory context
   - Recent Activity: "Reply drafted"

4. **Approval** (6s)
   - Dashboard shows notification
   - Tap "Approve" one-tap
   - Recent Activity: "Email approved + sent to Sarah"

**Total: <10 seconds from form to qualified + reply drafted + approved**

**What to say:** "Leads come in hot. By the time you finish your coffee, it's qualified, responded, and logged. No lost time."

---

### Scene 5: Pre-Call Briefing (2 min)
**"Before a call, get everything you need"**

**Setup:** Incoming call scheduled for 2 PM (recruiting prospect)

**Action:**
1. Click Recent Activity → "Incoming call in 5 min with Marcus Chen"
2. Dashboard shows **Pre-Call Briefing** popup:
   ```
   INCOMING CALL: Marcus Chen
   
   BACKGROUND:
   - Recruiter prospect, 3 years exp, interested Jan 2024
   - Silent 10+ days (anomaly flagged)
   - Last conversation: "Wants to join your team but worried about desk costs"
   
   RECENT:
   - You closed 4 deals this month (vs 2 average)
   - Market: SW Calgary hot (12% inventory ↓)
   - Competitor: Davids Group hired 2 agents this week
   
   MEMORY:
   - Marcus: Family man, 2 kids, loves golf
   - Concern: "Don't want to abandon current brokerage"
   - Interest: "Your reputation for lead quality"
   
   SUGGESTED OPENING:
   "Hey Marcus! Been a few days. How's the family? I've got an update on our team structure that addresses your desk-cost concern..."
   ```

3. **Tap "Answer"** → Voice call begins (or mock audio)
   - Agent briefing stays visible
   - You can ask the Chief of Staff mid-call if needed
   - All conversation recorded + stored

**What to say:** "You walk in informed. The AI read 6 months of history in 2 seconds. You just close."

---

### Scene 6: Voice Call Conversation (5 min)
**"Real-time agent in the call"**

During mock call (or real call via Vapi/Retell):

**You speak:** 
> "Marcus, great to hear from you. So, we've updated our desk structure. What questions do you have?"

**Chief of Staff (invisible agent):**
- Listens to conversation
- Detects key moments:
  - "We value lead quality" → Research Agent flags market insights
  - "Concerned about costs" → Pipeline Agent searches past desk-cost discussions
  - "My family..." → Memory Scribe captures family details for next time
- **Mid-call capability:** Say "Chief of Staff, what's his current team at Davids Group?"
  - Agent: (pause) "You're in a call. That search will be logged. Continue when ready."

**After call (30 sec later):**
- Dashboard notification: "Call ended. Summary drafted."
- Recent Activity shows:
  - "Call with Marcus Chen (15 min)"
  - "Outcomes: Discussed desk costs, addressed lead-quality concern, Marcus interested in trial. Next step: send desk structure docs."
  - **Drafts prepared:**
    - Email: "Sending desk structure + comp chart"
    - Calendar: "Follow-up call, Wed 2 PM"
    - Memory: "Marcus likes lead quality over brand loyalty"

**Tap "Approve"** → All actions logged

**What to say:** "That call was just you + the voice assistant. No transcription, no notes app. Everything is remembered, everything is logged."

---

### Scene 7: Custom Agent (2 min)
**"Create a watcher agent in 30 seconds"**

**Setup:** Show Agent Builder tool

**Action:**
Speak or type:
> "Create an agent that watches Davids Group job postings and alerts me when they hire agents in the NW."

**Agent Builder response:**
```
I'll create: "Davids Group Watcher"

This agent will:
- Daily: web_search for "Davids Group Calgary hiring"
- Check: LinkedIn, eXp Realty postings, local news
- Alert you if: New hire detected in NW Calgary
- History: Track hires over time
- Scheduled: 9 AM daily, report in morning brief

Ready to activate? (Approve/Deny)
```

**Tap "Approve"** → Agent created, runs tomorrow morning

**What to say:** "You don't hire engineers to build your own features. The AI does it for you in plain English."

---

## Demo Script Walkthrough (20 min)

### Suggested Pacing
1. **Open dashboard** (30 sec) → Show JARVIS aesthetic
2. **Morning Brief** (2 min) → Explain agent orchestration
3. **Voice Command** (3 min) → Speak a question, watch orchestration
4. **Approval Queue** (2 min) → Show approval flow
5. **Lead Form** (2 min) → Simulate incoming lead, watch <10s flow
6. **Pre-Call Briefing** (2 min) → Show context before call
7. **Voice Call** (5 min) → Optional: do a real call or mock
8. **Custom Agent** (1 min) → Show extensibility

**Total: ~20 minutes**

### Key Talking Points

**Problem:** Real estate agents spend 30% of time on admin (CRM, email, follow-up, research). Chaos when leads come in.

**Solution:** "Chief of Staff" AI that works silently in the background. You talk to it like a person. It qualifies leads in <10s, remembers everything, routes approvals to you.

**Why it matters:**
- Leads don't wait (response time = conversion)
- You stay in control (approval gates, audit trail)
- Memory compounds over time (switching cost for competitors)
- Voice-first (better than CRM clicking)

**Business model:**
- SaaS: $125/month
- Custom: Quote-based (for teams, CRM integration)

---

## Reset Command

```bash
# Restore demo state
python backend/scripts/reset_demo.py --org getty-group

# What it does:
# 1. Delete all data for Getty Group org
# 2. Create fresh org: Getty Group, Shawn Getty (owner)
# 3. Seed 20 recruits (3 flagged as silent)
# 4. Seed 30 leads (mix of qualified, pipeline, lost)
# 5. Seed 10+ conversations + memories
# 6. Set response_time baseline to 85 min (anomaly)
# 7. Schedule 2 PM recruiting call (Marcus Chen)
# 8. Seed web_search results for Calgary market
```

---

## Troubleshooting

**Voice not working?**
- Check OPENAI_API_KEY, ELEVENLABS_API_KEY in .env
- Fallback: Play pre-recorded audio instead

**Lead form not showing?**
- Ensure backend /api/lead/form endpoint is live
- Check webhook URL in form action

**Agent not delegating?**
- Check logs: `docker logs chief-of-staff-backend`
- Verify agent records exist in database
- Test with direct API call: `curl http://localhost:8000/api/demo/test-delegation`

**Approval queue empty?**
- Run reset command
- Trigger a draft action (voice, lead form, etc)

---

## Post-Demo: Next Steps with Shawn

1. **"What would make this real for you?"**
   - Does he want to connect his actual CRM?
   - Which phone number should agents use?
   - Any specific workflows he needs?

2. **"Let's run a pilot"**
   - 1 week: He uses it with real leads
   - We gather metrics: response time, lead quality, agent accuracy
   - We iterate based on feedback

3. **"Then we make you the case study"**
   - Document his metrics (before/after)
   - Feature him in our landing page
   - Launch SaaS with his testimonial

---

## Demo Checklist

- [ ] Backend running (http://localhost:8000)
- [ ] Frontend running (http://localhost:5173)
- [ ] Database seeded (reset_demo.py ran)
- [ ] OpenAI API key valid
- [ ] ElevenLabs API key valid
- [ ] Lead form HTML ready (docs/demo-form.html)
- [ ] Vapi/Retell account set up (optional, for real voice)
- [ ] Mobile phone ready for approval page test
- [ ] Screenshots/recording software ready (optional)
- [ ] Backup internet connection (hotspot)

---

**Goal: Show Shawn what's possible. Make him want to pilot. Make him the case study.**
