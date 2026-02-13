/**
 * Archive AI Analysis JavaScript
 * Handles AI-powered image analysis for archive items
 */

class ArchiveAnalysis {
    constructor() {
        this.analyzeBtn = document.getElementById('aiAnalyzeBtn');
        this.modal = document.getElementById('aiAnalysisModal');
        this.closeBtn = document.getElementById('closeAnalysisModal');
        this.loading = document.getElementById('aiAnalysisLoading');
        this.result = document.getElementById('aiAnalysisResult');
        this.typeBtns = document.querySelectorAll('.ai-type-btn');

        // Get config from data attributes
        const container = document.getElementById('archiveAnalysisConfig');
        if (!container) return;

        this.archiveId = container.dataset.archiveId;
        this.analyzeUrl = container.dataset.analyzeUrl;

        this.init();
    }

    init() {
        if (!this.analyzeBtn || !this.modal) return;

        this.analyzeBtn.addEventListener('click', () => this.openModal());

        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.closeModal());
        }

        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) this.closeModal();
        });

        this.typeBtns.forEach(btn => {
            btn.addEventListener('click', () => this.analyze(btn.dataset.type));
        });
    }

    getCsrfToken() {
        return document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] || '';
    }

    openModal() {
        this.modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    closeModal() {
        this.modal.classList.remove('active');
        document.body.style.overflow = '';
    }

    async analyze(type) {
        this.loading.classList.remove('hidden');
        this.result.innerHTML = '';

        try {
            const response = await fetch(this.analyzeUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ archive_id: this.archiveId, type: type })
            });

            const data = await response.json();
            this.loading.classList.add('hidden');

            if (data.success) {
                this.result.innerHTML = data.content.replace(/\n/g, '<br>');
            } else {
                this.result.innerHTML = '<p class="text-red-500">' + (data.error || 'Analysis failed. Please try again.') + '</p>';
            }
        } catch (err) {
            this.loading.classList.add('hidden');
            this.result.innerHTML = '<p class="text-red-500">Connection error. Please try again.</p>';
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('aiAnalyzeBtn')) {
        new ArchiveAnalysis();
    }
});
