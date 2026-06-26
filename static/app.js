/**
 * Biney Bot AI - Frontend Core Interaction Script
 * Handles text streaming, dynamic UI rendering, and accessibility tasks.
 */

document.addEventListener("DOMContentLoaded", () => {
    // Core Interface Elements
    const chatInput = document.getElementById("chatInput");
    const sendBtn = document.getElementById("sendBtn");
    const chatContainer = chatInput?.closest('.overflow-y-auto');

    /* ==========================================================================
       1. TEXTAREA AUTOMATIC RESIZING
       ========================================================================== */
    if (chatInput) {
        chatInput.addEventListener("input", function () {
            // Reset height to compute target scroll height accurately
            this.style.height = "auto";
            
            // Apply maximum constraint of 160px, otherwise expand with typing lines
            const dynamicHeight = Math.min(this.scrollHeight, 160);
            this.style.height = `${dynamicHeight}px`;
        });
    }

    /* ==========================================================================
       2. CHAT STREAMING & SYSTEM LOGIC
       ========================================================================== */
    const processUserMessage = () => {
        const queryText = chatInput.value.trim();
        if (!queryText) return;

        // Clear input console box and restore original height state
        chatInput.value = "";
        chatInput.style.height = "auto";

        console.log(`Payload captured successfully: "${queryText}"`);
        
        // Auto-scroll chat area box to show the newest messages seamlessly
        if (chatContainer) {
            chatContainer.scrollTo({
                top: chatContainer.scrollHeight,
                behavior: 'smooth'
            });
        }
        
        // Note: Hook this function directly into your FastAPI backend "/api/chat" endpoint via fetch()
    };

    /* ==========================================================================
       3. EVENT LISTENERS
       ========================================================================== */
    if (sendBtn && chatInput) {
        // Trigger action on mouse click
        sendBtn.addEventListener("click", processUserMessage);

        // Trigger action on Enter key (while allowing linebreaks via Shift + Enter)
        chatInput.addEventListener("keydown", (event) => {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                processUserMessage();
            }
        });
    }

    /* ==========================================================================
       4. INTERACTIVE TOOL TILES HOVER ACTION
       ========================================================================== */
    const widgetTiles = document.querySelectorAll(".grid > div");
    widgetTiles.forEach(tile => {
        tile.addEventListener("click", () => {
            const featureTitle = tile.querySelector("h4")?.textContent || "Feature Route";
            if (chatInput) {
                chatInput.value = `Tell me more details about ${featureTitle}... `;
                chatInput.focus();
                chatInput.dispatchEvent(new Event('input')); // Recalculate input box height
            }
        });
    });
});
