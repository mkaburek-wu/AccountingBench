'use strict';

// ── Inject Clerk script dynamically ──────────────────────────────────────────
// CLERK_PUBLISHABLE_KEY and CLERK_JS_URL come from config.js (loaded first).
(function() {
  var s = document.createElement('script');
  s.async = true;
  s.crossOrigin = 'anonymous';
  s.setAttribute('data-clerk-publishable-key', CLERK_PUBLISHABLE_KEY);
  s.src = CLERK_JS_URL;
  document.head.appendChild(s);
})();

// ── waitForClerk ──────────────────────────────────────────────────────────────
// Polls every 100ms until window.Clerk exists AND window.Clerk.load is a
// function. The Clerk script tag has async, so it can finish loading at any
// point relative to the DOMContentLoaded / load events. Waits up to 10 seconds
// before giving up.
//
// Usage:
//   waitForClerk(function() {
//     window.Clerk.load().then(function() { ... });
//   });
//
function waitForClerk(callback, attempts) {
  attempts = attempts || 0;
  if (
    typeof window.Clerk !== 'undefined' &&
    typeof window.Clerk.load === 'function'
  ) {
    callback();
  } else if (attempts < 100) {
    setTimeout(function() { waitForClerk(callback, attempts + 1); }, 100);
  } else {
    // Clerk failed to load after 10 seconds — show a generic error
    var errEl = document.getElementById('authError') ||
                document.getElementById('formError');
    if (errEl) {
      errEl.textContent = 'Authentication service could not be loaded. Please refresh the page.';
      errEl.style.display = 'block';
    }
    console.error('Clerk failed to load after 10 seconds.');
  }
}


// ── Message helpers ───────────────────────────────────────────────────────────

/**
 * showError(elementId, message)
 * Shows a red error banner and hides any success banner on the same page.
 *
 * Example:
 *   showError('authError', 'Incorrect email or password.');
 */
function showError(elementId, message) {
  var el = document.getElementById(elementId);
  if (!el) return;
  el.textContent    = message;
  el.style.display  = 'block';
  // Hide sibling success banner if present
  var successId = elementId.replace('Error', 'Success');
  var successEl = document.getElementById(successId);
  if (successEl) successEl.style.display = 'none';
}

/**
 * showSuccess(elementId, message)
 * Shows a green success banner and hides any error banner on the same page.
 *
 * Example:
 *   showSuccess('authSuccess', 'Signed in successfully. Redirecting…');
 */
function showSuccess(elementId, message) {
  var el = document.getElementById(elementId);
  if (!el) return;
  el.textContent   = message;
  el.style.display = 'block';
  // Hide sibling error banner if present
  var errorId = elementId.replace('Success', 'Error');
  var errorEl = document.getElementById(errorId);
  if (errorEl) errorEl.style.display = 'none';
}

/**
 * hideMessages(elementIds)
 * Hides one or more message banners by ID.
 *
 * Example:
 *   hideMessages(['authError', 'authSuccess']);
 */
function hideMessages(elementIds) {
  (elementIds || []).forEach(function(id) {
    var el = document.getElementById(id);
    if (el) el.style.display = 'none';
  });
}


// ── Button loading state ──────────────────────────────────────────────────────

/**
 * setLoading(buttonId, isLoading, label)
 * Disables a button and shows a spinner when loading, or re-enables it.
 *
 * Example:
 *   setLoading('signInBtn', true, 'Signing in…');
 *   setLoading('signInBtn', false, 'Sign In');
 */
function setLoading(buttonId, isLoading, label) {
  var btn = document.getElementById(buttonId);
  if (!btn) return;
  btn.disabled  = isLoading;
  btn.innerHTML = isLoading
    ? '<span class="btn-spinner"></span>' + label
    : label;
}


// ── HTML escaping ─────────────────────────────────────────────────────────────

/**
 * escHtml(text)
 * Escapes a string for safe insertion into HTML.
 * Prevents XSS when rendering user-supplied content.
 *
 * Example:
 *   element.innerHTML = escHtml(userInput);
 */
function escHtml(text) {
  var div = document.createElement('div');
  div.textContent = String(text || '');
  return div.innerHTML;
}


// ── Clerk error handler ───────────────────────────────────────────────────────

/**
 * handleClerkError(err, errorElementId)
 * Extracts a human-readable message from a Clerk API error and shows it.
 * Maps common technical Clerk error messages to friendlier text.
 *
 * Example:
 *   handleClerkError(err, 'authError');
 */
function handleClerkError(err, errorElementId) {
  errorElementId = errorElementId || 'authError';

  var raw = (
    (err && err.errors && err.errors[0] && (err.errors[0].longMessage || err.errors[0].message)) ||
    (err && err.message) ||
    'An unexpected error occurred. Please try again.'
  );

  var msg = raw;

  if (raw.toLowerCase().indexOf('password') >= 0 ||
      raw.toLowerCase().indexOf('identifier') >= 0) {
    msg = 'Incorrect email or password. Please try again.';

  } else if (raw.toLowerCase().indexOf('too many') >= 0) {
    msg = 'Too many attempts. Please wait a moment and try again.';

  } else if (raw.toLowerCase().indexOf('not found') >= 0) {
    msg = 'No account found with that email address. Please register first.';

  } else if (raw.toLowerCase().indexOf('taken') >= 0 ||
             raw.toLowerCase().indexOf('already') >= 0) {
    msg = 'This email address is already registered. Try signing in instead.';

  } else if (raw.toLowerCase().indexOf('weak') >= 0 ||
             raw.toLowerCase().indexOf('short') >= 0) {
    msg = 'Password is too weak. Please choose a stronger password (min. 8 characters).';

  } else if (raw.toLowerCase().indexOf('incorrect') >= 0 ||
             raw.toLowerCase().indexOf('invalid') >= 0) {
    msg = 'Incorrect verification code. Please check your email and try again.';

  } else if (raw.toLowerCase().indexOf('expired') >= 0) {
    msg = 'The verification code has expired. Please request a new one.';
  }

  showError(errorElementId, msg);
  console.error('Clerk error:', err);
}


// ── Step switcher ─────────────────────────────────────────────────────────────

/**
 * showStep(stepId)
 * Shows one .auth-step div and hides all others on the page.
 *
 * Example:
 *   showStep('stepCode');
 */
function showStep(stepId) {
  document.querySelectorAll('.auth-step').forEach(function(el) {
    el.classList.remove('active');
  });
  var target = document.getElementById(stepId);
  if (target) target.classList.add('active');
}


// ── Code input helper ─────────────────────────────────────────────────────────

/**
 * setupCodeInput(inputId, onComplete)
 * Configures a 6-digit code input:
 *   - Strips non-numeric characters on input
 *   - Calls onComplete() automatically when 6 digits are entered
 *   - Calls onComplete() when Enter is pressed
 *
 * Example:
 *   setupCodeInput('codeInput', handleVerifyCode);
 */
function setupCodeInput(inputId, onComplete) {
  var input = document.getElementById(inputId);
  if (!input) return;

  input.addEventListener('input', function(e) {
    var val     = e.target.value.replace(/\D/g, '');
    e.target.value = val;
    if (val.length === 6 && typeof onComplete === 'function') {
      onComplete();
    }
  });

  input.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && typeof onComplete === 'function') {
      onComplete();
    }
  });
}

async function checkOrPoll(submissionId) {
  try {
    clerkToken = await window.Clerk.session.getToken();
    var res = await fetch(API + '/submissions/' + submissionId + '/status', {
      headers: { 'Authorization': 'Bearer ' + clerkToken },
    });
    if (!res.ok) { showProcessing(); startPolling(submissionId); return; }

    var data = await res.json();

    if (data.status === 'done') {
      // Already done — show results immediately, no spinner needed
      showResult(data.model_scores || []);

    } else if (data.status === 'error') {
      showResultError();

    } else {
      // Still processing — show spinner and start polling
      showProcessing();
      startPolling(submissionId);
    }

  } catch (err) {
    // Could not reach server — show spinner and try polling
    showProcessing();
    startPolling(submissionId);
  }
}