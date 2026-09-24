# Business & Product Requirements Document
## AI Chief of Staff — Working Title: "Second Brain for Business"

**Owner:** Eric Omughelli
**Version:** 1.0 — Foundational
**Date:** 23 September 2026
**Status:** Pre-build. Pilot customer identified.

---

## 1. Executive Summary

We are building an **AI Chief of Staff** for solo entrepreneurs, one-person businesses, and small teams — a voice-first, proactive AI partner that learns the business inside out and then runs the operational layer of it.

This is not a chatbot and not a dashboard. It is positioned, priced, and built as **a person, not a tool**. It wakes the user up, briefs them, answers their leads, makes and takes phone calls, writes their content, books their meetings and dinners, and tells them where their business is leaking.

**Two commercial products:**

| Product | Price | Motion |
|---|---|---|
| **SaaS (self-serve)** | $125/month | Landing page, demo video, no sales call |
| **Custom Build** | ~$3,000 setup + $500+/month retainer | Consultative, scoped per client |

**Pilot customer:** Shawn Getty, Getty Group (eXp Realty), Calgary AB.

---

## 2. The Problem

A human Chief of Staff costs $150,000–$300,000 per year. A competent executive assistant costs $60,000+. Solo operators, consultants, agents, and one-person businesses cannot afford either — so they do the work themselves, badly, at 11pm.

Specifically, what falls through:

- **Lead response time.** Inbound leads go cold because nobody answers within the window that matters.
- **Follow-up.** The second, fifth, and twelfth touch never happen.
- **Market awareness.** No time to track the industry, the competition, or the policy environment that moves their market.
- **Content.** Blogs, social, newsletters — always "next week."
- **Self-diagnosis.** Nobody tells them where the business is actually failing. They find out from the bank statement.

**Secondary problem — the one that becomes our moat:** businesses that *do* adopt general-purpose AI hand their proprietary data and intellectual property to large platforms, with no control over retention or training. They either lose control of their IP or they don't adopt at all.

---

## 3. Positioning

> **People can cut their own hair. They still go to a salon.**

Anyone *could* wire an LLM to their CRM, their calendar, their phone system. Almost nobody will. We are the salon: we build it, we connect it, we run it, we keep it updated as models, skills, and connectors improve.

**We are not selling software. We are selling a hire.**

This reframing does three things:
1. **Price anchor moves.** $125/month against other software feels expensive. $125/month against a $150k Chief of Staff feels absurd. We compete with *hiring*, not with apps.
2. **Churn drops.** People switch software casually. They do not casually replace someone who knows them.
3. **The personal layer becomes core, not decoration.** A tool waits to be opened. A person notices things.

---

## 4. Target Customer

**Primary (beachhead):** Calgary real estate agents and small teams — reached through the pilot customer's network.

**Primary (broad):** Solo operators and 1–10 person businesses with an inbound lead flow and a personal brand:
- Real estate agents and team leaders
- Consultants and coaches
- Agency owners
- Independent professionals (mortgage brokers, financial advisors, contractors)

**Secondary:** Small enterprises wanting an AI layer over their systems without surrendering IP — served through the Custom Build product.

---

## 5. Core Features

### 5.1 Onboarding Interview
A **conversation, not a form.** On signup the agent interviews the user: their business, their market, their competitors, their bottleneck, their working hours, their communication style, what they want watched — business *and* personal.

**Requirement:** Onboarding must produce the first piece of real output within the same session. The user must never see an empty dashboard.

### 5.2 The Daily Rhythm

This is the heart of the product, and the order matters.

**Evening check-in (the night before):**
- Are you training tomorrow? What time?
- What do you want to wake up to?
- Anything on your mind for tomorrow?
- Confirms tomorrow's calendar shape

**Morning sequence — the ramp:**
1. **Ground first.** Music, prayer, meditation, or motivational content — the user's own choice, captured at onboarding. *No business content in this block.*
2. **Gentle transition.** Broad shape of the day. Time until first commitment. Whether anything urgent landed overnight.
3. **The Brief** — only once the user is ready, ideally on request:
   - Calendar and commitments
   - Priority emails needing a human
   - Industry and market movement
   - Competitor activity
   - Macro/policy news *connected to business impact* (e.g. "Ottawa held rates — expect buyers to move")
   - Personal interest layer (sport, teams, whatever they follow)

**Requirement:** The system must never lead with work. Most entrepreneurs do not want to be hit with inventory statistics before they have opened both eyes.

### 5.3 Communication & Action Layer
- **Outbound calling** — the agent phones people on the user's behalf
- **Inbound calling** — it answers the user's line, qualifies, routes, and reports
- **It calls the user** — proactively, when something warrants interrupting them
- **Email** — drafts, replies, sends with approval
- **SMS / iMessage / WhatsApp / Slack**
- **Meeting booking** — negotiates times across calendars, no back-and-forth
- **Social replies** — comments, DMs, blog comments

### 5.4 Content Engine
- Blog posts and articles
- Social posts across channels
- Client reports and newsletters
- Pre-call talking points and briefing notes
- All written in the user's learned voice

### 5.5 Research & Intelligence
Four continuous streams, personalised per user. For the pilot (real estate, Calgary):
1. **Global / national market** — rates, migration, policy, buyer behaviour
2. **Local market** — inventory, days-on-market, price trends by neighbourhood
3. **Competitor tracking** — other teams and agents, listing volume, what they're doing, where the gaps are
4. **Own-business diagnosis** — response times, follow-up gaps, where leads are dying, and concrete fixes

Stream 4 is the differentiator. **Most tools tell you what happened. This one tells you what you're doing wrong.**

### 5.6 Operational Heartbeat ★
Continuous monitoring of the **vital signs of the business**, reported proactively when the rhythm goes off:
- Leads in vs. leads contacted
- Response time trend
- Listings/deals sitting too long
- Pipeline conversion by stage
- Revenue pace against target
- Recruiting conversations gone quiet
- Anomaly detection — flags drift *before* it becomes a problem

This is a named, headline feature. It is the thing that makes it a partner rather than an assistant.

### 5.7 Agent Orchestration ★
Users **create agents by describing a need in plain language** — not by picking from a menu.

> "I need something watching my competitors' listings."

The system spins up an agent with a role, a permitted toolset, and its own memory. Users can then talk to that agent directly, or have it report into the main agent. Users can convene a **meeting with multiple agents at once**.

**Ships with a standard set:**

| Agent | Job |
|---|---|
| Research | Market, industry, competitor, macro |
| Sales / Lead Qualification | Scores inbound, researches, routes or parks |
| Content | Blogs, social, newsletters, reports |
| Communications | Calls, email, SMS, scheduling |
| Operational Heartbeat | Business health monitoring, anomaly flags |
| Concierge (personal) | Restaurants, bookings, reminders, personal admin |

### 5.8 Personal Concierge
- Researches and **books restaurants by phone**
- Remembers dietary preferences of the user's clients and contacts
- Proactive: *"You've got the Hendersons closing Thursday — want me to book somewhere to celebrate?"*
- Personal reminders (birthdays, anniversaries)

**Note:** The personal features are not decoration. They are what makes the business features believable. Users do not tell their friends about lead qualification. They tell them it booked dinner and remembered their wife's birthday.

### 5.9 Memory & CRM
- Learns contacts, relationship history, every decision and the reason behind it
- Semantic recall — mention a client's name, it surfaces everything ever said about them
- Tracks owners and commitments so nothing is dropped
- Two-way sync with the user's existing CRM

### 5.10 Inbox Triage
Auto-sorts into needs-you / drafted-and-waiting / handled. Surfaces what needs a human. Suppresses the rest.

### 5.11 Value Recap
Monthly: leads handled, hours saved, meetings booked, content produced, deals influenced. **This is the renewal conversation making itself.**

---

## 6. Phase Two Features

### 6.1 Self-Building Connector Agent ★
If a customer uses software we have no connector for, a **developer agent reads that software's API documentation and writes the connector itself.**

- Must run in a sandbox and pass tests before touching live client data
- Requires human approval before production deployment
- **Why it matters:** competitors support a fixed app list. We support anything.

**Trigger to build:** when paying customers start asking for tools we don't support. Not before.

### 6.2 Cross-Client Benchmarking ★★
**The most defensible thing in this document.**

Every client's data stays private. The *patterns across clients* become an asset we own.

Once there are fifty Calgary realtors on the system, we can see what nobody else can see:
- Average lead response time in this market
- What conversion rate separates top quartile from bottom
- How fast the best performers follow up
- Which lead sources actually close vs. which just look busy

The product stops saying *"here's your data"* and starts saying:

> *"You're responding to leads in four hours. The top performers in your market do it in twenty minutes. That gap is costing you roughly three deals a month."*

**No general-purpose AI can ever say this,** because it requires the dataset. And it compounds: every new client sharpens the benchmark, which makes the product more valuable, which attracts more clients.

**Hard rule:** aggregates only. Individual client data is never exposed. Done properly this is a selling point, not a privacy risk.

---

## 7. Why This Isn't an AI Wrapper

Features get copied in a weekend. These compound:

1. **Proprietary memory.** After a year it knows every deal, every client quirk, every decision and why. A competitor can copy the interface. They cannot copy eighteen months of accumulated context. Switching cost becomes emotional, not technical.
2. **Integration depth.** Once the CRM, phone system, and accounting are wired in, ripping it out is a project nobody wants to run.
3. **Cross-client benchmarking.** Gets stronger with every customer. Structurally unavailable to general-purpose AI.
4. **The service layer.** We are not selling software, we are selling someone who manages it. That is the salon, and it does not commoditise.
5. **IP protection.** Their data stays theirs, in infrastructure we manage. The large platforms cannot offer this.

---

## 8. Business Model

### 8.1 SaaS — $125/month
- Self-serve signup, no sales call
- Full agent access, unlimited text conversation
- **30 voice exchanges/month included** — enough to fall in love with it, capped to protect margin
- Overage or upgrade beyond that
- Standard pre-built connectors

**Why 30 voice exchanges:** voice is the expensive layer (~$0.10–0.20/min all-in). Text is cheap and sits underneath as the always-available default, so nobody is ever blocked. The voice allowance is a taster of the Jarvis moment — the ones who love it upgrade themselves without being sold to.

### 8.2 Custom Build — quoted
- ~$3,000–$10,000 setup, $500+/month retainer
- Bespoke integrations into their internal systems
- Industry-specific agents
- Managed infrastructure

**Strategic note:** custom work funds SaaS development, and features built custom for one client frequently become product features for everyone.

### 8.3 Unit Economics

**At 10 SaaS + 1 Custom:**

| Line | Monthly |
|---|---|
| SaaS revenue (10 × $125) | $1,250 |
| Custom retainer | $500 |
| **Total recurring** | **$1,750** |
| Hosting, DB, Zapier | ($150) |
| Model usage (11 clients) | ($150) |
| Voice + telephony | ($200) |
| **Total cost** | **($500)** |
| **Net** | **$1,250 (~71% margin)** |

Plus ~$3,000 upfront from the custom client.

**Honest read:** this is not yet a living. The custom client carries it. That is normal and expected early.

**At 50 SaaS clients:** ~$6,250/month revenue against ~$1,000 costs — roughly **$5,000/month clear.** Costs barely move while revenue quadruples. That is where it becomes a real business.

---

## 9. Pilot Customer: Shawn Getty

**Who:** Shawn Getty, Getty Group, brokered by eXp Realty, Calgary AB.

**Track record:**
- Rookie of the Year at his brokerage
- 186 homes sold in the first half of his third year
- 60 homes in 60 days, with zero ad spend
- Grew Getty Group from 4 to 48 agents in an 8-month window

**The reframe that matters:** his public focus is **recruiting agents**, not just selling homes. He has openly described working on the main bottleneck in his business. So the pitch is *not* "help you sell more homes." It is:

> *"An agent that handles your recruiting pipeline, qualifies prospective agents, follows up automatically, and briefs you before every recruiting conversation."*

**Known personal layer:** Canadian politics — which for him is business-relevant, not trivial. Interest rate decisions, housing policy, and immigration targets all move Calgary real estate directly. His brief connects the two. Sport and personal interests sit at the end of the brief.

**Unknown:** his current CRM. Not public — must be asked directly. Likely candidates with existing connectors: Follow Up Boss, Real Geeks, kvCORE, CINC, RealScout, Zillow Tech Connect.

**Pilot offer:** free for one month as founding pilot, in exchange for honest feedback and — if it works — a testimonial and appearance in the promo video.

**What we need from him:** one hour of his time, and CRM access.

---

## 10. User Journey — Shawn, End to End

**Day 1 — Signup.** Lands in a conversation, not a form. Asked about his business, his team, his market, his bottleneck, what he wants watched (including Canadian politics and sport). Fifteen minutes. Feels like talking to a new hire.

**Day 1, within the hour — First brief.** Calgary market snapshot, one competitor note, something out of Ottawa that affects housing. Value delivered before he has done anything.

**Day 2 — Connection.** CRM and calendar wired in. The agent starts answering inbound leads, qualifying them, and following up on the ones going cold.

**End of Week 1 — The click.** It briefs him before a recruiting call with everything it knows about that agent prospect. This is the moment it stops being software.

**Week 2 onward — It speaks first.** Flags that his response times have slipped. Notes a competitor's listing volume jumped.

**Month 1 — The recap.** Leads handled, hours saved, conversations booked. Renewal sells itself.

---

## 11. Security, Privacy & Governance

Given that IP protection is a core selling point, this is product, not overhead.

- **Data isolation** — row-level security; each client's data physically separated
- **Zero data retention** agreements with model providers; **no training on customer data**. This is the IP promise, in writing.
- **Audit logging** on every agent action — a record of what the AI did, when, and on whose instruction
- **Role-based access control**
- **Secrets in a managed vault**, not scattered environment variables
- **Approval gates** on any action that writes to a client system or sends on their behalf
- **Sandbox testing** for any auto-generated connector before production

**SOC 2 is deliberately deferred.** It costs $15–20k and is a sales unlock for enterprise deals — solo realtors will never ask for it. But the underlying practices above are implemented from day one, so certification later is a documentation exercise, not a rebuild.

---

## 12. Open Questions

1. What CRM is Shawn actually using?
2. Where exactly should the voice allowance cap sit after real pilot usage data?
3. Does the upgraded heavy-voice tier become a third price point, or an overage line on the existing two?
4. Product name — not yet decided.
5. Legal entity, T&Cs, and data processing agreement for the IP promise.

---

## 13. Decisions Locked

- ✅ Two products: self-serve SaaS + quoted Custom Build. Not three tiers.
- ✅ $125/month SaaS (revised up from $80 — underpriced against the "chief of staff" story)
- ✅ 30 voice exchanges included; text always available underneath
- ✅ Voice-first, proactive, personal-then-business morning ramp
- ✅ Operational Heartbeat as a named headline feature
- ✅ Cross-client benchmarking as the long-term moat
- ✅ Shawn Getty as pilot, positioned on recruiting not home sales
- ✅ SOC 2 deferred; underlying security practices from day one
- ✅ Zapier as the initial connector layer, replaced with direct APIs at ~10 customers
- ✅ Self-building connector agent is Phase 2, not week one
