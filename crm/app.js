// KEYSTONE B2B OUTREACH CRM - STANDALONE APP LOGIC
const STORAGE_KEY = 'KEYSTONE_B2B_CRM_CENTERS_V2';

const STATE = {
  centers: [],
  activeDistrict: 'ALL',
  activeStatus: 'ALL',
  cardsPerPage: 5,
  currentPage: 1,
  searchQuery: '',
  currentEmployee: 'Munim (Founder)',
  activeModalCenterId: null
};

const elements = {
  districtSelect: document.getElementById('districtSelect'),
  quickDistricts: document.getElementById('quickDistricts'),
  searchInput: document.getElementById('searchInput'),
  limitBtns: document.querySelectorAll('.limit-btn'),
  tabBtns: document.querySelectorAll('.tab-btn'),
  cardsGrid: document.getElementById('cardsGrid'),
  emptyState: document.getElementById('emptyState'),
  employeeSelect: document.getElementById('employeeSelect'),
  exportBtn: document.getElementById('exportBtn'),
  templatesBtn: document.getElementById('templatesBtn'),
  
  statTotal: document.getElementById('statTotal'),
  statEager: document.getElementById('statEager'),
  statFollowUp: document.getElementById('statFollowUp'),
  statCold: document.getElementById('statCold'),
  statPartnered: document.getElementById('statPartnered'),
  statStudents: document.getElementById('statStudents'),

  countAll: document.getElementById('countAll'),
  countEager: document.getElementById('countEager'),
  countFollowUp: document.getElementById('countFollowUp'),
  countNew: document.getElementById('countNew'),
  countCold: document.getElementById('countCold'),
  countPartnered: document.getElementById('countPartnered'),
  countToday: document.getElementById('countToday'),

  paginationBox: document.getElementById('paginationBox'),
  pageInfo: document.getElementById('pageInfo'),
  prevPageBtn: document.getElementById('prevPageBtn'),
  nextPageBtn: document.getElementById('nextPageBtn'),

  noteModal: document.getElementById('noteModal'),
  modalCenterName: document.getElementById('modalCenterName'),
  modalDistrict: document.getElementById('modalDistrict'),
  modalPhone: document.getElementById('modalPhone'),
  modalStatusBadge: document.getElementById('modalStatusBadge'),
  modalNoteInput: document.getElementById('modalNoteInput'),
  modalFollowUpDate: document.getElementById('modalFollowUpDate'),
  saveNoteBtn: document.getElementById('saveNoteBtn'),
  closeModalBtn: document.getElementById('closeModalBtn'),
  logsList: document.getElementById('logsList'),

  studentModal: document.getElementById('studentModal'),
  studentCenterName: document.getElementById('studentCenterName'),
  studentForm: document.getElementById('studentForm'),
  closeStudentModalBtn: document.getElementById('closeStudentModalBtn'),
  studentReferralsList: document.getElementById('studentReferralsList'),

  templatesModal: document.getElementById('templatesModal'),
  closeTemplatesModalBtn: document.getElementById('closeTemplatesModalBtn'),
};

async function initApp() {
  await loadData();
  populateDistrictSelect();
  setupEventListeners();
  renderApp();
}

async function loadData() {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) {
    try {
      STATE.centers = JSON.parse(stored);
    } catch (e) {
      console.error('Error loading stored data', e);
      await fetchFallbackJSON();
    }
  } else {
    await fetchFallbackJSON();
  }

  STATE.centers.forEach(c => {
    if (!c.students) c.students = [];
    if (!c.notes) c.notes = [];
  });
}

async function fetchFallbackJSON() {
  try {
    const res = await fetch('./all_bangladesh_centers.json');
    STATE.centers = await res.json();
  } catch (e) {
    console.error('Failed to load JSON file', e);
  }
}

function saveData() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(STATE.centers));
  updateStatsAndCounts();
}

function populateDistrictSelect() {
  const districtCounts = {};
  STATE.centers.forEach(c => {
    const dist = c.district || 'Unknown';
    districtCounts[dist] = (districtCounts[dist] || 0) + 1;
  });

  const sortedDistricts = Object.keys(districtCounts).sort();

  elements.districtSelect.innerHTML = `<option value="ALL">🌐 All Districts (${STATE.centers.length} Centers)</option>`;
  
  sortedDistricts.forEach(dist => {
    const opt = document.createElement('option');
    opt.value = dist;
    opt.textContent = `📍 ${dist} (${districtCounts[dist]} Centers)`;
    elements.districtSelect.appendChild(opt);
  });

  const popularDistricts = ['Rajshahi', 'Dhaka', 'Bogura', 'Chittagong', 'Sylhet', 'Cumilla', 'Barishal', 'Khulna', 'Dinajpur'];
  elements.quickDistricts.innerHTML = '';
  
  const allPill = document.createElement('button');
  allPill.className = 'pill-btn active';
  allPill.textContent = 'All Districts';
  allPill.onclick = () => selectDistrict('ALL');
  elements.quickDistricts.appendChild(allPill);

  popularDistricts.forEach(dist => {
    if (districtCounts[dist]) {
      const pill = document.createElement('button');
      pill.className = 'pill-btn';
      pill.textContent = `${dist} (${districtCounts[dist]})`;
      pill.onclick = () => selectDistrict(dist);
      elements.quickDistricts.appendChild(pill);
    }
  });
}

function selectDistrict(dist) {
  STATE.activeDistrict = dist;
  elements.districtSelect.value = dist;
  STATE.currentPage = 1;
  
  document.querySelectorAll('.pill-btn').forEach(btn => {
    if ((dist === 'ALL' && btn.textContent.startsWith('All')) || btn.textContent.startsWith(dist)) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  renderApp();
}

function setupEventListeners() {
  elements.districtSelect.addEventListener('change', (e) => {
    selectDistrict(e.target.value);
  });

  elements.employeeSelect.addEventListener('change', (e) => {
    STATE.currentEmployee = e.target.value;
  });

  elements.limitBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      elements.limitBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      STATE.cardsPerPage = parseInt(btn.dataset.limit, 10);
      STATE.currentPage = 1;
      renderApp();
    });
  });

  elements.tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      elements.tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      STATE.activeStatus = btn.dataset.status;
      STATE.currentPage = 1;
      renderApp();
    });
  });

  elements.searchInput.addEventListener('input', (e) => {
    STATE.searchQuery = e.target.value.toLowerCase().trim();
    STATE.currentPage = 1;
    renderApp();
  });

  elements.prevPageBtn.addEventListener('click', () => {
    if (STATE.currentPage > 1) {
      STATE.currentPage--;
      renderApp();
    }
  });

  elements.nextPageBtn.addEventListener('click', () => {
    STATE.currentPage++;
    renderApp();
  });

  elements.exportBtn.addEventListener('click', exportDataJSON);

  elements.templatesBtn.addEventListener('click', () => {
    elements.templatesModal.classList.remove('hidden');
  });

  elements.closeTemplatesModalBtn.addEventListener('click', () => {
    elements.templatesModal.classList.add('hidden');
  });

  document.querySelectorAll('.copy-tpl-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.dataset.template;
      const text = document.getElementById(targetId).value;
      navigator.clipboard.writeText(text).then(() => {
        const origText = btn.textContent;
        btn.textContent = '✅ Copied!';
        setTimeout(() => btn.textContent = origText, 2000);
      });
    });
  });

  elements.closeModalBtn.addEventListener('click', closeModal);
  elements.saveNoteBtn.addEventListener('click', saveModalNote);
  elements.noteModal.addEventListener('click', (e) => {
    if (e.target === elements.noteModal) closeModal();
  });

  elements.closeStudentModalBtn.addEventListener('click', closeStudentModal);
  elements.studentForm.addEventListener('submit', handleStudentFormSubmit);
  elements.studentModal.addEventListener('click', (e) => {
    if (e.target === elements.studentModal) closeStudentModal();
  });
}

function getFilteredCenters() {
  const todayStr = new Date().toISOString().split('T')[0];

  return STATE.centers.filter(center => {
    if (STATE.activeDistrict !== 'ALL' && center.district !== STATE.activeDistrict) {
      return false;
    }

    if (STATE.activeStatus === 'TODAY') {
      if (!center.followUpDate || center.followUpDate !== todayStr) return false;
    } else if (STATE.activeStatus !== 'ALL' && center.status !== STATE.activeStatus) {
      return false;
    }

    if (STATE.searchQuery) {
      const q = STATE.searchQuery;
      const matchName = center.name.toLowerCase().includes(q);
      const matchPhone = center.phone.toLowerCase().includes(q);
      const matchDistrict = center.district.toLowerCase().includes(q);
      if (!matchName && !matchPhone && !matchDistrict) return false;
    }

    return true;
  });
}

function updateStatsAndCounts() {
  const todayStr = new Date().toISOString().split('T')[0];
  
  let eager = 0, followup = 0, cold = 0, partnered = 0, newCount = 0, today = 0, totalStudents = 0;

  STATE.centers.forEach(c => {
    if (c.status === 'Eager') eager++;
    else if (c.status === 'FollowUp') followup++;
    else if (c.status === 'Cold') cold++;
    else if (c.status === 'Partnered') partnered++;
    else newCount++;

    if (c.followUpDate === todayStr) today++;

    if (c.students && c.students.length > 0) {
      totalStudents += c.students.length;
    }
  });

  elements.statTotal.textContent = STATE.centers.length;
  elements.statEager.textContent = eager;
  elements.statFollowUp.textContent = followup;
  elements.statCold.textContent = cold;
  elements.statPartnered.textContent = partnered;
  elements.statStudents.textContent = totalStudents;

  elements.countAll.textContent = STATE.centers.length;
  elements.countEager.textContent = eager;
  elements.countFollowUp.textContent = followup;
  elements.countNew.textContent = newCount;
  elements.countCold.textContent = cold;
  elements.countPartnered.textContent = partnered;
  elements.countToday.textContent = today;
}

function renderApp() {
  updateStatsAndCounts();
  const filtered = getFilteredCenters();

  if (filtered.length === 0) {
    elements.cardsGrid.innerHTML = '';
    elements.emptyState.classList.remove('hidden');
    elements.paginationBox.classList.add('hidden');
    return;
  }

  elements.emptyState.classList.add('hidden');
  elements.paginationBox.classList.remove('hidden');

  const total = filtered.length;
  const perPage = STATE.cardsPerPage;
  const maxPage = Math.ceil(total / perPage);
  
  if (STATE.currentPage > maxPage) STATE.currentPage = maxPage || 1;

  const startIdx = (STATE.currentPage - 1) * perPage;
  const endIdx = Math.min(startIdx + perPage, total);
  const pageCenters = filtered.slice(startIdx, endIdx);

  elements.pageInfo.textContent = `Showing ${startIdx + 1} - ${endIdx} of ${total} Centers`;
  elements.prevPageBtn.disabled = STATE.currentPage === 1;
  elements.nextPageBtn.disabled = STATE.currentPage >= maxPage;

  elements.cardsGrid.innerHTML = pageCenters.map(center => renderCenterCardHTML(center)).join('');

  attachCardEvents();
}

function renderCenterCardHTML(center) {
  const cleanPhone = center.phone ? center.phone.replace(/[^0-9+]/g, '') : '';
  const hasWhatsapp = cleanPhone.startsWith('+8801') || cleanPhone.startsWith('01');
  const waUrl = hasWhatsapp ? `https://wa.me/${cleanPhone.replace('+', '')}?text=Hello%20${encodeURIComponent(center.name)},%20this%20is%20${encodeURIComponent(STATE.currentEmployee)}%20from%20Keystone%20Education%20Consultancy.` : '#';

  const statusClass = `status-${center.status}`;
  const badgeClass = `badge-${center.status}`;

  const lastLog = center.notes && center.notes.length > 0 ? center.notes[center.notes.length - 1] : null;
  const studentCount = center.students ? center.students.length : 0;

  return `
    <div class="center-card ${statusClass}" data-id="${center.id}">
      <div class="card-top">
        <span class="district-tag">📍 ${center.district}</span>
        <span class="status-badge ${badgeClass}">${formatStatusName(center.status)}</span>
      </div>

      <h3 class="card-title">${center.name}</h3>

      <div class="card-contact-row">
        <div class="contact-item">
          <span>📞 Phone:</span>
          <strong>${center.phone || 'No phone listed'}</strong>
        </div>
        ${center.lastContact ? `<div class="contact-item"><span>🕒 Last Called:</span> <span>${center.lastContact} (${center.employee || 'Employee'})</span></div>` : ''}
        ${center.followUpDate ? `<div class="contact-item"><span>📅 Callback Date:</span> <strong style="color:var(--color-followup)">${center.followUpDate}</strong></div>` : ''}
        ${studentCount > 0 ? `<div class="contact-item"><span>🎓 Referrals:</span> <strong style="color:var(--color-teal)">${studentCount} Students</strong></div>` : ''}
      </div>

      <div class="action-buttons-row">
        ${cleanPhone ? `<a href="tel:${cleanPhone}" class="btn-contact btn-call" title="Call directly">📞 Call</a>` : ''}
        ${hasWhatsapp ? `<a href="${waUrl}" target="_blank" class="btn-contact btn-whatsapp" title="Open WhatsApp">💬 WhatsApp</a>` : ''}
        ${center.url ? `<a href="${center.url}" target="_blank" class="btn-contact btn-source" title="Open Facebook / Google Maps">🔗 Link</a>` : ''}
      </div>

      <div class="decision-bar">
        <span class="decision-label">Employee Call Decision:</span>
        <div class="decision-options">
          <button class="decision-btn btn-eager ${center.status === 'Eager' ? 'active' : ''}" data-action="Eager" data-id="${center.id}">
            <span>🔥</span>
            <span>Eager</span>
          </button>
          <button class="decision-btn btn-followup ${center.status === 'FollowUp' ? 'active' : ''}" data-action="FollowUp" data-id="${center.id}">
            <span>📞</span>
            <span>Follow Up</span>
          </button>
          <button class="decision-btn btn-cold ${center.status === 'Cold' ? 'active' : ''}" data-action="Cold" data-id="${center.id}">
            <span>❄️</span>
            <span>Cold</span>
          </button>
        </div>
      </div>

      <div class="card-footer">
        <div class="card-footer-actions">
          <button class="btn-add-stu open-student-btn" data-id="${center.id}" title="Add Referred Student">
            🎓 +Student ${studentCount > 0 ? `(${studentCount})` : ''}
          </button>
          <button class="btn-note open-note-btn" data-id="${center.id}">📝 Logs</button>
        </div>
        <span class="note-snippet">${lastLog ? `💬 "${lastLog.text.substring(0, 25)}..."` : ''}</span>
      </div>
    </div>
  `;
}

function formatStatusName(status) {
  switch (status) {
    case 'Eager': return '🔥 Eager / Hot';
    case 'FollowUp': return '📞 Follow Up';
    case 'Cold': return '❄️ Cold / Declined';
    case 'Partnered': return '🤝 Partnered';
    default: return '🆕 New Lead';
  }
}

function attachCardEvents() {
  document.querySelectorAll('.decision-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = btn.dataset.id;
      const actionStatus = btn.dataset.action;
      updateCenterStatus(id, actionStatus);
    });
  });

  document.querySelectorAll('.open-note-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      openModal(btn.dataset.id);
    });
  });

  document.querySelectorAll('.open-student-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      openStudentModal(btn.dataset.id);
    });
  });
}

function updateCenterStatus(id, newStatus) {
  const center = STATE.centers.find(c => c.id === id);
  if (!center) return;

  const nowStr = new Date().toLocaleString('en-US', { dateStyle: 'short', timeStyle: 'short' });
  center.status = newStatus;
  center.lastContact = nowStr;
  center.employee = STATE.currentEmployee;

  if (!center.notes) center.notes = [];
  center.notes.push({
    date: nowStr,
    employee: STATE.currentEmployee,
    text: `Marked status as [${formatStatusName(newStatus)}]`
  });

  saveData();

  if (newStatus === 'FollowUp') {
    openModal(id);
  } else {
    renderApp();
  }
}

function openStudentModal(id) {
  STATE.activeModalCenterId = id;
  const center = STATE.centers.find(c => c.id === id);
  if (!center) return;

  elements.studentCenterName.textContent = center.name;
  elements.studentForm.reset();

  renderStudentReferrals(center);
  elements.studentModal.classList.remove('hidden');
}

function closeStudentModal() {
  elements.studentModal.classList.add('hidden');
  STATE.activeModalCenterId = null;
}

function handleStudentFormSubmit(e) {
  e.preventDefault();
  if (!STATE.activeModalCenterId) return;

  const center = STATE.centers.find(c => c.id === STATE.activeModalCenterId);
  if (!center) return;

  const name = document.getElementById('stuName').value.trim();
  const phone = document.getElementById('stuPhone').value.trim();
  const country = document.getElementById('stuCountry').value;
  const program = document.getElementById('stuProgram').value.trim() || 'Degree / EAP';
  const ielts = document.getElementById('stuIelts').value.trim() || 'N/A';
  const commission = parseInt(document.getElementById('stuCommission').value, 10) || 5000;
  const stage = document.getElementById('stuStage').value;
  const commissionStatus = document.getElementById('stuCommissionStatus').value;

  const nowStr = new Date().toLocaleString('en-US', { dateStyle: 'short', timeStyle: 'short' });

  const studentObj = {
    id: `stu-${Date.now()}`,
    name,
    phone,
    targetCountry: country,
    program,
    ieltsScore: ielts,
    commissionAmount: commission,
    commissionStatus,
    stage,
    dateAdded: nowStr,
    addedBy: STATE.currentEmployee
  };

  if (!center.students) center.students = [];
  center.students.push(studentObj);

  if (center.status === 'New' || center.status === 'FollowUp') {
    center.status = 'Partnered';
  }

  saveData();
  renderStudentReferrals(center);
  elements.studentForm.reset();
  renderApp();
}

function renderStudentReferrals(center) {
  if (!center.students || center.students.length === 0) {
    elements.studentReferralsList.innerHTML = '<p style="color:var(--text-muted); font-size:0.8rem">No student referrals added yet for this center.</p>';
    return;
  }

  elements.studentReferralsList.innerHTML = center.students.slice().reverse().map(stu => `
    <div class="log-item" style="border-left-color: var(--color-teal)">
      <div class="log-meta">
        <strong>🎓 ${stu.name} (${stu.phone})</strong>
        <span>${stu.targetCountry} — ${stu.stage}</span>
      </div>
      <div class="log-text">
        Program: ${stu.program} | IELTS: ${stu.ieltsScore} | Commission: ৳${stu.commissionAmount} (${stu.commissionStatus})
      </div>
    </div>
  `).join('');
}

function openModal(id) {
  STATE.activeModalCenterId = id;
  const center = STATE.centers.find(c => c.id === id);
  if (!center) return;

  elements.modalCenterName.textContent = center.name;
  elements.modalDistrict.textContent = center.district;
  elements.modalPhone.textContent = center.phone || 'N/A';
  elements.modalStatusBadge.textContent = formatStatusName(center.status);
  elements.modalStatusBadge.className = `badge badge-${center.status}`;

  elements.modalNoteInput.value = '';
  elements.modalFollowUpDate.value = center.followUpDate || '';

  renderModalLogs(center);
  elements.noteModal.classList.remove('hidden');
}

function renderModalLogs(center) {
  if (!center.notes || center.notes.length === 0) {
    elements.logsList.innerHTML = '<p style="color:var(--text-muted); font-size:0.8rem">No conversation logs recorded yet.</p>';
    return;
  }

  elements.logsList.innerHTML = center.notes.slice().reverse().map(log => `
    <div class="log-item">
      <div class="log-meta">
        <span>👤 ${log.employee || 'Employee'}</span>
        <span>🕒 ${log.date}</span>
      </div>
      <div class="log-text">${log.text}</div>
    </div>
  `).join('');
}

function closeModal() {
  elements.noteModal.classList.add('hidden');
  STATE.activeModalCenterId = null;
}

function saveModalNote() {
  if (!STATE.activeModalCenterId) return;
  const center = STATE.centers.find(c => c.id === STATE.activeModalCenterId);
  if (!center) return;

  const noteText = elements.modalNoteInput.value.trim();
  const followUpDate = elements.modalFollowUpDate.value;
  const nowStr = new Date().toLocaleString('en-US', { dateStyle: 'short', timeStyle: 'short' });

  if (noteText) {
    if (!center.notes) center.notes = [];
    center.notes.push({
      date: nowStr,
      employee: STATE.currentEmployee,
      text: noteText
    });
  }

  if (followUpDate) {
    center.followUpDate = followUpDate;
    if (center.status === 'New') {
      center.status = 'FollowUp';
    }
  }

  center.lastContact = nowStr;
  center.employee = STATE.currentEmployee;

  saveData();
  closeModal();
  renderApp();
}

function exportDataJSON() {
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(STATE.centers, null, 2));
  const downloadAnchor = document.createElement('a');
  downloadAnchor.setAttribute("href", dataStr);
  downloadAnchor.setAttribute("download", `Keystone_B2B_CRM_Updated_${new Date().toISOString().split('T')[0]}.json`);
  document.body.appendChild(downloadAnchor);
  downloadAnchor.click();
  downloadAnchor.remove();
}

document.addEventListener('DOMContentLoaded', initApp);
