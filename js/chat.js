/**
 * chat.js
 *
 * Handles the chat interface interactions for CrossDebate.
 * - Captures user input.
 * - Sends messages to the backend API via sendMessage (defined in HTML).
 * - Displays user messages and model responses.
 * - Manages loading/typing indicators.
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log("Chat script loaded.");

    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const chatOutput = document.getElementById('chat-output');
    const modelSelect = document.getElementById('modelSelect'); // Needed to check if a model is selected

    if (!chatInput || !sendButton || !chatOutput || !modelSelect) {
        console.error("Chat UI elements not found. Chat functionality may be limited.");
        return; // Exit if essential elements are missing
    }

    /**
     * Appends a message to the chat output area.
     * @param {string} message - The message text.
     * @param {string} sender - 'user' or 'model'.
     */
    const displayMessage = (message, sender) => {
        if (!chatOutput) return;

        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', sender); // Add 'chat-message' and sender-specific class

        // Basic Markdown-like formatting (bold, italic) - can be expanded
        message = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'); // Bold
        message = message.replace(/\*(.*?)\*/g, '<em>$1</em>');     // Italic

        // Handle newlines (convert \n to <br>)
        messageElement.innerHTML = message.replace(/\n/g, '<br>');

        chatOutput.appendChild(messageElement);

        // Scroll to the bottom of the chat output
        chatOutput.scrollTop = chatOutput.scrollHeight;
    };

    /**
     * Displays a temporary typing indicator for the model.
     * @returns {HTMLElement} The indicator element.
     */
    const showTypingIndicator = () => {
        if (!chatOutput) return null;
        const indicator = document.createElement('div');
        indicator.classList.add('chat-message', 'model', 'typing-indicator');
        indicator.innerHTML = `<span></span><span></span><span></span>`; // Simple CSS dots animation
        chatOutput.appendChild(indicator);
        chatOutput.scrollTop = chatOutput.scrollHeight;

        // Add CSS for the typing indicator (could also be in style.css)
        const styleId = 'typing-indicator-style';
        if (!document.getElementById(styleId)) {
            const style = document.createElement('style');
            style.id = styleId;
            style.textContent = `
                .typing-indicator span {
                    height: 8px;
                    width: 8px;
                    background-color: var(--nav-text); /* Use theme color */
                    border-radius: 50%;
                    display: inline-block;
                    margin: 0 2px;
                    animation: bounce 1.4s infinite ease-in-out both;
                }
                .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
                .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
                @keyframes bounce {
                    0%, 80%, 100% { transform: scale(0); }
                    40% { transform: scale(1.0); }
                }
            `;
            document.head.appendChild(style);
        }
        return indicator;
    };

    /**
     * Removes the typing indicator.
     * @param {HTMLElement} indicator - The indicator element to remove.
     */
    const removeTypingIndicator = (indicator) => {
        if (indicator && indicator.parentNode) {
            indicator.remove();
        }
    };

    /**
     * Handles sending the message from the input field.
     */
    const handleSendMessage = async () => {
        const message = chatInput.value.trim();
        const selectedModel = modelSelect.value;

        if (!selectedModel) {
            // Use the showNotification function defined in the HTML/interactivity.js
            if (typeof showNotification === 'function') {
                showNotification('Por favor, selecione um modelo GGUF antes de enviar uma mensagem.', 'warning');
            } else {
                alert('Por favor, selecione um modelo GGUF.');
            }
            return;
        }

        if (message) {
            // 1. Display user message
            displayMessage(message, 'user');

            // 2. Clear input field
            chatInput.value = '';
            chatInput.focus(); // Keep focus on input

            // 3. Show typing indicator
            const typingIndicator = showTypingIndicator();

            // 4. Send message to backend (using function from index.html)
            // Ensure sendMessage is globally available or imported if using modules
            if (typeof sendMessage === 'function') {
                const responseData = await sendMessage(message);

                // 5. Remove typing indicator
                removeTypingIndicator(typingIndicator);

                // 6. Handle response
                if (responseData && responseData.response) {
                    displayMessage(responseData.response, 'model');

                    // 7. (Optional) Trigger HoT update if data is present
                    if (responseData.hotUpdate && typeof updateHypergraph === 'function') {
                        console.log("HoT update received, triggering visualization update.");
                        updateHypergraph(responseData.hotUpdate); // Assumes updateHypergraph exists in hypergraph_interaction.js
                    } else if (responseData.hotUpdate) {
                        console.warn("HoT update data received, but updateHypergraph function not found.");
                    }

                } else if (responseData && responseData.error) {
                    // Display error message from backend in chat
                    displayMessage(`Erro do modelo: ${responseData.error}`, 'model error'); // Add an 'error' class for styling
                } else if (!responseData) {
                    // Network or other error handled by sendMessage, notification already shown.
                    // Optionally display a generic error message in chat too.
                    // displayMessage("Desculpe, não foi possível obter uma resposta.", 'model error');
                }
            } else {
                console.error("sendMessage function is not defined globally or not imported.");
                removeTypingIndicator(typingIndicator);
                 displayMessage("Erro: Função de envio não encontrada.", 'model error');
            }
        }
    };

    // --- Event Listeners ---

    // Send on button click
    sendButton.addEventListener('click', handleSendMessage);

    // Send on Enter key press in the input field
    chatInput.addEventListener('keypress', (event) => {
        // Check if Enter key was pressed (and not Shift+Enter for newline)
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault(); // Prevent default form submission or newline
            handleSendMessage();
        }
    });

    console.log("Chat listeners added.");

}); // End DOMContentLoaded
