// ── API base URL ─────────────────────────────────────────────────────────────
// Development:  http://127.0.0.1:8000
// Production:   https://your-backend.onrender.com
var API = 'http://127.0.0.1:8000';

// ── Clerk ─────────────────────────────────────────────────────────────────────
// Publishable key from Clerk dashboard → API Keys
// Development:  pk_test_...
// Production:   pk_live_...
var CLERK_PUBLISHABLE_KEY = 'pk_test_YW11c2VkLWh5ZW5hLTk5LmNsZXJrLmFjY291bnRzLmRldiQ';

// Clerk JS URL — the subdomain (amused-hyena-99) is unique to your Clerk instance
// Find it in any existing HTML page or in the Clerk dashboard
var CLERK_JS_URL = 'https://amused-hyena-99.clerk.accounts.dev/npm/@clerk/clerk-js@latest/dist/clerk.browser.js';
