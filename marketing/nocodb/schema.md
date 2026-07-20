# NocoDB schema — Keystone marketing & pipeline system of record

Replaces the Google Sheets CRM (Strategy §5, §9). Create one NocoDB **base** =
"Keystone" with these four tables. Column types in brackets.

## 1. `Students` (the lead→enrolled pipeline)
| Column | Type | Notes |
|---|---|---|
| Name | SingleLineText | |
| Phone | PhoneNumber | WhatsApp number |
| Source | SingleSelect | facebook, whatsapp, seminar, referral, b2b_center, google, walk_in |
| Country | SingleSelect | Korea (default), Malaysia, Canada, UK |
| IELTS | SingleLineText | score or "নেই" |
| HSC_Year | Number | |
| Stage | SingleSelect | **Lead → Qualified → Counselling → Docs → AuditGate → Submitted → Visa → Enrolled → Departed** |
| Assigned_To | SingleSelect | Marina, Hasibul, Fahim |
| University | SingleLineText | from Korea_Master_University_List |
| Referred_By | LinkToRecord → Students | for the ৳10k referral payout |
| Next_Action | SingleLineText | |
| Created | CreatedTime | |
| Updated | LastModifiedTime | |

The **Stage** field is the Kanban view and the funnel KPI source (§9). `AuditGate`
links to the existing `audit-system/` — nothing is submitted on a red verdict.

## 2. `B2B_Partners` (the 859-center engine, §6)
Columns match `seed_b2b_from_csv.py`: `Center_Name, District, WhatsApp_Mobile,
Source_URL, Priority (1-3), Status (new/contacted/interested/signed/dead), Owner,
Last_contact (Date), Referrals (Number), Commission_due_bdt (Number)`.
Seed it with `python3 seed_b2b_from_csv.py --base-url … --table-id … --token …`.

> ⚑ **Coverage gap found in the CSV:** it contains **0 centers in Narsingdi or
> Gazipur** (the home offices), and is strongest in Mymensingh (33), Kishoreganj
> (27), Tangail (13) + nationwide. **Build the home-district list separately** with
> `gosom/google-maps-scraper` (query "IELTS center Narsingdi", "study abroad Gazipur")
> and import it at Priority 1. The national rows are best worked by WhatsApp/phone.

## 3. `Content` (the posting calendar, §3–4)
| Column | Type | Notes |
|---|---|---|
| Title | SingleLineText | |
| Pillar | SingleSelect | 5_questions, rate_your_agency, check_5_things, proof, why_cheaper, without_ielts, weekly_status |
| Body_Bangla | LongText | |
| Asset | Attachment | image/reel |
| Channel | MultiSelect | fb_page, reels, youtube, whatsapp_status |
| Status | SingleSelect | idea, drafted, qa_done, scheduled, posted |
| Source_Video | SingleLineText | which long asset it was cut from |
| Post_Date | Date | |

## 4. `Referrals` (student + B2B payouts)
| Column | Type | Notes |
|---|---|---|
| Referrer | SingleLineText | student name or center |
| Type | SingleSelect | student (৳10k), b2b_center (৳5–10k) |
| Enrolled_Student | LinkToRecord → Students | payout triggers on Stage=Enrolled |
| Amount_bdt | Number | |
| Paid | Checkbox | |

## API access for n8n / seeders
Create a NocoDB API token (Account → Tokens). The workflows read it from
`NOCODB_TOKEN`, and table ids from `NOCODB_STUDENTS_TABLE` / `NOCODB_B2B_TABLE`
(see `marketing/deploy/.env.example`).
