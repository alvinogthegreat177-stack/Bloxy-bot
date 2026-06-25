/* ================================================= */
/* BLOXY-BOT AI - APP.JS COMPLETE V2.1 */
/* ERROR-FREE PRODUCTION VERSION */
/* ================================================= */

/* ================================================= */
/* APPLICATION STATE */
/* ================================================= */

const AppState = {
    chats: [],
    currentChatId: null,
    currentModel: "auto",
    theme: localStorage.getItem("bloxy_theme") || "dark",
    user: null,
    providers: {},
    memories: [],
    notifications: [],
    isLoading: false,
    activeProvider: "openrouter"
};

/* ================================================= */
/* DOM ELEMENT REFERENCES */
/* ================================================= */

const sidebar = document.getElementById("sidebar");
const mobileOverlay = document.getElementById("mobileOverlay");
const menuToggle = document.getElementById("menuToggle");
const newChatBtn = document.getElementById("newChatBtn");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const stopBtn = document.getElementById("stopBtn");
const toastContainer = document.getElementById("toastContainer");
const themeBtn = document.getElementById("themeBtn");
const modelSelector = document.getElementById("modelSelector");
const chatContainer = document.getElementById("chatContainer");
const typingIndicator = document.getElementById("typingIndicator");
const welcomeSection = document.getElementById("welcomeSection");
const chatSection = document.getElementById("chatSection");

const researchBtn = document.getElementById("researchBtn");
const webSearchBtn = document.getElementById("webSearchBtn");
const attachFileBtn = document.getElementById("attachFileBtn");
const imageUploadBtn = document.getElementById("imageUploadBtn");
const voiceBtn = document.getElementById("voiceBtn");
const settingsBtn = document.getElementById("settingsBtn");
const settingsModal = document.getElementById("settingsModal");
const profileModal = document.getElementById("profileModal");
const providerStatusBtn = document.getElementById("providerStatusBtn");
const providerModal = document.getElementById("providerModal");
const adminModal = document.getElementById("adminModal");

const fileInput = document.getElementById("fileInput");
const imageInput = document.getElementById("imageInput");

/* ================================================= */
/* UTILITY FUNCTIONS */
/* ================================================= */

function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

function formatTime(date = new Date()) {
    return date.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });
}

function saveLocal(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
        console.error("LocalStorage error:", e);
    }
}

function loadLocal(key, fallback = null) {
    try {
        const item = localStorage.getItem(key);
        if (!item) return fallback;
        return JSON.parse(item);
    } catch (e) {
        console.error("LocalStorage parse error:", e);
        return fallback;
    }
}

/* ================================================= */
/* TOAST NOTIFICATIONS */
/* ================================================= */

function showToast(message, type = "success", duration = 4000) {
    if (!toastContainer) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    toast.style.animation = "slideIn 0.3s ease-out";

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = "slideOut 0.3s ease-in";
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/* ================================================= */
/* MOBILE SIDEBAR MANAGEMENT */
/* ================================================= */

function openSidebar() {
    if (sidebar) sidebar.classList.add("sidebar-open");
    if (mobileOverlay) mobileOverlay.classList.add("overlay-show");
}

function closeSidebar() {
    if (sidebar) sidebar.classList.remove("sidebar-open");
    if (mobileOverlay) mobileOverlay.classList.remove("overlay-show");
}

if (menuToggle) {
    menuToggle.addEventListener("click", openSidebar);
}

if (mobileOverlay) {
    mobileOverlay.addEventListener("click", closeSidebar);
}

/* ================================================= */
/* THEME SYSTEM */
/* ================================================= */

function applyTheme(theme) {
    document.body.setAttribute("data-theme", theme);
    AppState.theme = theme;
    localStorage.setItem("bloxy_theme", theme);
    
    if (themeBtn) {
        const icon = themeBtn.querySelector("i");
        if (icon) {
            icon.className = theme === "dark" 
                ? "fa-solid fa-sun" 
                : "fa-solid fa-moon";
        }
    }
}

function toggleTheme() {
    const nextTheme = AppState.theme === "dark" ? "light" : "dark";
    applyTheme(nextTheme);
    showToast(`Theme changed to ${nextTheme}`, "info");
}

if (themeBtn) {
    themeBtn.addEventListener("click", toggleTheme);
}

/* ================================================= */
/* MODEL SELECTOR */
/* ================================================= */

if (modelSelector) {
    modelSelector.addEventListener("change", (e) => {
        AppState.currentModel = e.target.value;
        localStorage.setItem("bloxy_model", e.target.value);
        showToast(`Model set to ${e.target.value}`, "success");
    });
}

/* ================================================= */
/* NEW CHAT CREATION */
/* ================================================= */

function createNewChat() {
    const chat = {
        id: generateId(),
        title: "New Chat",
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now()
    };

    AppState.chats.unshift(chat);
    AppState.currentChatId = chat.id;

    if (chatContainer) {
        chatContainer.innerHTML = "";
    }

    saveLocal("bloxy_chats", AppState.chats);
    showToast("New chat created ✨", "success");
    
    if (welcomeSection) welcomeSection.classList.add("hidden");
    if (chatSection) chatSection.classList.remove("hidden");
    
    refreshChatHistory();
}

if (newChatBtn) {
    newChatBtn.addEventListener("click", createNewChat);
}

/* ================================================= */
/* AUTO RESIZE INPUT */
/* ================================================= */

if (messageInput) {
    messageInput.addEventListener("input", () => {
        messageInput.style.height = "auto";
        messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + "px";
    });
}

/* ================================================= */
/* TYPING INDICATOR */
/* ================================================= */

function showTyping() {
    if (!typingIndicator) return;
    typingIndicator.classList.remove("hidden");
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

function hideTyping() {
    if (!typingIndicator) return;
    typingIndicator.classList.add("hidden");
}

/* ================================================= */
/* LOADING SCREEN */
/* ================================================= */

function initializeLoadingScreen() {
    const loadingScreen = document.getElementById("loadingScreen");
    if (!loadingScreen) return;

    setTimeout(() => {
        loadingScreen.classList.add("loading-complete");
    }, 1800);
}

/* ================================================= */
/* MESSAGE RENDERING */
/* ================================================= */

function addMessage(role, content) {
    if (!chatContainer) return;

    const message = document.createElement("div");
    message.className = `message message-${role}`;

    const time = formatTime();

    message.innerHTML = `
        <div class="message-header">
            <span class="message-role">
                ${role === "user" ? "You" : "Bloxy-bot AI"}
            </span>
            <span class="message-time">${time}</span>
        </div>
        <div class="message-content">
            ${escapeHtml(content)}
        </div>
    `;

    chatContainer.appendChild(message);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

/* ================================================= */
/* CHAT STORAGE */
/* ================================================= */

function saveCurrentChatMessage(role, content) {
    const chat = AppState.chats.find(c => c.id === AppState.currentChatId);
    if (!chat) return;

    chat.messages.push({
        role,
        content,
        timestamp: Date.now()
    });

    if (chat.title === "New Chat" && role === "user") {
        chat.title = content.substring(0, 50);
    }

    chat.updatedAt = Date.now();
    saveLocal("bloxy_chats", AppState.chats);
}

/* ================================================= */
/* CHAT HISTORY PANEL */
/* ================================================= */

function refreshChatHistory() {
    const history = document.getElementById("chatHistory");
    if (!history) return;

    history.innerHTML = "";

    AppState.chats.forEach(chat => {
        const item = document.createElement("div");
        item.className = "history-item";
        item.textContent = chat.title;

        item.addEventListener("click", () => {
            loadChat(chat.id);
            closeSidebar();
        });

        history.appendChild(item);
    });
}

function loadChat(chatId) {
    const chat = AppState.chats.find(c => c.id === chatId);
    if (!chat) return;

    AppState.currentChatId = chatId;

    if (chatContainer) {
        chatContainer.innerHTML = "";
        chat.messages.forEach(msg => {
            addMessage(msg.role, msg.content);
        });
    }

    if (welcomeSection) welcomeSection.classList.add("hidden");
    if (chatSection) chatSection.classList.remove("hidden");
}

/* ================================================= */
/* API REQUEST HANDLER */
/* ================================================= */

async function sendToAI(message) {
    try {
        showTyping();

        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message,
                provider: AppState.currentModel,
                model: AppState.currentModel,
                web_search: false,
                deep_research: false,
                use_memory: true
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        hideTyping();

        return data.response || "No response received.";
    } catch (error) {
        hideTyping();
        console.error("AI request error:", error);
        showToast("Failed to get response. Try again.", "error");
        return "Sorry, I encountered an error. Please try again.";
    }
}

/* ================================================= */
/* SEND MESSAGE */
/* ================================================= */

async function sendMessage() {
    const text = messageInput.value.trim();

    if (!text) return;

    if (!AppState.currentChatId) {
        createNewChat();
    }

    addMessage("user", text);
    saveCurrentChatMessage("user", text);

    messageInput.value = "";
    messageInput.style.height = "auto";

    const aiReply = await sendToAI(text);

    addMessage("assistant", aiReply);
    saveCurrentChatMessage("assistant", aiReply);

    refreshChatHistory();
}

if (sendBtn) {
    sendBtn.addEventListener("click", sendMessage);
}

/* ================================================= */
/* ENTER TO SEND */
/* ================================================= */

if (messageInput) {
    messageInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

/* ================================================= */
/* WELCOME MESSAGE */
/* ================================================= */

window.addEventListener("load", () => {
    if (AppState.chats.length === 0) {
        createNewChat();
        addMessage("assistant", `👋 Welcome to Bloxy-bot AI!

I can help you with:
• AI Chat & Reasoning
• Web Search & Research
• News & Headlines
• Finance & Markets
• Sports & Live Scores
• Weather & Forecasts
• Movies & Entertainment
• Coding & Programming
• Dictionary & Wikipedia
• And Much More!

What can I assist you with today?`);
    }

    refreshChatHistory();
});

/* ================================================= */
/* FILE UPLOADS */
/* ================================================= */

if (attachFileBtn) {
    attachFileBtn.addEventListener("click", () => {
        fileInput.click();
    });
}

if (fileInput) {
    fileInput.addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        showToast(`File selected: ${file.name}`, "info");

        const formData = new FormData();
        formData.append("file", file);

        try {
            await fetch("/upload", {
                method: "POST",
                body: formData
            });
            showToast("File uploaded!", "success");
        } catch {
            showToast("Upload failed", "error");
        }
    });
}

/* ================================================= */
/* IMAGE UPLOADS */
/* ================================================= */

if (imageUploadBtn) {
    imageUploadBtn.addEventListener("click", () => {
        imageInput.click();
    });
}

if (imageInput) {
    imageInput.addEventListener("change", (e) => {
        const image = e.target.files[0];
        if (!image) return;

        showToast(`Image: ${image.name}`, "info");
    });
}

/* ================================================= */
/* VOICE INPUT */
/* ================================================= */

let recognition = null;

if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (messageInput) {
            messageInput.value = transcript;
        }
        showToast("Voice captured 🎤", "success");
    };

    recognition.onerror = () => {
        showToast("Voice recognition failed", "error");
    };
}

if (voiceBtn && recognition) {
    voiceBtn.addEventListener("click", () => {
        recognition.start();
        showToast("Listening... 🎙️", "info");
    });
}

/* ================================================= */
/* EXPORT CHAT */
/* ================================================= */

function exportChat(type = "json") {
    const chat = AppState.chats.find(c => c.id === AppState.currentChatId);
    if (!chat) return;

    let content = JSON.stringify(chat, null, 2);

    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `chat-${chat.id.substring(0, 8)}.${type}`;
    a.click();
    URL.revokeObjectURL(url);

    showToast("Chat exported!", "success");
}

/* ================================================= */
/* MEMORY SYSTEM */
/* ================================================= */

function addMemory(text) {
    AppState.memories.push({
        id: generateId(),
        text,
        createdAt: Date.now()
    });
    saveLocal("bloxy_memories", AppState.memories);
}

function loadMemories() {
    AppState.memories = loadLocal("bloxy_memories", []);
}

/* ================================================= */
/* PANEL HELPERS */
/* ================================================= */

function openPanel(panel) {
    if (!panel) return;
    panel.classList.remove("hidden");
}

function closePanel(panel) {
    if (!panel) return;
    panel.classList.add("hidden");
}

/* ================================================= */
/* RESEARCH FUNCTIONALITY */
/* ================================================= */

async function startDeepResearch() {
    const query = messageInput.value.trim();

    if (!query) {
        showToast("Enter a research topic", "error");
        return;
    }

    try {
        showTyping();

        const response = await fetch("/research", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query, max_sources: 10 })
        });

        const data = await response.json();
        hideTyping();

        if (data.success) {
            addMessage("assistant", `Research Results for "${query}":\n\n${JSON.stringify(data.results, null, 2)}`);
            showToast("Research completed!", "success");
        } else {
            showToast("Research failed", "error");
        }
    } catch (error) {
        hideTyping();
        console.error("Research error:", error);
        showToast("Research failed", "error");
    }
}

if (researchBtn) {
    researchBtn.addEventListener("click", startDeepResearch);
}

/* ================================================= */
/* WEB SEARCH */
/* ================================================= */

async function performSearch() {
    const query = messageInput.value.trim();

    if (!query) return;

    try {
        showTyping();

        const response = await fetch("/news/search?query=" + encodeURIComponent(query));
        const data = await response.json();

        hideTyping();

        if (data.success) {
            let searchResults = "Search Results:\n\n";
            data.articles.slice(0, 5).forEach((article, i) => {
                searchResults += `${i + 1}. ${article.title}\n   ${article.url}\n\n`;
            });
            addMessage("assistant", searchResults);
            showToast("Search complete!", "success");
        }
    } catch (error) {
        hideTyping();
        console.error("Search error:", error);
        showToast("Search failed", "error");
    }
}

if (webSearchBtn) {
    webSearchBtn.addEventListener("click", performSearch);
}

/* ================================================= */
/* PROVIDER DIAGNOSTICS */
/* ================================================= */

async function loadProviderHealth() {
    try {
        const response = await fetch("/ai/providers/health");
        const data = await response.json();

        const container = document.getElementById("providerDiagnostics");
        if (!container) return;

        container.innerHTML = "";

        Object.entries(data).forEach(([name, status]) => {
            const card = document.createElement("div");
            card.className = "provider-health-card";
            card.innerHTML = `
                <h3>${name}</h3>
                <p>${status.online ? "Online ✓" : "Offline ✗"}</p>
                <p>Latency: ${status.latency}ms</p>
            `;
            container.appendChild(card);
        });
    } catch (error) {
        console.error("Provider health error:", error);
    }
}

setInterval(loadProviderHealth, 60000);
loadProviderHealth();

/* ================================================= */
/* CLOSE PANELS */
/* ================================================= */

document.querySelectorAll(".close-panel").forEach((btn) => {
    btn.addEventListener("click", () => {
        const panel = btn.closest(".floating-panel");
        if (panel) closePanel(panel);
    });
});

/* ================================================= */
/* SETTINGS MODAL */
/* ================================================= */

if (settingsBtn) {
    settingsBtn.addEventListener("click", () => {
        if (settingsModal) settingsModal.classList.add("show");
    });
}

document.querySelectorAll(".close-modal").forEach((btn) => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".modal").forEach((modal) => {
            modal.classList.remove("show");
        });
    });
});

/* ================================================= */
/* ADMIN DASHBOARD */
/* ================================================= */

async function updateAdminStats() {
    try {
        const response = await fetch("/admin/stats");
        const data = await response.json();

        const totalUsers = document.getElementById("totalUsers");
        const totalChats = document.getElementById("totalChats");
        const apiHealth = document.getElementById("apiHealth");
        const systemStatus = document.getElementById("systemStatus");

        if (totalUsers) totalUsers.textContent = data.users || 0;
        if (totalChats) totalChats.textContent = data.chats || 0;
        if (apiHealth) apiHealth.textContent = data.apiHealth || "Healthy";
        if (systemStatus) systemStatus.textContent = data.status || "Online";
    } catch (error) {
        console.error("Admin stats error:", error);
    }
}

if (providerStatusBtn) {
    providerStatusBtn.addEventListener("click", async () => {
        if (providerModal) providerModal.classList.add("show");
        await loadProviderHealth();
    });
}

/* ================================================= */
/* KEYBOARD SHORTCUTS */
/* ================================================= */

document.addEventListener("keydown", (event) => {
    if (event.ctrlKey && event.key.toLowerCase() === "k") {
        event.preventDefault();
        if (messageInput) messageInput.focus();
    }

    if (event.ctrlKey && event.key.toLowerCase() === "n") {
        event.preventDefault();
        createNewChat();
    }
});

/* ================================================= */
/* NOTIFICATIONS */
/* ================================================= */

function addNotification(title, message) {
    AppState.notifications.unshift({
        id: generateId(),
        title,
        message,
        time: formatTime()
    });

    renderNotifications();
}

function renderNotifications() {
    const list = document.getElementById("notificationList");
    if (!list) return;

    list.innerHTML = "";

    AppState.notifications.slice(0, 10).forEach((n) => {
        const item = document.createElement("div");
        item.className = "notification-item";
        item.innerHTML = `
            <h4>${n.title}</h4>
            <p>${n.message}</p>
            <span>${n.time}</span>
        `;
        list.appendChild(item);
    });
}

/* ================================================= */
/* APP VERSION */
/* ================================================= */

const APP_VERSION = "2.1.0";

/* ================================================= */
/* STARTUP CHECKS */
/* ================================================= */

async function startupChecks() {
    try {
        const response = await fetch("/health");
        const data = await response.json();

        if (data.status === "healthy") {
            showToast("✓ Bloxy-bot AI is online!", "success");
            addNotification("System", `Bloxy-bot AI v${APP_VERSION} started`);
        }
    } catch (error) {
        showToast("⚠ Connection issue detected", "warning");
    }
}

/* ================================================= */
/* RESTORE SESSION */
/* ================================================= */

function restoreSession() {
    const savedModel = localStorage.getItem("bloxy_model");
    if (savedModel && modelSelector) {
        modelSelector.value = savedModel;
        AppState.currentModel = savedModel;
    }
}

/* ================================================= */
/* FINAL INITIALIZATION */
/* ================================================= */

window.addEventListener("load", async () => {
    console.log(`%cBloxy-bot AI v${APP_VERSION}`, "color: #ff7a00; font-size: 16px; font-weight: bold");

    applyTheme(AppState.theme);
    AppState.chats = loadLocal("bloxy_chats", []);
    loadMemories();

    restoreSession();
    initializeLoadingScreen();

    await startupChecks();

    renderNotifications();

    setInterval(updateAdminStats, 30000);
    setInterval(loadProviderHealth, 60000);

    showToast("Welcome to Bloxy-bot AI! 🤖", "success");
});

/* ================================================= */
/* ERROR HANDLER */
/* ================================================= */

window.addEventListener("error", (event) => {
    console.error("Global error:", event.error);
    addNotification("Error", event.error?.message || "An error occurred");
});

/* ================================================= */
/* END OF APP.JS */
/* =================================================
