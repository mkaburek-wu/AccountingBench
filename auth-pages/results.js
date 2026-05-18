'use strict';

var clerkToken   = null;
var pollInterval = null;
var submissionId = null;

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

    var params = new URLSearchParams(window.location.search);
    var sid    = params.get('submission');

    if (!sid) {
      document.getElementById('processingView').style.display = 'none';
      document.getElementById('noIdView').style.display       = 'block';
      return;
    }

    submissionId = parseInt(sid, 10);
    await checkStatus(submissionId);
  });
});

async function checkStatus(sid) {
  try {
    clerkToken  = await window.Clerk.session.getToken();
    var res     = await fetch(API + '/submissions/' + sid + '/status', {
      headers: { 'Authorization': 'Bearer ' + clerkToken },
    });

    if (!res.ok) {
      showError('Server returned ' + res.status + '. Please try refreshing the page.');
      return;
    }

    var data = await res.json();

    if (data.status === 'done') {
      showResult(data.model_scores || []);
    } else if (data.status === 'error') {
      showError(data.error_message || null);
    } else {
      showProcessing();
      startPolling(sid);
    }

  } catch (err) {
    showError('Could not load the result. Please refresh. (' + err.message + ')');
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
        showResult(data.model_scores || []);
      } else if (data.status === 'error') {
        clearInterval(pollInterval);
        showError(data.error_message || null);
      } else if (attempts >= 100) {
        clearInterval(pollInterval);
        showError(
          'The benchmark is taking longer than expected. ' +
          'One or more models may still be running.<br><br>' +
          '<button class="btn-secondary" onclick="location.reload()">Refresh to check again</button>'
        );
      }
    } catch (err) {
      console.error('Poll error:', err);
    }
  }, 3000);
}

function showProcessing() {
  document.getElementById('processingView').style.display = 'block';
  document.getElementById('resultView').style.display     = 'none';
  document.getElementById('errorView').style.display      = 'none';
  document.getElementById('heroTitle').textContent        = 'Running Benchmark';
  document.getElementById('heroSub').textContent =
    'Your task is being evaluated against all models. Please keep this page open.';
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showResult(scores) {
  document.getElementById('processingView').style.display = 'none';
  document.getElementById('resultView').style.display     = 'block';
  document.getElementById('errorView').style.display      = 'none';
  document.getElementById('heroTitle').textContent        = 'Benchmark Complete';
  document.getElementById('heroSub').textContent =
    'Results are shown below. They are private until reviewed by the administrator.';

  var rows = document.getElementById('resultsRows');

  if (!scores || scores.length === 0) {
    rows.innerHTML = '<div class="results-empty">No scores available yet.</div>';
    return;
  }

  rows.innerHTML = scores.map(function(s) {
    var v        = (s.score !== null && s.score !== undefined) ? s.score : null;
    var cls      = v === null ? '' : v >= 75 ? 'score-high' : v >= 60 ? 'score-mid' :
                   v >= 45 ? 'score-low' : 'score-poor';
    var scoreStr = v !== null ? v.toFixed(1) + '%' : '—';
    var method   = s.method === 'sc_mc_formula' ? 'SC/MC Formula' :
                   s.method === 'judge'          ? 'LLM Judge'     :
                   (s.method || '—');
    return (
      '<div class="result-row">' +
        '<div class="result-model-name">' + escHtml(s.model)  + '</div>' +
        '<div class="result-score ' + cls + '">' + scoreStr   + '</div>' +
        '<div class="result-method">'  + escHtml(method)      + '</div>' +
      '</div>'
    );
  }).join('');

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showError(msg) {
  document.getElementById('processingView').style.display = 'none';
  document.getElementById('resultView').style.display     = 'none';
  document.getElementById('errorView').style.display      = 'block';
  document.getElementById('heroTitle').textContent        = 'Benchmark Error';
  document.getElementById('heroSub').textContent =
    'Something went wrong while processing your task.';
  if (msg) document.getElementById('errorMsg').innerHTML = msg;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
