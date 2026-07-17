// ============================================================
// Keystone WhatsApp Bot — Marina Branch Enhancement
// Add this to your existing C:\keystone-wa\index.js
// ============================================================

const BRANCH_CONFIG = {
  narsingdi: {
    name: "Keystone Education — Narsingdi",
    counsellor: "Marina",
    phone: "01328-224600",
    address: "Narsingdi Bazar, Narsingdi",
    hours: "Saturday-Thursday, 10:00-18:00",
    specialties: ["South Korea", "Malaysia"],
    languages: ["Bangla", "English"]
  },
  gazipur: {
    name: "Keystone Education — Gazipur",
    counsellor: "Hasibul",
    phone: "017XXXXXXXX",
    address: "Rajendrapur Bazar, Gazipur",
    hours: "Saturday-Thursday, 10:00-18:00",
    specialties: ["South Korea", "Malaysia", "Canada", "UK"],
    languages: ["Bangla", "English", "Korean"]
  }
};

// Detect branch based on which number the student messaged
function detectBranch(fromNumber) {
  // If message comes to Narsingdi number, route to Marina
  if (fromNumber.includes("NARSINGDI_NUMBER")) return "narsingdi";
  return "gazipur";
}

// Marina-specific greeting
function getMarinaGreeting() {
  const greetings = [
    "আসসালামু আলাইকুম! আমি মারিনা, কিস্টোন এডুকেশন নারসিংদি থেকে বলছি। কীভাবে সাহায্য করতে পারি?",
    "আসসালামু আলাইকুম! মারিনা এখানে। কোরিয়া বা মালয়েশিয়ায় পড়াশোনা নিয়ে জানতে চাইলে বলুন।",
    "আসসালামু আলাইকুম! কিস্টোন এডুকেশন, নারসিংদি। আমি মারিনা। কোন দেশে পড়তে চান?"
  ];
  return greetings[Math.floor(Math.random() * greetings.length)];
}

// Enhanced qualification flow for Marina
const MARINA_QUALIFICATION_FLOW = [
  {
    question: "আপনার সর্বোচ্চ কোয়ালিফিকেশন কী? (SSC/HSC/অনার্স/মাস্টার্স)",
    field: "qualification",
    validate: (ans) => ans.length > 2
  },
  {
    question: "HSC/সর্বোচ্চ ডিগ্রি পাশের সাল কত?",
    field: "hsc_year",
    validate: (ans) => /^\d{4}$/.test(ans)
  },
  {
    question: "আপনার জন্ম তারিখ কী? (দিন/মাস/সাল)",
    field: "dob",
    validate: (ans) => ans.length > 5
  },
  {
    question: "কোন দেশে পড়তে চান? (কোরিয়া/মালয়েশিয়া/কানাডা/অন্য)",
    field: "country",
    validate: (ans) => ans.length > 2
  },
  {
    question: "IELTS আছে? থাকলে স্কোর কত? না থাকলে 'নেই' লিখুন।",
    field: "ielts",
    validate: (ans) => true
  },
  {
    question: "আপনার বাজেট কত? (আনুমানিক)",
    field: "budget",
    validate: (ans) => true
  }
];

// Save lead to Google Sheets (via webhook or direct API)
async function saveLeadToSheets(leadData) {
  const SHEET_WEBHOOK_URL = process.env.SHEET_WEBHOOK_URL || "";

  if (!SHEET_WEBHOOK_URL) {
    console.log("⚠️  No sheet webhook configured. Lead saved locally only.");
    // Save to local JSON as backup
    const fs = require('fs');
    const leads = JSON.parse(fs.readFileSync('leads_backup.json', 'utf8') || '[]');
    leads.push({...leadData, timestamp: new Date().toISOString()});
    fs.writeFileSync('leads_backup.json', JSON.stringify(leads, null, 2));
    return;
  }

  try {
    await axios.post(SHEET_WEBHOOK_URL, leadData);
    console.log("✅ Lead saved to Google Sheets");
  } catch (e) {
    console.error("❌ Failed to save lead:", e.message);
  }
}

// Marina's follow-up sequence (automated)
const MARINA_FOLLOWUP_SEQUENCE = {
  day0: "আসসালামু আলাইকুম [NAME]! কিস্টোন এডুকেশন থেকে মারিনা। আপনি কোরিয়া নিয়ে জানতে চেয়েছিলেন। আর কোনো প্রশ্ন আছে?",
  day2: "[NAME], আসসালামু আলাইকুম! আপনার সার্টিফিকেট নিয়ে একবার অফিসে আসুন। ফ্রি কাউন্সেলিং দিচ্ছি। কবে আসতে পারবেন?",
  day5: "[NAME], আপনি কোরিয়া নিয়ে আগ্রহী ছিলেন। আসন সীমিত, তাই দেরি না করে আজই আসুন। আমার WhatsApp: 01328-224600",
  day7: "[NAME], শেষ চেষ্টা! কোরিয়ার EAP প্রোগ্রামে আসন কমে আসছে। আপনি যদি এখনো আগ্রহী থাকেন, একবার কল করুন।"
};

// Schedule follow-up (requires cron or manual trigger)
function scheduleFollowUp(phone, name, day) {
  const message = MARINA_FOLLOWUP_SEQUENCE[`day${day}`].replace("[NAME]", name);
  // This would be triggered by a cron job or scheduled task
  console.log(`📅 Scheduled follow-up Day ${day} to ${phone}: ${message}`);
  return message;
}

// Export for use in main bot
module.exports = {
  BRANCH_CONFIG,
  detectBranch,
  getMarinaGreeting,
  MARINA_QUALIFICATION_FLOW,
  saveLeadToSheets,
  MARINA_FOLLOWUP_SEQUENCE,
  scheduleFollowUp
};
