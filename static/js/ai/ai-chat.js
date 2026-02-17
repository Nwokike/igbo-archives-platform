/**
 * AI Chat JavaScript
 * Handles chat messaging and Server-Side Text-to-Speech (YarnGPT/Gemini)
 */

class AIChat {
    constructor(sessionId, endpoints) {
        this.sessionId = sessionId;
        this.endpoints = endpoints;
        this.currentAudio = null; // Store current audio object
        this.isLoadingAudio = false;
        this.history = []; // Client-side conversation history
        this.STORAGE_KEY = 'igbo_ai_chat_history';

        this.elements = {
            chatMessages: document.getElementById('chatMessages'),
            chatForm: document.getElementById('chatForm'),
            messageInput: document.getElementById('messageInput'),
            sendBtn: document.getElementById('sendBtn'),
            typingIndicator: document.getElementById('typingIndicator'),
            emptyState: document.getElementById('emptyState'),
            sessionTitle: document.getElementById('sessionTitle'),
        };

        if (this.elements.chatForm) {
            this.init();
        }
    }

    init() {
        this.loadHistory();
        this.renderHistory();

        this.elements.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));
        this.scrollToBottom();
        this.elements.messageInput.focus();

        // Add TTS button event delegation
        this.elements.chatMessages.addEventListener('click', (e) => {
            const ttsBtn = e.target.closest('.tts-btn');
            if (ttsBtn) {
                this.handleTTSClick(ttsBtn);
            }
        });
    }

    scrollToBottom() {
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }

    addMessage(content, role, save = true) {
        if (this.elements.emptyState) {
            this.elements.emptyState.remove();
        }

        if (save) {
            this.history.push({ role, content });
            this.saveHistory();
        }

        const messageId = Date.now();
        const div = document.createElement('div');
        div.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'}`;

        // Only show Listen button for assistant
        // FIXED: Added <span> around text to prevent "setting properties of null" error
        const ttsButton = role === 'assistant' ?
            `<button class="tts-btn mt-2 text-xs text-vintage-beaver hover:text-vintage-gold transition-colors flex items-center gap-1" data-msg-id="${messageId}" title="Listen to response">
                <i class="fas fa-volume-up"></i> <span>Listen</span>
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
        if (typeof marked !== 'undefined') {
            try {
                // Use marked.js for full markdown rendering
                return marked.parse(content, {
                    breaks: true,
                    gfm: true
                });
            } catch (err) {
                console.error('Markdown parsing error:', err);
            }
        }

        // Fallback for basic links and line breaks if marked is not loaded
        content = content.replace(/\[([^\]]+)\]\(([^)]+)\)/g, function (match, text, url) {
            if (isSafeUrl(url)) {
                return '<a href="' + escapeHtml(url) + '" target="_blank">' + escapeHtml(text) + '</a>';
            }
            return escapeHtml(text);
        });
        return content.replace(/\n/g, '<br>');
    }

    getCsrfToken() {
        return getCookie('csrftoken');
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

    // New Server-Side TTS Logic (Replaces old speakText)
    async handleTTSClick(button) {
        const icon = button.querySelector('i');
        const textSpan = button.querySelector('span');
        const messageDiv = button.closest('.flex');

        // 1. If currently playing this exact message, stop it.
        if (this.currentAudio && this.currentAudio.dataset.btnId === button.dataset.msgId) {
            this.stopAudio();
            return;
        }

        // 2. If playing something else, stop that first.
        if (this.currentAudio) {
            this.stopAudio();
        }

        // 3. Get text content
        const rawContent = messageDiv?.dataset.rawContent ||
            button.parentElement.querySelector('.message-content')?.textContent || '';

        if (!rawContent || this.isLoadingAudio) return;

        // 4. Loading State
        this.isLoadingAudio = true;
        const originalIconClass = icon.className;
        icon.className = 'fas fa-spinner fa-spin';
        if (textSpan) textSpan.textContent = 'Wait... (up to 30s)';
        button.disabled = true;

        try {
            // 5. Call Server TTS Endpoint
            const response = await fetch('/ai/tts/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),
                },
                body: JSON.stringify({
                    text: rawContent,
                    language: 'default' // This tells backend to use default YarnGPT voice
                }),
            });

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'TTS generation failed');
            }

            // 6. Play Audio
            this.currentAudio = new Audio(data.url);
            this.currentAudio.dataset.btnId = button.dataset.msgId;

            // UI updates during playback
            this.currentAudio.addEventListener('play', () => {
                icon.className = 'fas fa-stop';
                if (textSpan) textSpan.textContent = 'Stop';
                button.disabled = false;
                this.isLoadingAudio = false;
            });

            this.currentAudio.addEventListener('ended', () => {
                this.resetButton(button);
                this.currentAudio = null;
            });

            this.currentAudio.addEventListener('error', () => {
                console.error('Audio playback error');
                this.resetButton(button);
                this.currentAudio = null;
                alert('Could not play audio.');
            });

            await this.currentAudio.play();

        } catch (error) {
            console.error('TTS Error:', error);
            this.resetButton(button, originalIconClass);
            this.isLoadingAudio = false;
            // Simple notification if global toast isn't available
            if (window.showToast) {
                window.showToast('Audio generation failed', 'error');
            } else {
                alert('Failed to generate audio. Please try again.');
            }
        }
    }

    stopAudio() {
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;

            // Find the button associated with this audio and reset it
            const btnId = this.currentAudio.dataset.btnId;
            const btn = document.querySelector(`.tts-btn[data-msg-id="${btnId}"]`);
            if (btn) this.resetButton(btn);

            this.currentAudio = null;
        }
    }

    loadHistory() {
        try {
            const stored = sessionStorage.getItem(this.STORAGE_KEY);
            this.history = stored ? JSON.parse(stored) : [];
        } catch (e) {
            console.error('Failed to load history:', e);
            this.history = [];
        }
    }

    saveHistory() {
        try {
            sessionStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.history));
        } catch (e) {
            console.error('Failed to save history:', e);
        }
    }

    renderHistory() {
        if (this.history.length > 0 && this.elements.emptyState) {
            this.elements.emptyState.remove();
        }
        this.history.forEach(msg => {
            this.addMessage(msg.content, msg.role, false);
        });
    }

    resetButton(button, iconClass = 'fas fa-volume-up') {
        const icon = button.querySelector('i');
        const textSpan = button.querySelector('span');
        if (icon) icon.className = iconClass;
        if (textSpan) textSpan.textContent = 'Listen';
        button.disabled = false;
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
                    history: this.history.slice(0, -1), // Send history EXCEPT the message we just added
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

    async deleteSession() {
        if (!confirm('Clear this conversation?')) return;
        // Stateless: just clear client-side history
        this.history = [];
        sessionStorage.removeItem(this.STORAGE_KEY);
        window.location.reload();
    }
}

// Auto-initialize from data attributes
document.addEventListener('DOMContentLoaded', () => {
    const config = document.getElementById('aiChatConfig');
    if (!config) return;

    const sessionId = parseInt(config.dataset.sessionId, 10);
    const endpoints = {
        send: config.dataset.sendUrl,
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