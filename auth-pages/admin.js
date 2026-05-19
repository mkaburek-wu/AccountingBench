'use strict';

var clerkToken = null;
var currentTaskFilter = 'pending';

// ── Auth + admin guard ────────────────────────────────────────────────────────
window.addEventListener('load', function() {
  waitForClerk(async function() {
    await window.Clerk.load();
    if (!window.Clerk.user) { window.location.href = 'sign-in.html'; return; }
    clerkToken = await window.Clerk.session.getToken();

    var res = await fetch(API + '/me', {
      headers: { 'Authorization': 'Bearer ' + clerkToken },
    });
    if (!res.ok) { window.location.href = 'landing.html'; return; }
    var me = await res.json();
    if (!me.is_admin) { window.location.href = 'landing.html'; return; }

    showTab('tasks');
  });
});

// ── Tab switching ─────────────────────────────────────────────────────────────
function showTab(tab) {
  document.querySelectorAll('.admin-section').forEach(function(el) {
    el.style.display = 'none';
  });
  document.querySelectorAll('.admin-tab').forEach(function(el) {
    el.classList.remove('active');
  });
  document.getElementById('section-' + tab).style.display = 'block';
  document.getElementById('tab-' + tab).classList.add('active');

  if (tab === 'tasks')   loadTasks();
  if (tab === 'users')   loadUsers();
  if (tab === 'stats')   loadStats();
  if (tab === 'domains') loadDomains();
}

// ── Stats ─────────────────────────────────────────────────────────────────────
async function loadStats() {
  try {
    var token = await window.Clerk.session.getToken();
    var res = await fetch(API + '/admin/stats', {
      headers: { 'Authorization': 'Bearer ' + token },
    });
    if (!res.ok) return;
    var s = await res.json();

    setText('kpi-pending',   s.tasks.pending);
    setText('kpi-users',     s.users.total);
    setText('kpi-week',      s.submissions.this_week);
    setText('kpi-revenue',
      s.revenue.total_cents > 0
        ? '€' + (s.revenue.total_cents / 100).toFixed(2)
        : '—');
    setText('kpi-approved',   s.tasks.approved);
    setText('kpi-rejected',   s.tasks.rejected);
    setText('kpi-processing', s.submissions.processing);
    setText('kpi-today',      s.submissions.today);
    setText('kpi-users-active', s.users.active + ' active');
  } catch (e) {
    console.error('[admin] loadStats', e);
  }
}

function setText(id, val) {
  var el = document.getElementById(id);
  if (el) el.textContent = val;
}

// ── Tasks ─────────────────────────────────────────────────────────────────────
function setTaskFilter(filter) {
  currentTaskFilter = filter;
  document.querySelectorAll('.admin-filter-btn').forEach(function(btn) {
    btn.classList.toggle('active', btn.dataset.filter === filter);
  });
  loadTasks();
}

async function loadTasks() {
  var tbody = document.getElementById('tasks-tbody');
  tbody.innerHTML = '<tr><td colspan="6" class="admin-table-msg">Loading…</td></tr>';
  try {
    var token = await window.Clerk.session.getToken();
    var res = await fetch(API + '/admin/tasks?status=' + currentTaskFilter, {
      headers: { 'Authorization': 'Bearer ' + token },
    });
    if (!res.ok) throw new Error('Server error ' + res.status);
    var tasks = await res.json();

    if (tasks.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="admin-table-msg">No tasks with status “' + escHtml(currentTaskFilter) + '”.</td></tr>';
      return;
    }
    tbody.innerHTML = tasks.map(buildTaskRow).join('');
  } catch (e) {
    console.error('[admin] loadTasks', e);
    tbody.innerHTML = '<tr><td colspan="6" class="admin-table-msg">Error loading tasks.</td></tr>';
  }
}

function buildTaskRow(t) {
  var date     = t.created_at ? new Date(t.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : '—';
  var category = (t.category || '—').replace(/_/g, ' ').replace(/\b\w/g, function(l) { return l.toUpperCase(); });
  var preview  = (t.prompt || '').substring(0, 72) + ((t.prompt || '').length > 72 ? '…' : '');
  var ansType  = (t.answer_type || '—').replace(/_/g, ' ');

  var actions = '';
  if (t.validation_status !== 'approved') {
    actions += '<button class="btn-tbl-approve" onclick="approveTask(' + t.id + ',event)">Approve</button>';
  }
  if (t.validation_status !== 'rejected') {
    actions += '<button class="btn-tbl-reject" onclick="rejectTask(' + t.id + ',event)">Reject</button>';
  }

  var scores = (t.model_scores || []).map(function(s) {
    return escHtml(s.model) + ': ' + (s.score !== null ? s.score.toFixed(1) + '%' : '—');
  }).join(' &middot; ');

  var did = 'det-' + t.id;

  return (
    '<tr class="task-main-row" onclick="toggleDetail(\'' + did + '\')">' +
      '<td><span class="admin-mono">' + escHtml(t.question_id) + '</span></td>' +
      '<td>' + escHtml(category) + '</td>' +
      '<td class="task-preview-cell">' + escHtml(preview) + '</td>' +
      '<td>' + escHtml(ansType) + '</td>' +
      '<td>' + escHtml(date) + '</td>' +
      '<td class="task-actions-cell" onclick="event.stopPropagation()">' + actions + '</td>' +
    '</tr>' +
    '<tr class="task-detail-row" id="' + did + '" style="display:none">' +
      '<td colspan="6"><div class="task-detail-inner">' +
        '<div class="task-detail-field"><label>Question</label><p>' + escHtml(t.prompt || '—') + '</p></div>' +
        (t.options ? '<div class="task-detail-field"><label>Options</label><p>' + escHtml(t.options) + '</p></div>' : '') +
        '<div class="task-detail-field"><label>Correct Answer</label><p>' + escHtml(t.gold_answer || '—') + '</p></div>' +
        (t.grading_criteria ? '<div class="task-detail-field"><label>Grading Criteria</label><p>' + escHtml(t.grading_criteria) + '</p></div>' : '') +
        (scores ? '<div class="task-detail-field"><label>Model Scores</label><p class="admin-mono" style="font-size:12px">' + scores + '</p></div>' : '') +
      '</div></td>' +
    '</tr>'
  );
}

function toggleDetail(id) {
  var row = document.getElementById(id);
  if (row) row.style.display = row.style.display === 'none' ? 'table-row' : 'none';
}

async function approveTask(taskId, e) {
  if (e) e.stopPropagation();
  try {
    var token = await window.Clerk.session.getToken();
    var res = await fetch(API + '/admin/tasks/' + taskId + '/approve', {
      method: 'POST', headers: { 'Authorization': 'Bearer ' + token },
    });
    if (res.ok) loadTasks();
  } catch (e) { console.error('[admin] approveTask', e); }
}

async function rejectTask(taskId, e) {
  if (e) e.stopPropagation();
  try {
    var token = await window.Clerk.session.getToken();
    var res = await fetch(API + '/admin/tasks/' + taskId + '/reject', {
      method: 'POST', headers: { 'Authorization': 'Bearer ' + token },
    });
    if (res.ok) loadTasks();
  } catch (e) { console.error('[admin] rejectTask', e); }
}

// ── Users ─────────────────────────────────────────────────────────────────────
async function loadUsers() {
  var tbody = document.getElementById('users-tbody');
  tbody.innerHTML = '<tr><td colspan="5" class="admin-table-msg">Loading…</td></tr>';
  try {
    var token = await window.Clerk.session.getToken();
    var res = await fetch(API + '/admin/users', {
      headers: { 'Authorization': 'Bearer ' + token },
    });
    if (!res.ok) throw new Error('Server error ' + res.status);
    var users = await res.json();

    if (users.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="admin-table-msg">No users found.</td></tr>';
      return;
    }
    tbody.innerHTML = users.map(buildUserRow).join('');
  } catch (e) {
    console.error('[admin] loadUsers', e);
    tbody.innerHTML = '<tr><td colspan="5" class="admin-table-msg">Error loading users.</td></tr>';
  }
}

function buildUserRow(u) {
  var date   = u.created_at ? new Date(u.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : '—';
  var name   = [u.first_name, u.last_name].filter(Boolean).join(' ') || '—';
  var badge  = u.is_active
    ? '<span class="admin-badge admin-badge-green">Active</span>'
    : '<span class="admin-badge admin-badge-red">Inactive</span>';
  var toggle = u.is_active
    ? '<button class="btn-tbl-reject" onclick="toggleUser(\'' + escHtml(u.id) + '\',false)">Deactivate</button>'
    : '<button class="btn-tbl-approve" onclick="toggleUser(\'' + escHtml(u.id) + '\',true)">Activate</button>';

  return (
    '<tr>' +
      '<td>' + escHtml(name) + '</td>' +
      '<td>' + escHtml(u.email) + '</td>' +
      '<td>' + escHtml(date) + '</td>' +
      '<td style="text-align:center">' + escHtml(String(u.submission_count)) + '</td>' +
      '<td>' + badge + '&nbsp;' + toggle + '</td>' +
    '</tr>'
  );
}

async function toggleUser(userId, activate) {
  try {
    var token  = await window.Clerk.session.getToken();
    var action = activate ? 'activate' : 'deactivate';
    var res = await fetch(API + '/admin/users/' + userId + '/' + action, {
      method: 'POST', headers: { 'Authorization': 'Bearer ' + token },
    });
    if (res.ok) loadUsers();
  } catch (e) { console.error('[admin] toggleUser', e); }
}

// ── Domains ───────────────────────────────────────────────────────────────────
async function loadDomains() {
  var list = document.getElementById('domains-list');
  list.innerHTML = '<div class="admin-table-msg">Loading…</div>';
  try {
    var token = await window.Clerk.session.getToken();
    var res = await fetch(API + '/admin/domains', {
      headers: { 'Authorization': 'Bearer ' + token },
    });
    if (!res.ok) throw new Error('Server error ' + res.status);
    var domains = await res.json();

    if (domains.length === 0) {
      list.innerHTML = '<div class="admin-table-msg">No domains configured.</div>';
      return;
    }
    list.innerHTML = domains.map(function(d) {
      return (
        '<div class="domain-row">' +
          '<span class="admin-mono">' + escHtml(d.domain) + '</span>' +
          '<span class="domain-meta">added ' + escHtml(d.added_by || '—') + '</span>' +
          '<button class="btn-tbl-reject" onclick="removeDomain(' + d.id + ')">Remove</button>' +
        '</div>'
      );
    }).join('');
  } catch (e) { console.error('[admin] loadDomains', e); }
}

async function addDomain() {
  var input  = document.getElementById('newDomain');
  var domain = input.value.trim().replace(/^@/, '').toLowerCase();
  if (!domain) return;
  hideMessages(['domainError', 'domainSuccess']);

  try {
    var token = await window.Clerk.session.getToken();
    var res = await fetch(API + '/admin/domains', {
      method:  'POST',
      headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
      body:    JSON.stringify({ domain: domain }),
    });
    if (res.ok) {
      input.value = '';
      showSuccess('domainSuccess', 'Domain @' + domain + ' added.');
      loadDomains();
    } else {
      var err = await res.json().catch(function() { return {}; });
      showError('domainError', err.detail || 'Could not add domain.');
    }
  } catch (e) { console.error('[admin] addDomain', e); }
}

async function removeDomain(domainId) {
  try {
    var token = await window.Clerk.session.getToken();
    var res = await fetch(API + '/admin/domains/' + domainId, {
      method: 'DELETE', headers: { 'Authorization': 'Bearer ' + token },
    });
    if (res.ok) loadDomains();
  } catch (e) { console.error('[admin] removeDomain', e); }
}

// ── Sign out ──────────────────────────────────────────────────────────────────
async function handleSignOut() {
  try { await window.Clerk.signOut(); } catch (e) { /* ignore */ }
  window.location.href = 'sign-in.html';
}
