// Keystone Nationwide B2B & Student Management CRM Controller

let centers = [];
let students = [];
let selectedId = null; // selected center ID
let currentView = 'table'; // default to table view on desktop
let currentScriptTab = 'call';

const STORAGE_KEY_CENTERS = 'keystone_bd_b2b_crm_v3_centers';
const STORAGE_KEY_STUDENTS = 'keystone_bd_b2b_crm_v3_students';

// Supabase Cloud Integration & Real-time Sync state
let supabaseClient = null;
const STORAGE_KEY_SUPABASE_URL = 'keystone_supabase_url';
const STORAGE_KEY_SUPABASE_KEY = 'keystone_supabase_key';

document.addEventListener('DOMContentLoaded', async () => {
  initSupabase();
  await loadData();
  populateDistrictFilter();
  populateStudentCenterSelect();
  autoDetectView();
  if (centers.length > 0) {
    selectCenter(centers[0].id);
  }
});

// Auto-switch View based on Device Screen Width (Mobile Outreach vs Desktop Full Dashboard)
function autoDetectView() {
  const isMobile = window.innerWidth <= 768;
  currentView = isMobile ? 'mobile' : 'table';
  switchView(currentView);
}

window.addEventListener('resize', () => {
  const isMobile = window.innerWidth <= 768;
  if (isMobile && currentView === 'table') {
    switchView('mobile');
  } else if (!isMobile && currentView === 'mobile') {
    switchView('table');
  }
});

// Load Centers & Students Datasets
async function loadData() {
  if (supabaseClient) {
    await loadDataFromSupabase();
  } else {
    const savedCenters = localStorage.getItem(STORAGE_KEY_CENTERS);
    const savedStudents = localStorage.getItem(STORAGE_KEY_STUDENTS);

    if (savedCenters) {
      try { centers = JSON.parse(savedCenters); } catch (e) { console.error(e); }
    }
    if (savedStudents) {
      try { students = JSON.parse(savedStudents); } catch (e) { console.error(e); }
    }
  }

  if (centers.length === 0) {
    try {
      const res = await fetch('all_bangladesh_centers.json');
      centers = await res.json();
    } catch (e) { showToast('Failed to load centers dataset', 'error'); }
  }

  if (students.length === 0) {
    try {
      const res = await fetch('initial_students.json');
      students = await res.json();
    } catch (e) { students = []; }
  }

  saveToStorage();
}

function saveToStorage() {
  localStorage.setItem(STORAGE_KEY_CENTERS, JSON.stringify(centers));
  localStorage.setItem(STORAGE_KEY_STUDENTS, JSON.stringify(students));
}

// Supabase Cloud Synchronization & Settings
function initSupabase() {
  const url = localStorage.getItem(STORAGE_KEY_SUPABASE_URL);
  const key = localStorage.getItem(STORAGE_KEY_SUPABASE_KEY);
  const badge = document.getElementById('cloud-badge');
  const btn = document.getElementById('btn-cloud-sync');

  if (url && key && window.supabase) {
    try {
      supabaseClient = window.supabase.createClient(url, key);
      if (badge) {
        badge.innerHTML = '<i class="fa-solid fa-cloud-check"></i> Cloud Connected';
        badge.classList.add('connected');
      }
      if (btn) {
        btn.innerHTML = '<i class="fa-solid fa-cloud-check"></i> Cloud Connected';
        btn.className = 'btn btn-emerald';
      }
      setupRealtimeSubscriptions();
    } catch (e) {
      console.error('Supabase Init Error:', e);
    }
  } else {
    if (badge) {
      badge.innerHTML = '<i class="fa-solid fa-cloud"></i> Local Storage';
      badge.classList.remove('connected');
    }
    if (btn) {
      btn.innerHTML = '<i class="fa-solid fa-cloud-bolt"></i> Cloud Sync';
      btn.className = 'btn btn-cloud';
    }
  }
}

function openCloudSyncModal() {
  const url = localStorage.getItem(STORAGE_KEY_SUPABASE_URL) || '';
  const key = localStorage.getItem(STORAGE_KEY_SUPABASE_KEY) || '';
  document.getElementById('supabase-url').value = url;
  document.getElementById('supabase-key').value = key;
  document.getElementById('modal-cloud-sync').classList.add('active');
}

function closeCloudSyncModal() {
  document.getElementById('modal-cloud-sync').classList.remove('active');
}

async function saveCloudConfig() {
  const url = document.getElementById('supabase-url').value.trim();
  const key = document.getElementById('supabase-key').value.trim();

  if (!url || !key) {
    showToast('Please enter both Supabase URL and Anon Key', 'error');
    return;
  }

  localStorage.setItem(STORAGE_KEY_SUPABASE_URL, url);
  localStorage.setItem(STORAGE_KEY_SUPABASE_KEY, key);

  initSupabase();

  if (supabaseClient) {
    showToast('Connecting Supabase & syncing datasets...');
    await syncInitialDataToSupabase();
    await loadDataFromSupabase();
    closeCloudSyncModal();
    populateDistrictFilter();
    populateStudentCenterSelect();
    renderApp();
    showToast('Cloud Database Connected & Realtime Sync Active!');
  }
}

function disconnectCloudConfig() {
  localStorage.removeItem(STORAGE_KEY_SUPABASE_URL);
  localStorage.removeItem(STORAGE_KEY_SUPABASE_KEY);
  supabaseClient = null;
  initSupabase();
  closeCloudSyncModal();
  showToast('Switched to Local Storage mode');
}

async function syncInitialDataToSupabase() {
  if (!supabaseClient) return;
  try {
    const { data: existingCenters } = await supabaseClient.from('b2b_centers').select('id').limit(5);
    if (!existingCenters || existingCenters.length === 0) {
      for (let i = 0; i < centers.length; i += 50) {
        const batch = centers.slice(i, i + 50);
        await supabaseClient.from('b2b_centers').upsert(batch);
      }
    }
    const { data: existingStudents } = await supabaseClient.from('b2b_students').select('id').limit(5);
    if (!existingStudents || existingStudents.length === 0) {
      if (students.length > 0) {
        await supabaseClient.from('b2b_students').upsert(students);
      }
    }
  } catch (e) {
    console.error('Supabase initial sync error:', e);
  }
}

async function loadDataFromSupabase() {
  if (!supabaseClient) return;
  try {
    const { data: cData, error: cErr } = await supabaseClient.from('b2b_centers').select('*').order('id', { ascending: true });
    if (!cErr && cData && cData.length > 0) {
      centers = cData;
    }
    const { data: sData, error: sErr } = await supabaseClient.from('b2b_students').select('*').order('id', { ascending: true });
    if (!sErr && sData) {
      students = sData;
    }
    saveToStorage();
  } catch (e) {
    console.error('Failed to fetch from Supabase:', e);
  }
}

function setupRealtimeSubscriptions() {
  if (!supabaseClient) return;
  try {
    supabaseClient
      .channel('public:b2b_changes')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'b2b_centers' }, payload => {
        loadDataFromSupabase().then(() => {
          populateDistrictFilter();
          populateStudentCenterSelect();
          renderApp();
          showToast('Live update received from team member');
        });
      })
      .on('postgres_changes', { event: '*', schema: 'public', table: 'b2b_students' }, payload => {
        loadDataFromSupabase().then(() => {
          renderApp();
          showToast('Student list updated in real-time');
        });
      })
      .subscribe();
  } catch (e) {
    console.error('Realtime subscription error:', e);
  }
}

async function syncSingleCenterToCloud(center) {
  if (!supabaseClient) return;
  try {
    await supabaseClient.from('b2b_centers').upsert(center);
  } catch (e) {
    console.error('Error syncing center to cloud:', e);
  }
}

async function syncSingleStudentToCloud(student) {
  if (!supabaseClient) return;
  try {
    await supabaseClient.from('b2b_students').upsert(student);
  } catch (e) {
    console.error('Error syncing student to cloud:', e);
  }
}

// Reset Dataset
async function resetToInitial() {
  if (confirm('Are you sure you want to reset all CRM edits back to the initial dataset?')) {
    localStorage.removeItem(STORAGE_KEY_CENTERS);
    localStorage.removeItem(STORAGE_KEY_STUDENTS);
    centers = [];
    students = [];
    await loadData();
    populateDistrictFilter();
    populateStudentCenterSelect();
    renderApp();
    if (centers.length > 0) selectCenter(centers[0].id);
    showToast('CRM dataset reset to initial state');
  }
}

// Populate District Select Dropdown & Quick Selection Chips
function populateDistrictFilter() {
  const select = document.getElementById('filter-district');
  const chipsBar = document.getElementById('district-chips-bar');
  if (!select) return;

  const selectedValue = select.value || 'ALL';
  const counts = {};
  
  centers.forEach(c => {
    const d = c.district || 'Other';
    counts[d] = (counts[d] || 0) + 1;
  });

  const sortedDistricts = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);

  select.innerHTML = `<option value="ALL">📍 All 64 Districts — ${centers.length} Partner Centers</option>`;
  sortedDistricts.forEach(d => {
    const opt = document.createElement('option');
    opt.value = d;
    opt.textContent = `📍 ${d} District (${counts[d]} centers)`;
    select.appendChild(opt);
  });

  select.value = selectedValue;

  // Render Popular Quick District Chips
  if (chipsBar) {
    chipsBar.innerHTML = '';
    const popularDistricts = ['ALL', 'Rajshahi', 'Dhaka', 'Chittagong', 'Cumilla', 'Sylhet', 'Khulna', 'Bogura', 'Mymensingh', 'Dinajpur', 'Rangpur', 'Barishal'];

    popularDistricts.forEach(d => {
      const isSelected = d === select.value;
      const count = d === 'ALL' ? centers.length : (counts[d] || 0);

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = `btn btn-sm ${isSelected ? 'btn-primary' : 'btn-secondary'}`;
      btn.style.cssText = `padding: 0.25rem 0.65rem; font-size: 0.78rem; border-radius: 20px; font-weight: ${isSelected ? '700' : '500'};`;
      btn.innerHTML = d === 'ALL' ? `🌐 All Districts (${count})` : `📍 ${d} (${count})`;
      btn.onclick = () => {
        select.value = d;
        onDistrictSelectChange();
      };
      chipsBar.appendChild(btn);
    });
  }
}

function onDistrictSelectChange() {
  const selVal = document.getElementById('filter-district').value;
  const badge = document.getElementById('district-active-count');
  if (badge) {
    badge.textContent = selVal === 'ALL' ? 'Showing All 64 Districts' : `Active Filter: ${selVal} District`;
  }
  populateDistrictFilter(); // re-render chip highlights
  renderApp();
}

// Populate Center Dropdown in Add Student Modal
function populateStudentCenterSelect() {
  const select = document.getElementById('stu-center-id');
  if (!select) return;

  select.innerHTML = '';
  centers.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.id;
    opt.textContent = `[${c.district}] ${c.name} (${c.id})`;
    select.appendChild(opt);
  });
}

// Switch Navigation View
function switchView(view) {
  currentView = view;
  document.querySelectorAll('.nav-tab-btn').forEach(btn => btn.classList.remove('active'));
  const activeBtn = document.getElementById(`tab-btn-${view}`);
  if (activeBtn) activeBtn.classList.add('active');

  const mobileContainer = document.getElementById('view-mobile');
  if (mobileContainer) mobileContainer.style.display = view === 'mobile' ? 'flex' : 'none';

  document.getElementById('view-table').style.display = view === 'table' ? 'flex' : 'none';
  document.getElementById('view-students').style.display = view === 'students' ? 'flex' : 'none';
  document.getElementById('view-kanban').style.display = view === 'kanban' ? 'grid' : 'none';
  document.getElementById('view-ledger').style.display = view === 'ledger' ? 'block' : 'none';

  renderApp();
}

// Filter Centers
function getFilteredCenters() {
  const search = document.getElementById('search-input').value.toLowerCase().trim();
  const districtFilter = document.getElementById('filter-district').value;
  const statusFilter = document.getElementById('filter-status').value;
  const priorityFilter = document.getElementById('filter-priority').value;
  const commissionFilter = document.getElementById('filter-commission').value;

  return centers.filter(c => {
    const remarksText = Array.isArray(c.notes) ? c.notes.map(n => n.text).join(' ') : (c.remarks || '');
    
    const matchSearch = !search || 
      c.name.toLowerCase().includes(search) || 
      c.district.toLowerCase().includes(search) ||
      c.phone.toLowerCase().includes(search) || 
      (c.altPhone && c.altPhone.toLowerCase().includes(search)) ||
      (c.contactPerson && c.contactPerson.toLowerCase().includes(search)) ||
      remarksText.toLowerCase().includes(search);

    const matchDistrict = districtFilter === 'ALL' || c.district === districtFilter;
    const matchStatus = statusFilter === 'ALL' || c.status === statusFilter;
    const matchPriority = priorityFilter === 'ALL' || c.priority === priorityFilter;

    const rate = c.commissionRate || 5000;
    const earned = (c.enrolledStudents || 0) * rate;
    const paid = c.commissionPaid || 0;
    const pending = earned - paid;

    let matchCommission = true;
    if (commissionFilter === 'PENDING') matchCommission = pending > 0;
    if (commissionFilter === 'PAID') matchCommission = earned > 0 && pending <= 0;

    return matchSearch && matchDistrict && matchStatus && matchPriority && matchCommission;
  });
}

// Master Render App Controller
function renderApp() {
  updateMetrics();
  const filteredCenters = getFilteredCenters();
  document.getElementById('filtered-count').textContent = filteredCenters.length;

  if (currentView === 'mobile') {
    renderMobileView(filteredCenters);
  } else if (currentView === 'table') {
    renderTableView(filteredCenters);
  } else if (currentView === 'students') {
    renderStudentsView();
  } else if (currentView === 'kanban') {
    renderKanbanView(filteredCenters);
  } else if (currentView === 'ledger') {
    renderLedgerView(filteredCenters);
  }
}

// Render 0. Mobile Outreach Card Mode for Employees
function renderMobileView(filtered) {
  const container = document.getElementById('mobile-cards-container');
  if (!container) return;
  container.innerHTML = '';

  if (filtered.length === 0) {
    container.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 2rem; background: var(--bg-card); border-radius: var(--radius-md);">No coaching centers found matching your filter. Try selecting "All Districts" or clearing search.</div>`;
    return;
  }

  const displayList = filtered.slice(0, 100);

  displayList.forEach(c => {
    const primaryClean = c.phone ? c.phone.replace(/[^0-9+]/g, '') : '';
    const primaryWA = primaryClean.startsWith('+88') ? primaryClean.replace('+', '') : (primaryClean.startsWith('0') ? '88' + primaryClean : primaryClean);

    const altClean = c.altPhone ? c.altPhone.replace(/[^0-9+]/g, '') : '';
    const altWA = altClean.startsWith('+88') ? altClean.replace('+', '') : (altClean.startsWith('0') ? '88' + altClean : altClean);

    const card = document.createElement('div');
    card.className = `mobile-outreach-card ${c.id === selectedId ? 'selected' : ''}`;
    card.style.cssText = 'background: rgba(15, 23, 42, 0.95); border: 2px solid rgba(59, 130, 246, 0.3); border-radius: 12px; padding: 1rem; position: relative; box-shadow: 0 4px 15px rgba(0,0,0,0.3);';

    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
        <div>
          <span class="badge badge-district" style="font-size: 0.8rem; margin-bottom: 0.25rem;">📍 ${escapeHtml(c.district)} District</span>
          <h3 style="font-size: 1.1rem; font-weight: 700; color: white; margin-top: 0.25rem; line-height: 1.3;">${escapeHtml(c.name)}</h3>
          ${c.contactPerson ? `<div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 0.2rem;">👤 Contact: <strong>${escapeHtml(c.contactPerson)}</strong> ${c.designation ? `(${escapeHtml(c.designation)})` : ''}</div>` : ''}
        </div>
        <span class="badge ${getStatusBadgeClass(c.status)}" style="font-size: 0.85rem; padding: 0.3rem 0.6rem;">${c.status}</span>
      </div>

      <!-- GIANT EASY-TAP CALL & WHATSAPP BUTTONS -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.65rem; margin: 0.85rem 0;">
        ${c.phone ? `
          <a href="tel:${primaryClean}" class="btn btn-primary" style="justify-content: center; padding: 0.75rem; font-size: 0.95rem; font-weight: 700; text-decoration: none; border-radius: 8px;">
            <i class="fa-solid fa-phone" style="font-size: 1.1rem;"></i> 📞 CALL NOW
          </a>
          <a href="https://wa.me/${primaryWA}?text=${encodeURIComponent('আসসালামু আলাইকুম! কিস্টোন এডুকেশন থেকে B2B রেফারেল পার্টনারশিপ নিয়ে কথা বলতে চাচ্ছি।')}" target="_blank" class="btn btn-emerald" style="justify-content: center; padding: 0.75rem; font-size: 0.95rem; font-weight: 700; text-decoration: none; border-radius: 8px; background: #16a34a; color: white;">
            <i class="fa-brands fa-whatsapp" style="font-size: 1.2rem;"></i> 💬 WHATSAPP
          </a>
        ` : `<div style="grid-column: span 2; color: #94a3b8; font-style: italic; text-align: center;">No phone listed for this center</div>`}
      </div>

      ${c.altPhone ? `
        <div style="display: flex; gap: 0.5rem; margin-bottom: 0.85rem;">
          <a href="tel:${altClean}" class="btn btn-secondary btn-sm" style="flex: 1; justify-content: center; padding: 0.5rem;">
            <i class="fa-solid fa-phone-flip"></i> Call Alt: ${escapeHtml(c.altPhone)}
          </a>
          <a href="https://wa.me/${altWA}" target="_blank" class="btn btn-emerald btn-sm" style="flex: 1; justify-content: center; padding: 0.5rem;">
            <i class="fa-brands fa-whatsapp"></i> WA Alt Number
          </a>
        </div>
      ` : ''}

      <!-- 1-TAP QUICK STATUS ACTION BUTTONS -->
      <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; background: rgba(30, 41, 59, 0.7); padding: 0.65rem; border-radius: 8px; margin-top: 0.5rem;">
        <button class="btn btn-emerald btn-sm" onclick="quickUpdateStatus('${c.id}', 'Contacted')" style="flex: 1; min-width: 120px; justify-content: center; font-weight: 600;">
          <i class="fa-solid fa-circle-check"></i> ✅ Mark Contacted
        </button>
        <button class="btn btn-amber btn-sm" onclick="quickUpdateStatus('${c.id}', 'Interested')" style="flex: 1; min-width: 120px; justify-content: center; font-weight: 600;">
          <i class="fa-solid fa-star"></i> ⭐ Interested
        </button>
        <button class="btn btn-secondary btn-sm" onclick="selectCenter('${c.id}')" style="justify-content: center;">
          <i class="fa-solid fa-message"></i> Notes (${Array.isArray(c.notes) ? c.notes.length : 0})
        </button>
      </div>
    `;

    container.appendChild(card);
  });
}

function quickUpdateStatus(id, newStatus) {
  const c = centers.find(item => item.id === id);
  if (!c) return;

  const today = new Date().toISOString().split('T')[0];
  c.status = newStatus;
  c.lastContact = today;

  if (!Array.isArray(c.notes)) c.notes = [];
  c.notes.unshift({
    date: new Date().toLocaleString(),
    text: `📱 Employee marked status as ${newStatus} on ${today}`
  });

  saveToStorage();
  syncSingleCenterToCloud(c);
  renderApp();
  showToast(`Updated status of ${c.name} to ${newStatus}`);
}

// Update Top KPI Counters
function updateMetrics() {
  const totalCenters = centers.length;
  const districtsSet = new Set(centers.map(c => c.district));
  
  let totalReferred = 0;
  let totalEnrolled = 0;
  let totalEarned = 0;
  let totalPaid = 0;

  centers.forEach(c => {
    const ref = c.referredStudents || 0;
    const enr = c.enrolledStudents || 0;
    const rate = c.commissionRate || 5000;
    const paid = c.commissionPaid || 0;
    
    totalReferred += ref;
    totalEnrolled += enr;
    totalEarned += (enr * rate);
    totalPaid += paid;
  });

  const totalPending = totalEarned - totalPaid;

  document.getElementById('stat-total').textContent = totalCenters;
  document.getElementById('stat-districts').textContent = districtsSet.size;
  document.getElementById('stat-referred').textContent = totalReferred;
  document.getElementById('stat-enrolled').textContent = totalEnrolled;
  document.getElementById('stat-commission-earned').textContent = `৳${totalEarned.toLocaleString('en-IN')}`;
  document.getElementById('stat-commission-pending').textContent = `৳${totalPending.toLocaleString('en-IN')}`;
}

// Render Table View
function renderTableView(filtered) {
  const tbody = document.getElementById('centers-tbody');
  tbody.innerHTML = '';

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 2rem;">No matching coaching centers found.</td></tr>`;
    return;
  }

  const displayList = filtered.slice(0, 250);

  displayList.forEach(c => {
    const tr = document.createElement('tr');
    if (c.id === selectedId) tr.classList.add('selected');
    tr.onclick = () => selectCenter(c.id);

    const primaryClean = c.phone ? c.phone.replace(/[^0-9+]/g, '') : '';
    const primaryWA = primaryClean.startsWith('+88') ? primaryClean.replace('+', '') : (primaryClean.startsWith('0') ? '88' + primaryClean : primaryClean);

    const altClean = c.altPhone ? c.altPhone.replace(/[^0-9+]/g, '') : '';
    const altWA = altClean.startsWith('+88') ? altClean.replace('+', '') : (altClean.startsWith('0') ? '88' + altClean : altClean);

    const rate = c.commissionRate || 5000;
    const earned = (c.enrolledStudents || 0) * rate;
    const paid = c.commissionPaid || 0;
    const pending = earned - paid;

    tr.innerHTML = `
      <td style="font-weight: 600; color: var(--text-dim); font-size: 0.78rem;">${c.id}</td>
      <td style="font-weight: 600; color: var(--text-main);">
        ${escapeHtml(c.name)}
        ${c.link ? `<a href="${escapeHtml(c.link)}" target="_blank" onclick="event.stopPropagation()" style="margin-left: 4px; color: var(--text-dim);"><i class="fa-solid fa-arrow-up-right-from-square"></i></a>` : ''}
      </td>
      <td><span class="badge badge-district">${escapeHtml(c.district)}</span></td>
      <td>
        <div style="display: flex; flex-direction: column; gap: 0.2rem; font-size: 0.8rem;">
          ${c.phone ? `
            <div style="display: flex; align-items: center; gap: 0.3rem;">
              <span><i class="fa-solid fa-phone" style="font-size: 0.7rem; color: var(--primary);"></i> ${escapeHtml(c.phone)}</span>
              <a href="tel:${primaryClean}" onclick="event.stopPropagation()" class="action-link" title="Call Primary"><i class="fa-solid fa-phone"></i></a>
              <a href="https://wa.me/${primaryWA}" target="_blank" onclick="event.stopPropagation()" class="action-link wa" title="WhatsApp Primary"><i class="fa-brands fa-whatsapp"></i></a>
            </div>
          ` : '<span style="color: var(--text-dim); font-style: italic;">No Phone</span>'}

          ${c.altPhone ? `
            <div style="display: flex; align-items: center; gap: 0.3rem; color: var(--text-muted); font-size: 0.75rem;">
              <span><i class="fa-solid fa-phone-flip" style="font-size: 0.65rem; color: var(--accent-amber);"></i> ${escapeHtml(c.altPhone)}</span>
              <a href="tel:${altClean}" onclick="event.stopPropagation()" class="action-link" title="Call Alt"><i class="fa-solid fa-phone"></i></a>
              <a href="https://wa.me/${altWA}" target="_blank" onclick="event.stopPropagation()" class="action-link wa" title="WhatsApp Alt"><i class="fa-brands fa-whatsapp"></i></a>
            </div>
          ` : ''}
        </div>
      </td>
      <td><span class="badge ${getStatusBadgeClass(c.status)}">${c.status}</span></td>
      <td style="font-weight: 500;">
        <span style="color: #fbbf24;">${c.referredStudents || 0} Ref</span> / 
        <span style="color: #34d399; font-weight: 700;">${c.enrolledStudents || 0} Enr</span>
      </td>
      <td style="font-weight: 700; color: ${pending > 0 ? '#f87171' : '#94a3b8'};">
        ৳${pending.toLocaleString('en-IN')}
      </td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); selectCenter('${c.id}')">
          <i class="fa-solid fa-pen-to-square"></i> Select
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Render Students Directory View
function renderStudentsView() {
  const tbody = document.getElementById('students-tbody');
  tbody.innerHTML = '';

  const search = document.getElementById('search-input').value.toLowerCase().trim();
  const districtFilter = document.getElementById('filter-district').value;

  const filteredStudents = students.filter(s => {
    const matchSearch = !search || 
      s.name.toLowerCase().includes(search) || 
      s.phone.toLowerCase().includes(search) || 
      s.centerName.toLowerCase().includes(search) ||
      (s.targetCountry && s.targetCountry.toLowerCase().includes(search));

    const matchDistrict = districtFilter === 'ALL' || s.district === districtFilter;
    return matchSearch && matchDistrict;
  });

  document.getElementById('students-count').textContent = filteredStudents.length;

  if (filteredStudents.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-muted); padding: 2rem;">No student referrals found matching your search. Click "Add Student Referral" above to log a new student.</td></tr>`;
    return;
  }

  filteredStudents.forEach(s => {
    const tr = document.createElement('tr');

    const cleanPhone = s.phone ? s.phone.replace(/[^0-9+]/g, '') : '';
    const waPhone = cleanPhone.startsWith('+88') ? cleanPhone.replace('+', '') : (cleanPhone.startsWith('0') ? '88' + cleanPhone : cleanPhone);

    tr.innerHTML = `
      <td style="font-weight: 600; color: var(--text-dim); font-size: 0.78rem;">${s.id}</td>
      <td style="font-weight: 700; color: white;">${escapeHtml(s.name)}</td>
      <td>
        <div style="display: flex; align-items: center; gap: 0.3rem;">
          <span>${escapeHtml(s.phone)}</span>
          <a href="tel:${cleanPhone}" class="action-link"><i class="fa-solid fa-phone"></i></a>
          <a href="https://wa.me/${waPhone}" target="_blank" class="action-link wa"><i class="fa-brands fa-whatsapp"></i></a>
        </div>
      </td>
      <td style="font-weight: 600; color: var(--primary);">${escapeHtml(s.centerName)}</td>
      <td><span class="badge badge-district">${escapeHtml(s.district)}</span></td>
      <td>
        <div><strong>${escapeHtml(s.targetCountry)}</strong></div>
        <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(s.program || '')}</div>
      </td>
      <td><span class="badge badge-medium">${escapeHtml(s.ieltsScore || 'No IELTS')}</span></td>
      <td><span class="badge ${getStudentStageBadgeClass(s.stage)}">${s.stage}</span></td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="selectCenter('${s.centerId}'); switchView('table');">
          <i class="fa-solid fa-building"></i> View Partner
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function getStudentStageBadgeClass(stage) {
  switch (stage) {
    case 'Inquiry': return 'badge-new';
    case 'Counselled': return 'badge-contacted';
    case 'Docs Collected': return 'badge-interested';
    case 'Applied': return 'badge-scheduled';
    case 'Offer Received': return 'badge-scheduled';
    case 'Visa Issued': return 'badge-partnered';
    case 'Enrolled': return 'badge-partnered';
    default: return 'badge-new';
  }
}

// Render Kanban View
function renderKanbanView(filtered) {
  const board = document.getElementById('view-kanban');
  board.innerHTML = '';

  const columns = [
    { title: 'New Leads', status: 'New', color: 'badge-new' },
    { title: 'Contacted', status: 'Contacted', color: 'badge-contacted' },
    { title: 'Interested', status: 'Interested', color: 'badge-interested' },
    { title: 'Seminar Scheduled', status: 'Scheduled', color: 'badge-scheduled' },
    { title: 'Signed Partners', status: 'Partnered', color: 'badge-partnered' },
    { title: 'Ineligible / Dead', status: 'Rejected', color: 'badge-rejected' }
  ];

  columns.forEach(col => {
    const colCenters = filtered.filter(c => c.status === col.status);

    const colEl = document.createElement('div');
    colEl.className = 'kanban-col';
    colEl.innerHTML = `
      <div class="kanban-col-header">
        <span>${col.title}</span>
        <span class="badge ${col.color}">${colCenters.length}</span>
      </div>
      <div class="kanban-col-body">
        ${colCenters.slice(0, 50).map(c => `
          <div class="kanban-card ${c.id === selectedId ? 'selected' : ''}" onclick="selectCenter('${c.id}')">
            <h4>${escapeHtml(c.name)}</h4>
            <p><i class="fa-solid fa-location-dot"></i> ${escapeHtml(c.district)} District</p>
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; color: var(--text-dim);">
              <span>${c.phone || 'No phone'}</span>
              <span style="color: #34d399; font-weight: 600;">${c.enrolledStudents || 0} Enrolled</span>
            </div>
          </div>
        `).join('')}
      </div>
    `;
    board.appendChild(colEl);
  });
}

// Render Commission Ledger View
function renderLedgerView(filtered) {
  let totalEnrolled = 0;
  let totalEarned = 0;
  let totalPaid = 0;

  filtered.forEach(c => {
    const enr = c.enrolledStudents || 0;
    const rate = c.commissionRate || 5000;
    const paid = c.commissionPaid || 0;
    totalEnrolled += enr;
    totalEarned += (enr * rate);
    totalPaid += paid;
  });

  const totalPending = totalEarned - totalPaid;

  document.getElementById('ledger-enrolled-count').textContent = totalEnrolled;
  document.getElementById('ledger-total-earned').textContent = `৳${totalEarned.toLocaleString('en-IN')}`;
  document.getElementById('ledger-total-paid').textContent = `৳${totalPaid.toLocaleString('en-IN')}`;
  document.getElementById('ledger-total-pending').textContent = `৳${totalPending.toLocaleString('en-IN')}`;

  const tbody = document.getElementById('ledger-tbody');
  tbody.innerHTML = '';

  const activePartners = filtered.filter(c => (c.enrolledStudents || 0) > 0 || (c.commissionPaid || 0) > 0);

  if (activePartners.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-muted); padding: 2rem;">No student referrals/commissions logged yet. Select a center to add enrolled students.</td></tr>`;
    return;
  }

  activePartners.forEach(c => {
    const enr = c.enrolledStudents || 0;
    const rate = c.commissionRate || 5000;
    const earned = enr * rate;
    const paid = c.commissionPaid || 0;
    const pending = earned - paid;

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${c.id}</td>
      <td style="font-weight: 600;">${escapeHtml(c.name)}</td>
      <td><span class="badge badge-district">${escapeHtml(c.district)}</span></td>
      <td style="font-weight: 700; color: #34d399;">${enr} Students</td>
      <td>৳${rate.toLocaleString('en-IN')}</td>
      <td style="font-weight: 600;">৳${earned.toLocaleString('en-IN')}</td>
      <td style="color: #60a5fa;">৳${paid.toLocaleString('en-IN')}</td>
      <td style="font-weight: 700; color: ${pending > 0 ? '#f87171' : '#34d399'};">৳${pending.toLocaleString('en-IN')}</td>
      <td>
        ${pending > 0 ? `
          <button class="btn btn-emerald btn-sm" onclick="payCommissionPrompt('${c.id}')">
            <i class="fa-solid fa-money-bill-transfer"></i> Record Payout
          </button>
        ` : `<span style="color: #34d399; font-size: 0.8rem;"><i class="fa-solid fa-circle-check"></i> Settled</span>`}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Select Partner Center & Render Right Side Inspector Panel
function selectCenter(id) {
  selectedId = id;

  const c = centers.find(item => item.id === id);
  if (!c) return;

  document.getElementById('detail-id-badge').textContent = c.id;
  document.getElementById('detail-id-badge').className = `badge ${getStatusBadgeClass(c.status)}`;

  const primaryClean = c.phone ? c.phone.replace(/[^0-9+]/g, '') : '';
  const primaryWA = primaryClean.startsWith('+88') ? primaryClean.replace('+', '') : (primaryClean.startsWith('0') ? '88' + primaryClean : primaryClean);

  const altClean = c.altPhone ? c.altPhone.replace(/[^0-9+]/g, '') : '';
  const altWA = altClean.startsWith('+88') ? altClean.replace('+', '') : (altClean.startsWith('0') ? '88' + altClean : altClean);

  const rate = c.commissionRate || 5000;
  const earned = (c.enrolledStudents || 0) * rate;
  const paid = c.commissionPaid || 0;
  const pending = earned - paid;

  const centerStudents = students.filter(s => s.centerId === c.id);
  const notesList = Array.isArray(c.notes) ? c.notes : [];

  const container = document.getElementById('detail-content');
  container.innerHTML = `
    <div style="margin-bottom: 0.85rem;">
      <h4 style="font-size: 1.1rem; font-weight: 700; color: white; margin-bottom: 0.2rem;">${escapeHtml(c.name)}</h4>
      <p style="font-size: 0.8rem; color: var(--text-muted);"><i class="fa-solid fa-location-dot" style="color: var(--primary);"></i> ${escapeHtml(c.district)} District</p>
    </div>

    <!-- Phone & Alternative Number Box -->
    <div style="background: rgba(15, 23, 42, 0.6); padding: 0.75rem; border-radius: var(--radius-sm); margin-bottom: 1rem; border: 1px solid var(--border-color);">
      <div style="margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
        <div>
          <div style="font-size: 0.72rem; color: var(--text-dim);">Primary Phone / WhatsApp</div>
          <div style="font-weight: 600; font-size: 0.85rem;">${c.phone ? escapeHtml(c.phone) : '<span style="color: var(--text-dim);">None</span>'}</div>
        </div>
        ${c.phone ? `
          <div style="display: flex; gap: 0.35rem;">
            <a href="tel:${primaryClean}" class="btn btn-primary btn-sm"><i class="fa-solid fa-phone"></i> Call</a>
            <a href="https://wa.me/${primaryWA}" target="_blank" class="btn btn-emerald btn-sm"><i class="fa-brands fa-whatsapp"></i> WA</a>
          </div>
        ` : ''}
      </div>

      <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255, 255, 255, 0.05); padding-top: 0.5rem;">
        <div>
          <div style="font-size: 0.72rem; color: var(--text-dim);">Alternative / Secondary Number</div>
          <div style="font-weight: 600; font-size: 0.85rem; color: var(--accent-amber);">${c.altPhone ? escapeHtml(c.altPhone) : '<span style="color: var(--text-dim); font-weight: normal;">None listed</span>'}</div>
        </div>
        ${c.altPhone ? `
          <div style="display: flex; gap: 0.35rem;">
            <a href="tel:${altClean}" class="btn btn-secondary btn-sm"><i class="fa-solid fa-phone-flip"></i> Call</a>
            <a href="https://wa.me/${altWA}" target="_blank" class="btn btn-emerald btn-sm"><i class="fa-brands fa-whatsapp"></i> WA</a>
          </div>
        ` : ''}
      </div>
    </div>

    <!-- Student Referral Pipeline Tracker Box -->
    <div style="background: rgba(15, 23, 42, 0.6); padding: 0.75rem; border-radius: var(--radius-sm); margin-bottom: 1rem; border: 1px solid var(--border-color);">
      <div style="font-size: 0.8rem; font-weight: 600; color: white; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
        <span><i class="fa-solid fa-user-graduate" style="color: var(--accent-amber);"></i> Referred Students Pipeline</span>
        <button class="btn btn-emerald btn-sm" onclick="openAddStudentModal('${c.id}')"><i class="fa-solid fa-plus"></i> Add Student</button>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 0.65rem;">
        <div style="background: rgba(30, 41, 59, 0.6); padding: 0.5rem; border-radius: var(--radius-sm); text-align: center;">
          <div style="font-size: 0.7rem; color: var(--text-muted);">Referred Students</div>
          <div style="font-size: 1.2rem; font-weight: 700; color: #fbbf24;">${c.referredStudents || 0}</div>
          <div style="display: flex; justify-content: center; gap: 0.3rem; margin-top: 0.3rem;">
            <button class="btn btn-secondary btn-sm" onclick="adjustStudentCount('${c.id}', 'ref', -1)">-</button>
            <button class="btn btn-secondary btn-sm" onclick="adjustStudentCount('${c.id}', 'ref', 1)">+</button>
          </div>
        </div>

        <div style="background: rgba(30, 41, 59, 0.6); padding: 0.5rem; border-radius: var(--radius-sm); text-align: center;">
          <div style="font-size: 0.7rem; color: var(--text-muted);">Enrolled Students</div>
          <div style="font-size: 1.2rem; font-weight: 700; color: #34d399;">${c.enrolledStudents || 0}</div>
          <div style="display: flex; justify-content: center; gap: 0.3rem; margin-top: 0.3rem;">
            <button class="btn btn-secondary btn-sm" onclick="adjustStudentCount('${c.id}', 'enr', -1)">-</button>
            <button class="btn btn-secondary btn-sm" onclick="adjustStudentCount('${c.id}', 'enr', 1)">+</button>
          </div>
        </div>
      </div>

      <!-- Associated Student List -->
      <div style="font-size: 0.75rem; color: var(--text-dim); margin-bottom: 0.35rem;">Linked Students (${centerStudents.length}):</div>
      ${centerStudents.length > 0 ? centerStudents.map(s => `
        <div style="background: rgba(15, 23, 42, 0.8); padding: 0.45rem 0.65rem; border-radius: var(--radius-sm); margin-bottom: 0.35rem; font-size: 0.78rem; display: flex; justify-content: space-between; align-items: center;">
          <div>
            <strong style="color: white;">${escapeHtml(s.name)}</strong> (${escapeHtml(s.targetCountry)})
            <div style="font-size: 0.7rem; color: var(--text-muted);">${escapeHtml(s.phone)} · IELTS: ${escapeHtml(s.ieltsScore || 'None')}</div>
          </div>
          <span class="badge ${getStudentStageBadgeClass(s.stage)}">${s.stage}</span>
        </div>
      `).join('') : `<div style="font-size: 0.75rem; color: var(--text-dim); font-style: italic;">No specific students added yet. Click "Add Student" to link one.</div>`}
    </div>

    <!-- Financial & Commission Tracker Box -->
    <div style="background: rgba(15, 23, 42, 0.6); padding: 0.75rem; border-radius: var(--radius-sm); margin-bottom: 1rem; border: 1px solid rgba(16, 185, 129, 0.3);">
      <div style="font-size: 0.8rem; font-weight: 600; color: white; margin-bottom: 0.5rem;">
        <i class="fa-solid fa-coins" style="color: var(--accent-emerald);"></i> Partner Commission Tracker (BDT)
      </div>
      
      <div style="font-size: 0.78rem; display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
        <span style="color: var(--text-muted);">Rate per Student:</span>
        <span style="font-weight: 600;">৳${rate.toLocaleString('en-IN')}</span>
      </div>
      <div style="font-size: 0.78rem; display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
        <span style="color: var(--text-muted);">Total Earned (${c.enrolledStudents || 0} enrolled):</span>
        <span style="font-weight: 700; color: #34d399;">৳${earned.toLocaleString('en-IN')}</span>
      </div>
      <div style="font-size: 0.78rem; display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
        <span style="color: var(--text-muted);">Commission Paid Out:</span>
        <span style="font-weight: 600; color: #60a5fa;">৳${paid.toLocaleString('en-IN')}</span>
      </div>
      <div style="font-size: 0.85rem; display: flex; justify-content: space-between; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 0.3rem; margin-top: 0.3rem;">
        <span style="font-weight: 600;">Pending Due:</span>
        <span style="font-weight: 700; color: ${pending > 0 ? '#f87171' : '#34d399'};">৳${pending.toLocaleString('en-IN')}</span>
      </div>

      ${pending > 0 ? `
        <button class="btn btn-emerald btn-sm" style="width: 100%; margin-top: 0.6rem;" onclick="payCommissionPrompt('${c.id}')">
          <i class="fa-solid fa-money-bill-transfer"></i> Record Payout to Partner
        </button>
      ` : ''}
    </div>

    <!-- Main Lead Form Edit -->
    <form onsubmit="saveCenterDetails(event, '${c.id}')">
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
        <div class="form-group">
          <label>Contact Person</label>
          <input type="text" id="edit-contact-person" class="form-control" value="${escapeHtml(c.contactPerson || '')}" placeholder="e.g. Mr. Rahat">
        </div>
        <div class="form-group">
          <label>Designation</label>
          <input type="text" id="edit-designation" class="form-control" value="${escapeHtml(c.designation || '')}" placeholder="e.g. Director">
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
        <div class="form-group">
          <label>Primary Phone</label>
          <input type="text" id="edit-phone" class="form-control" value="${escapeHtml(c.phone || '')}">
        </div>
        <div class="form-group">
          <label>Alternative Phone</label>
          <input type="text" id="edit-alt-phone" class="form-control" value="${escapeHtml(c.altPhone || '')}" placeholder="Secondary mobile">
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
        <div class="form-group">
          <label>Outreach Status</label>
          <select id="edit-status" class="form-control">
            <option value="New" ${c.status === 'New' ? 'selected' : ''}>New (Not Contacted)</option>
            <option value="Contacted" ${c.status === 'Contacted' ? 'selected' : ''}>Contacted</option>
            <option value="Interested" ${c.status === 'Interested' ? 'selected' : ''}>Interested</option>
            <option value="Scheduled" ${c.status === 'Scheduled' ? 'selected' : ''}>Seminar Scheduled</option>
            <option value="Partnered" ${c.status === 'Partnered' ? 'selected' : ''}>Signed B2B Partner</option>
            <option value="Rejected" ${c.status === 'Rejected' ? 'selected' : ''}>Ineligible / Dead</option>
          </select>
        </div>

        <div class="form-group">
          <label>Priority</label>
          <select id="edit-priority" class="form-control">
            <option value="High" ${c.priority === 'High' ? 'selected' : ''}>High Priority (IELTS)</option>
            <option value="Medium" ${c.priority === 'Medium' ? 'selected' : ''}>Medium Priority</option>
          </select>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
        <div class="form-group">
          <label>Commission Rate (BDT)</label>
          <input type="number" id="edit-commission-rate" class="form-control" value="${c.commissionRate || 5000}">
        </div>
        <div class="form-group">
          <label>Last Contact Date</label>
          <input type="date" id="edit-last-contact" class="form-control" value="${c.lastContact || ''}">
        </div>
      </div>

      <div style="display: flex; gap: 0.5rem; margin-top: 0.75rem;">
        <button type="submit" class="btn btn-primary" style="flex: 1;"><i class="fa-solid fa-floppy-disk"></i> Update Profile</button>
        <button type="button" class="btn btn-secondary" onclick="logQuickTouch('${c.id}')" title="Set Today as Last Contact"><i class="fa-solid fa-clock-rotate-left"></i> Touch Today</button>
      </div>
    </form>

    <!-- Remarks & Activity Log Timeline Section -->
    <div style="margin-top: 1.25rem; border-top: 1px solid var(--border-color); padding-top: 1rem;">
      <div style="font-size: 0.85rem; font-weight: 600; color: white; margin-bottom: 0.65rem;">
        <i class="fa-solid fa-comments" style="color: var(--primary);"></i> Activity Remarks & Call History
      </div>

      <form onsubmit="addRemark(event, '${c.id}')" style="margin-bottom: 0.85rem;">
        <div class="form-group">
          <textarea id="new-remark-input" class="form-control" placeholder="Add a new call remark or activity log..." required></textarea>
        </div>
        <button type="submit" class="btn btn-emerald btn-sm" style="width: 100%;"><i class="fa-solid fa-plus"></i> Add Remark Log</button>
      </form>

      <div style="max-height: 220px; overflow-y: auto;">
        ${notesList.length > 0 ? notesList.map(n => `
          <div class="remark-entry">
            <div class="remark-date">${escapeHtml(n.date)}</div>
            <div>${escapeHtml(n.text)}</div>
          </div>
        `).join('') : `<p style="font-size: 0.78rem; color: var(--text-dim); font-style: italic;">No remarks added yet.</p>`}
      </div>
    </div>
  `;

  renderScript();
}

// Adjust Student Count Buttons
function adjustStudentCount(id, type, delta) {
  const c = centers.find(item => item.id === id);
  if (!c) return;

  if (type === 'ref') {
    c.referredStudents = Math.max(0, (c.referredStudents || 0) + delta);
  } else if (type === 'enr') {
    c.enrolledStudents = Math.max(0, (c.enrolledStudents || 0) + delta);
  }

  saveToStorage();
  syncSingleCenterToCloud(c);
  renderApp();
  selectCenter(id);
  showToast(`Updated student count for ${c.name}`);
}

// Pay Commission Prompt
function payCommissionPrompt(id) {
  const c = centers.find(item => item.id === id);
  if (!c) return;

  const rate = c.commissionRate || 5000;
  const earned = (c.enrolledStudents || 0) * rate;
  const paid = c.commissionPaid || 0;
  const pending = earned - paid;

  const amountStr = prompt(`Enter payout amount in BDT to record for ${c.name} (Pending Due: ৳${pending}):`, pending);
  if (!amountStr) return;

  const amount = parseInt(amountStr, 10);
  if (isNaN(amount) || amount <= 0) {
    showToast('Invalid payout amount', 'error');
    return;
  }

  c.commissionPaid = (c.commissionPaid || 0) + amount;
  
  if (!Array.isArray(c.notes)) c.notes = [];
  c.notes.unshift({
    date: new Date().toLocaleString(),
    text: `💰 Commission Payout Recorded by Founder: Paid ৳${amount.toLocaleString('en-IN')} (Total Paid: ৳${c.commissionPaid.toLocaleString('en-IN')})`
  });

  saveToStorage();
  syncSingleCenterToCloud(c);
  renderApp();
  selectCenter(id);
  showToast(`Recorded commission payout of ৳${amount.toLocaleString('en-IN')} to ${c.name}`);
}

// Add Timestamped Remark Log
function addRemark(e, id) {
  e.preventDefault();
  const c = centers.find(item => item.id === id);
  if (!c) return;

  const text = document.getElementById('new-remark-input').value.trim();
  if (!text) return;

  if (!Array.isArray(c.notes)) c.notes = [];
  c.notes.unshift({
    date: new Date().toLocaleString(),
    text: text
  });

  saveToStorage();
  syncSingleCenterToCloud(c);
  selectCenter(id);
  showToast('Remark added to partner timeline');
}

// Save Updated Center Details Form
function saveCenterDetails(e, id) {
  e.preventDefault();
  const c = centers.find(item => item.id === id);
  if (!c) return;

  c.contactPerson = document.getElementById('edit-contact-person').value.trim();
  c.designation = document.getElementById('edit-designation').value.trim();
  c.phone = document.getElementById('edit-phone').value.trim();
  c.altPhone = document.getElementById('edit-alt-phone').value.trim();
  c.status = document.getElementById('edit-status').value;
  c.priority = document.getElementById('edit-priority').value;
  c.commissionRate = parseInt(document.getElementById('edit-commission-rate').value, 10) || 5000;
  c.lastContact = document.getElementById('edit-last-contact').value;

  saveToStorage();
  syncSingleCenterToCloud(c);
  renderApp();
  selectCenter(id);
  showToast(`Updated details for ${c.name}`);
}

// Quick Log Today's Contact
function logQuickTouch(id) {
  const c = centers.find(item => item.id === id);
  if (!c) return;

  const today = new Date().toISOString().split('T')[0];
  c.lastContact = today;
  if (c.status === 'New') c.status = 'Contacted';

  if (!Array.isArray(c.notes)) c.notes = [];
  c.notes.unshift({
    date: new Date().toLocaleString(),
    text: `📞 Outreach Call/Message conducted on ${today}`
  });

  saveToStorage();
  syncSingleCenterToCloud(c);
  renderApp();
  selectCenter(id);
  showToast(`Logged outreach for today (${today})`);
}

// Cold Call Script Generator Engine
function switchScript(tab) {
  currentScriptTab = tab;
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  event.target.classList.add('active');
  renderScript();
}

function renderScript() {
  const container = document.getElementById('script-container');
  const c = centers.find(item => item.id === selectedId) || { name: '[CENTER_NAME]', district: '[DISTRICT]', contactPerson: 'স্যার/ম্যাম' };

  const centerName = c.name;
  const district = c.district;
  const person = c.contactPerson ? c.contactPerson : 'স্যার/ম্যাম';

  let text = '';

  if (currentScriptTab === 'call') {
    text = `📞 OUTREACH CALL PITCH (To ${centerName}, ${district}):

"আসসালামু আলাইকুম! আমি কিস্টোন এডুকেশন থেকে বলছি। আমরা ${district} জেলায় আপনার সেন্টারের সাথে একটি এক্সক্লুসিভ B2B রেফারেল পার্টনারশিপের জন্য নক করেছি। আপনার সেন্টারের ${person}-এর সাথে একটু কথা বলতে চাই।

আমরা দেখেছি আপনারা ${district}-এ IELTS ও ল্যাঙ্গুয়েজ কোচিং করাচ্ছেন। আপনাদের অনেক স্টুডেন্ট সাউথ কোরিয়া, মালয়েশিয়া বা কানাডায় উচ্চশিক্ষার জন্য যেতে চায়। 

আমরা অফার করছি:
আপনার সেন্টার থেকে যেকোনো স্টুডেন্ট আমাদের কাছে রেফার করলে এবং তাদের ভর্তি/ভিসা সম্পন্ন হলে, আমরা আপনাকে প্রতি ভর্তি স্টুডেন্টে ৳৫,০০০ – ৳১০,০০০ স্পট কমিশন দিব। 

আপনার সেন্টারের কোনো খরচ বা রিস্ক নেই — স্টুডেন্ট ভর্তি হলেই নগদ পেমেন্ট। আর স্টুডেন্টের জন্য আমাদের নীতি: 'নো ভিসা, নো ফি'।

আপনার WhatsApp নাম্বারটা দিলে কি আমাদের অফিশিয়াল B2B পার্টনারশিপ অফার পাঠাবো?"`;

  } else if (currentScriptTab === 'wa1') {
    text = `📱 TOUCH 1 — WHATSAPP INTRO (To ${centerName}, ${district}):

আসসালামু আলাইকুম ${person}! 

আমি কিস্টোন এডুকেশন থেকে বলছি। 

${district} জেলার অন্যতম শীর্ষ কোচিং সেন্টারের সাথে B2B রেফারেল পার্টনারশিপের জন্য আপনাকে নক করেছি।

🎯 আমাদের বিটুবি অফার:
✅ আপনার রেফার করা প্রতি ভর্তি স্টুডেন্টে ৳৫,০০০ - ৳১০,০০০ স্পট কমিশন
✅ কোনো রেজিস্ট্রেশন বা আগাম ফি নেই
✅ স্টুডেন্টের ভিসা ও ভর্তি নিশ্চিত হলেই পেমেন্ট
✅ আপনার সেন্টারের স্টুডেন্টদের জন্য ফ্রি স্কলারশিপ সেমিনার

🇰🇷 Special Focus: South Korea (IELTS সহ ও IELTS ছাড়া EAP প্রোগ্রাম)
🇲🇾 Malaysia | 🇨🇦 Canada | 🇬🇧 UK

📞 সরাসরি কথা বলুন: 01941646278
🌐 www.keystoneeducations.com
📍 কিস্টোন এডুকেশন`;

  } else if (currentScriptTab === 'wa2') {
    text = `🔄 TOUCH 2 & 3 — FOLLOW-UP MESSAGE (To ${centerName}):

আসসালামু আলাইকুম ${person}! 

আশা করি ভালো আছেন। কিস্টোন এডুকেশন থেকে বলছি। 

একটি কুইক ফলো-আপ — আপনার ${centerName} থেকে যদি মাসে মাত্র ২ জন স্টুডেন্টও আমাদের কাছে কোরিয়া বা মালয়েশিয়ার জন্য রেফার হয়, আপনার সেন্টারের অতিরিক্ত বোনাস ইনকাম ৳১০,০০০ - ৳২০,০০০/মাস!

স্টুডেন্টদের সম্পূর্ণ ফ্রি ফাইল এসেসমেন্ট ও কাউন্সেলিং আমরাই সম্পন্ন করবো। 

চলুন এই সপ্তাহে ফোনে ১০ মিনিটের একটি বিটুবি ডিসকাশন করি?

📞 সরাসরি ফোন: 01941646278`;

  } else if (currentScriptTab === 'objection') {
    text = `🛡️ OUTREACH OBJECTION HANDLERS:

1️⃣ Objection: "আপনাদের কেন বিশ্বাস করবো?"
👉 "আমাদের ফাউন্ডার সাউথ কোরিয়াতে ৯ বছর কাটিয়েছেন এবং বিশ্ববিদ্যালয়ের সাথে আমাদের সরাসরি নেটওয়ার্ক রয়েছে। আমরা কোনো অগ্রিম ফি নিই না — ভিসা না হলে কোনো টাকা দিতে হয় না। আপনি নিজে studyinkorea.go.kr থেকে সব তথ্য যাচাই করতে পারবেন।"

2️⃣ Objection: "আমরা তো অন্য এজেন্সির সাথে অলরেডি কাজ করি।"
👉 "আমরা আপনার বর্তমান এজেন্সির বিকল্প হতে চাই না, বরং আপনার স্টুডেন্টদের জন্য একটা বিশ্বস্ত অতিরিক্ত অপশন তৈরি করতে চাই। বিশেষ করে সাউথ কোরিয়ার EAP প্রোগ্রাম এবং IELTS স্কলারশিপ লেডারে আমরা সবচেয়ে দ্রুততম প্লেসমেন্ট দিই।"

3️⃣ Objection: "কমিশন কখন কীভাবে পাবো?"
👉 "স্টুডেন্টের অফার লেটার ও ভিসা কনফার্ম হলেই আপনার ব্যাংক একাউন্ট বা বিকাশ এ পার্টনার কমিশন ৳৫,০০০-১০,০০০ সরাসরি ক্যাশআউট করা হয়।"`;
  }

  container.textContent = text;
}

function copyCurrentScript() {
  const container = document.getElementById('script-container');
  navigator.clipboard.writeText(container.textContent).then(() => {
    showToast('Outreach script copied!');
  });
}

// Modal 1: B2B Coaching Center Modal Handlers
function openAddCenterModal() {
  document.getElementById('add-center-modal').classList.add('active');
}

function closeAddCenterModal() {
  document.getElementById('add-center-modal').classList.remove('active');
  document.getElementById('add-center-form').reset();
}

function handleAddCenter(e) {
  e.preventDefault();
  const name = document.getElementById('add-name').value.trim();
  const district = document.getElementById('add-district').value.trim();
  const phone = document.getElementById('add-phone').value.trim();
  const altPhone = document.getElementById('add-alt-phone').value.trim();
  const contactPerson = document.getElementById('add-contact').value.trim();
  const designation = document.getElementById('add-designation').value.trim();
  const link = document.getElementById('add-link').value.trim();
  const priority = document.getElementById('add-priority').value;
  const commissionRate = parseInt(document.getElementById('add-commission-rate').value, 10) || 5000;
  const remarksText = document.getElementById('add-remarks').value.trim();

  const newCenter = {
    id: `b2b-${(centers.length + 1).toString().padStart(4, '0')}`,
    name: name,
    district: district,
    phone: phone,
    altPhone: altPhone,
    contactPerson: contactPerson,
    designation: designation,
    link: link,
    status: 'New',
    priority: priority,
    lastContact: '',
    referredStudents: 0,
    enrolledStudents: 0,
    commissionRate: commissionRate,
    commissionPaid: 0,
    notes: remarksText ? [{ date: new Date().toLocaleString(), text: remarksText }] : []
  };

  centers.unshift(newCenter);
  saveToStorage();
  syncSingleCenterToCloud(newCenter);
  populateDistrictFilter();
  populateStudentCenterSelect();
  closeAddCenterModal();
  renderApp();
  selectCenter(newCenter.id);
  showToast(`Added new B2B center: ${name} (${district})`);
}

// Modal 2: Add Student Modal Handlers
function openAddStudentModal(preselectedCenterId) {
  populateStudentCenterSelect();
  if (preselectedCenterId) {
    document.getElementById('stu-center-id').value = preselectedCenterId;
  }
  document.getElementById('add-student-modal').classList.add('active');
}

function closeAddStudentModal() {
  document.getElementById('add-student-modal').classList.remove('active');
  document.getElementById('add-student-form').reset();
}

function handleAddStudent(e) {
  e.preventDefault();
  const centerId = document.getElementById('stu-center-id').value;
  const center = centers.find(c => c.id === centerId);
  if (!center) return;

  const name = document.getElementById('stu-name').value.trim();
  const phone = document.getElementById('stu-phone').value.trim();
  const targetCountry = document.getElementById('stu-country').value;
  const program = document.getElementById('stu-program').value.trim();
  const ieltsScore = document.getElementById('stu-ielts').value.trim();
  const stage = document.getElementById('stu-stage').value;

  const newStudent = {
    id: `stu-${(students.length + 1).toString().padStart(4, '0')}`,
    centerId: centerId,
    centerName: center.name,
    district: center.district,
    name: name,
    phone: phone,
    targetCountry: targetCountry,
    program: program,
    ieltsScore: ieltsScore,
    stage: stage,
    createdAt: new Date().toLocaleString()
  };

  students.unshift(newStudent);
  
  // Update center counts automatically
  center.referredStudents = (center.referredStudents || 0) + 1;
  if (stage === 'Visa Issued' || stage === 'Enrolled') {
    center.enrolledStudents = (center.enrolledStudents || 0) + 1;
  }

  saveToStorage();
  syncSingleCenterToCloud(center);
  syncSingleStudentToCloud(newStudent);
  closeAddStudentModal();
  renderApp();
  selectCenter(centerId);
  showToast(`Added student referral ${name} to ${center.name}`);
}

// Export CSV / JSON Datasets
function exportData(format) {
  if (format === 'json') {
    const exportObj = { centers: centers, students: students };
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(exportObj, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `Keystone_BD_CRM_Master_${new Date().toISOString().split('T')[0]}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    showToast('Exported full JSON dataset (Centers + Students)');
  } else if (format === 'csv') {
    const headers = ['ID', 'Center Name', 'District', 'Primary Phone', 'Alternative Phone', 'Contact Person', 'Designation', 'Status', 'Priority', 'Referred Students', 'Enrolled Students', 'Commission Rate', 'Commission Paid', 'Commission Pending Due', 'Last Contact', 'Remarks History'];
    
    const rows = centers.map(c => {
      const rate = c.commissionRate || 5000;
      const earned = (c.enrolledStudents || 0) * rate;
      const paid = c.commissionPaid || 0;
      const pending = earned - paid;
      const remarksStr = Array.isArray(c.notes) ? c.notes.map(n => `[${n.date}] ${n.text}`).join(' | ') : '';

      return [
        c.id,
        `"${(c.name || '').replace(/"/g, '""')}"`,
        `"${(c.district || '').replace(/"/g, '""')}"`,
        `"${(c.phone || '').replace(/"/g, '""')}"`,
        `"${(c.altPhone || '').replace(/"/g, '""')}"`,
        `"${(c.contactPerson || '').replace(/"/g, '""')}"`,
        `"${(c.designation || '').replace(/"/g, '""')}"`,
        c.status,
        c.priority,
        c.referredStudents || 0,
        c.enrolledStudents || 0,
        rate,
        paid,
        pending,
        c.lastContact || '',
        `"${remarksStr.replace(/"/g, '""')}"`
      ];
    });

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `Keystone_BD_CRM_Centers_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    showToast('Exported CSV dataset');
  }
}

// Toast System
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `<i class="fa-solid fa-circle-check" style="color: #34d399;"></i> <span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 3500);
}

function getStatusBadgeClass(status) {
  switch (status) {
    case 'New': return 'badge-new';
    case 'Contacted': return 'badge-contacted';
    case 'Interested': return 'badge-interested';
    case 'Scheduled': return 'badge-scheduled';
    case 'Partnered': return 'badge-partnered';
    case 'Rejected': return 'badge-rejected';
    default: return 'badge-new';
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
