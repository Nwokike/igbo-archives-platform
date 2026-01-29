/**
 * AI Chat JavaScript
 * Handles chat messaging, voice input (STT), text-to-speech (TTS), and session management
 */

class AIChat {
    constructor(sessionId, endpoints) {
        this.sessionId = sessionId;
        this.endpoints = endpoints;
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isSpeaking = false;
        this.speechSynthesis = window.speechSynthesis;

        this.elements = {
            chatMessages: document.getElementById('chatMessages'),
            chatForm: document.getElementById('chatForm'),
            messageInput: document.getElementById('messageInput'),
            sendBtn: document.getElementById('sendBtn'),
            voiceBtn: document.getElementById('voiceBtn'),
            typingIndicator: document.getElementById('typingIndicator'),
            emptyState: document.getElementById('emptyState'),
            sessionTitle: document.getElementById('sessionTitle'),
        };

        this.init();
    }

    init() {
        this.elements.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));
        this.elements.voiceBtn.addEventListener('click', () => this.toggleRecording());
        this.scrollToBottom();
        this.elements.messageInput.focus();

        // Add TTS button event delegation
        this.elements.chatMessages.addEventListener('click', (e) => {
            const ttsBtn = e.target.closest('.tts-btn');
            if (ttsBtn) {
                this.speakText(ttsBtn);
            }
        });
    }

    scrollToBottom() {
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }

    addMessage(content, role) {
        if (this.elements.emptyState) {
            this.elements.emptyState.remove();
        }

        const messageId = Date.now();
        const div = document.createElement('div');
        div.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'}`;

        const ttsButton = role === 'assistant' && this.speechSynthesis ?
            `<button class="tts-btn mt-2 text-xs text-vintage-beaver hover:text-vintage-gold transition-colors" data-msg-id="${messageId}" title="Listen">
                <i class="fas fa-volume-up"></i> Listen
            </button>` : '';

        div.innerHTML = `
            <div class="max-w-[85%] rounded-xl px-3.5 py-2.5 ${role === 'user' ? 'message-user text-white' : 'message-assistant text-dark-brown'}">
                <div class="prose prose-sm ${role === 'user' ? 'prose-invert' : ''} text-sm message-content">${this.formatContent(content)}</div>
                ${ttsButton}
            </div>
        `;
        div.dataset.rawContent = content;
        this.elements.chatMessages.insertBefore(div, this.elements.typingIndicator);
        this.scrollToBottom();
    }

    formatContent(content) {
        // Convert markdown links to HTML
        content = content.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="underline hover:text-vintage-gold">$1</a>');
        // Convert newlines to breaks
        content = content.replace(/\n/g, '<br>');
        return content;
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
            document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
    }

    showTyping() {
        this.elements.typingIndicator.classList.remove('hidden');
        this.elements.typingIndicator.classList.add('flex');
        this.scrollToBottom();
    }

    hideTyping() {
        this.elements.typingIndicator.classList.add('hidden');
        this.elements.typingIndicator.classList.remove('flex');
    }

    // Text-to-Speech using Web Speech API (client-side, no storage)
    speakText(button) {
        if (this.isSpeaking) {
            this.speechSynthesis.cancel();
            this.isSpeaking = false;
            button.innerHTML = '<i class="fas fa-volume-up"></i> Listen';
            return;
        }

        const messageDiv = button.closest('.flex');
        const rawContent = messageDiv?.dataset.rawContent ||
            button.parentElement.querySelector('.message-content')?.textContent || '';

        if (!rawContent) return;

        const utterance = new SpeechSynthesisUtterance(rawContent);
        utterance.lang = 'en-NG'; // Nigerian English (closest to Igbo region)
        utterance.rate = 0.9;
        utterance.pitch = 1;

        utterance.onstart = () => {
            this.isSpeaking = true;
            button.innerHTML = '<i class="fas fa-stop"></i> Stop';
        };

        utterance.onend = () => {
            this.isSpeaking = false;
            button.innerHTML = '<i class="fas fa-volume-up"></i> Listen';
        };

        utterance.onerror = () => {
            this.isSpeaking = false;
            button.innerHTML = '<i class="fas fa-volume-up"></i> Listen';
        };

        this.speechSynthesis.speak(utterance);
    }

    async handleSubmit(e) {
        e.preventDefault();

        const message = this.elements.messageInput.value.trim();
        if (!message) return;

        this.elements.messageInput.value = '';
        this.elements.sendBtn.disabled = true;

        this.addMessage(message, 'user');
        this.showTyping();

        try {
            const response = await fetch(this.endpoints.send, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId,
                }),
            });

            const data = await response.json();
            this.hideTyping();

            if (data.success) {
                this.addMessage(data.message, 'assistant');
                if (data.session_title && this.elements.sessionTitle) {
                    this.elements.sessionTitle.textContent = data.session_title;
                }
            } else {
                this.addMessage(data.error || data.message || 'Something went wrong. Please try again.', 'assistant');
            }
        } catch (error) {
            this.hideTyping();
            console.error('Chat error:', error);
            this.addMessage('Connection error. Please check your internet and try again.', 'assistant');
        }

        this.elements.sendBtn.disabled = false;
        this.elements.messageInput.focus();
    }

    async toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            this.startRecording();
        }
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (e) => this.audioChunks.push(e.data);
            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                await this.transcribeAudio(audioBlob);
                stream.getTracks().forEach(track => track.stop());
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            this.elements.voiceBtn.classList.add('recording', 'text-red-500', 'border-red-500');
            this.elements.voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
        } catch (err) {
            alert('Could not access microphone. Please allow microphone access.');
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.elements.voiceBtn.classList.remove('recording', 'text-red-500', 'border-red-500');
            this.elements.voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        }
    }

    async transcribeAudio(audioBlob) {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');

        this.elements.voiceBtn.disabled = true;
        this.elements.voiceBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            const response = await fetch(this.endpoints.transcribe, {
                method: 'POST',
                headers: { 'X-CSRFToken': this.getCsrfToken() },
                body: formData
            });

            const data = await response.json();
            if (data.success && data.text) {
                this.elements.messageInput.value = data.text;
                this.elements.messageInput.focus();
            }
        } catch (err) {
            console.error('Transcription error:', err);
        }

        this.elements.voiceBtn.disabled = false;
        this.elements.voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    }

    async deleteSession() {
        if (!confirm('Delete this conversation?')) return;

        try {
            await fetch(this.endpoints.delete, {
                method: 'POST',
                headers: { 'X-CSRFToken': this.getCsrfToken() },
            });
            window.location.href = this.endpoints.home;
        } catch (error) {
            alert('Could not delete conversation');
        }
    }
}

// Auto-initialize from data attributes
document.addEventListener('DOMContentLoaded', () => {
    const config = document.getElementById('aiChatConfig');
    if (!config) return;

    const sessionId = parseInt(config.dataset.sessionId, 10);
    const endpoints = {
        send: config.dataset.sendUrl,
        transcribe: config.dataset.transcribeUrl,
        delete: config.dataset.deleteUrl,
        home: config.dataset.homeUrl
    };

    const chat = new AIChat(sessionId, endpoints);

    const deleteBtn = document.getElementById('deleteBtn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => chat.deleteSession());
    }
});

// Export for backward compatibility
window.AIChat = AIChat;

