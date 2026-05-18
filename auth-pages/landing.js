'use strict';

window.addEventListener('load', function() {
  waitForClerk(async function() {
    await window.Clerk.load();
    if (!window.Clerk.user) { window.location.href = 'sign-in.html'; return; }

    var firstName = window.Clerk.user.firstName;
    if (firstName) {
      document.getElementById('userName').textContent = ', ' + firstName + '.';
    }

    await loadSubmissions();
  });
});

async function handleSignOut() {
  try { await window.Clerk.signOut(); } catch (e) { /* ignore */ }
  window.location.href = 'sign-in.html';
}

async function loadSubmissions() {
  var grid    = document.getElementById('submissionsGrid');
  var countEl = document.getElementById('submissionCount');

  try {
    var token = await window.Clerk.session.getToken();
    var res   = await fetch(API + '/submissions/mine', {
      headers: { 'Authorization': 'Bearer ' + token },
    });

    if (!res.ok) {
      grid.innerHTML =
        '<div class="submissions-empty">' +
        '<div class="submissions-empty-title">Could not load submissions</div>' +
        '<div class="submissions-empty-text">Server returned ' + res.status +
        '. Make sure the server is running and refresh.</div></div>';
      countEl.textContent = '0 submissions';
      return;
    }

    var submissions = await res.json();
    countEl.textContent =
      submissions.length + ' submission' + (submissions.length !== 1 ? 's' : '');

    if (submissions.length === 0) {
      grid.innerHTML =
        '<div class="submissions-empty">' +
        '<div class="submissions-empty-icon">📋</div>' +
        '<div class="submissions-empty-title">No submissions yet</div>' +
        '<div class="submissions-empty-text">Contribute your first accounting benchmark task to get started.</div>' +
        '<a href="upload.html" class="btn-primary">Contribute New Task</a>' +
        '</div>';
      return;
    }

    grid.innerHTML = submissions.map(buildCard).join('');

  } catch (err) {
    console.error('Failed to load submissions:', err);
    grid.innerHTML =
      '<div class="submissions-empty">' +
      '<div class="submissions-empty-title">Could not reach the server</div>' +
      '<div class="submissions-empty-text">Make sure the FastAPI server is running and refresh.</div>' +
      '</div>';
    countEl.textContent = '0 submissions';
  }
}

function buildCard(s) {
  var date = s.submitted_at
    ? new Date(s.submitted_at).toLocaleDateString('en-GB', {
        day: 'numeric', month: 'short', year: 'numeric'
      })
    : '—';

  var labels = {
    pending:    'Pending',
    processing: 'Processing',
    done:       'Done',
    error:      'Error',
    rejected:   'Rejected',
  };

  var category = s.task_category
    ? s.task_category.replace(/_/g, ' ').replace(/\b\w/g, function(l) { return l.toUpperCase(); })
    : '—';

  var safeId = encodeURIComponent(s.id);

  var viewBtn = s.status === 'done'
    ? '<a href="results.html?submission=' + safeId + '" class="btn-secondary" style="font-size:10px;padding:6px 14px;">View Result</a>'
    : '';

  var processingBtn = s.status === 'processing'
    ? '<a href="results.html?submission=' + safeId + '" class="btn-secondary" style="font-size:10px;padding:6px 14px;">View Progress</a>'
    : '';

  return (
    '<div class="submission-card">' +
      '<div class="submission-card-meta">' +
        '<span class="submission-date">' + escHtml(date) + '</span>' +
        '<span class="submission-status status-' + escHtml(s.status || 'pending') + '">' +
          escHtml(labels[s.status] || s.status) +
        '</span>' +
      '</div>' +
      '<div class="submission-category">' + escHtml(category) + '</div>' +
      '<div class="submission-prompt">' +
        escHtml(s.task_preview || 'Task details not available.') +
      '</div>' +
      viewBtn + processingBtn +
    '</div>'
  );
}
