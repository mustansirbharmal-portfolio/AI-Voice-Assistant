document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('voice-form');
    const textInput = document.getElementById('text-input');
    const voiceButton = document.getElementById('voice-button');
    const chatContainer = document.getElementById('chat-container');

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const message = textInput.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessageToChat('You', message);
        
        // Clear input
        textInput.value = '';

        try {
            const formData = new FormData();
            formData.append('message', message);

            const response = await fetch('/process_input', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            // Add bot response to chat
            addMessageToChat('Assistant', data.response);
            
        } catch (error) {
            console.error('Error:', error);
            addMessageToChat('Assistant', 'Sorry, there was an error processing your request.');
        }
    });

    // Voice recognition setup
    let recognition = null;
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onresult = function(event) {
            const text = event.results[0][0].transcript;
            textInput.value = text;
            voiceButton.classList.remove('recording');
            form.dispatchEvent(new Event('submit'));
        };

        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            voiceButton.classList.remove('recording');
        };
    }

    // Voice button click handler
    voiceButton.addEventListener('click', function() {
        if (recognition) {
            voiceButton.classList.add('recording');
            recognition.start();
        } else {
            alert('Speech recognition is not supported in your browser.');
        }
    });

    function addMessageToChat(sender, message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message-container';
        messageDiv.innerHTML = `
            <div class="${sender.toLowerCase()}-message">
                <strong>${sender}:</strong> ${message}
            </div>
        `;
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
});
