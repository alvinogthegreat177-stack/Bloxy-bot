document.addEventListener('DOMContentLoaded', () => {
    const sendBtn = document.getElementById('sendBtn');
    const userInput = document.getElementById('userInput');
    const messageContainer = document.getElementById('messageContainer');
    const chatAreaWrapper = document.getElementById('chatAreaWrapper');
    const welcomeMessage = document.getElementById('welcomeMessage');

    // 1. Add message to UI
    function addMessage(text, isUser, provider = null) {
        if (welcomeMessage && !isUser) welcomeMessage.style.display = 'none';

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
        const avatarIcon = isUser ? 'fa-user' : 'fa-robot';
        const name = isUser ? 'You' : 'Bloxy bot';

        let formattedText = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" style="color: #F59E0B;">$1</a>')
            .replace(/\n/g, '<br>');

        messageDiv.innerHTML = `
            <div class="avatar" style="background: ${isUser ? '#F59E0B' : '#252525'}; color: ${isUser ? '#0E0E0E' : '#FFFFFF'};">
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
        chatAreaWrapper.scrollTo(0, chatAreaWrapper.scrollHeight);
    }

    // 2. Send message to Claude's FastAPI backend
    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        userInput.value = '';
        addMessage(text, true);

        // Loading skeleton
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'loadingIndicator';
        loadingDiv.className = 'message ai-message';
        loadingDiv.innerHTML = `
            <div class="avatar" style="background: #252525;"><i class="fa-solid fa-robot"></i></div>
            <div class="content"><h4>Bloxy bot <span style="font-size:0.7rem; color:#6B7280;">Thinking...</span></h4></div>
        `;
        messageContainer.appendChild(loadingDiv);
        chatAreaWrapper.scrollTo(0, chatAreaWrapper.scrollHeight);

        try {
            // Match Claude's exact payload structure
            const response = await fetch('http://127.0.0.1:8000/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: [{ role: "user", content: text }],
                    model: "deepseek-chat", // Default model
                    provider: "deepseek",   // Default provider
                    stream: true
                })
            });

            // Handle Streaming Response
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let aiText = "";

            document.getElementById('loadingIndicator').remove();

            // Create a placeholder message for the streaming text
            const placeholderDiv = document.createElement('div');
            placeholderDiv.className = 'message ai-message';
            placeholderDiv.innerHTML = `
                <div class="avatar" style="background: #252525;"><i class="fa-solid fa-robot"></i></div>
                <div class="content"><h4>Bloxy bot</h4><p id="streamText"></p></div>
            `;
            messageContainer.appendChild(placeholderDiv);

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ') && line !== 'data: [DONE]') {
                        try {
                            const jsonData = JSON.parse(line.substring(6));
                            const delta = jsonData?.choices?.[0]?.delta?.content;
                            if (delta) {
                                aiText += delta;
                                document.getElementById('streamText').innerHTML = aiText.replace(/\n/g, '<br>');
                                chatAreaWrapper.scrollTo(0, chatAreaWrapper.scrollHeight);
                            }
                        } catch (e) { /* ignore parsing errors */ }
                    }
                }
            }

        } catch (error) {
            const loader = document.getElementById('loadingIndicator');
            if(loader) loader.remove();
            addMessage(`❌ System error: ${error.message}`, false);
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});
