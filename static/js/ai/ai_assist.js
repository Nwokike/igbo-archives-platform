/**
 * AI Assist Logic for Insights Editor
 */

(function () {
    let currentMode = 'draft';
    const modal = document.getElementById('aiAssistModal');

    // Check URL for archive_id to provide context
    const urlParams = new URLSearchParams(window.location.search);
    const archiveId = urlParams.get('archive_id');

    window.openAiModal = function () {
        if (modal) {
            modal.classList.add('active');
            // Reset state
            document.getElementById('aiPrompt').value = '';
            document.getElementById('aiLoading').classList.add('hidden');

            // Default to draft or refine if selection exists
            // TODO: If we could access Editor.js selection, we would switch to 'refine'.
            // For now, default to draft.
            setAiMode('draft');
        }
    };

    window.closeAiModal = function () {
        if (modal) modal.classList.remove('active');
    };

    window.setAiMode = function (mode) {
        currentMode = mode;
        const btns = document.querySelectorAll('.ai-mode-btn');
        btns.forEach(b => {
            if (b.dataset.mode === mode) b.classList.add('active');
            else b.classList.remove('active');
        });

        const contextSection = document.getElementById('aiContextSection');
        if (mode === 'refine') {
            contextSection.classList.remove('hidden');
            // Mock functionality for now as getting selection from Editor.js externally is tricky 
            // without custom tool integration. 
            // Users will paste content to refine in Prompt for now or we instruct them.
            document.getElementById('aiSelectedText').textContent = "Select text in the editor before opening (Coming Soon - Describe what to refine below)";
        } else {
            contextSection.classList.add('hidden');
        }
    };

    window.generateAiContent = async function () {
        const prompt = document.getElementById('aiPrompt').value;
        if (!prompt && currentMode === 'draft') return;

        const loading = document.getElementById('aiLoading');
        loading.classList.remove('hidden');

        try {
            const response = await fetch('/ai/generate-insight/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    topic: currentMode === 'draft' ? prompt : '',
                    instruction: prompt,
                    // If we had archive context
                    archive_context: archiveId ? `Archive ID: ${archiveId}` : ''
                })
            });

            const data = await response.json();

            if (data.success) {
                // Insert content
                // We'll insert as a text block
                const editor = window.IgboEditor && window.IgboEditor.editor;
                if (editor) {
                    const blocks = data.content.split('\n\n').filter(p => p.trim());

                    // Simple insertion
                    // Ideally check if editor is empty or append
                    const count = editor.blocks.getBlocksCount();

                    for (let text of blocks) {
                        editor.blocks.insert('paragraph', { text: text }, {}, count, false);
                    }

                    closeAiModal();

                    // Show success toast
                    // Assuming showToast exists or generic alert
                    // alert('Content generated!');
                }
            } else {
                if (window.showToast) {
                    window.showToast('AI Error: ' + data.error, 'error');
                } else {
                    console.error('AI Error: ' + data.error);
                }
            }
        } catch (e) {
            console.error(e);
            if (window.showToast) {
                window.showToast('Error connecting to AI service', 'error');
            }
        } finally {
            loading.classList.add('hidden');
        }
    };
})();
