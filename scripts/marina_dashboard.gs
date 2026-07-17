/**
 * Keystone Education — Marina's Daily Dashboard
 * Google Apps Script (runs in Google Sheets)
 * 
 * Setup:
 * 1. Create new Google Sheet: "Keystone - Marina Dashboard"
 * 2. Extensions → Apps Script
 * 3. Paste this code
 * 4. Save → Run onOpen() → Authorize
 * 5. Refresh the sheet
 * 
 * Features:
 * - Daily task checklist
 * - Lead tracking form
 * - Auto-calculated metrics
 * - Weekly summary
 * - Commission tracker
 */

const SHEET_NAME = "Marina Dashboard";
const LEADS_SHEET = "Leads";
const TASKS_SHEET = "Daily Tasks";
const METRICS_SHEET = "Metrics";
const COMMISSION_SHEET = "Commission";

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Keystone')
    .addItem('Initialize Dashboard', 'initializeDashboard')
    .addItem('Add New Lead', 'showAddLeadForm')
    .addItem('Mark Tasks Complete', 'markTasksComplete')
    .addItem('Generate Weekly Report', 'generateWeeklyReport')
    .addItem('Calculate Commission', 'calculateCommission')
    .addToUi();
}

function initializeDashboard() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // 1. Daily Tasks Sheet
  let tasksSheet = ss.getSheetByName(TASKS_SHEET);
  if (!tasksSheet) {
    tasksSheet = ss.insertSheet(TASKS_SHEET);
    tasksSheet.getRange("A1:E1").setValues([["Date", "Task", "Target", "Actual", "Done?"]]);
    tasksSheet.getRange("A1:E1").setFontWeight("bold").setBackground("#4285f4").setFontColor("white");

    const dailyTasks = [
      ["=TODAY()", "Post WhatsApp Status", "1", "0", "FALSE"],
      ["=TODAY()", "Call leads from yesterday", "5", "0", "FALSE"],
      ["=TODAY()", "Post on Facebook", "1", "0", "FALSE"],
      ["=TODAY()", "Join new Facebook groups", "2", "0", "FALSE"],
      ["=TODAY()", "Call IELTS institutes", "3", "0", "FALSE"],
      ["=TODAY()", "Visit college/campus", "1", "0", "FALSE"],
      ["=TODAY()", "Update lead tracker", "1", "0", "FALSE"],
      ["=TODAY()", "Report to founder", "1", "0", "FALSE"]
    ];
    tasksSheet.getRange(2, 1, dailyTasks.length, 5).setValues(dailyTasks);
    tasksSheet.getRange("E2:E" + (dailyTasks.length + 1)).setDataValidation(
      SpreadsheetApp.newDataValidation().requireCheckbox().setAllowInvalid(false).build()
    );
    tasksSheet.autoResizeColumns(1, 5);
  }

  // 2. Leads Sheet
  let leadsSheet = ss.getSheetByName(LEADS_SHEET);
  if (!leadsSheet) {
    leadsSheet = ss.insertSheet(LEADS_SHEET);
    leadsSheet.getRange("A1:K1").setValues([[
      "Date", "Name", "Phone", "Source", "District", "Qualification", "HSC Year", 
      "Country Interest", "IELTS", "Status", "Notes"
    ]]);
    leadsSheet.getRange("A1:K1").setFontWeight("bold").setBackground("#34a853").setFontColor("white");

    // Status dropdown
    leadsSheet.getRange("J2:J1000").setDataValidation(
      SpreadsheetApp.newDataValidation()
        .requireValueInList(["NEW", "CALLED", "QUALIFIED", "OFFICE_VISIT", "ENROLLED", "SUBMITTED", "OFFER", "VISA", "LANDED", "DROPPED"])
        .setAllowInvalid(false)
        .build()
    );
    leadsSheet.autoResizeColumns(1, 11);
  }

  // 3. Metrics Sheet
  let metricsSheet = ss.getSheetByName(METRICS_SHEET);
  if (!metricsSheet) {
    metricsSheet = ss.insertSheet(METRICS_SHEET);
    metricsSheet.getRange("A1:B1").setValues([["Metric", "Value"]]);
    metricsSheet.getRange("A1:B1").setFontWeight("bold").setBackground("#fbbc04").setFontColor("black");

    const metrics = [
      ["Week Starting", "=TODAY()-WEEKDAY(TODAY())+1"],
      ["Total Leads This Week", '=COUNTIF(Leads!A:A,">="&TODAY()-7)' ],
      ["Total Leads This Month", '=COUNTIF(Leads!A:A,">="&EOMONTH(TODAY(),-1)+1)' ],
      ["Qualified Leads", '=COUNTIF(Leads!J:J,"QUALIFIED")' ],
      ["Office Visits", '=COUNTIF(Leads!J:J,"OFFICE_VISIT")' ],
      ["Enrolled", '=COUNTIF(Leads!J:J,"ENROLLED")' ],
      ["Conversion Rate", '=IF(B4>0,B6/B4,0)' ],
      ["Calls Made Today", '=SUMIF('Daily Tasks'!A:A,TODAY(),'Daily Tasks'!D:D)' ],
      ["Tasks Completion %", '=COUNTIF('Daily Tasks'!E:E,TRUE)/COUNTA('Daily Tasks'!E:E)' ],
      ["Base Salary Earned", "=12000"],
      ["Commission Earned", '=B6*10000' ],
      ["Total Earnings", "=B10+B11"]
    ];
    metricsSheet.getRange(2, 1, metrics.length, 2).setValues(metrics);
    metricsSheet.getRange("B7").setNumberFormat("0.0%");
    metricsSheet.getRange("B12").setNumberFormat("৳#,##0");
    metricsSheet.autoResizeColumns(1, 2);
  }

  // 4. Commission Sheet
  let commissionSheet = ss.getSheetByName(COMMISSION_SHEET);
  if (!commissionSheet) {
    commissionSheet = ss.insertSheet(COMMISSION_SHEET);
    commissionSheet.getRange("A1:F1").setValues([["Month", "Base Salary", "Students Enrolled", "Commission", "Bonus", "Total"]]);
    commissionSheet.getRange("A1:F1").setFontWeight("bold").setBackground("#ea4335").setFontColor("white");
    commissionSheet.autoResizeColumns(1, 6);
  }

  SpreadsheetApp.getUi().alert("Dashboard initialized! Use the Keystone menu.");
}

function showAddLeadForm() {
  const html = HtmlService.createHtmlOutput(`
    <style>
      body { font-family: Arial; padding: 20px; }
      input, select, textarea { width: 100%; padding: 8px; margin: 5px 0; }
      button { background: #4285f4; color: white; padding: 10px 20px; border: none; cursor: pointer; }
    </style>
    <h3>Add New Lead</h3>
    <form id="leadForm">
      <input type="text" id="name" placeholder="Student Name" required>
      <input type="tel" id="phone" placeholder="Phone Number" required>
      <select id="source">
        <option>Facebook</option>
        <option>WhatsApp</option>
        <option>Referral</option>
        <option>College Seminar</option>
        <option>IELTS Institute</option>
        <option>Walk-in</option>
        <option>Other</option>
      </select>
      <input type="text" id="district" placeholder="District (e.g., Narsingdi)">
      <input type="text" id="qualification" placeholder="Highest Qualification (e.g., HSC)">
      <input type="text" id="hscYear" placeholder="HSC Passing Year">
      <select id="country">
        <option>South Korea</option>
        <option>Malaysia</option>
        <option>Canada</option>
        <option>UK</option>
        <option>Other</option>
      </select>
      <input type="text" id="ielts" placeholder="IELTS Score (or 'None')">
      <textarea id="notes" placeholder="Notes"></textarea>
      <button type="button" onclick="submitForm()">Add Lead</button>
    </form>
    <script>
      function submitForm() {
        const data = {
          name: document.getElementById('name').value,
          phone: document.getElementById('phone').value,
          source: document.getElementById('source').value,
          district: document.getElementById('district').value,
          qualification: document.getElementById('qualification').value,
          hscYear: document.getElementById('hscYear').value,
          country: document.getElementById('country').value,
          ielts: document.getElementById('ielts').value,
          notes: document.getElementById('notes').value
        };
        google.script.run.addLead(data);
        google.script.host.close();
      }
    </script>
  `).setWidth(400).setHeight(500);
  SpreadsheetApp.getUi().showModalDialog(html, "Add New Lead");
}

function addLead(data) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const leadsSheet = ss.getSheetByName(LEADS_SHEET);

  leadsSheet.appendRow([
    new Date(),
    data.name,
    data.phone,
    data.source,
    data.district,
    data.qualification,
    data.hscYear,
    data.country,
    data.ielts,
    "NEW",
    data.notes
  ]);

  SpreadsheetApp.getUi().alert("Lead added successfully!");
}

function markTasksComplete() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const tasksSheet = ss.getSheetByName(TASKS_SHEET);
  const today = new Date();
  today.setHours(0,0,0,0);

  const data = tasksSheet.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    const taskDate = new Date(data[i][0]);
    taskDate.setHours(0,0,0,0);
    if (taskDate.getTime() === today.getTime()) {
      tasksSheet.getRange(i+1, 5).setValue(true);
    }
  }
}

function generateWeeklyReport() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const metricsSheet = ss.getSheetByName(METRICS_SHEET);
  const metrics = metricsSheet.getRange(2, 1, 12, 2).getValues();

  let report = "📊 KEystone Weekly Report — Marina\n";
  report += "=" .repeat(30) + "\n\n";

  metrics.forEach(row => {
    report += `${row[0]}: ${row[1]}\n`;
  });

  report += "\nSent from Marina Dashboard";

  // Send to founder via email or WhatsApp (manual for now)
  const html = HtmlService.createHtmlOutput(`
    <h3>Weekly Report</h3>
    <pre style="white-space:pre-wrap;font-size:14px">${report}</pre>
    <p>Copy this and send to founder on WhatsApp.</p>
  `).setWidth(500).setHeight(600);

  SpreadsheetApp.getUi().showModalDialog(html, "Weekly Report");
}

function calculateCommission() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const leadsSheet = ss.getSheetByName(LEADS_SHEET);
  const commissionSheet = ss.getSheetByName(COMMISSION_SHEET);

  const enrolled = leadsSheet.getRange("J:J").getValues().filter(v => v[0] === "ENROLLED").length;
  const baseSalary = 12000;
  const commission = enrolled * 10000;
  const total = baseSalary + commission;

  const month = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "MMMM yyyy");
  commissionSheet.appendRow([month, baseSalary, enrolled, commission, 0, total]);

  SpreadsheetApp.getUi().alert(`Commission calculated!\nEnrolled: ${enrolled}\nTotal Earnings: ৳${total}`);
}
