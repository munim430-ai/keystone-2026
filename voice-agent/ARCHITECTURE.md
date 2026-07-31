# Architecture — Keystone Voice Agent

**Deliverable 1.** Exact stack, data flow, latency budget, hardware allocation,
and cost. This describes the system as built in `voice-agent/`.

---

## 1. Stack

| Layer | Component | Where it runs | Notes |
|-------|-----------|---------------|-------|
| Telephony | **Twilio Programmable Voice + Media Streams** | cloud | bidirectional mu-law 8 kHz over WebSocket; outbound to BD mobiles |
| Ingress | **FastAPI + Uvicorn** (`app.py`) | operator laptop (32 GB) | webhooks + media WS + dashboard API, one async process |
| VAD | energy detector w/ adaptive noise floor (`vad.py`) | laptop | pure numpy, ~0 ms |
| STT | **Groq Whisper large-v3** *(default)* or **Sarvam Saarika** | cloud API | Bangla + code-switching |
| Brain | **Groq Llama 3.3 70B** *(default)* or **NVIDIA NIM** | cloud API | OpenAI-compatible, tool calling |
| TTS | **Sarvam Bulbul v2/v3** | cloud API | Bangla, prosody control, 8 kHz out |
| State/logs | **SQLite** (WAL) (`db.py`) | laptop | centers, calls, turns, callbacks |
| Dashboard | single-file HTML/JS (`dashboard/index.html`) | laptop browser | polls REST API every 3 s |
| Audio codec | G.711 mu-law + linear resample (`audio.py`) | laptop | numpy; no `audioop` (gone in 3.13) |

Language: **Python 3.10+**, fully async. No GPU required for the core loop
(F5-TTS voice cloning is an optional Phase-2 add-on — see
[VOICE_CLONING.md](VOICE_CLONING.md)).

Everything is **provider-swappable** behind small interfaces (`stt/`, `llm/`,
`tts/`), and every provider has a **mock** so the whole system runs with zero
keys and places no real calls (`DEMO_MODE=1`).

---

## 2. Data flow (one turn)

```
caller speaks
   │  Twilio media frames  (mu-law 8 kHz, 20 ms, base64, over WS)
   ▼
CallSession.feed_ulaw()  ── decode → PCM16 → VAD.feed()
   │                                   │
   │                         (barge-in: caller talks over agent →
   │                          clear outbound queue, cancel TTS)
   ▼  utterance (silence-terminated)
STT.transcribe()  → Bangla text
   ▼
SalesAgent.respond()
   │  build messages: [system persona] + history + [stage guide]
   │  LLM.chat(tools=…)  ──▶ text + tool_calls
   │     tool_calls → dispatch(): set_stage · capture_whatsapp ·
   │        schedule_callback · mark_outcome · transfer_to_human · end_call
   │        (writes straight to SQLite; updates ConversationState)
   ▼  reply text (sanitized: no markdown/emoji, Bangla digits)
TTS.synth(text, prosody[stage])  → mu-law 8 kHz   (cache hit = 0 API calls)
   ▼
CallSession._speak()  → 20 ms frames → Twilio  (real-time paced)
   ▼
caller hears the agent
```

A short **filler clip** ("জি জি, শুনছি…") plays if the LLM+TTS round exceeds
`FILLER_AFTER_MS`, so the caller never hears dead air. Two unanswered silence
prompts end the call gracefully.

---

## 3. Latency budget

Target from the mission: **< 1.5 s** end of caller speech → start of agent
audio. Budget with the default cloud providers:

| Step | Typical | Notes |
|------|---------|-------|
| VAD endpointing | `VAD_SILENCE_MS` = 600 ms | tunable; this is the "did they stop talking" wait, not compute |
| STT (Groq Whisper) | 150–350 ms | 16 kHz upsample, `language=bn` |
| LLM first token (Groq 70B) | 200–400 ms | short replies (`max_tokens≈300`) |
| LLM full short reply | +100–250 ms | 1–3 sentences |
| TTS (Sarvam Bulbul, cache miss) | 200–500 ms | cache hit = ~0 |
| Framing + network | ~50 ms | |
| **Total after endpointing** | **~0.7–1.5 s** | within target; fillers hide the tail |

Levers when it's tight: lower `VAD_SILENCE_MS`, keep replies short (already
enforced in the persona), pre-generate more phrases (`pregen`), or move STT to
Sarvam if Groq is far from BD.

---

## 4. Hardware allocation

| Machine (operator's) | Role |
|----------------------|------|
| **Laptop 1 — 32 GB RAM, 4 GB VRAM** | the server: FastAPI, VAD, SQLite, dashboard, audio buffering. The 4 GB VRAM is idle unless you enable F5-TTS voice cloning (Phase 2). |
| **Laptop 2 — 16 GB RAM** | backup / monitoring — open the dashboard here, or run a warm standby. |
| **Android phone** | the receiving end for Test-1 self-calls. |

The heavy lifting (STT/LLM/TTS inference) is all cloud API, so the laptop only
orchestrates. One process comfortably handles the concurrent-call counts a
solo operator will run (1–3 at a time within the daily cap).

---

## 5. Cost per call (honest)

Per ~3-minute call, using pay-as-you-go rates (verify current pricing — these
are 2026 ballpark figures, **not quotes**):

| Component | ~Cost/call |
|-----------|-----------|
| Twilio outbound to BD mobile (~3 min) | $0.12–0.15 |
| STT | $0.02–0.06 |
| LLM (Groq 70B, short turns) | $0.01–0.02 |
| TTS (Sarvam, cache warm) | $0.03–0.06 |
| **Total** | **~$0.20–0.28** |

**859 centers × ~$0.25 ≈ $215**, plus setup/testing ≈ $50 → **~$265** to work
the entire list once.

> ⚠️ **On the mission's ROI figure.** The "2,828% ROI" assumes a 10% partner
> conversion and 2 students/partner/year converting to enrollment. Those are
> *hopeful* assumptions, not forecasts — real B2B cold-call-to-partner rates
> are usually low single digits, and partner→enrolled-student is its own
> funnel. Treat the cost side ($265 to reach everyone) as solid and the
> revenue side as a hypothesis to validate with the Test-5 pilot before
> scaling spend. The system is deliberately cheap so the downside is bounded.

Telephony dominates cost, so the biggest lever is **conversation quality**
(shorter dead-ends, better targeting of Korean-language centers first), not
shaving fractions of a cent off the AI.

---

## 6. Concurrency & failure model

- Each call is one `CallSession` bound to one Media Streams WebSocket; sessions
  are independent async tasks. The daily cap and min-gap keep concurrency low.
- Provider calls have timeouts and one retry; an LLM failure ends the turn
  gracefully rather than hanging the call.
- The **kill switch** (`db.killed`) is checked every loop iteration and before
  every dial; flipping it stops new dials and wraps up active calls politely.
- SQLite in WAL mode tolerates the dashboard reading while calls write.
- Notifications (Telegram) are best-effort and never block a call.
