/* ================================================= */
/* BLOXY-BOT - APP.JS PART 1 */
/* ================================================= */

const AppState = {

```
chats: [],

currentChatId: null,

currentModel: "auto",

theme: localStorage.getItem("nova_theme") || "dark",

user: null,

providers: {},

memories: [],

notifications: []
```

};

/* ================================================= */
/* DOM REFERENCES */
/* ================================================= */

const sidebar =
document.getElementById("sidebar");

const mobileOverlay =
document.getElementById("mobileOverlay");

const menuToggle =
document.getElementById("menuToggle");

const newChatBtn =
document.getElementById("newChatBtn");

const messageInput =
document.getElementById("messageInput");

const sendBtn =
document.getElementById("sendBtn");

const stopBtn =
document.getElementById("stopBtn");

const toastContainer =
document.getElementById("toastContainer");

const themeBtn =
document.getElementById("themeBtn");

const modelSelector =
document.getElementById("modelSelector");

const chatContainer =
document.getElementById("chatContainer");

const typingIndicator =
document.getElementById("typingIndicator");

/* ================================================= */
/* UTILITIES */
/* ================================================= */

function generateId() {

```
return Date.now() +
       Math.floor(Math.random() * 999999);
```

}

function formatTime() {

```
return new Date().toLocaleTimeString(
    [],
    {
        hour: "2-digit",
        minute: "2-digit"
    }
);
```

}

function saveLocal(key, value) {

```
localStorage.setItem(
    key,
    JSON.stringify(value)
);
```

}

function loadLocal(key, fallback) {

```
const item =
    localStorage.getItem(key);

if (!item)
    return fallback;

try {

    return JSON.parse(item);

} catch {

    return fallback;

}
```

}

/* ================================================= */
/* TOAST NOTIFICATIONS */
/* ================================================= */

function showToast(
message,
type = "success"
) {

```
const toast =
    document.createElement("div");

toast.className =
    `toast ${type}`;

toast.innerHTML = `
    <span>${message}</span>
`;

toastContainer.appendChild(
    toast
);

setTimeout(() => {

    toast.classList.add(
        "toast-show"
    );

}, 10);

setTimeout(() => {

    toast.remove();

}, 4000);
```

}

/* ================================================= */
/* MOBILE SIDEBAR */
/* ================================================= */

function openSidebar() {

```
sidebar.classList.add(
    "sidebar-open"
);

mobileOverlay.classList.add(
    "overlay-show"
);
```

}

function closeSidebar() {

```
sidebar.classList.remove(
    "sidebar-open"
);

mobileOverlay.classList.remove(
    "overlay-show"
);
```

}

if (menuToggle) {

```
menuToggle.addEventListener(
    "click",
    openSidebar
);
```

}

if (mobileOverlay) {

```
mobileOverlay.addEventListener(
    "click",
    closeSidebar
);
```

}

/* ================================================= */
/* THEME SYSTEM */
/* ================================================= */

function applyTheme(theme) {

```
document.body.setAttribute(
    "data-theme",
    theme
);

AppState.theme = theme;

localStorage.setItem(
    "nova_theme",
    theme
);
```

}

function toggleTheme() {

```
const nextTheme =
    AppState.theme === "dark"
    ? "light"
    : "dark";

applyTheme(nextTheme);

showToast(
    `Theme changed to ${nextTheme}`
);
```

}

if (themeBtn) {

```
themeBtn.addEventListener(
    "click",
    toggleTheme
);
```

}

/* ================================================= */
/* MODEL SELECTOR */
/* ================================================= */

if (modelSelector) {

```
modelSelector.addEventListener(
    "change",
    (e) => {

        AppState.currentModel =
            e.target.value;

        showToast(
            `Model set to ${e.target.value}`
        );

    }
);
```

}

/* ================================================= */
/* NEW CHAT */
/* ================================================= */

function createNewChat() {

```
const chat = {

    id: generateId(),

    title: "New Chat",

    messages: [],

    createdAt: Date.now()

};

AppState.chats.unshift(chat);

AppState.currentChatId =
    chat.id;

chatContainer.innerHTML = "";

saveLocal(
    "nova_chats",
    AppState.chats
);

showToast(
    "New chat created"
);
```

}

if (newChatBtn) {

```
newChatBtn.addEventListener(
    "click",
    createNewChat
);
```

}

/* ================================================= */
/* AUTO RESIZE INPUT */
/* ================================================= */

if (messageInput) {

```
messageInput.addEventListener(
    "input",
    () => {

        messageInput.style.height =
            "auto";

        messageInput.style.height =
            messageInput.scrollHeight +
            "px";

    }
);
```

}

/* ================================================= */
/* TYPING INDICATOR */
/* ================================================= */

function showTyping() {

```
if (!typingIndicator)
    return;

typingIndicator.classList.remove(
    "hidden"
);
```

}

function hideTyping() {

```
if (!typingIndicator)
    return;

typingIndicator.classList.add(
    "hidden"
);
```

}

/* ================================================= */
/* LOADING SCREEN */
/* ================================================= */

function initializeLoadingScreen() {

```
const loadingScreen =
    document.getElementById(
        "loadingScreen"
    );

if (!loadingScreen)
    return;

setTimeout(() => {

    loadingScreen.classList.add(
        "loading-complete"
    );

}, 1800);
```

}

/* ================================================= */
/* APP STARTUP */
/* ================================================= */

window.addEventListener(
"load",
() => {

```
    applyTheme(
        AppState.theme
    );

    AppState.chats =
        loadLocal(
            "nova_chats",
            []
        );

    initializeLoadingScreen();

    showToast(
        "Nova AI Initialized"
    );

}
```

);
/* ================================================= */
/* NOVA AI - APP.JS PART 2 */
/* ================================================= */

/* ================================================= */
/* MESSAGE RENDERING */
/* ================================================= */

function addMessage(
role,
content
) {

```
if (!chatContainer)
    return;

const message =
    document.createElement("div");

message.className =
    `message ${role}`;

const time =
    formatTime();

message.innerHTML = `
    <div class="message-header">
        <span class="message-role">
            ${role === "user"
                ? "You"
                : "Nova AI"}
        </span>

        <span class="message-time">
            ${time}
        </span>
    </div>

    <div class="message-content">
        ${content}
    </div>
`;

chatContainer.appendChild(
    message
);

chatContainer.scrollTop =
    chatContainer.scrollHeight;
```

}

/* ================================================= */
/* CHAT STORAGE */
/* ================================================= */

function saveCurrentChatMessage(
role,
content
) {

```
const chat =
    AppState.chats.find(
        c =>
        c.id ===
        AppState.currentChatId
    );

if (!chat)
    return;

chat.messages.push({

    role,

    content,

    timestamp:
        Date.now()

});

if (
    chat.title === "New Chat" &&
    role === "user"
) {

    chat.title =
        content.substring(
            0,
            40
        );

}

saveLocal(
    "nova_chats",
    AppState.chats
);
```

}

/* ================================================= */
/* CHAT HISTORY PANEL */
/* ================================================= */

function refreshChatHistory() {

```
const history =
    document.getElementById(
        "chatHistory"
    );

if (!history)
    return;

history.innerHTML = "";

AppState.chats.forEach(
    chat => {

        const item =
            document.createElement(
                "div"
            );

        item.className =
            "history-item";

        item.textContent =
            chat.title;

        item.addEventListener(
            "click",
            () => {

                loadChat(
                    chat.id
                );

            }
        );

        history.appendChild(
            item
        );

    }
);
```

}

function loadChat(chatId) {

```
const chat =
    AppState.chats.find(
        c => c.id === chatId
    );

if (!chat)
    return;

AppState.currentChatId =
    chatId;

chatContainer.innerHTML =
    "";

chat.messages.forEach(
    msg => {

        addMessage(
            msg.role,
            msg.content
        );

    }
);
```

}

/* ================================================= */
/* API REQUEST */
/* ================================================= */

async function sendToAI(
message
) {

```
try {

    showTyping();

    const response =
        await fetch(
            "/ai/chat",
            {

                method: "POST",

                headers: {

                    "Content-Type":
                        "application/json"

                },

                body:
                    JSON.stringify({

                        message,

                        model:
                            AppState.currentModel

                    })

            }
        );

    if (
        !response.ok
    ) {

        throw new Error(
            "AI request failed"
        );

    }

    const data =
        await response.json();

    hideTyping();

    return data.reply ||
           "No response.";

}

catch (error) {

    hideTyping();

    console.error(
        error
    );

    showToast(
        "AI request failed",
        "error"
    );

    return
    "Something went wrong.";

}
```

}

/* ================================================= */
/* SEND MESSAGE */
/* ================================================= */

async function sendMessage() {

```
const text =
    messageInput.value
    .trim();

if (!text)
    return;

if (
    !AppState.currentChatId
) {

    createNewChat();

}

addMessage(
    "user",
    text
);

saveCurrentChatMessage(
    "user",
    text
);

messageInput.value =
    "";

messageInput.style.height =
    "auto";

const aiReply =
    await sendToAI(
        text
    );

addMessage(
    "assistant",
    aiReply
);

saveCurrentChatMessage(
    "assistant",
    aiReply
);

refreshChatHistory();
```

}

/* ================================================= */
/* SEND BUTTON */
/* ================================================= */

if (sendBtn) {

```
sendBtn.addEventListener(
    "click",
    sendMessage
);
```

}

/* ================================================= */
/* ENTER TO SEND */
/* ================================================= */

if (messageInput) {

```
messageInput.addEventListener(
    "keydown",
    e => {

        if (

            e.key ===
            "Enter"

            &&

            !e.shiftKey

        ) {

            e.preventDefault();

            sendMessage();

        }

    }
);
```

}

/* ================================================= */
/* WELCOME MESSAGE */
/* ================================================= */

window.addEventListener(
"load",
() => {

```
    if (
        AppState.chats.length
        === 0
    ) {

        createNewChat();

        addMessage(
            "assistant",

            `Hello 👋
```

I am Nova AI.

I can help with:

• AI Chat
• Research
• News
• Finance
• Sports
• Weather
• Movies
• Wikipedia
• Dictionary
• Coding
• Wolfram Calculations

How can I assist you today?`

```
        );

    }

    refreshChatHistory();

}
```

);
/* ================================================= */
/* NOVA AI - APP.JS PART 3 */
/* ================================================= */

/* ================================================= */
/* DOM REFERENCES */
/* ================================================= */

const researchBtn =
    document.getElementById(
        "researchBtn"
    );

const webSearchBtn =
    document.getElementById(
        "webSearchBtn"
    );

const searchResultsPanel =
    document.getElementById(
        "searchResultsPanel"
    );

const citationsPanel =
    document.getElementById(
        "citationsPanel"
    );

const reasoningPanel =
    document.getElementById(
        "reasoningPanel"
    );

const researchWorkspace =
    document.getElementById(
        "researchWorkspace"
    );

const sourceList =
    document.getElementById(
        "sourceList"
    );

const confidenceScore =
    document.getElementById(
        "confidenceScore"
    );

/* ================================================= */
/* PANEL HELPERS */
/* ================================================= */

function openPanel(panel) {

    if (!panel)
        return;

    panel.classList.remove(
        "hidden"
    );

}

function closePanel(panel) {

    if (!panel)
        return;

    panel.classList.add(
        "hidden"
    );

}

/* ================================================= */
/* REASONING PANEL */
/* ================================================= */

function updateReasoningPanel(
    sources = [],
    confidence = 95
) {

    if (!sourceList)
        return;

    sourceList.innerHTML = "";

    sources.forEach(
        source => {

            const li =
                document.createElement(
                    "li"
                );

            li.textContent =
                source;

            sourceList.appendChild(
                li
            );

        }
    );

    if (confidenceScore) {

        confidenceScore.textContent =
            confidence + "%";

    }

}

/* ================================================= */
/* CITATIONS */
/* ================================================= */

function updateCitations(
    citations = []
) {

    const container =
        document.getElementById(
            "citationContent"
        );

    if (!container)
        return;

    container.innerHTML = "";

    citations.forEach(
        citation => {

            const item =
                document.createElement(
                    "div"
                );

            item.className =
                "citation-card";

            item.innerHTML = `

                <h4>
                    ${citation.title}
                </h4>

                <a
                  href="${citation.url}"
                  target="_blank">

                  Open Source

                </a>

            `;

            container.appendChild(
                item
            );

        }
    );

}

/* ================================================= */
/* SEARCH RESULTS */
/* ================================================= */

function updateSearchResults(
    results = []
) {

    const container =
        document.getElementById(
            "searchResultsContent"
        );

    if (!container)
        return;

    container.innerHTML = "";

    results.forEach(
        result => {

            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "search-result-card";

            card.innerHTML = `

                <h3>
                    ${result.title}
                </h3>

                <p>
                    ${result.snippet}
                </p>

            `;

            container.appendChild(
                card
            );

        }
    );

}

/* ================================================= */
/* DEEP RESEARCH */
/* ================================================= */

async function startDeepResearch() {

    const query =
        messageInput.value.trim();

    if (!query) {

        showToast(
            "Enter a research topic",
            "error"
        );

        return;

    }

    try {

        showTyping();

        openPanel(
            searchResultsPanel
        );

        openPanel(
            citationsPanel
        );

        openPanel(
            reasoningPanel
        );

        const response =
            await fetch(
                "/ai/research",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

                            query

                        })

                }
            );

        const data =
            await response.json();

        updateSearchResults(
            data.results || []
        );

        updateCitations(
            data.citations || []
        );

        updateReasoningPanel(
            data.sources || [],
            data.confidence || 95
        );

        hideTyping();

        showToast(
            "Research completed"
        );

    }

    catch (error) {

        hideTyping();

        console.error(
            error
        );

        showToast(
            "Research failed",
            "error"
        );

    }

}

/* ================================================= */
/* RESEARCH BUTTON */
/* ================================================= */

if (researchBtn) {

    researchBtn.addEventListener(
        "click",
        startDeepResearch
    );

}

/* ================================================= */
/* QUICK SEARCH */
/* ================================================= */

async function performSearch() {

    const query =
        messageInput.value.trim();

    if (!query)
        return;

    try {

        openPanel(
            searchResultsPanel
        );

        const response =
            await fetch(
                "/ai/search",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

                            query

                        })

                }
            );

        const data =
            await response.json();

        updateSearchResults(
            data.results || []
        );

        showToast(
            "Search complete"
        );

    }

    catch (error) {

        showToast(
            "Search failed",
            "error"
        );

    }

}

if (webSearchBtn) {

    webSearchBtn.addEventListener(
        "click",
        performSearch
    );

}

/* ================================================= */
/* PROVIDER DIAGNOSTICS */
/* ================================================= */

async function loadProviderHealth() {

    try {

        const response =
            await fetch(
                "/ai/providers/health"
            );

        const data =
            await response.json();

        const container =
            document.getElementById(
                "providerDiagnostics"
            );

        if (!container)
            return;

        container.innerHTML = "";

        Object.entries(
            data
        ).forEach(
            ([name, status]) => {

                const card =
                    document.createElement(
                        "div"
                    );

                card.className =
                    "provider-health-card";

                card.innerHTML = `

                    <h3>
                        ${name}
                    </h3>

                    <p>
                        ${status}
                    </p>

                `;

                container.appendChild(
                    card
                );

            }
        );

    }

    catch (error) {

        console.error(
            error
        );

    }

}

/* ================================================= */
/* RESEARCH WORKSPACE */
/* ================================================= */

function openResearchWorkspace() {

    if (!researchWorkspace)
        return;

    researchWorkspace
        .classList.remove(
            "hidden"
        );

    showToast(
        "Research workspace opened"
    );

}

/* ================================================= */
/* CLOSE PANELS */
/* ================================================= */

document
.querySelectorAll(
    ".close-panel"
)
.forEach(btn => {

    btn.addEventListener(
        "click",
        () => {

            const panel =
                btn.closest(
                    ".floating-panel"
                );

            if (panel) {

                closePanel(
                    panel
                );

            }

        }
    );

});

/* ================================================= */
/* AUTO LOAD PROVIDER HEALTH */
/* ================================================= */

setInterval(
    loadProviderHealth,
    60000
);

loadProviderHealth();
/* ================================================= */
/* NOVA AI - APP.JS PART 4 */
/* ================================================= */

/* ================================================= */
/* DOM REFERENCES */
/* ================================================= */

const fileInput =
    document.getElementById(
        "fileInput"
    );

const imageInput =
    document.getElementById(
        "imageInput"
    );

const attachFileBtn =
    document.getElementById(
        "attachFileBtn"
    );

const imageUploadBtn =
    document.getElementById(
        "imageUploadBtn"
    );

const voiceBtn =
    document.getElementById(
        "voiceBtn"
    );

const settingsBtn =
    document.getElementById(
        "settingsBtn"
    );

const settingsModal =
    document.getElementById(
        "settingsModal"
    );

const profileModal =
    document.getElementById(
        "profileModal"
    );

const notificationCenter =
    document.getElementById(
        "notificationCenter"
    );

/* ================================================= */
/* FILE UPLOADS */
/* ================================================= */

if (attachFileBtn) {

    attachFileBtn.addEventListener(
        "click",
        () => {

            fileInput.click();

        }
    );

}

if (fileInput) {

    fileInput.addEventListener(
        "change",
        async e => {

            const file =
                e.target.files[0];

            if (!file)
                return;

            showToast(
                `Uploaded: ${file.name}`
            );

            const formData =
                new FormData();

            formData.append(
                "file",
                file
            );

            try {

                await fetch(
                    "/upload",
                    {

                        method:
                            "POST",

                        body:
                            formData

                    }
                );

            }

            catch {

                showToast(
                    "Upload failed",
                    "error"
                );

            }

        }
    );

}

/* ================================================= */
/* IMAGE UPLOADS */
/* ================================================= */

if (imageUploadBtn) {

    imageUploadBtn.addEventListener(
        "click",
        () => {

            imageInput.click();

        }
    );

}

if (imageInput) {

    imageInput.addEventListener(
        "change",
        e => {

            const image =
                e.target.files[0];

            if (!image)
                return;

            showToast(
                `Image: ${image.name}`
            );

        }
    );

}

/* ================================================= */
/* VOICE INPUT */
/* ================================================= */

let recognition = null;

if (
    "webkitSpeechRecognition"
    in window
) {

    recognition =
        new webkitSpeechRecognition();

    recognition.continuous =
        false;

    recognition.interimResults =
        false;

    recognition.lang =
        "en-US";

    recognition.onresult =
        event => {

            const transcript =
                event.results[0][0]
                .transcript;

            messageInput.value =
                transcript;

            showToast(
                "Voice captured"
            );

        };

}

if (
    voiceBtn &&
    recognition
) {

    voiceBtn.addEventListener(
        "click",
        () => {

            recognition.start();

        }
    );

}

/* ================================================= */
/* EXPORT CHAT */
/* ================================================= */

function exportChat(
    type = "txt"
) {

    const chat =
        AppState.chats.find(
            c =>
            c.id ===
            AppState.currentChatId
        );

    if (!chat)
        return;

    let content =
        JSON.stringify(
            chat,
            null,
            2
        );

    const blob =
        new Blob(
            [content],
            {
                type:
                    "text/plain"
            }
        );

    const url =
        URL.createObjectURL(
            blob
        );

    const a =
        document.createElement(
            "a"
        );

    a.href = url;

    a.download =
        `chat.${type}`;

    a.click();

    URL.revokeObjectURL(
        url
    );

}

/* ================================================= */
/* MEMORY SYSTEM */
/* ================================================= */

function addMemory(
    text
) {

    AppState.memories.push({

        id: generateId(),

        text

    });

    saveLocal(
        "nova_memories",
        AppState.memories
    );

}

function loadMemories() {

    AppState.memories =
        loadLocal(
            "nova_memories",
            []
        );

}

/* ================================================= */
/* PROFILE SYSTEM */
/* ================================================= */

function openProfile() {

    if (!profileModal)
        return;

    profileModal.classList.add(
        "show"
    );

}

function closeProfile() {

    if (!profileModal)
        return;

    profileModal.classList.remove(
        "show"
    );

}

/* ================================================= */
/* NOTIFICATIONS */
/* ================================================= */

function addNotification(
    title,
    message
) {

    const notification = {

        id:
            generateId(),

        title,

        message,

        time:
            formatTime()

    };

    AppState.notifications
        .unshift(
            notification
        );

    renderNotifications();

}

function renderNotifications() {

    const list =
        document.getElementById(
            "notificationList"
        );

    if (!list)
        return;

    list.innerHTML = "";

    AppState.notifications
        .forEach(
            n => {

                const item =
                    document.createElement(
                        "div"
                    );

                item.className =
                    "notification-item";

                item.innerHTML = `

                    <h4>
                        ${n.title}
                    </h4>

                    <p>
                        ${n.message}
                    </p>

                    <span>
                        ${n.time}
                    </span>

                `;

                list.appendChild(
                    item
                );

            }
        );

}

/* ================================================= */
/* SETTINGS MODAL */
/* ================================================= */

if (settingsBtn) {

    settingsBtn.addEventListener(
        "click",
        () => {

            settingsModal
                ?.classList.add(
                    "show"
                );

        }
    );

}

document
.querySelectorAll(
    ".close-modal"
)
.forEach(btn => {

    btn.addEventListener(
        "click",
        () => {

            document
            .querySelectorAll(
                ".modal"
            )
            .forEach(
                modal => {

                    modal
                    .classList
                    .remove(
                        "show"
                    );

                }
            );

        }
    );

});

/* ================================================= */
/* INITIALIZE */
/* ================================================= */

window.addEventListener(
    "load",
    () => {

        loadMemories();

        renderNotifications();

    }
);
/* ================================================= */
/* NOVA AI - APP.JS PART 5 */
/* ================================================= */

/* ================================================= */
/* ADMIN DASHBOARD */
/* ================================================= */

const adminModal =
    document.getElementById(
        "adminModal"
    );

function openAdminDashboard() {

    if (!adminModal)
        return;

    adminModal.classList.add(
        "show"
    );

    updateAdminStats();

}

async function updateAdminStats() {

    try {

        const response =
            await fetch(
                "/admin/stats"
            );

        const data =
            await response.json();

        const totalUsers =
            document.getElementById(
                "totalUsers"
            );

        const totalChats =
            document.getElementById(
                "totalChats"
            );

        const apiHealth =
            document.getElementById(
                "apiHealth"
            );

        const systemStatus =
            document.getElementById(
                "systemStatus"
            );

        if (totalUsers)
            totalUsers.textContent =
                data.users || 0;

        if (totalChats)
            totalChats.textContent =
                data.chats || 0;

        if (apiHealth)
            apiHealth.textContent =
                data.apiHealth || "Healthy";

        if (systemStatus)
            systemStatus.textContent =
                data.status || "Online";

    }

    catch (error) {

        console.error(error);

    }

}

/* ================================================= */
/* PROVIDER STATUS */
/* ================================================= */

const providerModal =
    document.getElementById(
        "providerModal"
    );

const providerStatusBtn =
    document.getElementById(
        "providerStatusBtn"
    );

if (providerStatusBtn) {

    providerStatusBtn.addEventListener(
        "click",
        async () => {

            providerModal?.classList.add(
                "show"
            );

            await loadProviderHealth();

        }
    );

}

/* ================================================= */
/* COMMAND PALETTE */
/* ================================================= */

const commandPalette =
    document.getElementById(
        "commandPalette"
    );

function openCommandPalette() {

    if (!commandPalette)
        return;

    commandPalette.classList.remove(
        "hidden"
    );

    const input =
        commandPalette.querySelector(
            "input"
        );

    input?.focus();

}

function closeCommandPalette() {

    if (!commandPalette)
        return;

    commandPalette.classList.add(
        "hidden"
    );

}

/* ================================================= */
/* KEYBOARD SHORTCUTS */
/* ================================================= */

document.addEventListener(
    "keydown",
    event => {

        if (
            event.ctrlKey &&
            event.key.toLowerCase() ===
            "k"
        ) {

            event.preventDefault();

            openCommandPalette();

        }

        if (
            event.key ===
            "Escape"
        ) {

            closeCommandPalette();

        }

        if (
            event.ctrlKey &&
            event.key.toLowerCase() ===
            "n"
        ) {

            event.preventDefault();

            createNewChat();

        }

    }
);

/* ================================================= */
/* QUICK ACTION BUTTON */
/* ================================================= */

const quickFab =
    document.getElementById(
        "quickAccessFab"
    );

if (quickFab) {

    quickFab.addEventListener(
        "click",
        () => {

            openCommandPalette();

        }
    );

}

/* ================================================= */
/* GLOBAL LOADING */
/* ================================================= */

const globalLoading =
    document.getElementById(
        "globalLoadingOverlay"
    );

function showGlobalLoading() {

    if (!globalLoading)
        return;

    globalLoading.classList.remove(
        "hidden"
    );

}

function hideGlobalLoading() {

    if (!globalLoading)
        return;

    globalLoading.classList.add(
        "hidden"
    );

}

/* ================================================= */
/* PROVIDER HEALTH MONITOR */
/* ================================================= */

async function monitorProviders() {

    try {

        const response =
            await fetch(
                "/ai/providers/health"
            );

        const data =
            await response.json();

        AppState.providers =
            data;

    }

    catch (error) {

        console.error(
            "Provider monitor error",
            error
        );

    }

}

/* ================================================= */
/* APP VERSION */
/* ================================================= */

const APP_VERSION =
    "1.0.0";

/* ================================================= */
/* STARTUP CHECKS */
/* ================================================= */

async function startupChecks() {

    showGlobalLoading();

    try {

        await monitorProviders();

        showToast(
            "Providers Online"
        );

        addNotification(
            "System",
            "Nova AI started successfully"
        );

    }

    catch {

        showToast(
            "Startup issue detected",
            "error"
        );

    }

    finally {

        setTimeout(
            hideGlobalLoading,
            1000
        );

    }

}

/* ================================================= */
/* RESTORE SESSION */
/* ================================================= */

function restoreSession() {

    const savedModel =
        localStorage.getItem(
            "nova_model"
        );

    if (
        savedModel &&
        modelSelector
    ) {

        modelSelector.value =
            savedModel;

        AppState.currentModel =
            savedModel;

    }

}

/* ================================================= */
/* SAVE MODEL */
/* ================================================= */

if (modelSelector) {

    modelSelector.addEventListener(
        "change",
        () => {

            localStorage.setItem(
                "nova_model",
                modelSelector.value
            );

        }
    );

}

/* ================================================= */
/* WELCOME NOTIFICATIONS */
/* ================================================= */

function createWelcomeNotifications() {

    addNotification(
        "Research",
        "Deep Research ready"
    );

    addNotification(
        "Providers",
        "25 intelligence providers connected"
    );

    addNotification(
        "System",
        "Nova AI initialized"
    );

}

/* ================================================= */
/* FINAL INITIALIZATION */
/* ================================================= */

window.addEventListener(
    "load",
    async () => {

        console.log(
            `Nova AI v${APP_VERSION}`
        );

        restoreSession();

        createWelcomeNotifications();

        await startupChecks();

        setInterval(
            monitorProviders,
            300000
        );

    }
);

/* ================================================= */
/* END OF APP.JS */
/* ================================================= */
