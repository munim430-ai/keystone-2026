# Keystone Voice Agent 🎧

An autonomous, Bangla-speaking AI sales caller for **Keystone Education**'s B2B
outreach — it phones IELTS/Korean/language coaching centers across Bangladesh,
pitches the ৳5,000-per-student referral partnership in warm, natural Bangla,
handles objections, captures WhatsApp numbers, and logs every call to a
dashboard. Built so one solo operator can work a 859-center list without a
human calling team.

> **Ships demo-safe.** With zero API keys it runs entirely on mock
> STT/LLM/TTS and places **no real phone calls**. You rehearse the whole
> system for free, then flip `DEMO_MODE=0` when you're ready to go live.

```
 Twilio  ──audio──▶  VAD  ──▶  STT  ──▶  LLM brain (+tools)  ──▶  TTS  ──audio──▶  Twilio
 (phone)            (utterance)  (Bangla)   (Groq / NIM)          (Sarvam)         (caller)
                                              │
                                     SQLite  ◀┘  ──▶  Dashboard (live calls, funnel, kill switch)
```

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for the full stack, latency budget,
and honest cost model, **[TESTING.md](TESTING.md)** for the 5-phase go-live
protocol, and **[OPERATIONS.md](OPERATIONS.md)** for the 859-center calling
plan, compliance guardrails, and runbook.

---

## Quick start (demo mode — no keys, no calls)

```bash
cd voice-agent
python -m venv .venv && source .venv/bin/activate     # optional
pip install -r requirements.txt

cp .env.example .env                 # defaults are demo-safe (DEMO_MODE=1)

python -m keystone_voice.cli init-db
python -m keystone_voice.cli import-centers            # loads ../data/IELTS_Partners_Tier2.csv
python -m keystone_voice.cli status

# rehearse the brain in your terminal (type as the center owner, in Bangla):
python -m keystone_voice.cli console

# or run the web dashboard:
python -m keystone_voice.cli serve                     # http://127.0.0.1:8080
```

In the dashboard, **Call next** simulates a dial (no PSTN) so you can watch the
funnel, transcripts, and kill switch behave before spending a taka.

---

## Going live (real calls)

You need three accounts (all pay-as-you-go, no subscriptions):

| Service | Purpose | Rough cost |
|---------|---------|-----------|
| **Twilio** | outbound telephony + call recording | ~$0.04–0.05/min to BD |
| **Groq** *(or NVIDIA NIM)* | the LLM brain (Llama 3.3 70B) + Whisper STT | ~$0.02/call |
| **Sarvam** | Bangla TTS (Bulbul) — and optionally Bangla STT (Saarika) | ~$0.06/call |

1. Fill the keys in `.env` and set `DEMO_MODE=0`.
2. Expose your laptop so Twilio can reach it:
   `ngrok http 8080` → put the hostname in `PUBLIC_HOST`.
3. Warm the audio cache: `python -m keystone_voice.cli pregen`.
4. **Run the [testing protocol](TESTING.md) — do not skip it.** Start with a
   self-test call to your own phone:
   `python -m keystone_voice.cli test-call` (needs `OPERATOR_PHONE`).
5. When Tests 1–5 pass, start dialing at 20/day from the dashboard.

`python -m keystone_voice.cli status` always tells you exactly what's still
missing before live calls can go out.

---

## Commands

```
keystone-voice init-db                 create the SQLite database
keystone-voice import-centers [--csv]  import the scraped centers list
keystone-voice status                  funnel + go-live readiness
keystone-voice serve                   web server + dashboard
keystone-voice console [--center ID]   text simulator of a call (free)
keystone-voice pregen                  pre-generate cached audio clips
keystone-voice test-call               single self-test call to OPERATOR_PHONE
keystone-voice kill [--resume]         engage / release the kill switch
keystone-voice export centers|calls    export data to CSV
```

## Safety & honesty (built in, not optional)

- **Never denies being an AI.** If asked, she admits it and continues — see the
  hard rules in `keystone_voice/brain/persona.py`.
- **One consistent caller ID.** No number rotation (that's a robocaller
  pattern and violates carrier policy).
- **Business-hours only** (10–18 Dhaka, Friday prayer window skipped), daily
  cap, min-gap pacing, per-center attempt limit, and instant kill switch.
- **DNC honored** — "don't call again" permanently parks the center.
- No fabricated guarantees, no PII harvesting beyond a business WhatsApp number.

## Layout

```
voice-agent/
├── keystone_voice/
│   ├── config.py         env-driven config + go-live readiness check
│   ├── audio.py          mu-law codec, resampling, framing (numpy)
│   ├── vad.py            energy VAD + utterance segmentation
│   ├── db.py             SQLite: centers, calls, transcripts, callbacks
│   ├── telephony.py      Twilio calls + Media Streams protocol
│   ├── stt/              Groq-Whisper · Sarvam-Saarika · mock
│   ├── llm/              Groq / NVIDIA-NIM (OpenAI-compatible) · mock
│   ├── tts/              Sarvam Bulbul (prosody control) + cache · mock
│   ├── brain/            persona prompt · state machine · tool schemas
│   ├── agent.py          one LLM round incl. tool execution
│   ├── session.py        the real-time call loop (barge-in, fillers)
│   ├── scheduler.py      business hours, caps, pacing, callbacks
│   ├── app.py            FastAPI: webhooks, media WS, dashboard API
│   └── cli.py            command-line entry point
├── dashboard/index.html  single-file monitoring UI
├── tests/                36 tests (audio, VAD, DB, state machine, pipeline…)
└── docs → ARCHITECTURE.md · TESTING.md · OPERATIONS.md · VOICE_CLONING.md
```
