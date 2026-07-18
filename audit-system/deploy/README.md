# Keystone stack — deployment runbook (for Fahim)

One Ubuntu VPS, 4–8 GB RAM, CPU-only. Everything is Docker. No GPU, no Kubernetes.

## 0. Prerequisites (once)
```bash
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER   # log out/in after this
```

## 1. Configure
```bash
cd audit-system/deploy
cp .env.example .env
# generate each secret and paste it in:
openssl rand -hex 32     # use for the *_SECRET / *_KEY / *_JWT_* values
openssl rand -hex 64     # use for DOCUSEAL_SECRET_KEY_BASE
nano .env                # fill every CHANGE_ME
```
`.env` holds real secrets — it is gitignored; never commit it.

## 2. Phase 1 — the audit core (start here)
```bash
docker compose --profile phase1 up -d
docker compose logs -f paperless      # wait for "paperless-ngx ready"
```
- Paperless: `http://<vps-ip>:8000` — log in with `PAPERLESS_ADMIN_USER/PASSWORD`.
- NocoDB: `http://<vps-ip>:8080` — create the base + Students/Partners tables.
- **Expected RAM, phase 1: ~1.3–1.8 GB.**

### Verify Bengali OCR works (do this before building on top)
Upload three real documents via the Paperless UI: one clean English (an IELTS
cert), one noisy Bangla NID scan, one bank statement. Then confirm the OCR text
is searchable and retrievable through the API:
```bash
# get a token
curl -s -X POST http://<vps-ip>:8000/api/token/ \
  -d "username=$PAPERLESS_ADMIN_USER&password=$PAPERLESS_ADMIN_PASSWORD"
# search (expect the Bangla doc to return on a Bangla query term)
curl -s "http://<vps-ip>:8000/api/documents/?query=পাসপোর্ট" \
  -H "Authorization: Token <TOKEN>" | jq '.count, .results[].title'
```
If the Bangla document does not come back searchable, the `ben` tesseract pack
didn't load — check `PAPERLESS_OCR_LANGUAGES` and rebuild. Use the EasyOCR sidecar
(`../sidecar/`) for the documents where Tesseract's Bangla is too weak to extract
field values.

## 3. Phase 2 — operations (once phase 1 is in daily use)
```bash
docker compose --profile phase2 up -d
```
- n8n: `http://<vps-ip>:5678` — import `n8n-workflows/document-uploaded-reminder.json`.
- DocuSeal: `http://<vps-ip>:3000` — service-agreement signing.
- Bigcapital: `http://<vps-ip>:4000` — set base currency BDT; **reconcile this
  compose against Bigcapital's current official `docker/` compose first** (its
  service topology shifts between releases).
- **Expected RAM, phases 1+2 together: ~3–4 GB.** If tight, run Bigcapital on its
  own or defer it.

## 4. Backups (cron this weekly)
Each named volume backs up with one command:
```bash
docker run --rm -v keystone_paperless_media:/v -v $PWD:/b alpine \
  tar czf /b/paperless_media_$(date +%F).tgz -C /v .
```
Repeat for `paperless_data`, `paperless_pgdata`, `nocodb_pgdata`, `n8n_data`,
`bigcapital_pgdata`. Store off-server. **The Paperless document media is the
irreplaceable one — every student's actual files live there.**

## 5. Updating images safely
```bash
docker compose pull                 # fetch newer tags
docker compose --profile phase1 up -d
```
Pinned to major tags, so `pull` gets patches, not breaking majors. Back up
volumes before any major bump. Read the project changelog for Paperless and
Bigcapital before jumping a major version.

## 6. Where the auditor fits
The Python auditor (`audit-system/audit.py`) reads a student's document folder +
`metadata.yaml` and produces a submit-ready / not-ready verdict. Pull document
text from Paperless (API) or the EasyOCR sidecar into `metadata.yaml`, run the
audit, and store the verdict back in the NocoDB Students row. n8n can call the
auditor on a schedule or on each upload.
