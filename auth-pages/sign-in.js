'use strict';

var signInAttempt = null;

window.addEventListener('load', function() {
  waitForClerk(async function() {
    await window.Clerk.load();
    if (window.Clerk.user) { window.location.href = 'landing.html'; }
  });
});

document.getElementById('passwordInput').addEventListener('keydown', function(e) {
  if (e.key === 'Enter') handleSignIn();
});
setupCodeInput('codeInput', handleVerifyCode);

async function handleSignIn() {
  hideMessages(['authError', 'authSuccess']);
  var email    = document.getElementById('emailInput').value.trim();
  var password = document.getElementById('passwordInput').value;
  if (!email || !password) { showError('authError', 'Please enter your email address and password.'); return; }

  setLoading('signInBtn', true, 'Signing in…');
  try {
    await window.Clerk.load();
    signInAttempt = await window.Clerk.client.signIn.create({ identifier: email, password: password });

    if (signInAttempt.status === 'complete') {
      await window.Clerk.setActive({ session: signInAttempt.createdSessionId });
      showSuccess('authSuccess', 'Signed in. Redirecting…');
      setTimeout(function() { window.location.href = 'landing.html'; }, 800);

    } else if (signInAttempt.status === 'needs_second_factor') {
      await signInAttempt.prepareSecondFactor({ strategy: 'email_code' });
      document.getElementById('codeInfoMsg').textContent =
        'You are signing in from a new device. A 6-digit code has been sent to ' + email + '. Enter it below.';
      showStep('stepCode');
      setLoading('signInBtn', false, 'Sign In');
      document.getElementById('codeInput').focus();

    } else if (signInAttempt.status === 'needs_first_factor') {
      await signInAttempt.prepareFirstFactor({ strategy: 'email_code' });
      showStep('stepCode');
      setLoading('signInBtn', false, 'Sign In');
      document.getElementById('codeInput').focus();

    } else {
      showError('authError', 'Unexpected response. Please try again.');
      setLoading('signInBtn', false, 'Sign In');
    }
  } catch (err) {
    setLoading('signInBtn', false, 'Sign In');
    handleClerkError(err, 'authError');
  }
}

async function handleVerifyCode() {
  hideMessages(['authError', 'authSuccess']);
  var code = document.getElementById('codeInput').value.trim();
  if (!code || code.length < 6) { showError('authError', 'Please enter the complete 6-digit code.'); return; }

  setLoading('verifyBtn', true, 'Verifying…');
  try {
    var result;
    if (signInAttempt.status === 'needs_second_factor') {
      result = await signInAttempt.attemptSecondFactor({ strategy: 'email_code', code: code });
    } else {
      result = await signInAttempt.attemptFirstFactor({ strategy: 'email_code', code: code });
    }
    if (result.status === 'complete') {
      await window.Clerk.setActive({ session: result.createdSessionId });
      showSuccess('authSuccess', 'Verified. Redirecting…');
      setTimeout(function() { window.location.href = 'landing.html'; }, 800);
    } else {
      showError('authError', 'Verification incomplete. Please try again.');
      setLoading('verifyBtn', false, 'Verify & Sign In');
    }
  } catch (err) {
    setLoading('verifyBtn', false, 'Verify & Sign In');
    document.getElementById('codeInput').value = '';
    handleClerkError(err, 'authError');
  }
}

async function handleResendCode() {
  hideMessages(['authError', 'authSuccess']);
  try {
    if (signInAttempt.status === 'needs_second_factor') {
      await signInAttempt.prepareSecondFactor({ strategy: 'email_code' });
    } else {
      await signInAttempt.prepareFirstFactor({ strategy: 'email_code' });
    }
    showSuccess('authSuccess', 'A new code has been sent to your email.');
    document.getElementById('codeInput').value = '';
    document.getElementById('codeInput').focus();
  } catch (err) { showError('authError', 'Could not resend. Please refresh the page.'); }
}

function goBack() {
  signInAttempt = null;
  hideMessages(['authError', 'authSuccess']);
  document.getElementById('codeInput').value = '';
  showStep('stepCredentials');
  document.getElementById('emailInput').focus();
}
