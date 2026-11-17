/**
 * Authentication & User Profile Management
 * Requirements:
 * - Username is user's Gmail (e.g. user@gmail.com)
 * - Editable password system (Change Password modal + Forgot Password reset)
 * - 1-Click Quick Demo Login
 * - Real-time password strength meter & validation
 */

window.currentUser = null;

// Helper: Show notification toast
window.showToast = function (message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  const bgColors = {
    success: 'bg-emerald-500/90 text-white border-emerald-400',
    error: 'bg-rose-500/90 text-white border-rose-400',
    info: 'bg-cyan-500/90 text-white border-cyan-400',
    warning: 'bg-amber-500/90 text-white border-amber-400'
  };

  const icons = {
    success: 'fa-check-circle',
    error: 'fa-exclamation-circle',
    info: 'fa-info-circle',
    warning: 'fa-exclamation-triangle'
  };

  toast.className = `flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg border backdrop-blur-md transition-all duration-300 transform translate-y-2 opacity-0 text-sm font-medium ${bgColors[type] || bgColors.info}`;
  toast.innerHTML = `
    <i class="fas ${icons[type] || icons.info} text-base"></i>
    <span>${message}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.remove('translate-y-2', 'opacity-0');
  }, 10);

  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 3800);
};

// Check active session on load
async function checkAuthSession() {
  try {
    const res = await fetch('/api/auth/me');
    const data = await res.json();
    if (data.authenticated) {
      window.currentUser = data.user;
      renderUserUI(data.user);
    } else {
      window.currentUser = null;
      renderGuestUI();
    }
  } catch (e) {
    console.error('Session check error:', e);
    renderGuestUI();
  }
}

// Update UI when logged in
function renderUserUI(user) {
  const userActions = document.getElementById('user-nav-actions');
  if (!userActions) return;

  userActions.innerHTML = `
    <div class="relative group">
      <button id="profile-menu-btn" class="btn-reactive flex items-center gap-2 px-3 py-1.5 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 transition-all text-sm">
        <div class="w-7 h-7 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white text-xs font-bold shadow-md">
          ${user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
        </div>
        <div class="text-left hidden md:block leading-tight">
          <div class="font-semibold text-xs theme-text-primary max-w-[120px] truncate">${user.full_name || 'Trader'}</div>
          <div class="text-[10px] text-cyan-400 max-w-[120px] truncate">${user.email}</div>
        </div>
        <i class="fas fa-chevron-down text-[10px] text-slate-400 group-hover:rotate-180 transition-transform"></i>
      </button>

      <!-- Dropdown Menu -->
      <div class="absolute right-0 mt-2 w-56 rounded-2xl glass-panel p-2 shadow-2xl border border-white/10 hidden group-hover:block z-50 animate-fadeIn">
        <div class="px-3 py-2 border-b border-white/10 mb-1">
          <p class="text-xs font-semibold theme-text-primary truncate">${user.full_name}</p>
          <p class="text-[11px] text-slate-400 truncate">${user.email}</p>
        </div>
        <button onclick="openEditPasswordModal()" class="btn-reactive w-full text-left px-3 py-2 rounded-xl text-xs flex items-center gap-2.5 text-slate-200 hover:text-white hover:bg-white/10 transition-colors">
          <i class="fas fa-key text-cyan-400"></i>
          <span>Edit / Change Password</span>
        </button>
        <button onclick="openProfileModal()" class="btn-reactive w-full text-left px-3 py-2 rounded-xl text-xs flex items-center gap-2.5 text-slate-200 hover:text-white hover:bg-white/10 transition-colors">
          <i class="fas fa-user-circle text-blue-400"></i>
          <span>Account Settings</span>
        </button>
        <div class="border-t border-white/10 my-1"></div>
        <button onclick="handleLogout()" class="btn-reactive w-full text-left px-3 py-2 rounded-xl text-xs flex items-center gap-2.5 text-rose-400 hover:bg-rose-500/10 transition-colors">
          <i class="fas fa-sign-out-alt"></i>
          <span>Sign Out</span>
        </button>
      </div>
    </div>
  `;
}

// Update UI when guest
function renderGuestUI() {
  const userActions = document.getElementById('user-nav-actions');
  if (!userActions) return;

  userActions.innerHTML = `
    <button onclick="openAuthModal('login')" class="btn-reactive btn-secondary px-4 py-2 rounded-xl text-xs font-semibold">
      <i class="fas fa-sign-in-alt mr-1.5 text-cyan-400"></i> Sign In
    </button>
    <button onclick="openAuthModal('register')" class="btn-reactive btn-primary px-4 py-2 rounded-xl text-xs font-semibold hidden sm:flex items-center">
      <i class="fas fa-user-plus mr-1.5"></i> Register
    </button>
  `;
}

// Open Auth Modal with specific tab
window.openAuthModal = function (tab = 'login') {
  const modal = document.getElementById('auth-modal');
  if (!modal) return;
  modal.classList.remove('hidden');
  switchAuthTab(tab);
};

window.closeAuthModal = function () {
  const modal = document.getElementById('auth-modal');
  if (modal) modal.classList.add('hidden');
};

// Switch tabs inside Auth Modal (login / register / forgot)
window.switchAuthTab = function (tabName) {
  const tabs = ['login', 'register', 'forgot'];
  tabs.forEach((t) => {
    const pane = document.getElementById(`auth-pane-${t}`);
    const btn = document.getElementById(`auth-tab-${t}`);
    if (pane) pane.classList.toggle('hidden', t !== tabName);
    if (btn) btn.classList.toggle('active', t === tabName);
  });
};

// Login Handler
window.handleLogin = async function (e) {
  if (e) e.preventDefault();
  const emailInput = document.getElementById('login-email');
  const passwordInput = document.getElementById('login-password');
  const errorElem = document.getElementById('login-error');

  const email = emailInput.value.trim();
  const password = passwordInput.value;

  if (!email || !password) {
    if (errorElem) {
      errorElem.innerText = 'Please enter both your Gmail and password.';
      errorElem.classList.remove('hidden');
    }
    return;
  }

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();

    if (data.success) {
      window.currentUser = data.user;
      renderUserUI(data.user);
      closeAuthModal();
      showToast(`Welcome back, ${data.user.full_name}!`, 'success');
      if (window.loadWatchlist) window.loadWatchlist();
      if (window.loadPredictionHistory) window.loadPredictionHistory();
    } else {
      if (errorElem) {
        errorElem.innerText = data.message;
        errorElem.classList.remove('hidden');
      }
    }
  } catch (err) {
    if (errorElem) {
      errorElem.innerText = 'Connection error. Please try again.';
      errorElem.classList.remove('hidden');
    }
  }
};

// Quick Demo Login Handler
window.fillDemoAccount = function () {
  document.getElementById('login-email').value = 'trader@gmail.com';
  document.getElementById('login-password').value = 'demo12345';
  showToast('Demo account credentials prefilled! Signing in...', 'info');
  handleLogin();
};

// Register Handler
window.handleRegister = async function (e) {
  if (e) e.preventDefault();
  const nameInput = document.getElementById('reg-name');
  const emailInput = document.getElementById('reg-email');
  const passwordInput = document.getElementById('reg-password');
  const errorElem = document.getElementById('reg-error');

  const full_name = nameInput.value.trim();
  const email = emailInput.value.trim();
  const password = passwordInput.value;

  if (!email.includes('@')) {
    if (errorElem) {
      errorElem.innerText = 'Please enter a valid Gmail / email address.';
      errorElem.classList.remove('hidden');
    }
    return;
  }

  if (password.length < 6) {
    if (errorElem) {
      errorElem.innerText = 'Password must be at least 6 characters.';
      errorElem.classList.remove('hidden');
    }
    return;
  }

  try {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name, email, password })
    });
    const data = await res.json();

    if (data.success) {
      window.currentUser = data.user;
      renderUserUI(data.user);
      closeAuthModal();
      showToast('Registration successful! Account created.', 'success');
      if (window.loadWatchlist) window.loadWatchlist();
    } else {
      if (errorElem) {
        errorElem.innerText = data.message;
        errorElem.classList.remove('hidden');
      }
    }
  } catch (err) {
    if (errorElem) {
      errorElem.innerText = 'Registration failed. Please check network.';
      errorElem.classList.remove('hidden');
    }
  }
};

// Reset Password Handler (Direct by Gmail)
window.handleResetPassword = async function (e) {
  if (e) e.preventDefault();
  const emailInput = document.getElementById('reset-email');
  const newPassInput = document.getElementById('reset-new-password');
  const confirmPassInput = document.getElementById('reset-confirm-password');
  const errorElem = document.getElementById('reset-error');

  const email = emailInput.value.trim();
  const new_password = newPassInput.value;
  const confirm = confirmPassInput.value;

  if (new_password !== confirm) {
    if (errorElem) {
      errorElem.innerText = 'Passwords do not match.';
      errorElem.classList.remove('hidden');
    }
    return;
  }

  try {
    const res = await fetch('/api/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, new_password })
    });
    const data = await res.json();

    if (data.success) {
      showToast(data.message, 'success');
      switchAuthTab('login');
      document.getElementById('login-email').value = email;
      document.getElementById('login-password').value = new_password;
    } else {
      if (errorElem) {
        errorElem.innerText = data.message;
        errorElem.classList.remove('hidden');
      }
    }
  } catch (err) {
    if (errorElem) {
      errorElem.innerText = 'Password reset failed.';
      errorElem.classList.remove('hidden');
    }
  }
};

// Open Edit Password Modal for logged-in user
window.openEditPasswordModal = function () {
  const modal = document.getElementById('edit-password-modal');
  if (!modal) return;
  modal.classList.remove('hidden');
  document.getElementById('edit-pass-current').value = '';
  document.getElementById('edit-pass-new').value = '';
  document.getElementById('edit-pass-confirm').value = '';
  document.getElementById('edit-pass-error').classList.add('hidden');
};

window.closeEditPasswordModal = function () {
  const modal = document.getElementById('edit-password-modal');
  if (modal) modal.classList.add('hidden');
};

// Submit Edit Password (with Current Password Verification)
window.handleUpdatePassword = async function (e) {
  if (e) e.preventDefault();
  const current_password = document.getElementById('edit-pass-current').value;
  const new_password = document.getElementById('edit-pass-new').value;
  const confirm_pass = document.getElementById('edit-pass-confirm').value;
  const errorElem = document.getElementById('edit-pass-error');

  if (new_password.length < 6) {
    errorElem.innerText = 'New password must be at least 6 characters.';
    errorElem.classList.remove('hidden');
    return;
  }

  if (new_password !== confirm_pass) {
    errorElem.innerText = 'New passwords do not match.';
    errorElem.classList.remove('hidden');
    return;
  }

  try {
    const res = await fetch('/api/auth/update-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ current_password, new_password })
    });
    const data = await res.json();

    if (data.success) {
      closeEditPasswordModal();
      showToast('Password successfully updated!', 'success');
    } else {
      errorElem.innerText = data.message;
      errorElem.classList.remove('hidden');
    }
  } catch (err) {
    errorElem.innerText = 'Failed to update password.';
    errorElem.classList.remove('hidden');
  }
};

// Open Profile / Account Settings Modal
window.openProfileModal = function () {
  const modal = document.getElementById('profile-modal');
  if (!modal || !window.currentUser) return;
  document.getElementById('prof-name-input').value = window.currentUser.full_name || '';
  document.getElementById('prof-email-display').value = window.currentUser.email || '';
  modal.classList.remove('hidden');
};

window.closeProfileModal = function () {
  const modal = document.getElementById('profile-modal');
  if (modal) modal.classList.add('hidden');
};

// Save Profile Updates
window.handleSaveProfile = async function (e) {
  if (e) e.preventDefault();
  const full_name = document.getElementById('prof-name-input').value.trim();
  const theme_pref = document.documentElement.getAttribute('data-theme') || 'dark';

  try {
    const res = await fetch('/api/auth/update-profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name, theme_pref })
    });
    const data = await res.json();
    if (data.success) {
      window.currentUser.full_name = full_name;
      renderUserUI(window.currentUser);
      closeProfileModal();
      showToast('Profile successfully updated!', 'success');
    }
  } catch (err) {
    showToast('Failed to update profile.', 'error');
  }
};

// Logout Handler
window.handleLogout = async function () {
  try {
    await fetch('/api/auth/logout', { method: 'POST' });
    window.currentUser = null;
    renderGuestUI();
    showToast('You have been logged out.', 'info');
  } catch (err) {
    console.error(err);
  }
};

// Toggle password visibility in inputs
window.togglePasswordVisibility = function (inputId, eyeIconId) {
  const input = document.getElementById(inputId);
  const icon = document.getElementById(eyeIconId);
  if (!input || !icon) return;

  if (input.type === 'password') {
    input.type = 'text';
    icon.classList.remove('fa-eye');
    icon.classList.add('fa-eye-slash');
  } else {
    input.type = 'password';
    icon.classList.remove('fa-eye-slash');
    icon.classList.add('fa-eye');
  }
};

// Initialize session
document.addEventListener('DOMContentLoaded', checkAuthSession);
