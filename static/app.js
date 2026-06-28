/* =============================================================
   BLOXY-BOT AI — app.js
   Complete frontend logic — all parts integrated
============================================================= */

'use strict';

/* =============================================================
   PART 1 — CONFIG, STATE, DOM REFS, UTILITIES
============================================================= */

// ── Admin emails ──────────────────────────────────────────────
const ADMIN_EMAILS = [
  'alvinogthegreat177@gmail.com',
  'alvinogthegreat177@outlook.com'
];

// ── App state ─────────────────────────────────────────────────
const State = {
  user: null,
  chats: {},
  activeChatId: null,
  isStreaming: false,
  abortController: null,
  activeModel: 'gpt-4o',
  activeProvider: 'openai',
  activeTool: null,
  webSearchEnabled: false,
  settings: {
    streaming: true,
    autoscroll: true,
    enterSend: true,
    memory: true,
    language: 'en',
    defaultModel: 'gpt-4o',
    maxTokens: 4096,
    temperature: 0.7,
    systemPrompt: '',
    fontSize: 'md',
    reduceMotion: false,
    contextWindow: 20,
    memoryEnabled: true,
    integrations: {
      tavily: true,
      exa: false,
      firecrawl: true,
      wikipedia: true,
      weather: true,
      finance: true,
      news: true,
      sports: true,
      tmdb: true
    }
  },
  pendingDeleteChatId: null,
  importData: null,
  sidebarOpen: false
};

// ── DOM refs ──────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const $$ = sel => document.querySelectorAll(sel);

const DOM = {
  app: $('app'),
  sidebar: $('sidebar'),
  sidebarOverlay: $('sidebar-overlay'),
  mobileMenuBtn: $('mobile-menu-btn'),
  newChatBtn: $('new-chat-btn'),
  chatSearch: $('chat-search'),
  chatHistoryList: $('chat-history-list'),
  heroScreen: $('hero-screen'),
  messagesContainer: $('messages-container'),
  typingIndicator: $('typing-indicator'),
  chatInput: $('chat-input'),
  sendBtn: $('send-btn'),
  stopBtn: $('stop-btn'),
  attachBtn: $('attach-btn'),
  fileInput: $('file-input'),
  filePreviewStrip: $('file-preview-strip'),
  activeToolBadge: $('active-tool-badge'),
  activeToolName: $('active-tool-name'),
  activeToolIcon: $('active-tool-icon'),
  activeToolRemove: $('active-tool-remove'),
  composerWrap: $('composer-wrap'),
  modelSelectorBtn: $('model-selector-btn'),
  modelDropdown: $('model-dropdown'),
  currentModelName: $('current-model-name'),
  modelDot: $('model-dot'),
  modelSelector: $('model-selector'),
  webSearchToggle: $('web-search-toggle'),
  toolsToggleBtn: $('tools-toggle-btn'),
  toolsPanel: $('tools-panel'),
  toolsPanelClose: $('tools-panel-close'),
  importChatBtn: $('import-chat-btn'),
  shortcutsBtn: $('shortcuts-btn'),
  sidebarUserBtn: $('sidebar-user-btn'),
  sidebarUsername: $('sidebar-username'),
  sidebarUserPlan: $('sidebar-user-plan'),
  userInitials: $('user-initials'),
  settingsBtn: $('settings-btn'),
  helpBtn: $('help-btn'),
  exportBtn: $('export-btn'),
  toastContainer: $('toast-container'),
  // Modals
  userMenu: $('user-menu'),
  userMenuName: $('user-menu-name'),
  userMenuEmail: $('user-menu-email'),
  userMenuInitials: $('user-menu-initials'),
  adminBadge: $('admin-badge'),
  adminPanelLi: $('admin-panel-li'),
  loginMenuLi: $('login-menu-li'),
  logoutMenuLi: $('logout-menu-li'),
  loginMenuBtn: $('login-menu-btn'),
  logoutBtn: $('logout-btn'),
  adminPanelBtn: $('admin-panel-btn'),
  profileBtn: $('profile-btn'),
  authModalOverlay: $('auth-modal-overlay'),
  authModalClose: $('auth-modal-close'),
  tabLogin: $('tab-login'),
  tabRegister: $('tab-register'),
  panelLogin: $('panel-login'),
  panelRegister: $('panel-register'),
  panelForgot: $('panel-forgot'),
  loginForm: $('login-form'),
  registerForm: $('register-form'),
  forgotForm: $('forgot-form'),
  forgotPasswordBtn: $('forgot-password-btn'),
  backToLoginBtn: $('back-to-login-btn'),
  googleLoginBtn: $('google-login-btn'),
  githubLoginBtn: $('github-login-btn'),
  googleRegisterBtn: $('google-register-btn'),
  githubRegisterBtn: $('github-register-btn'),
  toggleLoginPassword: $('toggle-login-password'),
  toggleRegisterPassword: $('toggle-register-password'),
  settingsModalOverlay: $('settings-modal-overlay'),
  settingsModalClose: $('settings-modal-close'),
  settingsCancelBtn: $('settings-cancel-btn'),
  settingsSaveBtn: $('settings-save-btn'),
  shortcutsModalOverlay: $('shortcuts-modal-overlay'),
  shortcutsModalClose: $('shortcuts-modal-close'),
  helpModalOverlay: $('help-modal-overlay'),
  helpModalClose: $('help-modal-close'),
  confirmModalOverlay: $('confirm-modal-overlay'),
  confirmCancelBtn: $('confirm-cancel-btn'),
  confirmOkBtn: $('confirm-ok-btn'),
  importModalOverlay: $('import-modal-overlay'),
  importModalClose: $('import-modal-close'),
  importDropZone: $('import-drop-zone'),
  importBrowseBtn: $('import-browse-btn'),
  importFileInput: $('import-file-input'),
  importCancelBtn: $('import-cancel-btn'),
  importConfirmBtn: $('import-confirm-btn'),
  adminModalOverlay: $('admin-modal-overlay'),
  adminModalClose: $('admin-modal-close'),
  adminRefreshBtn: $('admin-refresh-btn'),
  checkProvidersBtn: $('check-providers-btn'),
};

// ── Storage helpers ───────────────────────────────────────────
const Storage = {
  get(key, fallback = null) {
    try {
      const v = localStorage.getItem(`bloxy_${key}`);
      return v !== null ? JSON.parse(v) : fallback;
    } catch { return fallback; }
  },
  set(key, value) {
    try { localStorage.setItem(`bloxy_${key}`, JSON.stringify(value)); } catch {}
  },
  remove(key) {
    try { localStorage.removeItem(`bloxy_${key}`); } catch {}
  }
};

// ── Toast notifications ───────────────────────────────────────
function showToast(message, type = 'info', duration = 3500) {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'assertive');

  const icons = {
    success: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    error: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
    info: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
    warning: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
  };

  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <span class="toast-msg">${escapeHtml(message)}</span>
    <button class="toast-close" aria-label="Dismiss notification">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
    </button>`;

  toast.querySelector('.toast-close').addEventListener('click', () => dismissToast(toast));
  DOM.toastContainer.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('toast-show'));
  setTimeout(() => dismissToast(toast), duration);
  return toast;
}

function dismissToast(toast) {
  toast.classList.remove('toast-show');
  toast.classList.add('toast-hide');
  setTimeout(() => toast.remove(), 350);
}

// ── Utility functions ─────────────────────────────────────────
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function generateId() {
  return `${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

function formatTime(ts) {
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatDate(ts) {
  const d = new Date(ts);
  const now = new Date();
  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);
  if (d.toDateString() === now.toDateString()) return 'Today';
  if (d.toDateString() === yesterday.toDateString()) return 'Yesterday';
  const diff = Math.floor((now - d) / 86400000);
  if (diff < 7) return 'Last 7 days';
  if (diff < 30) return 'Last 30 days';
  return d.toLocaleDateString([], { month: 'short', year: 'numeric' });
}

function getInitials(name) {
  if (!name) return 'U';
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
}

function isAdmin(email) {
  return ADMIN_EMAILS.includes((email || '').toLowerCase());
}

function autoResizeTextarea(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 200) + 'px';
}

function closeAllDropdowns() {
  DOM.modelSelector.setAttribute('aria-expanded', 'false');
  DOM.modelDropdown.classList.remove('open');
  DOM.userMenu.hidden = true;
}

/* =============================================================
   PART 2 — AUTH (LOGIN, REGISTER, FORGOT, GOOGLE, GITHUB)
============================================================= */

// ── Show / hide auth modal ────────────────────────────────────
function openAuthModal(panel = 'login') {
  DOM.authModalOverlay.hidden = false;
  document.body.classList.add('modal-open');
  switchAuthPanel(panel);
  requestAnimationFrame(() => DOM.authModalOverlay.classList.add('modal-visible'));
}

function closeAuthModal() {
  DOM.authModalOverlay.classList.remove('modal-visible');
  setTimeout(() => {
    DOM.authModalOverlay.hidden = true;
    document.body.classList.remove('modal-open');
  }, 250);
}

function switchAuthPanel(panel) {
  DOM.panelLogin.hidden = panel !== 'login';
  DOM.panelRegister.hidden = panel !== 'register';
  DOM.panelForgot.hidden = panel !== 'forgot';
  DOM.tabLogin.setAttribute('aria-selected', panel === 'login');
  DOM.tabRegister.setAttribute('aria-selected', panel === 'register');
  DOM.tabLogin.classList.toggle('active', panel === 'login');
  DOM.tabRegister.classList.toggle('active', panel === 'register');
  clearAuthErrors();
}

function clearAuthErrors() {
  $$('.form-error').forEach(el => { el.textContent = ''; });
}

function setFormLoading(form, loading) {
  const btn = form.querySelector('[type="submit"]');
  if (!btn) return;
  btn.disabled = loading;
  btn.querySelector('.btn-text').style.opacity = loading ? '0' : '1';
  btn.querySelector('.btn-spinner').hidden = !loading;
}

function showFieldError(id, msg) {
  const el = $(id);
  if (el) el.textContent = msg;
}

// ── Session management ────────────────────────────────────────
async function checkSession() {
  try {
    const res = await fetch('/api/auth/me', { credentials: 'include' });
    if (res.ok) {
      const data = await res.json();
      setUser(data.user);
    } else {
      setUser(null);
    }
  } catch {
    setUser(null);
  }
}

function setUser(user) {
  State.user = user;
  updateUserUI();
  if (user && isAdmin(user.email)) {
    DOM.adminPanelLi.hidden = false;
    DOM.adminBadge.hidden = false;
  } else {
    DOM.adminPanelLi.hidden = true;
    DOM.adminBadge.hidden = true;
  }
}

function updateUserUI() {
  const u = State.user;
  const name = u ? u.name : 'Guest User';
  const plan = u ? (isAdmin(u.email) ? '⚡ Admin' : 'Free plan') : 'Free plan';
  const initials = u ? getInitials(u.name) : 'G';
  const email = u ? u.email : 'Not signed in';

  DOM.sidebarUsername.textContent = name;
  DOM.sidebarUserPlan.textContent = plan;
  DOM.userInitials.textContent = initials;
  DOM.userMenuName.textContent = name;
  DOM.userMenuEmail.textContent = email;
  DOM.userMenuInitials.textContent = initials;

  DOM.loginMenuLi.hidden = !!u;
  DOM.logoutMenuLi.hidden = !u;
}

// ── Login ─────────────────────────────────────────────────────
DOM.loginForm.addEventListener('submit', async e => {
  e.preventDefault();
  clearAuthErrors();
  const email = $('login-email').value.trim();
  const password = $('login-password').value;
  const remember = $('remember-me').checked;

  if (!email) return showFieldError('login-email-error', 'Email is required.');
  if (!password) return showFieldError('login-password-error', 'Password is required.');

  setFormLoading(DOM.loginForm, true);
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password, remember })
    });
    const data = await res.json();
    if (res.ok) {
      setUser(data.user);
      closeAuthModal();
      showToast(`Welcome back, ${data.user.name}!`, 'success');
      loadChats();
    } else {
      showFieldError('login-global-error', data.detail || 'Login failed. Please try again.');
    }
  } catch {
    showFieldError('login-global-error', 'Network error. Please try again.');
  } finally {
    setFormLoading(DOM.loginForm, false);
  }
});

// ── Register ──────────────────────────────────────────────────
DOM.registerForm.addEventListener('submit', async e => {
  e.preventDefault();
  clearAuthErrors();
  const name = $('register-name').value.trim();
  const email = $('register-email').value.trim();
  const password = $('register-password').value;

  if (!name) return showFieldError('register-name-error', 'Name is required.');
  if (!email) return showFieldError('register-email-error', 'Email is required.');
  if (password.length < 8) return showFieldError('register-password-error', 'Password must be at least 8 characters.');

  setFormLoading(DOM.registerForm, true);
  try {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ name, email, password })
    });
    const data = await res.json();
    if (res.ok) {
      setUser(data.user);
      closeAuthModal();
      showToast(`Account created! Welcome, ${data.user.name}!`, 'success');
      loadChats();
    } else {
      showFieldError('register-global-error', data.detail || 'Registration failed. Please try again.');
    }
  } catch {
    showFieldError('register-global-error', 'Network error. Please try again.');
  } finally {
    setFormLoading(DOM.registerForm, false);
  }
});

// ── Forgot password ───────────────────────────────────────────
DOM.forgotForm.addEventListener('submit', async e => {
  e.preventDefault();
  clearAuthErrors();
  const email = $('forgot-email').value.trim();
  if (!email) return showFieldError('forgot-email-error', 'Email is required.');

  setFormLoading(DOM.forgotForm, true);
  try {
    const res = await fetch('/api/auth/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    if (res.ok) {
      showToast('Reset link sent! Check your inbox.', 'success');
      switchAuthPanel('login');
    } else {
      const data = await res.json();
      showFieldError('forgot-global-error', data.detail || 'Failed to send reset link.');
    }
  } catch {
    showFieldError('forgot-global-error', 'Network error. Please try again.');
  } finally {
    setFormLoading(DOM.forgotForm, false);
  }
});

// ── Google OAuth ──────────────────────────────────────────────
function handleGoogleAuth() {
  window.location.href = '/api/auth/google';
}
DOM.googleLoginBtn.addEventListener('click', handleGoogleAuth);
DOM.googleRegisterBtn.addEventListener('click', handleGoogleAuth);

// ── GitHub OAuth ──────────────────────────────────────────────
function handleGitHubAuth() {
  window.location.href = '/api/auth/github';
}
DOM.githubLoginBtn.addEventListener('click', handleGitHubAuth);
DOM.githubRegisterBtn.addEventListener('click', handleGitHubAuth);

// ── Logout ────────────────────────────────────────────────────
DOM.logoutBtn.addEventListener('click', async () => {
  DOM.userMenu.hidden = true;
  try {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
  } catch {}
  setUser(null);
  State.chats = {};
  State.activeChatId = null;
  showHeroScreen();
  renderChatHistory();
  showToast('Signed out successfully.', 'info');
});

// ── Auth modal events ─────────────────────────────────────────
DOM.authModalClose.addEventListener('click', closeAuthModal);
DOM.authModalOverlay.addEventListener('click', e => { if (e.target === DOM.authModalOverlay) closeAuthModal(); });
DOM.tabLogin.addEventListener('click', () => switchAuthPanel('login'));
DOM.tabRegister.addEventListener('click', () => switchAuthPanel('register'));
DOM.forgotPasswordBtn.addEventListener('click', () => switchAuthPanel('forgot'));
DOM.backToLoginBtn.addEventListener('click', () => switchAuthPanel('login'));
DOM.loginMenuBtn.addEventListener('click', () => { DOM.userMenu.hidden = true; openAuthModal('login'); });

// ── Password visibility toggles ───────────────────────────────
DOM.toggleLoginPassword.addEventListener('click', () => {
  const inp = $('login-password');
  inp.type = inp.type === 'password' ? 'text' : 'password';
});
DOM.toggleRegisterPassword.addEventListener('click', () => {
  const inp = $('register-password');
  inp.type = inp.type === 'password' ? 'text' : 'password';
});

/* =============================================================
   PART 3 — CHAT ENGINE (NEW CHAT, SEND, STREAMING, MARKDOWN)
============================================================= */

// ── Markdown renderer setup ───────────────────────────────────
function setupMarked() {
  if (typeof marked === 'undefined') return;
  marked.setOptions({
    highlight: (code, lang) => {
      if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
        return hljs.highlight(code, { language: lang }).value;
      }
      return typeof hljs !== 'undefined' ? hljs.highlightAuto(code).value : escapeHtml(code);
    },
    breaks: true,
    gfm: true
  });
}

function renderMarkdown(text) {
  if (typeof marked === 'undefined') return `<p>${escapeHtml(text)}</p>`;
  try {
    const raw = marked.parse(text);
    return typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(raw) : raw;
  } catch {
    return `<p>${escapeHtml(text)}</p>`;
  }
}

// ── New chat ──────────────────────────────────────────────────
function createNewChat() {
  const id = generateId();
  State.chats[id] = {
    id,
    title: 'New Chat',
    messages: [],
    model: State.activeModel,
    provider: State.activeProvider,
    createdAt: Date.now(),
    updatedAt: Date.now()
  };
  State.activeChatId = id;
  saveChats();
  showHeroScreen();
  renderChatHistory();
  DOM.chatInput.focus();
  closeMobileSidebar();
  return id;
}

function showHeroScreen() {
  DOM.heroScreen.hidden = false;
  DOM.messagesContainer.hidden = true;
  DOM.typingIndicator.hidden = true;
}

function showChatScreen() {
  DOM.heroScreen.hidden = true;
  DOM.messagesContainer.hidden = false;
}

// ── Load / save chats ─────────────────────────────────────────
function saveChats() {
  Storage.set('chats', State.chats);
}

function loadChats() {
  const saved = Storage.get('chats', {});
  State.chats = saved;
  renderChatHistory();
}

// ── Switch to a chat ──────────────────────────────────────────
function switchChat(id) {
  if (!State.chats[id]) return;
  State.activeChatId = id;
  showChatScreen();
  DOM.messagesContainer.innerHTML = '';
  const chat = State.chats[id];
  chat.messages.forEach(msg => appendMessage(msg, false));
  scrollToBottom(false);
  renderChatHistory();
  closeMobileSidebar();
}

// ── Render chat history sidebar ───────────────────────────────
function renderChatHistory(filter = '') {
  const groups = { today: [], yesterday: [], week: [], older: [] };
  const now = Date.now();

  Object.values(State.chats)
    .sort((a, b) => b.updatedAt - a.updatedAt)
    .filter(c => !filter || c.title.toLowerCase().includes(filter.toLowerCase()))
    .forEach(chat => {
      const label = formatDate(chat.updatedAt);
      if (label === 'Today') groups.today.push(chat);
      else if (label === 'Yesterday') groups.yesterday.push(chat);
      else if (label === 'Last 7 days') groups.week.push(chat);
      else groups.older.push(chat);
    });

  const container = DOM.chatHistoryList;
  container.innerHTML = '';

  const groupDefs = [
    { key: 'today', label: 'Today' },
    { key: 'yesterday', label: 'Yesterday' },
    { key: 'week', label: 'Last 7 days' },
    { key: 'older', label: 'Older' }
  ];

  groupDefs.forEach(({ key, label }) => {
    if (!groups[key].length) return;
    const groupEl = document.createElement('div');
    groupEl.className = 'history-group';
    groupEl.innerHTML = `<span class="history-label">${label}</span>`;
    const ul = document.createElement('ul');
    ul.className = 'history-list';
    ul.setAttribute('role', 'list');

    groups[key].forEach(chat => {
      const li = document.createElement('li');
      li.className = `history-item${chat.id === State.activeChatId ? ' active' : ''}`;
      li.dataset.chatId = chat.id;
      li.setAttribute('role', 'listitem');
      li.innerHTML = `
        <button class="history-item-btn"${chat.id === State.activeChatId ? ' aria-current="page"' : ''}>
          <span class="history-icon">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          </span>
          <span class="history-title">${escapeHtml(chat.title)}</span>
        </button>
        <div class="history-item-actions">
          <button class="history-action-btn rename-btn" aria-label="Rename chat" title="Rename">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          </button>
          <button class="history-action-btn danger delete-btn" aria-label="Delete chat" title="Delete">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
          </button>
        </div>`;

      li.querySelector('.history-item-btn').addEventListener('click', () => switchChat(chat.id));
      li.querySelector('.rename-btn').addEventListener('click', e => { e.stopPropagation(); startRenameChat(chat.id, li); });
      li.querySelector('.delete-btn').addEventListener('click', e => { e.stopPropagation(); confirmDeleteChat(chat.id); });
      ul.appendChild(li);
    });

    groupEl.appendChild(ul);
    container.appendChild(groupEl);
  });

  if (!Object.values(groups).flat().length) {
    container.innerHTML = `<div class="history-empty"><p>No chats yet.<br>Start a new conversation!</p></div>`;
  }
}

// ── Rename chat ───────────────────────────────────────────────
function startRenameChat(id, liEl) {
  const titleEl = liEl.querySelector('.history-title');
  const current = State.chats[id]?.title || '';
  const input = document.createElement('input');
  input.type = 'text';
  input.className = 'history-rename-input';
  input.value = current;
  input.setAttribute('aria-label', 'Rename chat');
  titleEl.replaceWith(input);
  input.focus();
  input.select();

  function commit() {
    const newTitle = input.value.trim() || current;
    if (State.chats[id]) {
      State.chats[id].title = newTitle;
      saveChats();
    }
    renderChatHistory();
  }

  input.addEventListener('blur', commit);
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); commit(); }
    if (e.key === 'Escape') { renderChatHistory(); }
  });
}

// ── Delete chat ───────────────────────────────────────────────
function confirmDeleteChat(id) {
  State.pendingDeleteChatId = id;
  DOM.confirmModalOverlay.hidden = false;
  document.body.classList.add('modal-open');
  requestAnimationFrame(() => DOM.confirmModalOverlay.classList.add('modal-visible'));
}

DOM.confirmOkBtn.addEventListener('click', () => {
  const id = State.pendingDeleteChatId;
  if (id && State.chats[id]) {
    delete State.chats[id];
    saveChats();
    if (State.activeChatId === id) {
      State.activeChatId = null;
      showHeroScreen();
    }
    renderChatHistory();
    showToast('Chat deleted.', 'info');
  }
  closeConfirmModal();
});

DOM.confirmCancelBtn.addEventListener('click', closeConfirmModal);
DOM.confirmModalOverlay.addEventListener('click', e => { if (e.target === DOM.confirmModalOverlay) closeConfirmModal(); });

function closeConfirmModal() {
  DOM.confirmModalOverlay.classList.remove('modal-visible');
  setTimeout(() => { DOM.confirmModalOverlay.hidden = true; document.body.classList.remove('modal-open'); }, 250);
  State.pendingDeleteChatId = null;
}

// ── Send message ──────────────────────────────────────────────
async function sendMessage() {
  const text = DOM.chatInput.value.trim();
  const file = DOM.fileInput.files[0] || null;
  if (!text && !file) return;
  if (State.isStreaming) return;

  if (!State.activeChatId || !State.chats[State.activeChatId]) {
    createNewChat();
  }

  const userMsg = {
    id: generateId(),
    role: 'user',
    content: text,
    timestamp: Date.now(),
    file: file ? { name: file.name, type: file.type } : null
  };

  State.chats[State.activeChatId].messages.push(userMsg);
  if (State.chats[State.activeChatId].messages.length === 1) {
    State.chats[State.activeChatId].title = text.slice(0, 50) || 'New Chat';
  }
  State.chats[State.activeChatId].updatedAt = Date.now();
  saveChats();

  DOM.chatInput.value = '';
  autoResizeTextarea(DOM.chatInput);
  DOM.sendBtn.disabled = true;
  clearFilePreview();

  showChatScreen();
  appendMessage(userMsg, true);
  renderChatHistory();
  showTypingIndicator();

  try {
    await streamResponse(text, file);
  } catch (err) {
    hideTypingIndicator();
    if (err.name !== 'AbortError') {
      showToast('Failed to get response. Please try again.', 'error');
      appendErrorMessage('Sorry, something went wrong. Please try again.');
    }
  }
}

// ── Streaming response ────────────────────────────────────────
async function streamResponse(userText, file = null) {
  State.isStreaming = true;
  State.abortController = new AbortController();
  DOM.stopBtn.hidden = false;
  DOM.sendBtn.hidden = true;

  const chat = State.chats[State.activeChatId];
  const contextMessages = chat.messages
    .slice(-(State.settings.contextWindow || 20))
    .map(m => ({ role: m.role, content: m.content }));

  const payload = {
    messages: contextMessages,
    model: State.activeModel,
    provider: State.activeProvider,
    tool: State.activeTool,
    web_search: State.webSearchEnabled,
    max_tokens: State.settings.maxTokens,
    temperature: State.settings.temperature,
    system_prompt: State.settings.systemPrompt,
    stream: State.settings.streaming
  };

  if (file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('data', JSON.stringify(payload));
    var fetchOptions = { method: 'POST', body: formData, signal: State.abortController.signal, credentials: 'include' };
  } else {
    var fetchOptions = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: State.abortController.signal,
      credentials: 'include'
    };
  }

  const res = await fetch('/api/chat', fetchOptions);

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  hideTypingIndicator();

  const assistantMsgId = generateId();
  const assistantMsg = {
    id: assistantMsgId,
    role: 'assistant',
    content: '',
    timestamp: Date.now(),
    model: State.activeModel,
    provider: State.activeProvider
  };
  chat.messages.push(assistantMsg);
  appendMessage(assistantMsg, true);

  const msgEl = document.querySelector(`[data-msg-id="${assistantMsgId}"] .message-body`);

  if (State.settings.streaming && res.headers.get('content-type')?.includes('text/event-stream')) {
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          if (data === '[DONE]') break;
          try {
            const parsed = JSON.parse(data);
            const delta = parsed.choices?.[0]?.delta?.content || parsed.content || '';
            assistantMsg.content += delta;
            if (msgEl) msgEl.innerHTML = renderMarkdown(assistantMsg.content);
            addCodeCopyButtons(msgEl);
            if (State.settings.autoscroll) scrollToBottom();
          } catch {}
        }
      }
    }
  } else {
    const data = await res.json();
    assistantMsg.content = data.content || data.choices?.[0]?.message?.content || '';
    if (msgEl) msgEl.innerHTML = renderMarkdown(assistantMsg.content);
    addCodeCopyButtons(msgEl);
  }

  finalizeResponse(assistantMsg, assistantMsgId);
}

function finalizeResponse(msg, id) {
  State.isStreaming = false;
  State.abortController = null;
  DOM.stopBtn.hidden = true;
  DOM.sendBtn.hidden = false;
  saveChats();

  const msgEl = document.querySelector(`[data-msg-id="${id}"]`);
  if (msgEl) addMessageActions(msgEl, msg);
  if (State.settings.autoscroll) scrollToBottom();
  renderChatHistory();
}

// ── Append message to DOM ─────────────────────────────────────
function appendMessage(msg, animate = true) {
  const isUser = msg.role === 'user';
  const wrap = document.createElement('div');
  wrap.className = `message-wrap ${isUser ? 'message-user' : 'message-assistant'}${animate ? ' message-enter' : ''}`;
  wrap.dataset.msgId = msg.id;

  if (isUser) {
    wrap.innerHTML = `
      <div class="message-bubble user-bubble">
        <div class="message-body">${escapeHtml(msg.content)}</div>
        ${msg.file ? `<div class="message-file"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg> ${escapeHtml(msg.file.name)}</div>` : ''}
        <div class="message-meta">
          <span class="message-time">${formatTime(msg.timestamp)}</span>
          <button class="msg-action-btn edit-btn" aria-label="Edit message" title="Edit">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          </button>
        </div>
      </div>`;
    wrap.querySelector('.edit-btn')?.addEventListener('click', () => editMessage(msg, wrap));
  } else {
    wrap.innerHTML = `
      <div class="message-avatar" aria-hidden="true">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" fill="#f97316" opacity="0.15"/>
          <path d="M8 12.5C8 10.567 9.567 9 11.5 9H13C14.657 9 16 10.343 16 12C16 13.657 14.657 15 13 15H11L9 17V15H8V12.5Z" fill="#f97316"/>
          <circle cx="11" cy="12" r="1" fill="#fff"/>
          <circle cx="13.5" cy="12" r="1" fill="#fff"/>
        </svg>
      </div>
      <div class="message-bubble assistant-bubble">
        <div class="message-body">${msg.content ? renderMarkdown(msg.content) : ''}</div>
        <div class="message-meta">
          <span class="message-time">${formatTime(msg.timestamp)}</span>
          <span class="message-model">${escapeHtml(msg.model || State.activeModel)}</span>
        </div>
      </div>`;
    const bodyEl = wrap.querySelector('.message-body');
    if (msg.content) addCodeCopyButtons(bodyEl);
    if (!State.isStreaming) addMessageActions(wrap, msg);
  }

  DOM.messagesContainer.appendChild(wrap);
  if (animate && State.settings.autoscroll) scrollToBottom();
}

function appendErrorMessage(text) {
  const wrap = document.createElement('div');
  wrap.className = 'message-wrap message-error';
  wrap.innerHTML = `
    <div class="message-bubble error-bubble">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      <span>${escapeHtml(text)}</span>
    </div>`;
  DOM.messagesContainer.appendChild(wrap);
  scrollToBottom();
}

// ── Message actions (copy, regenerate, continue) ──────────────
function addMessageActions(wrap, msg) {
  const existing = wrap.querySelector('.message-actions');
  if (existing) existing.remove();

  if (msg.role !== 'assistant') return;

  const actions = document.createElement('div');
  actions.className = 'message-actions';
  actions.innerHTML = `
    <button class="msg-action-btn copy-msg-btn" aria-label="Copy message" title="Copy">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
    </button>
    <button class="msg-action-btn regenerate-btn" aria-label="Regenerate response" title="Regenerate">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
    </button>
    <button class="msg-action-btn continue-btn" aria-label="Continue response" title="Continue">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="13 17 18 12 13 7"/><polyline points="6 17 11 12 6 7"/></svg>
    </button>`;

  actions.querySelector('.copy-msg-btn').addEventListener('click', () => {
    navigator.clipboard.writeText(msg.content).then(() => showToast('Copied to clipboard!', 'success'));
  });
  actions.querySelector('.regenerate-btn').addEventListener('click', () => regenerateMessage(msg));
  actions.querySelector('.continue-btn').addEventListener('click', () => continueMessage(msg));

  wrap.querySelector('.message-bubble')?.appendChild(actions);
}

async function regenerateMessage(msg) {
  if (State.isStreaming) return;
  const chat = State.chats[State.activeChatId];
  const idx = chat.messages.findIndex(m => m.id === msg.id);
  if (idx === -1) return;
  chat.messages.splice(idx, 1);
  saveChats();
  const lastWrap = DOM.messagesContainer.querySelector(`[data-msg-id="${msg.id}"]`);
  if (lastWrap) lastWrap.remove();
  showTypingIndicator();
  try {
    await streamResponse(chat.messages[chat.messages.length - 1]?.content || '');
  } catch (err) {
    hideTypingIndicator();
    if (err.name !== 'AbortError') showToast('Regeneration failed.', 'error');
  }
}

async function continueMessage(msg) {
  if (State.isStreaming) return;
  const continuePrompt = '[Continue the previous response from exactly where it left off]';
  DOM.chatInput.value = continuePrompt;
  await sendMessage();
}

// ── Edit user message ─────────────────────────────────────────
function editMessage(msg, wrap) {
  const bubble = wrap.querySelector('.message-body');
  const original = msg.content;
  bubble.innerHTML = '';
  const textarea = document.createElement('textarea');
  textarea.className = 'edit-message-input';
  textarea.value = original;
  textarea.setAttribute('aria-label', 'Edit message');
  bubble.appendChild(textarea);
  autoResizeTextarea(textarea);
  textarea.focus();

  const btnRow = document.createElement('div');
  btnRow.className = 'edit-message-actions';
  btnRow.innerHTML = `<button class="btn-primary btn-sm" id="edit-save">Save & Resend</button><button class="btn-ghost btn-sm" id="edit-cancel">Cancel</button>`;
  bubble.appendChild(btnRow);

  btnRow.querySelector('#edit-cancel').addEventListener('click', () => {
    bubble.innerHTML = escapeHtml(original);
  });

  btnRow.querySelector('#edit-save').addEventListener('click', async () => {
    const newText = textarea.value.trim();
    if (!newText) return;
    const chat = State.chats[State.activeChatId];
    const idx = chat.messages.findIndex(m => m.id === msg.id);
    if (idx !== -1) {
      chat.messages.splice(idx);
      msg.content = newText;
      chat.messages.push(msg);
      saveChats();
    }
    const allWraps = DOM.messagesContainer.querySelectorAll('.message-wrap');
    allWraps.forEach((w, i) => { if (i >= idx) w.remove(); });
    bubble.innerHTML = escapeHtml(newText);
    showTypingIndicator();
    try {
      await streamResponse(newText);
    } catch (err) {
      hideTypingIndicator();
      if (err.name !== 'AbortError') showToast('Failed to resend.', 'error');
    }
  });
}

// ── Code copy buttons ─────────────────────────────────────────
function addCodeCopyButtons(container) {
  if (!container) return;
  container.querySelectorAll('pre').forEach(pre => {
    if (pre.querySelector('.code-copy-btn')) return;
    const btn = document.createElement('button');
    btn.className = 'code-copy-btn';
    btn.setAttribute('aria-label', 'Copy code');
    btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy`;
    btn.addEventListener('click', () => {
      const code = pre.querySelector('code')?.innerText || pre.innerText;
      navigator.clipboard.writeText(code).then(() => {
        btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> Copied!`;
        setTimeout(() => { btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy`; }, 2000);
      });
    });
    pre.style.position = 'relative';
    pre.appendChild(btn);
  });
}

// ── Typing indicator ──────────────────────────────────────────
function showTypingIndicator() {
  DOM.typingIndicator.hidden = false;
  scrollToBottom();
}
function hideTypingIndicator() {
  DOM.typingIndicator.hidden = true;
}

// ── Scroll ────────────────────────────────────────────────────
function scrollToBottom(smooth = true) {
  const container = DOM.messagesContainer;
  container.scrollTo({ top: container.scrollHeight, behavior: smooth ? 'smooth' : 'auto' });
}

// ── Stop generation ───────────────────────────────────────────
DOM.stopBtn.addEventListener('click', () => {
  if (State.abortController) {
    State.abortController.abort();
    State.isStreaming = false;
    DOM.stopBtn.hidden = true;
    DOM.sendBtn.hidden = false;
    hideTypingIndicator();
    showToast('Generation stopped.', 'info');
  }
});

// ── Composer events ───────────────────────────────────────────
DOM.chatInput.addEventListener('input', () => {
  autoResizeTextarea(DOM.chatInput);
  DOM.sendBtn.disabled = !DOM.chatInput.value.trim() && !DOM.fileInput.files.length;
});

DOM.chatInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey && State.settings.enterSend) {
    e.preventDefault();
    if (!DOM.sendBtn.disabled) sendMessage();
  }
});

DOM.sendBtn.addEventListener('click', sendMessage);

// ── Suggested prompts ─────────────────────────────────────────
$$('.prompt-card').forEach(card => {
  card.addEventListener('click', () => {
    const prompt = card.dataset.prompt;
    if (prompt) {
      DOM.chatInput.value = prompt;
      autoResizeTextarea(DOM.chatInput);
      DOM.sendBtn.disabled = false;
      DOM.chatInput.focus();
      sendMessage();
    }
  });
});

// ── File attach ───────────────────────────────────────────────
DOM.attachBtn.addEventListener('click', () => DOM.fileInput.click());
DOM.fileInput.addEventListener('change', () => {
  const file = DOM.fileInput.files[0];
  if (!file) return;
  showFilePreview(file);
  DOM.sendBtn.disabled = !DOM.chatInput.value.trim() && !file;
});

function showFilePreview(file) {
  DOM.filePreviewStrip.hidden = false;
  DOM.filePreviewStrip.innerHTML = `
    <div class="file-preview-item">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
      <span>${escapeHtml(file.name)}</span>
      <button class="file-preview-remove" aria-label="Remove file">
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>`;
  DOM.filePreviewStrip.querySelector('.file-preview-remove').addEventListener('click', clearFilePreview);
}

function clearFilePreview() {
  DOM.fileInput.value = '';
  DOM.filePreviewStrip.hidden = true;
  DOM.filePreviewStrip.innerHTML = '';
  DOM.sendBtn.disabled = !DOM.chatInput.value.trim();
}

/* =============================================================
   PART 4 — TOOLS PANEL
============================================================= */

const TOOL_LABELS = {
  web_search: 'Web Search',
  deep_research: 'Deep Research',
  translator: 'Translator',
  summarizer: 'Summarizer',
  rewrite: 'Rewrite',
  grammar: 'Grammar Fixer',
  explain_code: 'Explain Code',
  code_assistant: 'Code Assistant',
  math_solver: 'Math Solver',
  pdf_chat: 'PDF Chat',
  url_reader: 'URL Reader',
  image_analysis: 'Image Analysis'
};

const TOOL_ICONS = {
  web_search: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>`,
  deep_research: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>`,
  translator: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/><path d="M2 5h12"/><path d="M7 2h1"/><path d="m22 22-5-10-5 10"/><path d="M14 18h6"/></svg>`,
  summarizer: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="21" y1="10" x2="3" y2="10"/><line x1="21" y1="6" x2="3" y2="6"/><line x1="21" y1="14" x2="3" y2="14"/><line x1="21" y1="18" x2="9" y2="18"/></svg>`,
  rewrite: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
  grammar: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
  explain_code: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
  code_assistant: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>`,
  math_solver: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="5" x2="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/></svg>`,
  pdf_chat: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`,
  url_reader: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>`,
  image_analysis: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>`
};

// ── Tools panel toggle ────────────────────────────────────────
DOM.toolsToggleBtn.addEventListener('click', () => {
  const isHidden = DOM.toolsPanel.hidden;
  DOM.toolsPanel.hidden = !isHidden;
  if (!isHidden) DOM.toolsPanel.hidden = true;
});

DOM.toolsPanelClose.addEventListener('click', () => {
  DOM.toolsPanel.hidden = true;
});

// ── Tool card selection ───────────────────────────────────────
$$('.tool-card').forEach(card => {
  card.addEventListener('click', () => {
    const tool = card.dataset.tool;
    if (State.activeTool === tool) {
      clearActiveTool();
    } else {
      setActiveTool(tool);
    }
    DOM.toolsPanel.hidden = true;
  });
});

function setActiveTool(tool) {
  State.activeTool = tool;
  DOM.activeToolBadge.hidden = false;
  DOM.activeToolName.textContent = TOOL_LABELS[tool] || tool;
  DOM.activeToolIcon.innerHTML = TOOL_ICONS[tool] || '';

  if (tool === 'pdf_chat') {
    DOM.attachBtn.click();
  }
  if (tool === 'url_reader') {
    DOM.chatInput.placeholder = 'Paste a URL to read…';
    DOM.chatInput.focus();
  }
  if (tool === 'translator') {
    DOM.chatInput.placeholder = 'Enter text to translate…';
    DOM.chatInput.focus();
  }
  if (tool === 'summarizer') {
    DOM.chatInput.placeholder = 'Paste text or a URL to summarize…';
    DOM.chatInput.focus();
  }

  showToast(`${TOOL_LABELS[tool]} activated.`, 'info', 2000);
}

function clearActiveTool() {
  State.activeTool = null;
  DOM.activeToolBadge.hidden = true;
  DOM.activeToolName.textContent = '';
  DOM.activeToolIcon.innerHTML = '';
  DOM.chatInput.placeholder = 'Message Bloxy-bot AI…';
}

DOM.activeToolRemove.addEventListener('click', clearActiveTool);

// ── Web search toggle ─────────────────────────────────────────
DOM.webSearchToggle.addEventListener('click', () => {
  State.webSearchEnabled = !State.webSearchEnabled;
  DOM.webSearchToggle.setAttribute('aria-pressed', State.webSearchEnabled);
  DOM.webSearchToggle.classList.toggle('active', State.webSearchEnabled);
  showToast(State.webSearchEnabled ? 'Web search enabled.' : 'Web search disabled.', 'info', 2000);
});

/* =============================================================
   PART 5 — MODEL SELECTOR, SIDEBAR, MOBILE
============================================================= */

// ── Model selector ────────────────────────────────────────────
DOM.modelSelectorBtn.addEventListener('click', e => {
  e.stopPropagation();
  const isOpen = DOM.modelSelector.getAttribute('aria-expanded') === 'true';
  DOM.modelSelector.setAttribute('aria-expanded', !isOpen);
  DOM.modelDropdown.classList.toggle('open', !isOpen);
  DOM.userMenu.hidden = true;
});

$$('.model-option').forEach(opt => {
  opt.addEventListener('click', () => {
    const model = opt.dataset.model;
    const provider = opt.dataset.provider;
    State.activeModel = model;
    State.activeProvider = provider;

    $$('.model-option').forEach(o => {
      o.classList.remove('active');
      o.setAttribute('aria-selected', 'false');
      o.querySelector('.model-check')?.remove();
    });

    opt.classList.add('active');
    opt.setAttribute('aria-selected', 'true');

    const check = document.createElement('svg');
    check.setAttribute('width', '13');
    check.setAttribute('height', '13');
    check.setAttribute('viewBox', '0 0 24 24');
    check.setAttribute('fill', 'none');
    check.setAttribute('stroke', 'currentColor');
    check.setAttribute('stroke-width', '2.5');
    check.setAttribute('stroke-linecap', 'round');
    check.setAttribute('stroke-linejoin', 'round');
    check.setAttribute('class', 'model-check');
    check.setAttribute('aria-hidden', 'true');
    check.innerHTML = '<polyline points="20 6 9 17 4 12"/>';
    opt.appendChild(check);

    const displayName = opt.querySelector('.model-option-name')?.textContent || model;
    DOM.currentModelName.textContent = displayName;

    const dotClass = `model-dot-${provider}`;
    DOM.modelDot.className = `model-dot ${provider}`;

    DOM.modelSelector.setAttribute('aria-expanded', 'false');
    DOM.modelDropdown.classList.remove('open');

    if (State.activeChatId && State.chats[State.activeChatId]) {
      State.chats[State.activeChatId].model = model;
      State.chats[State.activeChatId].provider = provider;
      saveChats();
    }

    showToast(`Switched to ${displayName}`, 'info', 2000);
  });
});

// ── User profile menu ─────────────────────────────────────────
DOM.sidebarUserBtn.addEventListener('click', e => {
  e.stopPropagation();
  const isHidden = DOM.userMenu.hidden;
  closeAllDropdowns();
  DOM.userMenu.hidden = !isHidden;
});

DOM.sidebarUserBtn.addEventListener('keydown', e => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    DOM.sidebarUserBtn.click();
  }
});

DOM.profileBtn.addEventListener('click', () => {
  DOM.userMenu.hidden = true;
  if (!State.user) { openAuthModal('login'); return; }
  showToast('Profile settings coming soon!', 'info');
});

$('appearance-btn')?.addEventListener('click', () => {
  DOM.userMenu.hidden = true;
  openSettingsModal('appearance');
});

$('api-keys-btn')?.addEventListener('click', () => {
  DOM.userMenu.hidden = true;
  showToast('API key management coming soon!', 'info');
});

// ── New chat button ───────────────────────────────────────────
DOM.newChatBtn.addEventListener('click', () => createNewChat());

// ── Chat search ───────────────────────────────────────────────
DOM.chatSearch.addEventListener('input', e => {
  renderChatHistory(e.target.value);
});

// ── Sidebar nav links ─────────────────────────────────────────
DOM.settingsBtn.addEventListener('click', () => openSettingsModal('general'));
DOM.helpBtn.addEventListener('click', () => openHelpModal());
DOM.exportBtn.addEventListener('click', () => exportChats());

// ── Mobile sidebar ────────────────────────────────────────────
DOM.mobileMenuBtn.addEventListener('click', () => {
  const isOpen = State.sidebarOpen;
  if (isOpen) { closeMobileSidebar(); } else { openMobileSidebar(); }
});

DOM.sidebarOverlay.addEventListener('click', closeMobileSidebar);

function openMobileSidebar() {
  State.sidebarOpen = true;
  DOM.sidebar.classList.add('sidebar-open');
  DOM.sidebarOverlay.classList.add('overlay-visible');
  DOM.mobileMenuBtn.setAttribute('aria-expanded', 'true');
  document.body.classList.add('sidebar-is-open');
}

function closeMobileSidebar() {
  State.sidebarOpen = false;
  DOM.sidebar.classList.remove('sidebar-open');
  DOM.sidebarOverlay.classList.remove('overlay-visible');
  DOM.mobileMenuBtn.setAttribute('aria-expanded', 'false');
  document.body.classList.remove('sidebar-is-open');
}

// ── Close dropdowns on outside click ─────────────────────────
document.addEventListener('click', e => {
  if (!DOM.modelSelector.contains(e.target)) {
    DOM.modelSelector.setAttribute('aria-expanded', 'false');
    DOM.modelDropdown.classList.remove('open');
  }
  if (!DOM.userMenu.contains(e.target) && !DOM.sidebarUserBtn.contains(e.target)) {
    DOM.userMenu.hidden = true;
  }
  if (!DOM.toolsPanel.contains(e.target) && !DOM.toolsToggleBtn.contains(e.target)) {
    DOM.toolsPanel.hidden = true;
  }
});

/* =============================================================
   PART 6 — SETTINGS, MODALS, ADMIN, SHORTCUTS, EXPORT/IMPORT
============================================================= */

// ── Settings modal ────────────────────────────────────────────
function openSettingsModal(tab = 'general') {
  DOM.settingsModalOverlay.hidden = false;
  document.body.classList.add('modal-open');
  requestAnimationFrame(() => DOM.settingsModalOverlay.classList.add('modal-visible'));
  switchSettingsTab(tab);
  loadSettingsUI();
}

function closeSettingsModal() {
  DOM.settingsModalOverlay.classList.remove('modal-visible');
  setTimeout(() => { DOM.settingsModalOverlay.hidden = true; document.body.classList.remove('modal-open'); }, 250);
}

function switchSettingsTab(tab) {
  $$('.settings-tab').forEach(t => {
    const isActive = t.dataset.tab === tab;
    t.classList.toggle('active', isActive);
    t.setAttribute('aria-selected', isActive);
  });
  $$('.settings-panel').forEach(p => {
    p.hidden = p.id !== `settings-${tab}`;
    p.classList.toggle('active', p.id === `settings-${tab}`);
  });
}

function loadSettingsUI() {
  const s = State.settings;
  const setCheck = (id, val) => { const el = $(id); if (el) el.checked = val; };
  const setVal = (id, val) => { const el = $(id); if (el) el.value = val; };

  setCheck('setting-streaming', s.streaming);
  setCheck('setting-autoscroll', s.autoscroll);
  setCheck('setting-enter-send', s.enterSend);
  setCheck('setting-memory', s.memory);
  setVal('setting-language', s.language);
  setVal('setting-default-model', s.defaultModel);
  setVal('setting-max-tokens', s.maxTokens);
  setVal('setting-temperature', s.temperature);
  $('temperature-value').textContent = s.temperature;
  setVal('setting-system-prompt', s.systemPrompt);
  setVal('setting-font-size', s.fontSize);
  setCheck('setting-reduce-motion', s.reduceMotion);
  setVal('setting-context-window', s.contextWindow);
  setCheck('setting-memory-enabled', s.memoryEnabled);

  Object.entries(s.integrations).forEach(([key, val]) => {
    setCheck(`integration-${key}`, val);
  });
}

function saveSettingsFromUI() {
  const getCheck = id => { const el = $(id); return el ? el.checked : false; };
  const getVal = id => { const el = $(id); return el ? el.value : ''; };

  State.settings.streaming = getCheck('setting-streaming');
  State.settings.autoscroll = getCheck('setting-autoscroll');
  State.settings.enterSend = getCheck('setting-enter-send');
  State.settings.memory = getCheck('setting-memory');
  State.settings.language = getVal('setting-language');
  State.settings.defaultModel = getVal('setting-default-model');
  State.settings.maxTokens = parseInt(getVal('setting-max-tokens')) || 4096;
  State.settings.temperature = parseFloat(getVal('setting-temperature')) || 0.7;
  State.settings.systemPrompt = getVal('setting-system-prompt');
  State.settings.fontSize = getVal('setting-font-size');
  State.settings.reduceMotion = getCheck('setting-reduce-motion');
  State.settings.contextWindow = parseInt(getVal('setting-context-window')) || 20;
  State.settings.memoryEnabled = getCheck('setting-memory-enabled');

  Object.keys(State.settings.integrations).forEach(key => {
    State.settings.integrations[key] = getCheck(`integration-${key}`);
  });

  Storage.set('settings', State.settings);
  applySettings();
}

function applySettings() {
  document.documentElement.setAttribute('data-font-size', State.settings.fontSize);
  if (State.settings.reduceMotion) {
    document.documentElement.classList.add('reduce-motion');
  } else {
    document.documentElement.classList.remove('reduce-motion');
  }
}

DOM.settingsModalClose.addEventListener('click', closeSettingsModal);
DOM.settingsCancelBtn.addEventListener('click', closeSettingsModal);
DOM.settingsModalOverlay.addEventListener('click', e => { if (e.target === DOM.settingsModalOverlay) closeSettingsModal(); });

DOM.settingsSaveBtn.addEventListener('click', () => {
  saveSettingsFromUI();
  closeSettingsModal();
  showToast('Settings saved!', 'success');
});

$$('.settings-tab').forEach(tab => {
  tab.addEventListener('click', () => switchSettingsTab(tab.dataset.tab));
});

$('setting-temperature')?.addEventListener('input', e => {
  $('temperature-value').textContent = parseFloat(e.target.value).toFixed(1);
});

$('clear-memory-btn')?.addEventListener('click', () => {
  Storage.remove('chats');
  State.chats = {};
  State.activeChatId = null;
  showHeroScreen();
  renderChatHistory();
  showToast('Memory cleared.', 'info');
});

$('export-memory-btn')?.addEventListener('click', () => {
  exportChats();
});

// ── Help modal ────────────────────────────────────────────────
function openHelpModal() {
  DOM.helpModalOverlay.hidden = false;
  document.body.classList.add('modal-open');
  requestAnimationFrame(() => DOM.helpModalOverlay.classList.add('modal-visible'));
}

function closeHelpModal() {
  DOM.helpModalOverlay.classList.remove('modal-visible');
  setTimeout(() => { DOM.helpModalOverlay.hidden = true; document.body.classList.remove('modal-open'); }, 250);
}

DOM.helpModalClose.addEventListener('click', closeHelpModal);
DOM.helpModalOverlay.addEventListener('click', e => { if (e.target === DOM.helpModalOverlay) closeHelpModal(); });

// ── Shortcuts modal ───────────────────────────────────────────
function openShortcutsModal() {
  DOM.shortcutsModalOverlay.hidden = false;
  document.body.classList.add('modal-open');
  requestAnimationFrame(() => DOM.shortcutsModalOverlay.classList.add('modal-visible'));
}

function closeShortcutsModal() {
  DOM.shortcutsModalOverlay.classList.remove('modal-visible');
  setTimeout(() => { DOM.shortcutsModalOverlay.hidden = true; document.body.classList.remove('modal-open'); }, 250);
}

DOM.shortcutsBtn.addEventListener('click', openShortcutsModal);
DOM.shortcutsModalClose.addEventListener('click', closeShortcutsModal);
DOM.shortcutsModalOverlay.addEventListener('click', e => { if (e.target === DOM.shortcutsModalOverlay) closeShortcutsModal(); });

// ── Import modal ──────────────────────────────────────────────
DOM.importChatBtn.addEventListener('click', () => {
  DOM.importModalOverlay.hidden = false;
  document.body.classList.add('modal-open');
  requestAnimationFrame(() => DOM.importModalOverlay.classList.add('modal-visible'));
});

function closeImportModal() {
  DOM.importModalOverlay.classList.remove('modal-visible');
  setTimeout(() => { DOM.importModalOverlay.hidden = true; document.body.classList.remove('modal-open'); }, 250);
  State.importData = null;
  DOM.importConfirmBtn.disabled = true;
  DOM.importDropZone.classList.remove('drop-active');
}

DOM.importModalClose.addEventListener('click', closeImportModal);
DOM.importCancelBtn.addEventListener('click', closeImportModal);
DOM.importModalOverlay.addEventListener('click', e => { if (e.target === DOM.importModalOverlay) closeImportModal(); });

DOM.importBrowseBtn.addEventListener('click', () => DOM.importFileInput.click());
DOM.importDropZone.addEventListener('click', () => DOM.importFileInput.click());

DOM.importDropZone.addEventListener('dragover', e => {
  e.preventDefault();
  DOM.importDropZone.classList.add('drop-active');
});
DOM.importDropZone.addEventListener('dragleave', () => DOM.importDropZone.classList.remove('drop-active'));
DOM.importDropZone.addEventListener('drop', e => {
  e.preventDefault();
  DOM.importDropZone.classList.remove('drop-active');
  const file = e.dataTransfer.files[0];
  if (file) readImportFile(file);
});

DOM.importFileInput.addEventListener('change', () => {
  const file = DOM.importFileInput.files[0];
  if (file) readImportFile(file);
});

function readImportFile(file) {
  const reader = new FileReader();
  reader.onload = e => {
    try {
      const data = JSON.parse(e.target.result);
      if (data.chats && typeof data.chats === 'object') {
        State.importData = data.chats;
        DOM.importConfirmBtn.disabled = false;
        showToast(`Found ${Object.keys(data.chats).length} chat(s) to import.`, 'info');
      } else {
        showToast('Invalid export file format.', 'error');
      }
    } catch {
      showToast('Failed to parse file. Ensure it is a valid JSON export.', 'error');
    }
  };
  reader.readAsText(file);
}

DOM.importConfirmBtn.addEventListener('click', () => {
  if (!State.importData) return;
  Object.assign(State.chats, State.importData);
  saveChats();
  renderChatHistory();
  closeImportModal();
  showToast('Chats imported successfully!', 'success');
});

// ── Export chats ──────────────────────────────────────────────
function exportChats() {
  const exportData = {
    version: '1.0',
    exportedAt: new Date().toISOString(),
    app: 'Bloxy-bot AI',
    chats: State.chats
  };
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `bloxy-bot-chats-${new Date().toISOString().slice(0, 10)}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast('Chats exported!', 'success');
}

// ── Admin panel ───────────────────────────────────────────────
DOM.adminPanelBtn.addEventListener('click', () => {
  DOM.userMenu.hidden = true;
  if (!State.user || !isAdmin(State.user.email)) {
    showToast('Admin access required.', 'error');
    return;
  }
  DOM.adminModalOverlay.hidden = false;
  document.body.classList.add('modal-open');
  requestAnimationFrame(() => DOM.adminModalOverlay.classList.add('modal-visible'));
  loadAdminDashboard();
});

function closeAdminModal() {
  DOM.adminModalOverlay.classList.remove('modal-visible');
  setTimeout(() => { DOM.adminModalOverlay.hidden = true; document.body.classList.remove('modal-open'); }, 250);
}

DOM.adminModalClose.addEventListener('click', closeAdminModal);
DOM.adminModalOverlay.addEventListener('click', e => { if (e.target === DOM.adminModalOverlay) closeAdminModal(); });

$$('.admin-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    const name = tab.dataset.adminTab;
    $$('.admin-tab').forEach(t => { t.classList.remove('active'); t.setAttribute('aria-selected', 'false'); });
    $$('.admin-panel').forEach(p => { p.hidden = true; p.classList.remove('active'); });
    tab.classList.add('active');
    tab.setAttribute('aria-selected', 'true');
    const panel = $(`admin-${name}`);
    if (panel) { panel.hidden = false; panel.classList.add('active'); }
    if (name === 'users') loadAdminUsers();
    if (name === 'chat-logs') loadAdminChatLogs();
    if (name === 'api-usage') loadAdminApiUsage();
    if (name === 'providers') checkAllProviders();
    if (name === 'system-logs') loadSystemLogs();
    if (name === 'error-logs') loadErrorLogs();
  });
});

async function loadAdminDashboard() {
  try {
    const res = await fetch('/api/admin/stats', { credentials: 'include' });
    if (!res.ok) return;
    const data = await res.json();
    $('stat-total-users').textContent = data.total_users ?? '—';
    $('stat-total-chats').textContent = data.total_chats ?? '—';
    $('stat-messages-today').textContent = data.messages_today ?? '—';
    $('stat-api-calls').textContent = data.api_calls_today ?? '—';
    $('stat-active-sessions').textContent = data.active_sessions ?? '—';
    $('stat-errors').textContent = data.errors_24h ?? '—';
    $('admin-last-updated').textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
  } catch {
    $('admin-last-updated').textContent = 'Failed to load stats.';
  }
}

DOM.adminRefreshBtn?.addEventListener('click', loadAdminDashboard);

async function loadAdminUsers() {
  const tbody = $('users-table-body');
  tbody.innerHTML = '<tr class="admin-table-loading"><td colspan="6"><span class="admin-loading-text">Loading…</span></td></tr>';
  try {
    const res = await fetch('/api/admin/users', { credentials: 'include' });
    const data = await res.json();
    if (!data.users?.length) { tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#666;padding:20px">No users found.</td></tr>'; return; }
    tbody.innerHTML = data.users.map(u => `
      <tr>
        <td><div class="admin-user-cell"><span class="admin-user-avatar">${getInitials(u.name)}</span>${escapeHtml(u.name)}${isAdmin(u.email) ? '<span class="admin-badge-pill" style="margin-left:6px;font-size:10px">Admin</span>' : ''}</div></td>
        <td>${escapeHtml(u.email)}</td>
        <td>${escapeHtml(u.role || 'user')}</td>
        <td>${new Date(u.created_at).toLocaleDateString()}</td>
        <td>${u.chat_count ?? 0}</td>
        <td><button class="btn-ghost btn-sm" onclick="showToast('User management coming soon!','info')">Manage</button></td>
      </tr>`).join('');
  } catch {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#ef4444;padding:20px">Failed to load users.</td></tr>';
  }
}

async function loadAdminChatLogs() {
  const tbody = $('chatlogs-table-body');
  tbody.innerHTML = '<tr class="admin-table-loading"><td colspan="6"><span class="admin-loading-text">Loading…</span></td></tr>';
  try {
    const res = await fetch('/api/admin/chat-logs', { credentials: 'include' });
    const data = await res.json();
    if (!data.logs?.length) { tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#666;padding:20px">No logs found.</td></tr>'; return; }
    tbody.innerHTML = data.logs.map(l => `
      <tr>
        <td>${escapeHtml(l.user_email || 'Guest')}</td>
        <td>${escapeHtml(l.model || '—')}</td>
        <td>${l.message_count ?? 0}</td>
        <td>${l.total_tokens ?? 0}</td>
        <td>${new Date(l.created_at).toLocaleDateString()}</td>
        <td><button class="btn-ghost btn-sm" onclick="showToast('Log viewer coming soon!','info')">View</button></td>
      </tr>`).join('');
  } catch {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#ef4444;padding:20px">Failed to load logs.</td></tr>';
  }
}

async function loadAdminApiUsage() {
  try {
    const res = await fetch('/api/admin/api-usage', { credentials: 'include' });
    const data = await res.json();
    const set = (id, val) => { const el = $(id); if (el) el.textContent = val ?? '—'; };
    set('openai-reqs', data.openai?.requests);
    set('openai-tokens', data.openai?.tokens?.toLocaleString());
    set('openai-latency', data.openai?.avg_latency ? `${data.openai.avg_latency}ms` : '—');
    set('groq-reqs', data.groq?.requests);
    set('groq-tokens', data.groq?.tokens?.toLocaleString());
    set('groq-latency', data.groq?.avg_latency ? `${data.groq.avg_latency}ms` : '—');
    set('openrouter-reqs', data.openrouter?.requests);
    set('openrouter-tokens', data.openrouter?.tokens?.toLocaleString());
    set('openrouter-latency', data.openrouter?.avg_latency ? `${data.openrouter.avg_latency}ms` : '—');
    set('kimi-reqs', data.kimi?.requests);
    set('kimi-tokens', data.kimi?.tokens?.toLocaleString());
    set('kimi-latency', data.kimi?.avg_latency ? `${data.kimi.avg_latency}ms` : '—');
    set('tavily-reqs', data.tavily?.requests);
    set('tavily-credits', data.tavily?.credits_used);
    set('tavily-latency', data.tavily?.avg_latency ? `${data.tavily.avg_latency}ms` : '—');
    set('firecrawl-reqs', data.firecrawl?.requests);
    set('firecrawl-pages', data.firecrawl?.pages_crawled);
    set('firecrawl-latency', data.firecrawl?.avg_latency ? `${data.firecrawl.avg_latency}ms` : '—');
  } catch {}
}

async function checkAllProviders() {
  try {
    const res = await fetch('/api/admin/provider-status', { credentials: 'include' });
    const data = await res.json();
    Object.entries(data).forEach(([key, info]) => {
      const latencyEl = $(`ps-${key}`);
      if (latencyEl) latencyEl.textContent = info.latency ? `${info.latency}ms` : (info.status === 'online' ? 'Online' : 'Offline');
      const row = latencyEl?.closest('.provider-status-row');
      if (row) {
        const dot = row.querySelector('.provider-status-dot');
        const badge = row.querySelector('.provider-status-badge');
        const online = info.status === 'online';
        if (dot) { dot.classList.toggle('online', online); dot.classList.toggle('offline', !online); }
        if (badge) { badge.classList.toggle('online', online); badge.classList.toggle('offline', !online); badge.textContent = online ? 'Operational' : 'Down'; }
      }
    });
  } catch {}
}

DOM.checkProvidersBtn?.addEventListener('click', checkAllProviders);

async function loadSystemLogs() {
  try {
    const res = await fetch('/api/admin/system-logs', { credentials: 'include' });
    const data = await res.json();
    const viewer = $('system-log-viewer');
    if (!viewer) return;
    viewer.innerHTML = (data.logs || []).map(l => `
      <div class="log-line ${l.level?.toLowerCase()}">
        <span class="log-time">${new Date(l.timestamp).toLocaleTimeString()}</span>
        <span class="log-level ${l.level?.toLowerCase()}">${escapeHtml(l.level || 'INFO')}</span>
        <span class="log-msg">${escapeHtml(l.message)}</span>
      </div>`).join('') || '<div class="log-line info"><span class="log-msg">No system logs.</span></div>';
    viewer.scrollTop = viewer.scrollHeight;
  } catch {}
}

async function loadErrorLogs() {
  try {
    const res = await fetch('/api/admin/error-logs', { credentials: 'include' });
    const data = await res.json();
    const viewer = $('error-log-viewer');
    if (!viewer) return;
    viewer.innerHTML = (data.logs || []).map(l => `
      <div class="log-line error">
        <span class="log-time">${new Date(l.timestamp).toLocaleTimeString()}</span>
        <span class="log-level error">ERROR</span>
        <span class="log-msg">${escapeHtml(l.message)}</span>
      </div>`).join('') || '<div class="log-line info"><span class="log-msg">No error logs.</span></div>';
    viewer.scrollTop = viewer.scrollHeight;
  } catch {}
}

$('clear-system-logs-btn')?.addEventListener('click', () => {
  const v = $('system-log-viewer');
  if (v) v.innerHTML = '<div class="log-line info"><span class="log-msg">Logs cleared.</span></div>';
});

$('clear-error-logs-btn')?.addEventListener('click', () => {
  const v = $('error-log-viewer');
  if (v) v.innerHTML = '<div class="log-line info"><span class="log-msg">Logs cleared.</span></div>';
});

$('users-search')?.addEventListener('input', e => {
  const q = e.target.value.toLowerCase();
  $$('#users-table-body tr').forEach(row => {
    row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
});

$('chatlogs-search')?.addEventListener('input', e => {
  const q = e.target.value.toLowerCase();
  $$('#chatlogs-table-body tr').forEach(row => {
    row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
});

// ── Keyboard shortcuts ────────────────────────────────────────
document.addEventListener('keydown', e => {
  const ctrl = e.ctrlKey || e.metaKey;

  if (e.key === 'Escape') {
    if (!DOM.settingsModalOverlay.hidden) { closeSettingsModal(); return; }
    if (!DOM.authModalOverlay.hidden) { closeAuthModal(); return; }
    if (!DOM.helpModalOverlay.hidden) { closeHelpModal(); return; }
    if (!DOM.shortcutsModalOverlay.hidden) { closeShortcutsModal(); return; }
    if (!DOM.confirmModalOverlay.hidden) { closeConfirmModal(); return; }
    if (!DOM.importModalOverlay.hidden) { closeImportModal(); return; }
    if (!DOM.adminModalOverlay.hidden) { closeAdminModal(); return; }
    if (State.isStreaming) { DOM.stopBtn.click(); return; }
    if (State.sidebarOpen) { closeMobileSidebar(); return; }
  }

  if (ctrl && e.key === 'n') { e.preventDefault(); createNewChat(); }
  if (ctrl && e.key === 'k') { e.preventDefault(); DOM.chatSearch.focus(); }
  if (ctrl && e.key === '/') { e.preventDefault(); openShortcutsModal(); }
  if (ctrl && e.shiftKey && e.key === 'E') { e.preventDefault(); exportChats(); }
  if (ctrl && e.shiftKey && e.key === 'S') { e.preventDefault(); openSettingsModal('general'); }
});

// ── OAuth callback handler ────────────────────────────────────
function handleOAuthCallback() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get('token');
  const error = params.get('error');
  if (token) {
    history.replaceState({}, '', '/');
    checkSession().then(() => {
      if (State.user) showToast(`Welcome, ${State.user.name}!`, 'success');
    });
  }
  if (error) {
    history.replaceState({}, '', '/');
    showToast(`Authentication failed: ${error}`, 'error');
  }
}

// ── Load saved settings ───────────────────────────────────────
function loadSavedSettings() {
  const saved = Storage.get('settings');
  if (saved) Object.assign(State.settings, saved);
  applySettings();
}

// ── Init ──────────────────────────────────────────────────────
async function init() {
  setupMarked();
  loadSavedSettings();
  handleOAuthCallback();
  await checkSession();
  loadChats();

  // If no chats exist, show empty hero
  if (!Object.keys(State.chats).length) {
    showHeroScreen();
  }

  // Focus composer
  DOM.chatInput.focus();
}

// Boot
document.addEventListener('DOMContentLoaded', init);
