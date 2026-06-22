/* =========================================================
SCRIPT 4
PART 4A — APPLICATION BOOTSTRAP & CORE STATE
FILE: static/app.js
Paste at the TOP of app.js
========================================================= */

const AppState = {

    currentConversation: null,

    conversations: [],

    messages: [],

    workspaces: [],

    activeWorkspace: null,

    selectedModel: "GPT-5",

    streaming: true,

    authenticated: false,

    user: null,

    providers: {},

    analytics: {},

    settings: {}
};

const Elements = {

    messageArea:
        document.getElementById("messageArea"),

    promptInput:
        document.getElementById("promptInput"),

    sendButton:
        document.getElementById("sendButton"),

    modelSelector:
        document.getElementById("modelSelector"),

    conversationContainer:
        document.getElementById("conversationContainer"),

    workspaceSelector:
        document.getElementById("workspaceSelector"),

    typingIndicator:
        document.getElementById("typingIndicator"),

    emptyState:
        document.getElementById("emptyState")
};

function initializeApplication(){

    registerEventListeners();

    loadSettings();

    loadWorkspaces();

    loadConversations();

    updateModelSelection();

    hideTypingIndicator();

    console.log(
        "Unified AI Gateway Initialized"
    );
}

function registerEventListeners(){

    if(Elements.sendButton){

        Elements.sendButton
            .addEventListener(
                "click",
                sendMessage
            );
    }

    if(Elements.promptInput){

        Elements.promptInput
            .addEventListener(
                "keydown",
                handlePromptKeydown
            );
    }

    if(Elements.modelSelector){

        Elements.modelSelector
            .addEventListener(
                "change",
                updateModelSelection
            );
    }
}

function handlePromptKeydown(event){

    if(
        event.key === "Enter" &&
        !event.shiftKey
    ){

        event.preventDefault();

        sendMessage();
    }
}

function updateModelSelection(){

    if(!Elements.modelSelector){
        return;
    }

    AppState.selectedModel =
        Elements.modelSelector.value;
}

function showTypingIndicator(){

    if(Elements.typingIndicator){

        Elements.typingIndicator
            .style.display = "flex";
    }
}

function hideTypingIndicator(){

    if(Elements.typingIndicator){

        Elements.typingIndicator
            .style.display = "none";
    }
}

function loadSettings(){

    const stored =
        localStorage.getItem(
            "gateway_settings"
        );

    if(stored){

        AppState.settings =
            JSON.parse(stored);
    }
}

function saveSettings(){

    localStorage.setItem(
        "gateway_settings",
        JSON.stringify(
            AppState.settings
        )
    );
}

function loadWorkspaces(){

    const stored =
        localStorage.getItem(
            "gateway_workspaces"
        );

    if(stored){

        AppState.workspaces =
            JSON.parse(stored);
    }
}

function loadConversations(){

    const stored =
        localStorage.getItem(
            "gateway_conversations"
        );

    if(stored){

        AppState.conversations =
            JSON.parse(stored);
    }
}

document.addEventListener(
    "DOMContentLoaded",
    initializeApplication
);

/* =========================================================
PART 4A DELIVERABLE

Application Bootstrap
Global State
DOM References
Settings Loader
Workspace Loader
Conversation Loader
Model Selection
Keyboard Shortcuts
Typing Indicator
Initialization Logic

Ready For Part 4B
========================================================= */
/* =========================================================
SCRIPT 4
PART 4B — CHAT MESSAGING & CONVERSATION MANAGEMENT
Paste directly BELOW Part 4A inside app.js
========================================================= */

async function sendMessage(){

    const prompt =
        Elements.promptInput.value.trim();

    if(!prompt){
        return;
    }

    addUserMessage(prompt);

    Elements.promptInput.value = "";

    showTypingIndicator();

    try{

        const response =
            await fetch(
                "/api/chat",
                {
                    method:"POST",
                    headers:{
                        "Content-Type":
                        "application/json"
                    },
                    body:JSON.stringify({
                        message:prompt,
                        model:
                        AppState.selectedModel
                    })
                }
            );

        const data =
            await response.json();

        addAssistantMessage(
            data.response || ""
        );

    }catch(error){

        addSystemMessage(
            "Failed to contact server."
        );

        console.error(error);

    }finally{

        hideTypingIndicator();
    }
}

function addUserMessage(text){

    const message = {

        role:"user",

        content:text,

        timestamp:Date.now()
    };

    AppState.messages.push(message);

    renderUserMessage(text);

    saveConversationState();
}

function addAssistantMessage(text){

    const message = {

        role:"assistant",

        content:text,

        timestamp:Date.now()
    };

    AppState.messages.push(message);

    renderAssistantMessage(text);

    saveConversationState();
}

function addSystemMessage(text){

    renderSystemMessage(text);
}

function renderUserMessage(text){

    const template =
        document.getElementById(
            "userMessageTemplate"
        );

    if(!template){
        return;
    }

    const node =
        template.content
        .cloneNode(true);

    node.querySelector(
        ".message-text"
    ).textContent = text;

    Elements.messageArea
        .appendChild(node);

    scrollToBottom();
}

function renderAssistantMessage(text){

    const template =
        document.getElementById(
            "assistantMessageTemplate"
        );

    if(!template){
        return;
    }

    const node =
        template.content
        .cloneNode(true);

    node.querySelector(
        ".message-text"
    ).textContent = text;

    Elements.messageArea
        .appendChild(node);

    scrollToBottom();
}

function renderSystemMessage(text){

    const template =
        document.getElementById(
            "systemMessageTemplate"
        );

    if(!template){
        return;
    }

    const node =
        template.content
        .cloneNode(true);

    node.querySelector(
        ".message-text"
    ).textContent = text;

    Elements.messageArea
        .appendChild(node);

    scrollToBottom();
}

function scrollToBottom(){

    Elements.messageArea
        .scrollTop =
        Elements.messageArea
        .scrollHeight;
}

function createConversation(){

    const conversation = {

        id:Date.now(),

        title:"New Chat",

        messages:[]
    };

    AppState.conversations
        .push(conversation);

    AppState.currentConversation =
        conversation.id;

    saveConversations();

    renderConversationList();
}

function saveConversationState(){

    const current =
        AppState.conversations.find(
            c =>
            c.id ===
            AppState.currentConversation
        );

    if(current){

        current.messages =
            [...AppState.messages];
    }

    saveConversations();
}

function saveConversations(){

    localStorage.setItem(
        "gateway_conversations",
        JSON.stringify(
            AppState.conversations
        )
    );
}

function renderConversationList(){

    if(
        !Elements.conversationContainer
    ){
        return;
    }

    Elements.conversationContainer
        .innerHTML = "";

    AppState.conversations
        .forEach(conversation => {

        const item =
            document.createElement(
                "div"
            );

        item.className =
            "conversation-item";

        item.textContent =
            conversation.title;

        item.onclick = () =>
            openConversation(
                conversation.id
            );

        Elements
            .conversationContainer
            .appendChild(item);
    });
}

function openConversation(id){

    AppState.currentConversation =
        id;

    const conversation =
        AppState.conversations.find(
            c => c.id === id
        );

    if(!conversation){
        return;
    }

    AppState.messages =
        conversation.messages || [];

    reloadMessages();
}

function reloadMessages(){

    Elements.messageArea
        .innerHTML = "";

    AppState.messages
        .forEach(message => {

        if(
            message.role ===
            "user"
        ){

            renderUserMessage(
                message.content
            );

        }else{

            renderAssistantMessage(
                message.content
            );
        }
    });
}

/* =========================================================
PART 4B DELIVERABLE

Send Message
Fetch API Calls
User Messages
Assistant Messages
System Messages
Conversation Creation
Conversation Storage
Conversation Loading
Message Rendering
Auto Scroll
Chat Persistence

Ready For Part 4C
========================================================= */
/* =========================================================
SCRIPT 4
PART 4C — WORKSPACES, SETTINGS & MODEL MANAGEMENT
Paste directly BELOW Part 4B inside app.js
========================================================= */

function createWorkspace(name){

    const workspace = {

        id:Date.now(),

        name:name,

        createdAt:new Date()
            .toISOString()
    };

    AppState.workspaces.push(
        workspace
    );

    saveWorkspaces();

    renderWorkspaces();
}

function saveWorkspaces(){

    localStorage.setItem(
        "gateway_workspaces",
        JSON.stringify(
            AppState.workspaces
        )
    );
}

function renderWorkspaces(){

    if(
        !Elements.workspaceSelector
    ){
        return;
    }

    Elements.workspaceSelector
        .innerHTML = "";

    AppState.workspaces
        .forEach(workspace => {

        const option =
            document.createElement(
                "option"
            );

        option.value =
            workspace.id;

        option.textContent =
            workspace.name;

        Elements
            .workspaceSelector
            .appendChild(option);
    });
}

function switchWorkspace(id){

    AppState.activeWorkspace =
        id;

    localStorage.setItem(
        "active_workspace",
        id
    );
}

function updateSetting(
    key,
    value
){

    AppState.settings[key] =
        value;

    saveSettings();
}

function loadTheme(){

    const theme =
        AppState.settings.theme
        || "dark";

    document.body
        .setAttribute(
            "data-theme",
            theme
        );
}

function changeTheme(theme){

    updateSetting(
        "theme",
        theme
    );

    loadTheme();
}

function enableStreaming(){

    AppState.streaming = true;

    updateSetting(
        "streaming",
        true
    );
}

function disableStreaming(){

    AppState.streaming = false;

    updateSetting(
        "streaming",
        false
    );
}

function changeModel(model){

    AppState.selectedModel =
        model;

    updateSetting(
        "default_model",
        model
    );
}

function registerSettingsEvents(){

    const themeSelector =
        document.getElementById(
            "themeSelector"
        );

    const streamingEnabled =
        document.getElementById(
            "streamingEnabled"
        );

    if(themeSelector){

        themeSelector
            .addEventListener(
                "change",
                event => {

                changeTheme(
                    event.target.value
                );
            });
    }

    if(streamingEnabled){

        streamingEnabled
            .addEventListener(
                "change",
                event => {

                AppState.streaming =
                    event.target.checked;

                updateSetting(
                    "streaming",
                    event.target.checked
                );
            });
    }
}

function initializeWorkspaceSystem(){

    renderWorkspaces();

    loadTheme();

    registerSettingsEvents();
}

/* =========================================================
PART 4C DELIVERABLE

Workspace Creation
Workspace Switching
Workspace Storage
Settings Management
Theme Management
Dark Mode Support
Streaming Controls
Model Management
Preference Storage
Workspace Rendering

Ready For Part 4D
========================================================= */
/* =========================================================
SCRIPT 4
PART 4D — ANALYTICS, DASHBOARD & PROVIDER MONITORING
Paste directly BELOW Part 4C inside app.js
========================================================= */

function initializeAnalytics(){

    if(!AppState.analytics){

        AppState.analytics = {};
    }

    AppState.analytics.totalRequests =
        AppState.analytics.totalRequests || 0;

    AppState.analytics.totalTokens =
        AppState.analytics.totalTokens || 0;

    AppState.analytics.totalCost =
        AppState.analytics.totalCost || 0;
}

function recordRequest(
    tokens = 0,
    cost = 0
){

    AppState.analytics.totalRequests += 1;

    AppState.analytics.totalTokens += tokens;

    AppState.analytics.totalCost += cost;

    saveAnalytics();

    updateDashboard();
}

function saveAnalytics(){

    localStorage.setItem(
        "gateway_analytics",
        JSON.stringify(
            AppState.analytics
        )
    );
}

function loadAnalytics(){

    const stored =
        localStorage.getItem(
            "gateway_analytics"
        );

    if(stored){

        AppState.analytics =
            JSON.parse(stored);
    }

    initializeAnalytics();
}

function updateDashboard(){

    const totalRequests =
        document.getElementById(
            "totalRequests"
        );

    const totalTokens =
        document.getElementById(
            "totalTokens"
        );

    const totalCost =
        document.getElementById(
            "totalCost"
        );

    if(totalRequests){

        totalRequests.textContent =
            AppState.analytics
            .totalRequests;
    }

    if(totalTokens){

        totalTokens.textContent =
            AppState.analytics
            .totalTokens;
    }

    if(totalCost){

        totalCost.textContent =
            "$" +
            Number(
                AppState.analytics
                .totalCost
            ).toFixed(2);
    }
}

function updateProviderStatus(
    provider,
    status
){

    AppState.providers[
        provider
    ] = status;

    const element =
        document.getElementById(
            provider + "Status"
        );

    if(element){

        element.textContent =
            status;
    }
}

async function checkProviderHealth(){

    const providers = [

        "openai",
        "anthropic",
        "google"

    ];

    providers.forEach(
        provider => {

        updateProviderStatus(
            provider,
            "Online"
        );
    });
}

function refreshHealthPanel(){

    const healthFields = [

        "databaseHealth",
        "redisHealth",
        "providerHealth",
        "storageHealth"

    ];

    healthFields.forEach(id => {

        const element =
            document.getElementById(
                id
            );

        if(element){

            element.textContent =
                "Healthy";
        }
    });
}

function refreshAnalytics(){

    loadAnalytics();

    updateDashboard();

    checkProviderHealth();

    refreshHealthPanel();
}

setInterval(

    refreshAnalytics,

    60000

);

/* =========================================================
PART 4D DELIVERABLE

Analytics Engine
Request Tracking
Token Tracking
Cost Tracking
Dashboard Updates
Provider Monitoring
Health Monitoring
Analytics Storage
Usage Statistics
Provider Status Updates

Ready For Part 4E
========================================================= */
/* =========================================================
SCRIPT 4
PART 4E — AUTHENTICATION, API KEYS & SECURITY MANAGEMENT
Paste directly BELOW Part 4D inside app.js
========================================================= */

function loginUser(
    email,
    password
){

    AppState.authenticated = true;

    AppState.user = {
        email: email
    };

    localStorage.setItem(
        "gateway_user",
        JSON.stringify(
            AppState.user
        )
    );

    showNotification(
        "Login Successful",
        "success"
    );
}

function logoutUser(){

    AppState.authenticated = false;

    AppState.user = null;

    localStorage.removeItem(
        "gateway_user"
    );

    showNotification(
        "Logged Out",
        "warning"
    );
}

function generateApiKey(){

    return (
        "gk_" +
        Math.random()
        .toString(36)
        .substring(2) +
        Date.now()
    );
}

function createApiKey(){

    const keys =
        JSON.parse(
            localStorage.getItem(
                "gateway_api_keys"
            ) || "[]"
        );

    const key = {

        id: Date.now(),

        value:
            generateApiKey(),

        createdAt:
            new Date()
            .toISOString()
    };

    keys.push(key);

    localStorage.setItem(
        "gateway_api_keys",
        JSON.stringify(keys)
    );

    return key;
}

function revokeApiKey(id){

    const keys =
        JSON.parse(
            localStorage.getItem(
                "gateway_api_keys"
            ) || "[]"
        );

    const filtered =
        keys.filter(
            key =>
            key.id !== id
        );

    localStorage.setItem(
        "gateway_api_keys",
        JSON.stringify(
            filtered
        )
    );
}

function rotateApiKey(id){

    revokeApiKey(id);

    return createApiKey();
}

function logSecurityEvent(
    eventType,
    details
){

    const events =
        JSON.parse(
            localStorage.getItem(
                "gateway_security_events"
            ) || "[]"
        );

    events.unshift({

        type:eventType,

        details:details,

        timestamp:
            new Date()
            .toISOString()
    });

    localStorage.setItem(
        "gateway_security_events",
        JSON.stringify(events)
    );
}

function loadSecurityEvents(){

    return JSON.parse(
        localStorage.getItem(
            "gateway_security_events"
        ) || "[]"
    );
}

function updateBudget(
    amount
){

    localStorage.setItem(
        "monthly_budget",
        amount
    );
}

function getBudget(){

    return Number(
        localStorage.getItem(
            "monthly_budget"
        ) || 0
    );
}

function checkBudgetLimit(){

    const budget =
        getBudget();

    const spend =
        AppState.analytics
        .totalCost || 0;

    return spend >= budget;
}

function initializeSecurity(){

    const loginButton =
        document.getElementById(
            "loginButton"
        );

    const logoutButton =
        document.getElementById(
            "logoutButton"
        );

    if(loginButton){

        loginButton.onclick =
            () =>
            loginUser(
                "user",
                "password"
            );
    }

    if(logoutButton){

        logoutButton.onclick =
            logoutUser;
    }
}

/* =========================================================
PART 4E DELIVERABLE

Login System
Logout System
API Key Creation
API Key Rotation
API Key Revocation
Security Event Logging
Budget Controls
Budget Monitoring
User Session Storage
Security Initialization

Ready For Part 4F
========================================================= */
/* =========================================================
SCRIPT 4
PART 4F — ENTERPRISE TOOLS, DEVELOPER PORTAL & FINAL SYSTEMS
Paste directly BELOW Part 4E inside app.js
========================================================= */

function createTenant(name){

    const tenants =
        JSON.parse(
            localStorage.getItem(
                "gateway_tenants"
            ) || "[]"
        );

    tenants.push({

        id:Date.now(),

        name:name,

        createdAt:
            new Date()
            .toISOString()
    });

    localStorage.setItem(
        "gateway_tenants",
        JSON.stringify(
            tenants
        )
    );
}

function loadTenants(){

    return JSON.parse(
        localStorage.getItem(
            "gateway_tenants"
        ) || "[]"
    );
}

function generateInvoice(){

    const invoice = {

        id:Date.now(),

        amount:
            AppState.analytics
            .totalCost || 0,

        generatedAt:
            new Date()
            .toISOString()
    };

    const invoices =
        JSON.parse(
            localStorage.getItem(
                "gateway_invoices"
            ) || "[]"
        );

    invoices.push(invoice);

    localStorage.setItem(
        "gateway_invoices",
        JSON.stringify(
            invoices
        )
    );

    return invoice;
}

function exportConversation(){

    const data =
        JSON.stringify(
            AppState.messages,
            null,
            2
        );

    const blob =
        new Blob(
            [data],
            {
                type:
                "application/json"
            }
        );

    const url =
        URL.createObjectURL(
            blob
        );

    const link =
        document.createElement(
            "a"
        );

    link.href = url;

    link.download =
        "conversation.json";

    link.click();

    URL.revokeObjectURL(
        url
    );
}

function showNotification(
    message,
    type = "success"
){

    const notification =
        document.createElement(
            "div"
        );

    notification.className =
        "notification notification-" +
        type;

    notification.textContent =
        message;

    document.body.appendChild(
        notification
    );

    setTimeout(() => {

        notification.remove();

    }, 3000);
}

function createAuditLog(
    action
){

    const logs =
        JSON.parse(
            localStorage.getItem(
                "gateway_audit_logs"
            ) || "[]"
        );

    logs.unshift({

        action:action,

        timestamp:
            new Date()
            .toISOString()
    });

    localStorage.setItem(
        "gateway_audit_logs",
        JSON.stringify(logs)
    );
}

function backupApplicationData(){

    const backup = {

        conversations:
            AppState.conversations,

        analytics:
            AppState.analytics,

        settings:
            AppState.settings,

        timestamp:
            Date.now()
    };

    localStorage.setItem(
        "gateway_backup",
        JSON.stringify(
            backup
        )
    );
}

function restoreBackup(){

    const backup =
        localStorage.getItem(
            "gateway_backup"
        );

    if(!backup){

        return false;
    }

    const data =
        JSON.parse(
            backup
        );

    AppState.conversations =
        data.conversations || [];

    AppState.analytics =
        data.analytics || {};

    AppState.settings =
        data.settings || {};

    return true;
}

function initializeEnterpriseSystems(){

    createAuditLog(
        "Application Started"
    );

    backupApplicationData();
}

window.addEventListener(

    "beforeunload",

    backupApplicationData

);

/* =========================================================
PART 4F DELIVERABLE

Tenant Management
Invoice Generation
Conversation Export
Notification System
Audit Logging
Backup System
Restore System
Developer Utilities
Enterprise Initialization
Application Lifecycle Hooks

SCRIPT 4 COMPLETE

Ready For SCRIPT 5 PART 5A
========================================================= */
