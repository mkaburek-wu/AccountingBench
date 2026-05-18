'use strict';

var clerkToken = null;

// ── Auth ──────────────────────────────────────────────────────────────────────
window.addEventListener('load', function() {
  waitForClerk(async function() {
    await window.Clerk.load();
    if (!window.Clerk.user) { window.location.href = 'sign-in.html'; return; }
    clerkToken = await window.Clerk.session.getToken();
    loadProfile();
  });
});

// ── Load profile from /me ─────────────────────────────────────────────────────
async function loadProfile() {
  try {
    var token = await window.Clerk.session.getToken();
    var res = await fetch(API + '/me', {
      headers: { 'Authorization': 'Bearer ' + token },
    });
    if (!res.ok) throw new Error('Could not load profile.');
    var user = await res.json();

    var name = [user.first_name, user.last_name].filter(Boolean).join(' ') || '—';
    document.getElementById('accountName').textContent  = name;
    document.getElementById('accountEmail').textContent = user.email || '—';
  } catch (e) {
    console.error('[account] loadProfile error', e);
    document.getElementById('accountName').textContent  = '—';
    document.getElementById('accountEmail').textContent = '—';
  }
}

// ── Delete flow ───────────────────────────────────────────────────────────────
function handleDeleteClick() {
  document.getElementById('deleteInitial').style.display = 'none';
  document.getElementById('deleteConfirm').style.display = 'block';
}

function handleCancelDelete() {
  document.getElementById('deleteConfirm').style.display = 'none';
  document.getElementById('deleteInitial').style.display = 'block';
  hideMessages(['accountError']);
}

async function handleConfirmDelete() {
  hideMessages(['accountError']);
  var btn = document.getElementById('confirmDeleteBtn');
  btn.disabled    = true;
  btn.textContent = 'Deleting…';

  try {
    clerkToken = await window.Clerk.session.getToken();
    var res = await fetch(API + '/users/me', {
      method:  'DELETE',
      headers: { 'Authorization': 'Bearer ' + clerkToken },
    });
    if (!res.ok) {
      var err = await res.json().catch(function() { return {}; });
      showError('accountError', err.detail || 'Account deletion failed. Please try again.');
      btn.disabled    = false;
      btn.textContent = 'Yes, permanently delete my account';
      return;
    }
    // DB deleted — sign out from Clerk and redirect
    await window.Clerk.signOut();
    window.location.href = 'sign-in.html';
  } catch (e) {
    console.error('[account] delete error', e);
    showError('accountError', 'Unexpected error: ' + e.message);
    btn.disabled    = false;
    btn.textContent = 'Yes, permanently delete my account';
  }
}

// ── Sign out ──────────────────────────────────────────────────────────────────
async function handleSignOut() {
  try { await window.Clerk.signOut(); } catch (e) { /* ignore */ }
  window.location.href = 'sign-in.html';
}
