'use strict';

var signUpAttempt = null;

window.addEventListener('load', function() {
  waitForClerk(async function() {
    await window.Clerk.load();
    if (window.Clerk.user) { window.location.href = 'landing.html'; }
  });
});

document.getElementById('passwordInput').addEventListener('keydown', function(e) {
  if (e.key === 'Enter') handleRegister();
});
setupCodeInput('codeInput', handleVerifyCode);

async function handleRegister() {
  hideMessages(['authError', 'authSuccess']);
  var firstName = document.getElementById('firstNameInput').value.trim();
  var lastName  = document.getElementById('lastNameInput').value.trim();
  var email     = document.getElementById('emailInput').value.trim();
  var password  = document.getElementById('passwordInput').value;

  if (!firstName || !lastName) { showError('authError', 'Please enter your first and last name.'); return; }
  if (!email)    { showError('authError', 'Please enter your email address.'); return; }
  if (!password || password.length < 8) { showError('authError', 'Password must be at least 8 characters long.'); return; }

  var emailDomain = email.split('@')[1].toLowerCase();
  setLoading('registerBtn', true, 'Checking domain…');
  try {
    var domainCheck = await fetch(API + '/auth/check-domain?domain=' + emailDomain);
    if (domainCheck.status === 403) {
      showError('authError', 'Your email domain (@' + emailDomain + ') is not authorised to register. Please contact the administrator.');
      setLoading('registerBtn', false, 'Create Account');
      return;
    }
  } catch (err) {
    // Server unreachable — proceed anyway, backend will block if needed
  }

  setLoading('registerBtn', true, 'Creating account…');
  try {
    await window.Clerk.load();
    signUpAttempt = await window.Clerk.client.signUp.create({
      firstName: firstName, lastName: lastName,
      emailAddress: email,  password: password,
    });
    await signUpAttempt.prepareEmailAddressVerification({ strategy: 'email_code' });
    document.getElementById('verifyInfoMsg').textContent =
      'A verification code has been sent to ' + email + '. Enter it below to activate your account.';
    showStep('stepVerify');
    setLoading('registerBtn', false, 'Create Account');
    showSuccess('authSuccess', 'Account created! Please check your email for the verification code.');
    document.getElementById('codeInput').focus();
  } catch (err) {
    setLoading('registerBtn', false, 'Create Account');
    handleClerkError(err, 'authError');
  }
}

async function handleVerifyCode() {
  hideMessages(['authError', 'authSuccess']);
  var code = document.getElementById('codeInput').value.trim();
  if (!code || code.length < 6) { showError('authError', 'Please enter the complete 6-digit code.'); return; }

  setLoading('verifyBtn', true, 'Verifying…');
  try {
    var result = await signUpAttempt.attemptEmailAddressVerification({ code: code });
    if (result.status === 'complete') {
      await window.Clerk.setActive({ session: result.createdSessionId });
      showSuccess('authSuccess', 'Email verified! Redirecting…');
      setTimeout(function() { window.location.href = 'landing.html'; }, 1000);
    } else {
      showError('authError', 'Verification incomplete. Please try again.');
      setLoading('verifyBtn', false, 'Verify Email & Sign In');
    }
  } catch (err) {
    setLoading('verifyBtn', false, 'Verify Email & Sign In');
    document.getElementById('codeInput').value = '';
    handleClerkError(err, 'authError');
  }
}

async function handleResendCode() {
  hideMessages(['authError', 'authSuccess']);
  try {
    await signUpAttempt.prepareEmailAddressVerification({ strategy: 'email_code' });
    showSuccess('authSuccess', 'A new code has been sent to your email.');
    document.getElementById('codeInput').value = '';
    document.getElementById('codeInput').focus();
  } catch (err) { showError('authError', 'Could not resend. Please refresh the page.'); }
}

function goBack() {
  signUpAttempt = null;
  hideMessages(['authError', 'authSuccess']);
  document.getElementById('codeInput').value = '';
  showStep('stepRegister');
}
