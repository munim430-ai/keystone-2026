# Money model — Bigcapital (BDT base, USD/KRW multi-currency)

Set Bigcapital's **base currency = BDT**; enable USD and KRW for university-side
invoices. The model mirrors the milestone fee ladder Keystone already uses
("we collect our fee ONLY after visa").

## Revenue — student service fee, billed by milestone
One **estimate** per student at counselling (total ~৳1,20,000), converted to
**invoices** as each milestone is reached. Collecting after visa is the trust
differentiator, so the big tranche lands at the visa milestone.

| Milestone (pipeline stage) | Invoice | Typical |
|---|---|---|
| Registration | Service fee — registration | ৳0 (free counselling) |
| Application submitted | Service fee — application | part payment |
| Offer received | Service fee — offer | part payment |
| **Visa granted** | Service fee — visa (final) | **the bulk of ৳1,20,000** |

## Costs & liabilities per student (Bills / expense accounts)
| Item | Account | Note |
|---|---|---|
| University application fee | COGS — application fee | e.g. KUAC USD 250 (**non-refundable if visa denied** — track as a real liability, not revenue) |
| Embassy fee | COGS — embassy | ~৳7,200 |
| Apostille / translation / notary | COGS — document prep | |
| Referral commission | Bill → Partner (A/P) | per enrolled student, links to the Partners table |
| DHL courier | COGS — logistics | |

## University-side commission (Accounts Receivable, in USD/KRW)
When a university/aggregator pays Keystone a commission per placed student,
raise a **USD/KRW A/R invoice** against them. Bigcapital handles the FX to BDT
for the P&L.

## Partner payouts (Accounts Payable, BDT)
Each IELTS/coaching-center referral that enrols becomes a **bill** to that
partner — mirrored from the NocoDB Partners table (`commission_owed`). Pay on the
same trigger as your own visa-milestone revenue so cash-out never precedes cash-in.

## The one-line P&L per student
`gross margin = student service fee (~৳1,20,000) − application/embassy/doc costs
(~৳35–40k) − referral commission` → **~৳80–85k**, matching the master plan.

## Wiring to the rest of the system
- The NocoDB **Payments** table is the operational log; Bigcapital is the book of record. Keep them reconciled (n8n can mirror a NocoDB payment row into a Bigcapital invoice via its API).
- Never book the KUAC USD 250 as revenue until the visa is granted — it is refundable-conditional and belongs in a liability account until then.
