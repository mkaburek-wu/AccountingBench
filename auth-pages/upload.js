'use strict';

var clerkToken = null;

// ── Show cancelled-payment banner when Stripe redirects back with ?cancelled=1 ─
(function() {
  if (new URLSearchParams(window.location.search).get('cancelled') === '1') {
    document.getElementById('cancelledBanner').style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
})();

// ── Auth ──────────────────────────────────────────────────────────────────────
window.addEventListener('load', function() {
  waitForClerk(async function() {
    await window.Clerk.load();
    if (!window.Clerk.user) { window.location.href = 'sign-in.html'; return; }
    clerkToken = await window.Clerk.session.getToken();
  });
});

// ── File name display ─────────────────────────────────────────────────────────
document.getElementById('pdfFile').addEventListener('change', function() {
  document.getElementById('pdfName').textContent = this.files[0] ? this.files[0].name : '';
});
document.getElementById('excelFile').addEventListener('change', function() {
  document.getElementById('excelName').textContent = this.files[0] ? this.files[0].name : '';
});

// ── Drag-and-drop area highlight ──────────────────────────────────────────────
['pdfArea', 'excelArea'].forEach(function(id) {
  var area = document.getElementById(id);
  area.addEventListener('dragover',  function(e) { e.preventDefault(); area.classList.add('dragover'); });
  area.addEventListener('dragleave', function()  { area.classList.remove('dragover'); });
  area.addEventListener('drop',      function()  { area.classList.remove('dragover'); });
});

// ── Conditional field visibility ──────────────────────────────────────────────
function handleAnswerTypeChange() {
  var type = document.getElementById('answerType').value;
  ['fieldOptions', 'fieldGrading', 'fieldTolerance'].forEach(function(id) {
    document.getElementById(id).classList.remove('visible');
  });
  if (type === 'single_choice' || type === 'multi_choice') {
    document.getElementById('fieldOptions').classList.add('visible');
    document.getElementById('goldAnswerHint').textContent =
      'Enter the correct letter(s): A, or A,C for multiple answers.';
  } else if (type === 'open_text' || type === 'journal_entry') {
    document.getElementById('fieldGrading').classList.add('visible');
    document.getElementById('goldAnswerHint').textContent =
      'Enter the reference answer for the LLM judge to compare against.';
  } else if (type === 'open_numeric') {
    document.getElementById('fieldGrading').classList.add('visible');
    document.getElementById('fieldTolerance').classList.add('visible');
    document.getElementById('goldAnswerHint').textContent =
      'Enter the correct numeric value, e.g. 1250.50';
  }
}

// ── Client-side validation ────────────────────────────────────────────────────
function validateForm() {
  var required = [
    { id: 'prompt',              label: 'Question / Prompt' },
    { id: 'answerType',          label: 'Answer Type' },
    { id: 'taskType',            label: 'Task Type' },
    { id: 'goldAnswer',          label: 'Correct Answer' },
    { id: 'category',            label: 'Category' },
    { id: 'regulatoryFramework', label: 'Regulatory Framework' },
    { id: 'regulatoryYear',      label: 'Applicable Year' },
    { id: 'educationLevel',      label: 'Education Level' },
  ];
  for (var i = 0; i < required.length; i++) {
    var el = document.getElementById(required[i].id);
    if (!el || !el.value.trim()) {
      showError('formError', 'Please fill in the required field: ' + required[i].label + '.');
      window.scrollTo({ top: 0, behavior: 'smooth' });
      if (el) el.focus();
      return false;
    }
  }
  var type = document.getElementById('answerType').value;
  if ((type === 'single_choice' || type === 'multi_choice') &&
      !document.getElementById('options').value.trim()) {
    showError('formError', 'Please enter the answer options for choice tasks.');
    window.scrollTo({ top: 0, behavior: 'smooth' });
    return false;
  }
  if (['open_text', 'journal_entry', 'open_numeric'].indexOf(type) >= 0 &&
      !document.getElementById('gradingCriteria').value.trim()) {
    showError('formError', 'Please enter grading criteria for open-ended tasks.');
    window.scrollTo({ top: 0, behavior: 'smooth' });
    return false;
  }
  return true;
}

// ── Show the preparing-payment loading state ──────────────────────────────────
function showPreparingPayment() {
  document.getElementById('preparingPaymentView').style.display = 'block';
  document.querySelector('.form-submit-area').style.display = 'none';
  document.querySelectorAll('.form-card').forEach(function(el) { el.style.display = 'none'; });
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── Poll status until checkout_url appears, then redirect to Stripe ───────────
async function pollForCheckout(submissionId) {
  console.log('[poll] starting for submission', submissionId);
  var maxAttempts = 30; // 15 seconds max (500 ms interval)
  for (var i = 0; i < maxAttempts; i++) {
    await new Promise(function(r) { setTimeout(r, 500); });
    console.log('[poll] attempt', i + 1);
    try {
      var token = await window.Clerk.session.getToken();
      var res   = await fetch(API + '/submissions/' + submissionId + '/status', {
        headers: { 'Authorization': 'Bearer ' + token },
      });
      console.log('[poll] status response', res.status);
      if (!res.ok) continue;
      var data = await res.json();
      console.log('[poll] data', JSON.stringify(data));

      if (data.checkout_url) {
        // Stripe session is ready — redirect
        console.log('[poll] navigating to', data.checkout_url);
        var pl = document.getElementById('paymentLink');
        if (pl) pl.href = data.checkout_url;
        document.getElementById('preparingPaymentView').style.display = 'none';
        document.getElementById('paymentReadyView').style.display = 'block';
        window.location.href = data.checkout_url;
        return;
      }

      // Dev mode (no Stripe): pipeline starts immediately
      if (data.status === 'processing' || data.status === 'done') {
        console.log('[poll] no-stripe path, going to results');
        window.location.href = 'results.html?submission=' + submissionId;
        return;
      }
    } catch (e) {
      console.log('[poll] error', e.message);
    }
  }

  // Timed out waiting for Stripe session
  document.getElementById('preparingPaymentView').style.display = 'none';
  document.querySelector('.form-submit-area').style.display = 'block';
  document.querySelectorAll('.form-card').forEach(function(el) { el.style.display = 'block'; });
  showError('formError', 'Payment setup timed out. Please try submitting again.');
  window.scrollTo({ top: 0, behavior: 'smooth' });
  var btn = document.getElementById('submitBtn');
  btn.disabled = false; btn.textContent = 'Submit & Run Benchmark';
}

// ── Form submit ───────────────────────────────────────────────────────────────
async function handleSubmit() {
  hideMessages(['formError']);
  if (!validateForm()) return;

  var btn = document.getElementById('submitBtn');
  btn.disabled    = true;
  btn.textContent = 'Submitting…';

  try {
    if (!window.Clerk || !window.Clerk.session) {
      showError('formError', 'Authentication not ready. Please wait a moment and try again.');
      window.scrollTo({ top: 0, behavior: 'smooth' });
      btn.disabled = false; btn.textContent = 'Submit & Run Benchmark';
      return;
    }

    clerkToken = await window.Clerk.session.getToken();
    if (!clerkToken) {
      showError('formError', 'Could not get authentication token. Please refresh the page.');
      window.scrollTo({ top: 0, behavior: 'smooth' });
      btn.disabled = false; btn.textContent = 'Submit & Run Benchmark';
      return;
    }

    var fd = new FormData();
    fd.append('prompt',                      document.getElementById('prompt').value.trim());
    fd.append('answer_type',                document.getElementById('answerType').value);
    fd.append('task_type',                  document.getElementById('taskType').value);
    fd.append('gold_answer',                document.getElementById('goldAnswer').value.trim());
    fd.append('category',                   document.getElementById('category').value);
    fd.append('regulatory_framework',       document.getElementById('regulatoryFramework').value);
    fd.append('applicable_regulatory_year', document.getElementById('regulatoryYear').value);
    fd.append('education_level',            document.getElementById('educationLevel').value);

    var optFields = {
      options:          'options',
      gradingCriteria:  'grading_criteria',
      numericTolerance: 'numeric_tolerance',
      context:          'context',
      subcategory:      'subcategory',
      notes:            'notes',
    };
    Object.keys(optFields).forEach(function(elId) {
      var el = document.getElementById(elId);
      if (el && el.value && el.value.trim()) fd.append(optFields[elId], el.value.trim());
    });

    var pdfFile   = document.getElementById('pdfFile').files[0];
    var excelFile = document.getElementById('excelFile').files[0];
    if (pdfFile)   fd.append('pdf_file',   pdfFile);
    if (excelFile) fd.append('excel_file', excelFile);

    console.log('[upload] fetch start, API=', API);
    var res = await fetch(API + '/submissions/prepare', {
      method:  'POST',
      headers: { 'Authorization': 'Bearer ' + clerkToken },
      body:    fd,
    });
    console.log('[upload] fetch done, status=', res.status);

    if (!res.ok) {
      var errData = await res.json().catch(function() { return {}; });
      showError('formError', 'Server error ' + res.status + ': ' +
        (errData.detail || 'Submission failed. Please try again.'));
      window.scrollTo({ top: 0, behavior: 'smooth' });
      btn.disabled = false; btn.textContent = 'Submit & Run Benchmark';
      return;
    }

    var data = await res.json();

    if (!data.submission_id) {
      showError('formError', 'Server did not return a submission ID. Please try again.');
      window.scrollTo({ top: 0, behavior: 'smooth' });
      btn.disabled = false; btn.textContent = 'Submit & Run Benchmark';
      return;
    }

    // The server returns immediately (checkout_url is null — Stripe session is
    // being created in a background task). Show spinner and poll until ready.
    console.log('[upload] submission_id=', data.submission_id, 'showing preparing view');
    showPreparingPayment();
    pollForCheckout(data.submission_id);

  } catch (err) {
    console.error('[upload] CATCH', err.name, err.message);
    showError('formError', 'Unexpected error: ' + err.message);
    window.scrollTo({ top: 0, behavior: 'smooth' });
    btn.disabled = false; btn.textContent = 'Submit & Run Benchmark';
  }
}
