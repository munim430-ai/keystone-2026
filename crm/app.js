// KEYSTONE B2B OUTREACH CRM - STANDALONE APP LOGIC
const STORAGE_KEY = 'KEYSTONE_B2B_CRM_CENTERS_V3';

const STATE = {
  centers: [],
  activeDistrict: 'ALL',
  activeStatus: 'ALL',
  cardsPerPage: 5,
  currentPage: 1,
  searchQuery: ''
};

const elements = {
  districtSelect: document.getElementById('districtSelect'),
  quickDistricts: document.getElementById('quickDistricts'),
  searchInput: document.getElementById('searchInput'),
  limitBtns: document.querySelectorAll('.limit-btn'),
  tabBtns: document.querySelectorAll('.tab-btn'),
  cardsGrid: document.getElementById('cardsGrid'),
  emptyState: document.getElementById('emptyState'),
  exportBtn: document.getElementById('exportBtn'),
  resetBtn: document.getElementById('resetBtn'),
  
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
  countLogged: document.getElementById('countLogged'),

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
  logsList: document.getElementById('logsList')
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
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed) && parsed.length >= 800) {
        STATE.centers = parsed;
      } else {
        await fetchFallbackJSON();
      }
    } catch (e) {
      await fetchFallbackJSON();
    }
  } else {
    await fetchFallbackJSON();
  }

  STATE.centers.forEach(c => {
    if (typeof c.studentCount !== 'number') c.studentCount = 0;
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

function resetToDefaultDatabase() {
  if (confirm('Reset database to load all 859 nationwide centers? Your logged notes will be refreshed.')) {
    localStorage.removeItem(STORAGE_KEY);
    fetchFallbackJSON().then(() => {
      populateDistrictSelect();
      renderApp();
    });
  }
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
  allPill.textContent = `All (${STATE.centers.length})`;
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
  elements.resetBtn.addEventListener('click', resetToDefaultDatabase);

  elements.closeModalBtn.addEventListener('click', closeModal);
  elements.saveNoteBtn.addEventListener('click', saveModalNote);
  elements.noteModal.addEventListener('click', (e) => {
    if (e.target === elements.noteModal) closeModal();
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
    } else if (STATE.activeStatus === 'LOGGED') {
      if (!center.notes || center.notes.length === 0) return false;
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
  
  let eager = 0, followup = 0, cold = 0, partnered = 0, newCount = 0, today = 0, totalStudents = 0, logged = 0;

  STATE.centers.forEach(c => {
    if (c.status === 'Eager') eager++;
    else if (c.status === 'FollowUp') followup++;
    else if (c.status === 'Cold') cold++;
    else if (c.status === 'Partnered') partnered++;
    else newCount++;

    if (c.followUpDate === todayStr) today++;
    if (c.notes && c.notes.length > 0) logged++;

    if (typeof c.studentCount === 'number') {
      totalStudents += c.studentCount;
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
  if (elements.countLogged) elements.countLogged.textContent = logged;
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
  const statusClass = `status-${center.status}`;
  const badgeClass = `badge-${center.status}`;

  const lastLog = center.notes && center.notes.length > 0 ? center.notes[center.notes.length - 1] : null;
  const studentCount = typeof center.studentCount === 'number' ? center.studentCount : 0;

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
        ${center.lastContact ? `<div class="contact-item"><span>🕒 Last Contact:</span> <span>${center.lastContact}</span></div>` : ''}
        ${center.followUpDate ? `<div class="contact-item"><span>📅 Callback Date:</span> <strong style="color:var(--color-followup)">${center.followUpDate}</strong></div>` : ''}
      </div>

      <!-- Quick Native Phone Dialer Button -->
      <div class="action-buttons-row">
        ${cleanPhone ? `<a href="tel:${cleanPhone}" class="btn-contact btn-call" title="Open Phone Dialer">📞 Call Phone Dialer</a>` : '<span class="no-phone-tag">No Phone Number</span>'}
        ${center.url ? `<a href="${center.url}" target="_blank" class="btn-contact btn-source" title="Open Facebook / Maps">🔗 Link</a>` : ''}
      </div>

      <!-- Agency Student Counter Control -->
      <div class="student-counter-box">
        <span class="student-counter-label">🎓 Agency Students:</span>
        <div class="counter-controls">
          <button class="cnt-btn btn-minus" data-id="${center.id}"> - </button>
          <span class="cnt-value">${studentCount}</span>
          <button class="cnt-btn btn-plus" data-id="${center.id}"> + </button>
        </div>
      </div>

      <!-- EMPLOYEE DECISION ACTION BAR -->
      <div class="decision-bar">
        <span class="decision-label">Select Center Status:</span>
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
          <button class="decision-btn btn-partnered ${center.status === 'Partnered' ? 'active' : ''}" data-action="Partnered" data-id="${center.id}">
            <span>🤝</span>
            <span>Partnered</span>
          </button>
        </div>
      </div>

      <!-- Call Notes & Response Summary -->
      <div class="card-notes-section">
        <div class="notes-header">
          <span>📜 Notes & Agency Responses (${center.notes ? center.notes.length : 0}):</span>
          <button class="btn-note open-note-btn" data-id="${center.id}">✍️ + Add Note</button>
        </div>
        ${lastLog ? `<div class="latest-note"><strong>${lastLog.date}:</strong> "${lastLog.text}"</div>` : '<div class="no-notes">No notes added yet. Click "+ Add Note" after calling.</div>'}
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

  document.querySelectorAll('.btn-plus').forEach(btn => {
    btn.addEventListener('click', () => {
      changeStudentCount(btn.dataset.id, 1);
    });
  });

  document.querySelectorAll('.btn-minus').forEach(btn => {
    btn.addEventListener('click', () => {
      changeStudentCount(btn.dataset.id, -1);
    });
  });
}

function changeStudentCount(id, delta) {
  const center = STATE.centers.find(c => c.id === id);
  if (!center) return;
  
  if (typeof center.studentCount !== 'number') center.studentCount = 0;
  center.studentCount = Math.max(0, center.studentCount + delta);
  
  saveData();
  renderApp();
}

function updateCenterStatus(id, newStatus) {
  const center = STATE.centers.find(c => c.id === id);
  if (!center) return;

  const nowStr = new Date().toLocaleString('en-US', { dateStyle: 'short', timeStyle: 'short' });
  center.status = newStatus;
  center.lastContact = nowStr;

  if (!center.notes) center.notes = [];
  center.notes.push({
    date: nowStr,
    text: `Marked status as [${formatStatusName(newStatus)}]`
  });

  saveData();

  if (newStatus === 'FollowUp') {
    openModal(id);
  } else {
    renderApp();
  }
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
    elements.logsList.innerHTML = '<p style="color:var(--text-muted); font-size:0.8rem">No call notes recorded yet.</p>';
    return;
  }

  elements.logsList.innerHTML = center.notes.slice().reverse().map(log => `
    <div class="log-item">
      <div class="log-meta">
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
