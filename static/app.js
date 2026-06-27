document.addEventListener('DOMContentLoaded', () => {
    // ============================================================
    // 1. UI ELEMENT REFERENCES
    // ============================================================
    const sendBtn = document.getElementById('sendBtn');
    const userInput = document.getElementById('userInput');
    const messageContainer = document.getElementById('messageContainer');
    const chatAreaWrapper = document.getElementById('chatAreaWrapper');
    const welcomeMessage = document.getElementById('welcomeMessage');
    const actionCards = document.querySelectorAll('.card');

    // ============================================================
    // 2. HELPER FUNCTIONS
    // ============================================================

    // Add a message to the chat UI
    function addMessage(text, isUser, provider = null) {
        // Hide the welcome message on first interaction
        if (welcomeMessage && !isUser) {
            welcomeMessage.style.display = 'none';
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
        
        const avatarIcon = isUser ? 'fa-user' : 'fa-robot';
        const avatarColor = isUser ? '#F59E0B' : '#252525';
        const avatarTextColor = isUser ? '#0E0E0E' : '#FFFFFF';
        const name = isUser ? 'You' : 'Bloxy bot';

        // Simple Markdown formatting (Bold, Links, Line Breaks)
        let formattedText = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" style="color: #F59E0B;">$1</a>')
            .replace(/\n/g, '<br>');

        messageDiv.innerHTML = `
            <div class="avatar" style="background: ${avatarColor}; color: ${avatarTextColor};">
                <i class="fa-solid ${avatarIcon}"></i>
            </div>
            <div class="content">
                <h4 style="font-weight: 600; margin-bottom: 4px;">
                    ${name} 
                    ${provider ? `<span style="font-size: 0.7rem; color:#6B7280; font-weight:normal;">via ${provider}</span>` : ''}
                </h4>
                <p style="color: #D1D5DB; line-height: 1.6;">${formattedText}</p>
            </div>
        `;
        messageContainer.appendChild(messageDiv);
        
        // Auto-scroll to bottom
        setTimeout(() => {
            chatAreaWrapper.scrollTo(0, chatAreaWrapper.scrollHeight);
        }, 50);
    }

    // ============================================================
    // 3. MAIN AI LOGIC (BROWSER-ONLY, NO PYTHON)
    // ============================================================

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        // Clear input and add user message to UI
        userInput.value = '';
        addMessage(text, true);

        // --- 3a. Get API Key ---
        let apiKey = localStorage.getItem('bloxy_deepseek_key');
        if (!apiKey) {
            apiKey = prompt("🔐 Enter your DeepSeek API Key (sk-...):");
            if (!apiKey || !apiKey.startsWith('sk-')) {
                addMessage("❌ Invalid API Key. Please refresh and try again.", false);
                return;
            }
            localStorage.setItem('bloxy_deepseek_key', apiKey);
        }

        // --- 3b. Show Loading Skeleton ---
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message ai-message';
        loadingDiv.id = 'loadingIndicator';
        loadingDiv.innerHTML = `
            <div class="avatar" style="background: #252525; color: #fff;"><i class="fa-solid fa-robot"></i></div>
            <div class="content">
                <h4 style="font-weight: 600; margin-bottom: 4px;">Bloxy bot <span style="font-size:0.7rem; color:#6B7280;">Thinking...</span></h4>
                <div style="width: 60%; height: 10px; background: #252525; border-radius: 4px; margin-top: 8px; animation: pulse 1.5s infinite;"></div>
                <div style="width: 80%; height: 10px; background: #252525; border-radius: 4px; margin-top: 6px; animation: pulse 1.5s infinite 0.2s;"></div>
            </div>
        `;
        messageContainer.appendChild(loadingDiv);
        chatAreaWrapper.scrollTo(0, chatAreaWrapper.scrollHeight);

        // --- 3c. Call DeepSeek API Directly ---
        try {
            const response = await fetch("https://api.deepseek.com/chat/completions", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${apiKey}`
                },
                body: JSON.stringify({
                    model: "deepseek-chat",
                    messages: [{ role: "user", content: text }],
                    stream: false
                })
            });

            // Remove loading
            const loader = document.getElementById('loadingIndicator');
            if(loader) loader.remove();

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`DeepSeek Error (${response.status}): ${errorData.error?.message || 'Unknown error'}`);
            }

            const data = await response.json();
            const aiReply = data.choices[0].message.content;
            
            // Add AI response to UI
            addMessage(aiReply, false, "DeepSeek");

        } catch (error) {
            // Remove loading
            const loader = document.getElementById('loadingIndicator');
            if(loader) loader.remove();

            // Handle specific errors
            let errorMsg = error.message;
            if (error.message.includes("401")) {
                errorMsg = "❌ Invalid API Key. Please refresh, enter a new key, and try again.";
                localStorage.removeItem('bloxy_deepseek_key'); // Clear bad key
            } else if (error.message.includes("429")) {
                errorMsg = "⚠️ Rate limit exceeded. Please wait a moment and try again.";
            } else if (error.message.includes("CORS") || error.message.includes("NetworkError")) {
                errorMsg = "❌ Network/CORS error. Since you don't have Python, you must use a browser extension like 'Allow CORS' to bypass this, or use a local backend.";
            }

            addMessage(`❌ ${errorMsg}`, false);
            console.error("AI Error:", error);
        }
    }

    // ============================================================
    // 4. EVENT LISTENERS
    // ============================================================

    // Send Button & Enter Key
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // Action Cards (Pre-fill prompts)
    actionCards.forEach(card => {
        card.addEventListener('click', () => {
            const title = card.querySelector('.card-title')?.innerText || '';
            const sub = card.querySelector('.card-sub')?.innerText || '';
            userInput.value = `${title} ${sub}`;
            sendMessage();
        });
    });

    // ============================================================
    // 5. WELCOME / FIRST RUN CHECK
    // ============================================================
    
    // If no key is saved, prompt user immediately so they are ready
    if (!localStorage.getItem('bloxy_deepseek_key')) {
        setTimeout(() => {
            addMessage("👋 To start chatting, click the input box below and send your first message. You will be prompted for your DeepSeek API key.", false);
        }, 500);
    }
});
