// ============================================================
// Keystone WhatsApp Follow-up Scheduler  (Strategy §8, Fix B)
// ------------------------------------------------------------
// Turns the STUBBED scheduleFollowUp() (which only console.log'd)
// into a real day0/2/5/7 sender that actually delivers over
// WhatsApp via the Evolution API — the ONLY approved WhatsApp
// channel (no unofficial clients; account-ban risk).
//
// Design: no long-running daemon and no hard cron dependency.
// A durable JSON queue holds pending follow-ups with due dates;
// `process` sends everything now due and marks it sent. Run it
// hourly from system cron or an n8n Schedule node:
//
//     0 * * * *  cd /path/to/bots && node followup_scheduler.js process
//
// Enqueue new leads from the main bot on first contact:
//     const { enqueueLead } = require('./followup_scheduler');
//     enqueueLead(phone, name);   // schedules day0/2/5/7
// ============================================================

const fs = require('fs');
const path = require('path');

const QUEUE_FILE = process.env.FOLLOWUP_QUEUE || path.join(__dirname, 'followups_queue.json');

// Evolution API (official-style WhatsApp). All three must be set to actually send.
const EVOLUTION_URL = process.env.EVOLUTION_API_URL || '';        // e.g. https://evo.your-vps
const EVOLUTION_INSTANCE = process.env.EVOLUTION_INSTANCE || '';   // your instance name
const EVOLUTION_KEY = process.env.EVOLUTION_API_KEY || '';         // apikey header

// The day0/2/5/7 copy (kept in sync with wa_bot_marina.js MARINA_FOLLOWUP_SEQUENCE).
const SEQUENCE = {
  0: 'আসসালামু আলাইকুম [NAME]! কিস্টোন এডুকেশন থেকে মারিনা। আপনি কোরিয়া নিয়ে জানতে চেয়েছিলেন। আর কোনো প্রশ্ন আছে?',
  2: '[NAME], আসসালামু আলাইকুম! আপনার সার্টিফিকেট নিয়ে একবার অফিসে আসুন। ফ্রি কাউন্সেলিং দিচ্ছি। কবে আসতে পারবেন?',
  5: '[NAME], আপনি কোরিয়া নিয়ে আগ্রহী ছিলেন। আসন সীমিত, তাই দেরি না করে আজই আসুন। আমার WhatsApp: 01328-224600',
  7: '[NAME], শেষ চেষ্টা! কোরিয়ার EAP প্রোগ্রামে আসন কমে আসছে। আপনি যদি এখনো আগ্রহী থাকেন, একবার কল করুন।',
};
const DAYS = [0, 2, 5, 7];
const DAY_MS = 24 * 60 * 60 * 1000;

function loadQueue() {
  try {
    return JSON.parse(fs.readFileSync(QUEUE_FILE, 'utf8'));
  } catch {
    return [];
  }
}

function saveQueue(q) {
  fs.writeFileSync(QUEUE_FILE, JSON.stringify(q, null, 2));
}

/** Normalise a BD number to WhatsApp JID form (8801XXXXXXXXX). */
function toWaNumber(phone) {
  let d = String(phone).replace(/[^\d]/g, '');
  if (d.startsWith('880')) return d;
  if (d.startsWith('0')) return '88' + d;
  if (d.startsWith('1')) return '880' + d;
  return d;
}

/** Enqueue the full day0/2/5/7 sequence for a lead. Idempotent per phone. */
function enqueueLead(phone, name) {
  const q = loadQueue();
  const wa = toWaNumber(phone);
  if (q.some((i) => i.wa === wa && i.status !== 'cancelled')) {
    return; // already scheduled; don't double-book
  }
  const now = Date.now();
  DAYS.forEach((day) => {
    q.push({
      wa,
      name: name || 'ভাই/আপু',
      day,
      due: new Date(now + day * DAY_MS).toISOString(),
      status: 'pending',
    });
  });
  saveQueue(q);
  console.log(`📥 Enqueued day0/2/5/7 follow-ups for ${wa}`);
}

/** Cancel remaining follow-ups once a lead replies / converts / opts out. */
function cancelLead(phone) {
  const wa = toWaNumber(phone);
  const q = loadQueue();
  let n = 0;
  for (const i of q) {
    if (i.wa === wa && i.status === 'pending') {
      i.status = 'cancelled';
      n++;
    }
  }
  saveQueue(q);
  console.log(`🛑 Cancelled ${n} pending follow-up(s) for ${wa}`);
  return n;
}

async function sendWhatsApp(wa, text) {
  if (!EVOLUTION_URL || !EVOLUTION_INSTANCE || !EVOLUTION_KEY) {
    console.log(`⚠️  Evolution API not configured — would send to ${wa}: ${text.slice(0, 60)}...`);
    return false; // treat as not-sent so it retries once configured
  }
  const url = `${EVOLUTION_URL.replace(/\/$/, '')}/message/sendText/${EVOLUTION_INSTANCE}`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', apikey: EVOLUTION_KEY },
    body: JSON.stringify({ number: wa, text }),
  });
  if (!res.ok) {
    console.error(`❌ Evolution API ${res.status} for ${wa}`);
    return false;
  }
  console.log(`✅ Sent day-follow-up to ${wa}`);
  return true;
}

/** Send every follow-up whose due time has passed. Call hourly from cron. */
async function processDue() {
  const q = loadQueue();
  const now = Date.now();
  let sent = 0;
  for (const item of q) {
    if (item.status !== 'pending') continue;
    if (new Date(item.due).getTime() > now) continue;
    const text = SEQUENCE[item.day].replace('[NAME]', item.name);
    // eslint-disable-next-line no-await-in-loop
    const ok = await sendWhatsApp(item.wa, text);
    if (ok) {
      item.status = 'sent';
      item.sent_at = new Date().toISOString();
      sent++;
    }
  }
  saveQueue(q);
  console.log(`📤 processDue: ${sent} message(s) sent; ${q.filter((i) => i.status === 'pending').length} still pending`);
  return sent;
}

module.exports = { enqueueLead, cancelLead, processDue, toWaNumber };

// CLI: node followup_scheduler.js process | enqueue <phone> <name> | cancel <phone>
if (require.main === module) {
  const [cmd, a, b] = process.argv.slice(2);
  if (cmd === 'process') {
    processDue().catch((e) => { console.error(e); process.exit(1); });
  } else if (cmd === 'enqueue' && a) {
    enqueueLead(a, b || '');
  } else if (cmd === 'cancel' && a) {
    cancelLead(a);
  } else {
    console.log('Usage: node followup_scheduler.js process | enqueue <phone> <name> | cancel <phone>');
  }
}
