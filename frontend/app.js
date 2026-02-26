const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const resourceList = document.getElementById('resource-list');

// Auto-focus input
userInput.focus();

// Event Listeners
sendBtn.addEventListener('click', () => sendMessage(false));
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage(false);
});

let currentSessionId = null;
let isListening = false;
let recognition = null;

// Initialize Speech Recognition
if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
        isListening = true;
        document.getElementById('mic-btn').classList.add('bg-red-500', 'animate-pulse');
        document.getElementById('mic-btn').classList.remove('bg-slate-700');
    };

    recognition.onend = () => {
        isListening = false;
        document.getElementById('mic-btn').classList.remove('bg-red-500', 'animate-pulse');
        document.getElementById('mic-btn').classList.add('bg-slate-700');
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        userInput.value = transcript;
        sendMessage(true); // Pass true for voice input
    };
}

function toggleVoice() {
    if (!recognition) {
        alert("Voice input is not supported in this browser.");
        return;
    }
    if (isListening) {
        recognition.stop();
    } else {
        recognition.start();
    }
}

async function sendMessage(isVoice = false) {
    const message = userInput.value.trim();
    if (!message) return;

    // Clear input
    userInput.value = '';

    // Add User Message
    appendMessage('user', message);

    // Show Loading Indicator
    const loadingId = showLoading();

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                session_id: currentSessionId
            })
        });

        const data = await response.json();
        currentSessionId = data.session_id; // Update session ID

        // Remove Loading
        removeLoading(loadingId);

        // Add AI Message
        appendMessage('assistant', data.response);

        // Speak Response ONLY if input was voice
        if (isVoice) {
            speakResponse(data.response);
        }

        // Update Resources if any
        if (data.resources && data.resources.length > 0) {
            updateResources(data.resources, data.detected_category);
        }

    } catch (error) {
        removeLoading(loadingId);
        appendMessage('assistant', "I'm having trouble connecting to my brain right now. Please try again.");
        console.error('Error:', error);
    }
}

function speakResponse(text) {
    if ('speechSynthesis' in window) {
        // Cancel any ongoing speech
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
    }
}

function startNewChat() {
    if (confirm("Are you sure you want to start a new chat? Current history will be cleared from view.")) {
        currentSessionId = null; // Reset session ID to force backend to create new one
        chatContainer.innerHTML = ''; // Clear chat UI
        resourceList.innerHTML = `
            <div class="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50 text-center text-slate-400 text-sm">
                Start chatting to discover resources...
            </div>
        `;
        // Add welcome message again
        const welcomeDiv = document.createElement('div');
        welcomeDiv.className = "flex gap-4 max-w-3xl mx-auto";
        welcomeDiv.innerHTML = `
            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-teal-400 to-blue-500 flex-shrink-0 flex items-center justify-center text-white">
                <i class="fas fa-robot"></i>
            </div>
            <div class="glass-panel p-4 rounded-2xl rounded-tl-none text-slate-200 max-w-xl">
                <p>Hello. I am Serenity, your mental health companion.</p>
                <p class="mt-2 text-sm text-slate-400">I use advanced Data Structures to understand you better. How are you feeling today?</p>
            </div>
        `;
        chatContainer.appendChild(welcomeDiv);
    }
}

async function downloadReport() {
    if (!currentSessionId) {
        alert("Please start a conversation first.");
        return;
    }

    const btn = document.getElementById('download-btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';

    try {
        const response = await fetch(`/report/${currentSessionId}`);
        if (!response.ok) throw new Error('Report generation failed');

        const data = await response.json();
        window.open(data.report_url, '_blank');

    } catch (error) {
        alert("Could not generate report. Please try again.");
        console.error(error);
    } finally {
        btn.innerHTML = originalText;
    }
}

function appendMessage(role, text) {
    const isUser = role === 'user';
    const div = document.createElement('div');
    div.className = `flex gap-4 max-w-3xl mx-auto ${isUser ? 'flex-row-reverse' : ''} animate-fade-in`;

    const avatar = isUser
        ? `<div class="w-10 h-10 rounded-full bg-slate-700 flex-shrink-0 flex items-center justify-center text-slate-300"><i class="fas fa-user"></i></div>`
        : `<div class="w-10 h-10 rounded-full bg-gradient-to-br from-teal-400 to-blue-500 flex-shrink-0 flex items-center justify-center text-white"><i class="fas fa-robot"></i></div>`;

    const bubbleClass = isUser
        ? 'bg-blue-600 text-white rounded-tr-none'
        : 'glass-panel text-slate-200 rounded-tl-none';

    div.innerHTML = `
        ${avatar}
        <div class="${bubbleClass} p-4 rounded-2xl max-w-xl message-bubble shadow-lg">
            <p class="leading-relaxed">${formatText(text)}</p>
        </div>
    `;

    chatContainer.appendChild(div);
    scrollToBottom();
}

function showLoading() {
    const id = 'loading-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = `flex gap-4 max-w-3xl mx-auto`;
    div.innerHTML = `
        <div class="w-10 h-10 rounded-full bg-gradient-to-br from-teal-400 to-blue-500 flex-shrink-0 flex items-center justify-center text-white"><i class="fas fa-robot"></i></div>
        <div class="glass-panel p-4 rounded-2xl rounded-tl-none text-slate-200 flex items-center gap-1">
            <div class="w-2 h-2 bg-slate-400 rounded-full typing-dot"></div>
            <div class="w-2 h-2 bg-slate-400 rounded-full typing-dot"></div>
            <div class="w-2 h-2 bg-slate-400 rounded-full typing-dot"></div>
        </div>
    `;
    chatContainer.appendChild(div);
    scrollToBottom();
    return id;
}

function removeLoading(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function updateResources(resources, category) {
    resourceList.innerHTML = ''; // Clear current

    if (category) {
        const header = document.createElement('div');
        header.className = 'mb-4 px-2';
        header.innerHTML = `<span class="text-xs font-bold text-teal-400 uppercase tracking-wider">Detected: ${category}</span>`;
        resourceList.appendChild(header);
    }

    resources.forEach(res => {
        const card = document.createElement('a');
        card.href = res.link || '#';
        card.target = "_blank";
        card.className = 'block p-4 rounded-xl bg-slate-800/50 border border-slate-700/50 hover:bg-slate-700/50 transition-colors group';
        card.innerHTML = `
            <h4 class="font-semibold text-slate-200 group-hover:text-teal-400 transition-colors mb-1">${res.title}</h4>
            <p class="text-xs text-slate-400">${res.desc}</p>
        `;
        resourceList.appendChild(card);
    });
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function formatText(text) {
    // Simple formatting for newlines
    return text.replace(/\n/g, '<br>');
}
