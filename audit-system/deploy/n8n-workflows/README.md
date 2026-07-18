# n8n workflow templates

## document-uploaded-reminder.json
When a document is uploaded (Paperless post-consume webhook or a NocoDB row change),
this flow maps the document's tag to a checklist item, marks it received in NocoDB,
and — if any *required* document is still missing — sends the family a Bengali
WhatsApp reminder via Evolution API.

### Import
1. n8n → Workflows → Import from File → pick this JSON.
2. Replace every `CHANGE_ME_*` placeholder:
   - NocoDB base URL, table id, and `xc-token` API token
   - Evolution API base URL, instance name, and `apikey`
   - the tag→checklist map in the **Map Tag → Checklist Item** function node (match your NocoDB column names)
3. The `missing_docs` / `whatsapp_number` fields are expected to come from your
   NocoDB update response — wire the **Update Checklist** node to return the row,
   or add a NocoDB "get record" node before the IF. (Left as a stub so you bind it
   to your real schema.)
4. Set credentials as n8n credentials rather than inline headers for production.
5. Toggle the workflow **Active** only after a test run with a dummy payload.

### Trigger URL
After activation the webhook lives at `${N8N_WEBHOOK_URL}webhook/keystone-doc-uploaded`.
Point Paperless's post-consume script or a NocoDB webhook at it.
