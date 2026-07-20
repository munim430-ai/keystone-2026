# Runbook — bring up the Keystone marketing machine

Order matters: the two ~2-hour fixes deliver value on day one, before the full stack.

## Day 1 — the two quick fixes (highest leverage, ~2 hrs each)
### Fix A — Facebook auto-poster
1. Get a Hugging Face token (huggingface.co/settings/tokens) → `HF_API_TOKEN`.
2. Get a Facebook Page access token for Page `1003817206350395` → `FB_PAGE_TOKEN`.
3. `export HF_API_TOKEN=… FB_PAGE_TOKEN=…` then test:
   `python3 bots/fb_poster.py --post-type korea_tip` (posts one image+caption).
4. Schedule daily: `0 10 * * * cd /opt/keystone/bots && python3 fb_poster.py --schedule`.

### Fix B — WhatsApp follow-up scheduler (already coded)
1. Stand up Evolution API (its own compose) → set `EVOLUTION_API_URL/INSTANCE/API_KEY`.
2. The WA bot calls `scheduleFollowUp(phone, name)` on first contact (already wired).
3. Cron the drain hourly: `0 * * * * cd /opt/keystone/bots && node followup_scheduler.js process`
   — or import `marketing/n8n/whatsapp-followup.json` and activate it.
4. Verify: `node followup_scheduler.js enqueue 01712345678 "টেস্ট"` then `... process`.

## Week 1 — the stack
1. `cp marketing/deploy/.env.example marketing/deploy/.env` and fill every value.
2. `cd marketing/deploy && docker compose up -d`.
3. **NocoDB** (:8080): create the 4 tables from `marketing/nocodb/schema.md`; make an API
   token; put it + table ids in `.env`; restart n8n.
4. Seed B2B: `python3 marketing/nocodb/seed_b2b_from_csv.py --base-url $NOCODB_URL --table-id $NOCODB_B2B_TABLE --token $NOCODB_TOKEN`.
5. **n8n** (:5678): import the 4 workflows from `marketing/n8n/`; activate lead-intake,
   whatsapp-followup, b2b-followup.
6. **Postiz** (:4200): connect the FB Page (+ YouTube/IG) via official APIs; wire the
   content-repurpose workflow's schedule step to it.
7. **Umami** (:3000): add the website; drop the tracking snippet on keystoneeducations.com.
8. **Chatwoot** (:3001): create the shared inbox (Marina + founder); enable the website
   widget; point its form webhook at the n8n `keystone-lead` URL.

## Health checks
- `node followup_scheduler.js process` prints "N sent / M pending" — M should fall as due times pass.
- NocoDB `Students` gains a row per form submit; `Stage` moves as staff work it.
- Umami shows visitors; Postiz shows scheduled posts.

## Guardrails (never break)
- WhatsApp only via Evolution API; FB/IG only via Postiz official APIs. No unofficial clients.
- Maps-scraper for B2B institutes only; never scrape students or FB groups.
- Bangla captions get a human pass before publish. No visa/bank advice from any bot.
