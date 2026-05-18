'use strict';

var clerkToken   = null;
var pollInterval = null;

var STATUS_MSGS = [
  'Sending task to models…',
  'Running trial 1 of 3…',
  'Running trial 2 of 3…',
  'Running trial 3 of 3…',
  'Consolidating answers…',
  'Running LLM judge evaluation…',
  'Writing results to database…',
  'Almost done…',
];

window.addEventListener('load', function() {
  waitForClerk(async function() {
    await window.Clerk.load();
    if (!window.Clerk.user) { window.location.href = 'sign-in.html'; return; }
    clerkToken = await window.Clerk.session.getToken();

    var params        = new URLSearchParams(window.location.search);
    var sid           = params.get('submission');
    var stripeSession = params.get('stripe_session');

    if (!sid || !stripeSession) {
      window.location.href = 'landing.html';
      return;
    }

    setView('confirmingView', 'Confirming Payment', 'Please wait while we verify your payment with Stripe.');
    await confirmPayment(parseInt(sid, 10), stripeSession);
  });
});

function setView(viewId, title, sub) {
  ['confirmingView', 'processingView', 'errorView'].forEach(function(id) {
    document.getElementById(id).style.display = 'none';
  });
  document.getElementById(viewId).style.display  = 'block';
  document.getElementById('heroTitle').textContent = title;
  document.getElementById('heroSub').textContent   = sub;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function confirmPayment(sid, sessionId) {
  try {
    clerkToken  = await window.Clerk.session.getToken();
    var res     = await fetch(API + '/submissions/' + sid + '/confirm-payment', {
      method:  'POST',
      headers: { 'Authorization': 'Bearer ' + clerkToken, 'Content-Type': 'application/json' },
      body:    JSON.stringify({ session_id: sessionId }),
    });

    if (!res.ok) {
      var err = await res.json().catch(function() { return {}; });
      setView('errorView', 'Payment Error', 'There was a problem confirming your payment.');
      document.getElementById('errorMsg').textContent = err.detail || 'Please contact support.';
      return;
    }

    setView('processingView', 'Running Benchmark',
      'Your task is being evaluated against all models. Please keep this page open.');
    startPolling(sid);

  } catch (err) {
    setView('errorView', 'Connection Error', 'Could not reach the server.');
    document.getElementById('errorMsg').textContent = 'Please refresh the page. (' + err.message + ')';
  }
}

function startPolling(sid) {
  var attempts = 0;
  pollInterval = setInterval(async function() {
    attempts++;
    document.getElementById('processingStatus').textContent =
      STATUS_MSGS[Math.min(attempts - 1, STATUS_MSGS.length - 1)];

    try {
      clerkToken  = await window.Clerk.session.getToken();
      var res     = await fetch(API + '/submissions/' + sid + '/status', {
        headers: { 'Authorization': 'Bearer ' + clerkToken },
      });
      if (!res.ok) return;

      var data = await res.json();

      if (data.status === 'done') {
        clearInterval(pollInterval);
        window.location.href = 'results.html?submission=' + sid;
      } else if (data.status === 'error') {
        clearInterval(pollInterval);
        setView('errorView', 'Benchmark Error', 'Something went wrong while processing your task.');
        document.getElementById('errorMsg').textContent =
          data.error_message || 'Please contact the administrator.';
      } else if (attempts >= 100) {
        clearInterval(pollInterval);
        setView('errorView', 'Taking Longer Than Expected',
          'One or more models may still be running.');
        document.getElementById('errorMsg').innerHTML =
          '<button class="btn-secondary" onclick="location.reload()">Refresh to check again</button>';
      }
    } catch (err) {
      console.error('Poll error:', err);
    }
  }, 3000);
}
