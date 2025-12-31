/**
 * AI Chat JavaScript
 * Handles chat messaging, voice input, and session management
 */

class AIChat {
    constructor(sessionId, endpoints) {
        this.sessionId = sessionId;
        this.endpoints = endpoints;
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];

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
    }

    scrollToBottom() {
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }

    addMessage(content, role) {
        if (this.elements.emptyState) {
            this.elements.emptyState.remove();
        }

        const div = document.createElement('div');
        div.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'}`;
        div.innerHTML = `
            <div class="max-w-[80%] rounded-2xl px-4 py-3 ${role === 'user' ? 'message-user text-white' : 'message-assistant text-dark-brown'}">
                <div class="prose prose-sm ${role === 'user' ? 'prose-invert' : ''}">${this.formatContent(content)}</div>
            </div>
        `;
        this.elements.chatMessages.insertBefore(div, this.elements.typingIndicator);
        this.scrollToBottom();
    }

    formatContent(content) {
        // Convert markdown links to HTML
        content = content.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="underline hover:text-vintage-gold">$1</a>');
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

// Export for use
window.AIChat = AIChat;
