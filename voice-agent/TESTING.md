# Testing Protocol — go-live gate

**Deliverable 5 (testing half).** No real center calls until every phase
passes. The system enforces the spirit of this by shipping in `DEMO_MODE=1`;
you consciously flip it off only after Test 1.

Before any of this, the free checks that need **no keys and no calls**:

```bash
python -m pytest -q                       # 36 automated tests must be green
python -m keystone_voice.cli console      # rehearse the brain by typing in Bangla
```

The console simulator runs the *exact* brain used on real calls, so tune the
persona, objection handling, and hooks here first — it costs nothing.

---

## Test 1 — Self-test (human-ness ≥ 7/10)

**Goal:** the agent sounds like a real person to you.

```bash
# .env: DEMO_MODE=0, Twilio + Groq + Sarvam keys set, PUBLIC_HOST via ngrok,
#        OPERATOR_PHONE = your number
python -m keystone_voice.cli pregen        # warm the audio cache first
python -m keystone_voice.cli test-call     # calls your own phone
```

Answer, role-play a center owner for ~3 minutes. Rate human-ness 1–10 from the
recording (dashboard → call → ▶). **Need 7+ to proceed.** If it's robotic:
adjust prosody in `brain/state_machine.py`, shorten replies in the persona, or
pre-generate more phrases.

## Test 2 — Friend test (≥ 80% "sounds real")

Call 5 friends/family, each role-playing a different owner personality:
interested, skeptical, rude, busy, confused. **≥ 80% must say "sounds like a
real person."** Watch how it recovers from interruptions and off-script replies.

## Test 3 — Hook A/B (pick the winner)

Try 3 opening hooks across 15 test calls (5 each). Edit the greeting/hook lines
in `brain/persona.py` (`canned_lines` + hook stage guide). Compare conversation
duration and how many reach the PITCH stage (dashboard shows `final_stage`).
Keep the winner.

## Test 4 — Stress test (graceful under chaos)

On test calls, deliberately: interrupt mid-sentence (barge-in should cut her
off), stay silent 5 s (she re-prompts, then exits politely), talk very fast,
and use heavy regional dialect. She must handle all four without crashing,
talking over you, or looping.

## Test 5 — Pilot (10 real centers)

Dial **10 real centers** from the list. Listen live or review recordings.

- **≥ 3 show genuine interest** → scale to 20/day.
- **0–1 interested** → stop, fix (targeting? hook? offer clarity?), retest.

Start the pilot with **Korean-language centers** — they're the hottest leads
and the dialer already prioritizes them.

---

## What "pass" looks like on the dashboard

- Transcripts read like a real conversation, not a monologue.
- `whatsapp_captured` and `interested` counts climbing on answered calls.
- Round latency (shown per agent turn) mostly under ~1.5 s.
- No calls stuck "streaming" — they reach a terminal outcome.

Only after Test 5 passes do you raise the daily cap. See
[OPERATIONS.md](OPERATIONS.md) for the scale-up ladder.
