# Operations — running the 859-center campaign

**Deliverable 5 (deployment half).** Scheduling, compliance, the runbook, and
troubleshooting.

---

## The list

`../data/IELTS_Partners_Tier2.csv` — 859 rows scraped across 49 districts. On
import (`import-centers`) each row is:

- **phone-normalized** to `+8801XXXXXXXXX`; rows without a valid BD mobile are
  parked as `invalid` (≈187 of them — mostly Facebook page links with no
  number). ~647 are immediately dialable.
- **de-duplicated** by phone.
- **categorized** from the name (korean / ielts / japanese / german / visa /
  english) and **prioritized**: Korean-language centers first (hottest leads,
  students already want Korea), then IELTS/visa, then the rest.

The dialer always serves due **callbacks** first, then the highest-priority
fresh lead.

## Scheduling & pacing (enforced in `scheduler.py`)

| Control | Default | Env |
|---------|---------|-----|
| Business hours | 10:00–18:00 Asia/Dhaka | `CALL_HOURS_START/END` |
| Friday prayer block | 12:00–14:00 skipped | (built in) |
| Daily cap | 20 dials/day | `DAILY_CALL_CAP` |
| Min gap between dials | 180 s + jitter | `MIN_GAP_SECONDS` |
| Attempts per center | 3, then `exhausted` | `MAX_ATTEMPTS` |
| Max call length | 420 s | `MAX_CALL_SECONDS` |
| No-answer/busy | auto-retry callback in ~3 h | (built in) |

**Two dialer modes:**

- `assist` *(default, recommended)* — nothing dials itself. You click **Call
  next** on the dashboard; the same policy checks decide if the button is
  allowed. Keeps a human in the loop.
- `auto` — a background loop dials within policy on its own. Only switch to
  this after Test 5 and a few supervised `assist` days.

## Scale-up ladder

| Phase | Rate | Gate |
|-------|------|------|
| Pilot | 10 total | Test 5: ≥3 interested |
| Ramp | 20/day | pilot passed |
| Grow | 50/day | conversion holding, no complaints |
| Full | 100/day | proven; ~9 days clears the list |

At 20/day the ~647 dialable centers take ~32 working days; at 50/day, ~13.

## Compliance & anti-spam — do this the legitimate way

This is a real business calling real business owners to offer them money. Keep
it that way:

- **One consistent caller ID.** The mission mentions "rotate if needed" — **don't.**
  Number rotation to dodge spam filters is the defining robocaller pattern, it
  violates Twilio's Acceptable Use Policy (grounds for account termination),
  and it destroys callback trust. A stable, recognizable number that owners can
  save and call back is an asset, not a liability.
- **Respect the caps and hours.** They exist so you look like a company, not a
  robodialer. Don't raise them to "just get through the list."
- **Honor DNC instantly and permanently.** "আর কল দিয়েন না" → the agent
  confirms, marks `dnc`, and the center is never dialed again.
- **Never deny being an AI.** If asked, she says so and continues. This is a
  hard rule in the persona and a reputational must — a coaching-center owner who
  later feels deceived is a lost partner and a bad story in a tight-knit market.
- **Record only where lawful** and tell people if your jurisdiction requires it.
  `RECORD_CALLS` is on by default for quality review; know your obligations.
- **No PII harvesting** beyond a business WhatsApp number the owner volunteers.

If Twilio can't deliver to BD reliably or cost is high, evaluate a Bangladeshi
SIP/VoIP provider or a masking-number service — but keep the *one stable ID*
principle whatever the carrier.

## Daily runbook

```bash
# once
python -m keystone_voice.cli init-db
python -m keystone_voice.cli import-centers
python -m keystone_voice.cli pregen              # after keys are set

# each working day
python -m keystone_voice.cli serve               # open the dashboard
#   → check the gate says "ready to dial"
#   → click "Call next" through the day (assist mode), or let auto mode run
#   → watch hot leads (WhatsApp captured) — Telegram pings if configured
#   → follow up captured WhatsApp numbers from the OFFICIAL number 01328-224600

# anytime
python -m keystone_voice.cli status              # funnel + readiness
python -m keystone_voice.cli export calls --out exports/calls.csv
python -m keystone_voice.cli kill                # STOP everything now
python -m keystone_voice.cli kill --resume       # release
```

The red **Kill switch** button on the dashboard does the same as `kill` — one
click stops new dials and politely wraps up any live call.

## Human handoff

When the brain hits a real negotiation ("মালিকের সাথে কথা বলব", custom
commission talk, legal questions), it calls `transfer_to_human`: schedules a
high-priority callback and (if Telegram is set) pings you to call back
personally that day. The AI opens doors; you close the important ones.

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|-------------------|
| `status` lists missing items | fill those `.env` keys; `PUBLIC_HOST` must be your live ngrok/cloudflared host |
| Twilio call connects then silence | `PUBLIC_HOST` wrong or not HTTPS/WSS reachable; check Twilio debugger + `serve` logs |
| "outside business hours" but it's daytime | server timezone vs `TIMEZONE`; the gate uses `TIMEZONE` (Asia/Dhaka) regardless of host TZ |
| Agent talks over the caller | lower `BARGE_IN_MS`; check inbound audio level vs `VAD_RMS_FLOOR` |
| Long dead air before replies | warm cache (`pregen`), lower `VAD_SILENCE_MS`, ensure Groq/Sarvam reachable from BD |
| Robotic voice | tune `PROSODY` per stage in `brain/state_machine.py`; try Bulbul v3 |
| Everything mock in `/health` | `DEMO_MODE=1` or keys unset — expected until you go live |
| 403 on Twilio webhooks | signature check; ensure `PUBLIC_HOST` exactly matches the URL Twilio calls |
