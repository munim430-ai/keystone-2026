#!/usr/bin/env python3
"""
pitch_generator.py — WeBring University Partnership Pitch Generator
Keystone Education Consultancy 2026

For each top-ranked Korean university, generates a customized partnership
pitch letter for WeBring (Jo Mi-young / Tina) to send to international
admission offices.

WeBring presents itself as: a multi-country global student settlement &
aggregation platform (NOT a Bangladesh-only, one-agent shop).

Usage:
    python pitch_generator.py --input ranked_universities.json --top 15
    python pitch_generator.py --input ranked_universities.json --university "Kyungsung University"

Output:
    pitches/  (individual .md files per university)
    webring_university_outreach_pack.md  (combined)
"""

import json, argparse, os, re
from pathlib import Path
from datetime import datetime

# ──────────────────────────────────────────────────────────────────────────────
# UNIVERSITY INTELLIGENCE DATABASE
# Admission contact details, key facts, and custom talking points
# ──────────────────────────────────────────────────────────────────────────────

UNIV_INTEL = {
    "Kyungsung University": {
        "city": "Busan",
        "type": "Private",
        "ieqas_tier": "Excellent",
        "korean_name": "경성대학교",
        "int_office_email": "international@ks.ac.kr",
        "int_office_phone": "+82-51-663-4114",
        "int_office_url": "https://international.ks.ac.kr",
        "app_fee_krw": 80000,
        "ielts_min": 5.5,
        "visa_type": "D-2 Regional",
        "scholarship": "30–50% based on IELTS",
        "dorm": "Yes",
        "bd_partner": "WeCare Education (current)",
        "annual_int_students": "~2,000+",
        "talking_points": [
            "Busan's #1 international student hub — established BD community already",
            "Regional visa D-2 = high approval rate, reduces desertion risk",
            "WeBring's Busan settlement network is a natural fit",
            "Current BD agent (WeCare) has high fees — students actively seeking alternatives",
            "Scholarship ladder (IELTS 5.5→30%, 7.5→50%) is a strong sales hook",
        ],
        "pain_points": [
            "High student desertion from debt-laden BD cohorts placed by expensive agents",
            "Need for a settlement partner who ensures students attend class (attendance-linked disbursement)",
            "No Narsingdi/Gazipur-region BD pipeline currently (only Dhaka agents serve them)",
        ],
    },

    "Sejong University": {
        "city": "Seoul",
        "type": "Private",
        "ieqas_tier": "Excellent",
        "korean_name": "세종대학교",
        "int_office_email": "iab@sejong.ac.kr",
        "int_office_phone": "+82-2-3408-3118",
        "int_office_url": "https://oia.sejong.ac.kr",
        "app_fee_krw": 150000,
        "ielts_min": 6.5,
        "visa_type": "D-2 (regional for IT majors)",
        "scholarship": "30% (IELTS 5.5+), 50% (IELTS 6.5+), 80% (IELTS 8.0+)",
        "dorm": "Yes",
        "bd_partner": "WeCare Education (current)",
        "annual_int_students": "~3,000+",
        "talking_points": [
            "Seoul's most recognizable 'aspiration' university for BD families",
            "Hotel & Tourism Management + Aviation programs = employment-ready graduates",
            "WeBring's employment placement arm is a direct value-add for hospitality grads",
            "Scholarship up to 80% at IELTS 8.0 — compelling for high-achievers",
            "E-APOSTILLE chain already mapped — zero surprise rejections",
        ],
        "pain_points": [
            "IELTS 6.5 floor filters many BD students — WeBring's Korean language prep fills the gap",
            "Seoul cost of living → financial stress → desertion risk at 90 days",
            "WeBring's accommodation brokerage directly neutralizes the #1 Seoul drop-out driver",
        ],
    },

    "Kyung Hee University": {
        "city": "Seoul / Suwon",
        "type": "Private",
        "ieqas_tier": "Excellent",
        "korean_name": "경희대학교",
        "int_office_email": "interadm@khu.ac.kr",
        "int_office_phone": "+82-2-961-0524",
        "int_office_url": "https://www.khu.ac.kr/kor/foreign/index.do",
        "app_fee_krw": 100000,
        "ielts_min": 6.0,
        "visa_type": "D-2",
        "scholarship": "Merit-based, partial",
        "dorm": "Yes",
        "bd_partner": "PranBin Education (agency-claimed only)",
        "annual_int_students": "~4,000+",
        "talking_points": [
            "Top-30 Korean university — highest brand prestige in WeBring's pitch deck",
            "UN-designated 'University for Peace' — strong international reputation",
            "BD market: premium students (medical families, corporate sponsors) target KHU",
            "No confirmed BD agency partner — an opening for WeBring to establish first-mover position",
            "Tourism and Hotel Management + performing arts faculties → WeBring employment angle",
        ],
        "pain_points": [
            "No structured BD pipeline — students arrive via generic agents with weak file quality",
            "KHU needs higher-quality, pre-screened BD applicants to improve international metrics",
            "WeBring's AI settlement bot can handle multilingual BD student onboarding at scale",
        ],
    },

    "Dongshin University": {
        "city": "Naju (Jeonnam)",
        "type": "Private",
        "ieqas_tier": "Standard-4yr",
        "korean_name": "동신대학교",
        "int_office_email": "global@dsu.ac.kr",
        "int_office_phone": "+82-61-330-3114",
        "int_office_url": "https://www.dsu.ac.kr",
        "app_fee_krw": 100000,
        "ielts_min": 5.5,
        "visa_type": "D-2",
        "scholarship": "30–70% ladder (IELTS 5.5→30%, 8.0→70%)",
        "dorm": "Yes",
        "bd_partner": "WeCare Education",
        "annual_int_students": "~800+",
        "talking_points": [
            "Cheapest tuition in target set: ৳3.7M–4.0M KRW/sem — best value for mid-income BD families",
            "Lowest bank balance floor ($16k acceptable) — unlocks the largest BD market segment",
            "Naju location = lower living costs, less factory-work temptation (lower desertion)",
            "TESOL + Software Convergence + Global Business — employment paths WeBring can plug into",
            "WeBring's rural-area settlement expansion could use Dongshin as a test case",
        ],
        "pain_points": [
            "Low city profile means students need extra pastoral support post-arrival",
            "WeBring's settlement model is exactly what Dongshin students (far from Seoul) need",
            "IEQAS certification status flagged as unclear — WeBring/Keystone to verify before pitching families",
        ],
    },

    "Kangwon National University": {
        "city": "Chuncheon (Gangwon)",
        "type": "National",
        "ieqas_tier": "Standard-4yr",
        "korean_name": "강원대학교",
        "int_office_email": "ois@kangwon.ac.kr",
        "int_office_phone": "+82-33-250-6026",
        "int_office_url": "https://ois.kangwon.ac.kr",
        "app_fee_krw": 70000,
        "ielts_min": 5.5,
        "visa_type": "D-2",
        "scholarship": "Partial, merit-based",
        "dorm": "Yes (priority for internationals)",
        "bd_partner": "WeCare Education",
        "annual_int_students": "~1,500+",
        "talking_points": [
            "National university = lower tuition, higher credibility for BD families",
            "Chuncheon — university town with low crime, ideal for first-time overseas students",
            "Strong engineering, agriculture, medicine programs — career-relevant for BD aspirations",
            "WeBring can pitch KNU as the 'safe, affordable, national university' option in marketing",
        ],
        "pain_points": [
            "Gangwon-do region = limited Korean-speaking support network for BD students",
            "WeBring's multilingual settlement services directly fill this gap",
            "BD students placed by WeCare often arrive without bank balance knowledge — high visa risk",
        ],
    },

    "Gachon University": {
        "city": "Seongnam (Gyeonggi)",
        "type": "Private",
        "ieqas_tier": "Standard-4yr",
        "korean_name": "가천대학교",
        "int_office_email": "global@gachon.ac.kr",
        "int_office_phone": "+82-31-750-5114",
        "int_office_url": "https://www.gachon.ac.kr",
        "app_fee_krw": 120000,
        "ielts_min": 5.5,
        "visa_type": "D-2 (E-VISA)",
        "scholarship": "50% first semester guaranteed",
        "dorm": "Yes",
        "bd_partner": "unconfirmed",
        "annual_int_students": "~2,000+",
        "talking_points": [
            "Seoul metro location (Seongnam) — strong employment access in Korea's tech hub",
            "50% guaranteed first-semester scholarship = easiest scholarship story to sell",
            "Medical, Nursing, IT programs — top aspirational fields for BD families",
            "No confirmed BD agency — first-mover opportunity for WeBring channel exclusive",
            "E-VISA available = faster processing, no in-person embassy visit queue",
        ],
        "pain_points": [
            "Strictest document standards (name-spelling, gap verification) — pre-audited files essential",
            "Keystone's audit system directly prevents the #1 cause of Gachon rejection",
            "Seoul metro cost → desertion risk → WeBring settlement essential",
        ],
    },

    "Kyungdong University": {
        "city": "Goseong, Gangwon-do",
        "type": "Private",
        "ieqas_tier": "Standard-4yr",
        "korean_name": "경동대학교",
        "int_office_email": "info@kduniv.ac.kr",
        "int_office_phone": "+82-33-639-0218",
        "int_office_url": "https://global.kduniv.ac.kr",
        "app_fee_krw": 0,  # via KUAC — varies
        "ielts_min": 5.0,
        "visa_type": "D-4-7 Regional",
        "scholarship": "EAP bridge — no IELTS required to enter",
        "dorm": "Yes (priority)",
        "bd_partner": "KUAC (official) + Keystone (exclusive BD)",
        "annual_int_students": "~1,200+",
        "talking_points": [
            "EAP pathway = NO IELTS required to START — opens the largest BD student pool",
            "D-4-7 regional visa = ~95% approval, lowest rejection in the entire portfolio",
            "Gangwon-do rural campus = low living cost, low desertion temptation",
            "Keystone founder is a KDU alumnus — unique trust signal to the university",
            "WeBring can position this as the 'safest first step to Korea' for risk-averse BD families",
        ],
        "pain_points": [
            "Remote location = students need strong post-arrival community & support",
            "WeBring's settlement model was designed for exactly this student profile",
            "No large city distractions = better academic retention = better university KPIs",
        ],
    },

    "Dong-A University": {
        "city": "Busan",
        "type": "Private",
        "ieqas_tier": "Standard-4yr",
        "korean_name": "동아대학교",
        "int_office_email": "intladmin@dau.ac.kr",
        "int_office_phone": "+82-51-200-6114",
        "int_office_url": "https://www.dau.ac.kr",
        "app_fee_krw": 80000,
        "ielts_min": 5.5,
        "visa_type": "D-2",
        "scholarship": "Merit-based partial",
        "dorm": "Yes",
        "bd_partner": "WeCare Education",
        "annual_int_students": "~1,500+",
        "talking_points": [
            "Busan — Korea's second city, lower cost than Seoul but full employment market",
            "Law, Medicine, Engineering — top BD family aspirational programs",
            "Busan port city = large South Asian expat community for student support",
            "WeBring can offer BD students guaranteed Busan accommodation on arrival",
        ],
        "pain_points": [
            "WeCare currently holds the BD pipeline — an opening exists to compete",
            "BD students from rural Bangladesh struggle in big-city Busan without support",
            "Attendance-linked settlement (WeBring USP) directly improves university retention stats",
        ],
    },

    "Tongmyong University": {
        "city": "Busan",
        "type": "Private",
        "ieqas_tier": "Standard-4yr",
        "korean_name": "동명대학교",
        "int_office_email": "global@tu.ac.kr",
        "int_office_phone": "+82-51-629-1114",
        "int_office_url": "https://global.tu.ac.kr",
        "app_fee_krw": 80000,
        "ielts_min": 5.5,
        "visa_type": "D-2",
        "scholarship": "Partial",
        "dorm": "Yes",
        "bd_partner": "WeCare Education",
        "annual_int_students": "~1,000+",
        "talking_points": [
            "Busan location — Korea's digital media and design hub",
            "IT, Design, Architecture programs = strong employment match with WeBring's job placement",
            "Lower profile than Kyungsung = less crowded BD applicant pool, higher acceptance rate",
            "WeBring + Tongmyong = 'Busan Cluster' strategy (same city, shared settlement ops)",
        ],
        "pain_points": [
            "Less aspirational brand means BD students need more support and motivation post-arrival",
            "WeBring's community and mentorship programs directly provide this",
        ],
    },

    "Inha University": {
        "city": "Incheon",
        "type": "Private",
        "ieqas_tier": "Excellent",
        "korean_name": "인하대학교",
        "int_office_email": "international@inha.ac.kr",
        "int_office_phone": "+82-32-860-7114",
        "int_office_url": "https://inha.ac.kr",
        "app_fee_krw": 100000,
        "ielts_min": 6.0,
        "visa_type": "D-2",
        "scholarship": "Merit-based",
        "dorm": "Yes",
        "bd_partner": "unconfirmed",
        "annual_int_students": "~2,500+",
        "talking_points": [
            "Incheon = next to airport and industrial zone — strong student employment access",
            "Aerospace engineering, medicine — Korea's top technical programs",
            "EXCELLENT IEQAS tier = easiest visa processing, fastest approval",
            "Korean Air partnership history — aviation students have built-in employment runway",
            "WeBring's employment placement arm perfectly matches Inha's career-focused graduates",
        ],
        "pain_points": [
            "No structured BD pipeline — most BD students apply ad-hoc, with weak files",
            "WeBring can establish an exclusive Incheon settlement desk for BD students",
        ],
    },

    "Sun Moon University": {
        "city": "Asan, Chungnam",
        "type": "Private",
        "ieqas_tier": "Standard-4yr",
        "korean_name": "선문대학교",
        "int_office_email": "korean@sunmoon.ac.kr",
        "int_office_phone": "+82-41-530-2089",
        "int_office_url": "https://www.sunmoon.ac.kr",
        "app_fee_krw": 50000,
        "ielts_min": 0,  # KLP requires no English — Korean language program
        "visa_type": "D-4 (KLP) → D-2",
        "scholarship": "Partial",
        "dorm": "Yes (priority foreigners)",
        "bd_partner": "unconfirmed (large BD community confirmed)",
        "annual_int_students": "~3,000+ KLP alumni",
        "talking_points": [
            "27,495 language alumni from 154 countries — the most internationally diverse campus in the portfolio",
            "Asan has the largest confirmed BD student community OUTSIDE Seoul",
            "KLP (Korean Language Program) = no English or IELTS requirement to START",
            "Bank balance only $6,000 USD — accessible for BD middle-income families",
            "4 intakes/year (Mar/Jun/Sep/Dec) = most flexible entry points in portfolio",
        ],
        "pain_points": [
            "Large BD community = large social pressure risk (students influence each other to abscond)",
            "WeBring's attendance-linked disbursement model directly mitigates this",
            "No structured agency managing the BD pipeline — a major gap and an opportunity",
        ],
    },

    "Hanyang University": {
        "city": "Seoul / Ansan (ERICA)",
        "type": "Private",
        "ieqas_tier": "Excellent",
        "korean_name": "한양대학교",
        "int_office_email": "intl@hanyang.ac.kr",
        "int_office_phone": "+82-2-2220-0114",
        "int_office_url": "https://www.hanyang.ac.kr/web/www/en",
        "app_fee_krw": 100000,
        "ielts_min": 6.5,
        "visa_type": "D-2",
        "scholarship": "Merit-based",
        "dorm": "Yes",
        "bd_partner": "unconfirmed",
        "annual_int_students": "~5,000+",
        "talking_points": [
            "Korea's 2nd most recognized university brand internationally",
            "ERICA campus (Ansan) = industrial zone adjacency → direct employment access",
            "Engineering, Architecture programs = Korea's top job-placement rates",
            "WeBring's employment placement arm perfectly positions Hanyang grads",
            "A WeBring × Hanyang MOU would be the flagship credential for WeBring's portfolio",
        ],
        "pain_points": [
            "IELTS 6.5 floor means BD students need Korean language prep first",
            "WeBring's KLP → D-2 pathway planning is the missing piece for BD applicants",
            "High prestige = high desertion risk from Seoul cost pressure — WeBring essential",
        ],
    },

    "Woosong University": {
        "city": "Daejeon",
        "type": "Private",
        "ieqas_tier": "Standard-4yr",
        "korean_name": "우송대학교",
        "int_office_email": "via english.wsi.ac.kr",
        "int_office_phone": "+82-42-630-9114",
        "int_office_url": "https://english.wsi.ac.kr",
        "app_fee_krw": 50000,
        "ielts_min": 0,
        "visa_type": "D-4 (KLP) → D-2",
        "scholarship": "Partial",
        "dorm": "Yes",
        "bd_partner": "unconfirmed (BD students at Woosong confirmed)",
        "annual_int_students": "~2,000+",
        "talking_points": [
            "LOWEST bank balance requirement: USD $3,000 ONLY — the most accessible in the portfolio",
            "Daejeon = Korea's 'science city', strong tech employment access",
            "4 intakes/year (reopening Fall 2026) = immediate pipeline opportunity",
            "SolBridge (BBA/MBA) on the same campus = clear academic upgrade pathway",
            "Culinary Arts programs — popular with BD students seeking hospitality careers",
        ],
        "pain_points": [
            "Reopening international admissions Fall 2026 — an opportunity to be the FIRST BD pipeline",
            "Low bank floor attracts financially stressed students → WeBring's support is critical",
        ],
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# WEBRING IDENTITY BLOCK (always included — positions WeBring as global aggregator)
# ──────────────────────────────────────────────────────────────────────────────

WEBRING_IDENTITY = """
**About WeBring (위브링):**
WeBring is a Korea-based international student settlement and aggregation platform. Since 2021, we have served **10,000+ international students** from **Vietnam, India, Bangladesh, Nepal, and Southeast Asia**, providing end-to-end settlement services: visa consulting, airport reception, accommodation, insurance, part-time employment, and career placement. We hold MOUs with **9 Korean universities** and are accredited partners of Korea's leading student welfare ecosystem.

WeBring operates as a **multi-country, multi-agency aggregator** — our role is to ensure every international student who arrives in Korea, regardless of their home country or originating agency, receives a professional, transparent, and caring settlement experience. We do not represent any single country or agency exclusively.
"""

# ──────────────────────────────────────────────────────────────────────────────
# PITCH TEMPLATE ENGINE
# ──────────────────────────────────────────────────────────────────────────────

def generate_pitch(univ_name: str, intel: dict, rank: int) -> str:
    """Generate a customized university partnership pitch for WeBring to send."""

    tp = "\n".join(f"  - {p}" for p in intel["talking_points"])
    pain = "\n".join(f"  - {p}" for p in intel["pain_points"])
    date = datetime.now().strftime("%B %Y")

    # Determine how many countries to mention (always plural to avoid single-country impression)
    countries_served = "Vietnam, India, Bangladesh, Nepal, Philippines, and Southeast Asia"
    settlement_offer = (
        f"airport reception, UWAY/portal application support, "
        f"accommodation placement, health insurance enrollment, "
        f"part-time employment matching, and academic retention monitoring"
    )

    bd_partner_note = ""
    if "WeCare" in intel.get("bd_partner", ""):
        bd_partner_note = (
            f"\n> *Note: WeBring is aware that {univ_name} currently works with "
            f"WeCare Education for its Bangladesh pipeline. We respect existing relationships "
            f"and propose this as a complementary, multi-region aggregation layer — not a replacement.*\n"
        )

    pitch = f"""# WeBring Partnership Proposal
## {intel['korean_name']} ({univ_name})
**Prepared by:** Jo Mi-young (조미영), CEO, WeBring (WICA Corporation)
**Date:** {date}
**Rank in WeBring's priority list:** #{rank} (based on BD market demand intelligence)

---

## 1. WeBring Overview
{WEBRING_IDENTITY.strip()}

---

## 2. Why {univ_name}?

**University Profile:**
| Item | Detail |
|------|--------|
| **Location** | {intel['city']} |
| **Type** | {intel['type']} |
| **IEQAS Certification** | {intel['ieqas_tier']} |
| **Visa Type** | {intel['visa_type']} |
| **Min. Language Score** | {'No requirement (KLP entry)' if intel['ielts_min'] == 0 else f"IELTS {intel['ielts_min']}+"} |
| **Scholarship Available** | {intel['scholarship']} |
| **Dormitory** | {intel['dorm']} |
| **Est. Int'l Students** | {intel['annual_int_students']} |
| **Application Fee** | {'Varies' if intel['app_fee_krw'] == 0 else f"₩{intel['app_fee_krw']:,}"} |

**Why this university is a priority market for WeBring:**
{tp}

**Challenges WeBring directly solves for this university:**
{pain}
{bd_partner_note}
---

## 3. What WeBring Proposes

### Settlement Service Package (per student)
WeBring will deliver the following to every international student admitted to {univ_name}:

| Service | Detail |
|---------|--------|
| **Pre-arrival** | Visa documentation review, bank statement guidance, orientation pack |
| **Day-1 arrival** | Airport pickup, SIM card, T-money card, campus housing check-in |
| **Week-1 integration** | Insurance enrollment, bank account setup, campus tour, Korean basics |
| **Months 1–6** | Monthly check-ins, academic attendance monitoring, counselling |
| **Employment** | Part-time job matching (legally, within 20hr/week limit for students) |
| **Career (Year 2+)** | Job placement support, E-7 visa pathway guidance |

### Attendance-Linked Retention Program (WeBring Exclusive)
For universities concerned about student desertion, WeBring offers an optional
**Attendance-Linked Disbursement** program: a portion of the student's study fund
(held in WeBring's partner financial account) is released monthly only upon verified
80%+ class attendance. This model has demonstrated near-zero desertion in pilot cohorts.

### Proposed Commercial Structure
| Item | Terms |
|------|-------|
| **Settlement fee** | Paid by student (₩200,000–₩500,000 one-time, or monthly ₩50,000) |
| **University referral commission** | ₩0 — WeBring does not charge universities |
| **Agency channel** | Multi-country; WeBring aggregates from partner agencies in 10+ countries |
| **Exclusivity** | None required from university side |
| **Pilot cohort** | 5–10 students, any intake (Winter 2026 or Spring 2027) |
| **Reporting** | Monthly attendance & retention dashboard provided to university |

---

## 4. How the Pipeline Works

```
Bangladesh / Vietnam / India / Nepal
        │
    Local Partner Agencies
    (Keystone, etc. — pre-screen, document audit, visa)
        │
    Student arrives in Korea — VISA SECURED
        │
    WeBring Settlement Layer
    (Airport → Housing → Insurance → Attendance → Jobs → Career)
        │
    {univ_name} receives:
    ✅ Higher-quality, pre-audited students
    ✅ Lower desertion risk (attendance monitoring)
    ✅ Full pastoral support (no university staff burden)
    ✅ Employment-ready graduates
```

---

## 5. Proposed Next Steps

1. **15-minute intro call** with {univ_name} International Office
2. WeBring shares settlement service brochure + pilot MOU template
3. Agree on pilot cohort size (5–10 students, Winter 2026 intake preferred)
4. WeBring onboards students through its app on arrival
5. 3-month review: attendance rates, student satisfaction, zero-desertion tracking

---

## 6. Contact

**Jo Mi-young (조미영)**
CEO, WeBring (WICA Corporation)
📧 mycho@webring.kr
📞 +82 10-6331-6617
🌐 https://webringservice.co.kr | https://univ.webring.kr

**International Office Contact for {univ_name}:**
📧 {intel['int_office_email']}
📞 {intel['int_office_phone']}
🌐 {intel['int_office_url']}

---

*This proposal was prepared as part of WeBring's 2026 Pan-Asia University Partnership Program.
WeBring serves students from {countries_served}.*
"""
    return pitch.strip()


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="ranked_universities.json")
    parser.add_argument("--top", type=int, default=15)
    parser.add_argument("--university", default=None, help="Generate pitch for one university only")
    args = parser.parse_args()

    Path("pitches").mkdir(exist_ok=True)

    # Load ranked list
    try:
        with open(args.input, encoding="utf-8") as f:
            ranked = json.load(f)
    except FileNotFoundError:
        print(f"[!] {args.input} not found. Run fb_scraper.py first, or use --input signals_ranked.json")
        ranked = []

    # If single university requested
    if args.university:
        targets = [(1, args.university)]
    else:
        # Use top N from ranked list, but prioritize those we have intel for
        targets = []
        rank = 1
        for item in ranked[:args.top]:
            name = item["university_en"]
            # Try to find a match in UNIV_INTEL
            matched = None
            for k in UNIV_INTEL:
                if k.lower() in name.lower() or name.lower() in k.lower():
                    matched = k
                    break
            if matched:
                targets.append((rank, matched))
                rank += 1

        # Always include our core universities if not already in list
        core = list(UNIV_INTEL.keys())
        for univ in core:
            if not any(univ == t[1] for t in targets):
                targets.append((rank, univ))
                rank += 1

    combined_parts = []
    print(f"\n{'='*60}")
    print(f"  Generating WeBring pitches for {len(targets)} universities")
    print(f"{'='*60}\n")

    for rank, univ_name in targets:
        if univ_name not in UNIV_INTEL:
            print(f"  [SKIP] No intel for: {univ_name}")
            continue

        intel = UNIV_INTEL[univ_name]
        pitch = generate_pitch(univ_name, intel, rank)

        # Save individual file
        safe_name = re.sub(r'[^a-zA-Z0-9]+', '_', univ_name).lower()
        out_path = Path("pitches") / f"{rank:02d}_{safe_name}_webring_pitch.md"
        out_path.write_text(pitch, encoding="utf-8")
        print(f"  #{rank:2d} ✅ {univ_name} → {out_path}")

        combined_parts.append(f"\n\n{'='*80}\n\n")
        combined_parts.append(pitch)

    # Save combined pack
    combined = "# WeBring × Korean Universities — Full Outreach Pack\n"
    combined += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | {len(targets)} universities*\n"
    combined += "\n## Table of Contents\n"
    for i, (rank, name) in enumerate(targets):
        if name in UNIV_INTEL:
            combined += f"{i+1}. #{rank} [{name}](#{name.lower().replace(' ', '-')})\n"
    combined += "".join(combined_parts)

    pack_path = Path("webring_university_outreach_pack.md")
    pack_path.write_text(combined, encoding="utf-8")
    print(f"\n✅ Full pack saved to: {pack_path}")
    print(f"✅ Individual pitches in: pitches/")


if __name__ == "__main__":
    main()
