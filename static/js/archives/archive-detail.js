/**
 * JavaScript for Archive Detail page.
 * Handles Swiper initialization, community note creation, and note editing.
 */

document.addEventListener('DOMContentLoaded', function () {
    // Media Swiper Initialization
    if (document.querySelector('.swiper-slide')) {
        const swiper = new Swiper('.archive-swiper', {
            loop: false,
            autoHeight: true,
            spaceBetween: 20,
            navigation: { nextEl: '.swiper-button-next', prevEl: '.swiper-button-prev' },
            pagination: { el: '.swiper-pagination', clickable: true, dynamicBullets: true },
        });
    }

    // Community Notes Editor Logic (Add Note)
    const addBtn = document.getElementById('addNoteBtn');
    const cancelBtn = document.getElementById('cancelNoteBtn');
    const form = document.getElementById('noteForm');
    let editorInstance = null;

    if (addBtn && form) {
        addBtn.addEventListener('click', () => {
            form.classList.remove('hidden');
            addBtn.classList.add('hidden');

            if (!editorInstance) {
                editorInstance = window.IgboEditor.initSimple('editorjs-note', {
                    placeholder: 'Write your context, history, or corrections here...',
                    autofocus: true
                });

                setTimeout(function () {
                    if (window.EditorToolbar && editorInstance) {
                        window.EditorToolbar.init(editorInstance, 'editorjs-note', { hasImageTool: false });
                    }
                }, 300);
            }
        });

        cancelBtn.addEventListener('click', () => {
            form.classList.add('hidden');
            addBtn.classList.remove('hidden');
        });

        form.addEventListener('submit', function (e) {
            e.preventDefault();
            editorInstance.save().then((outputData) => {
                document.getElementById('id_content_json_note').value = JSON.stringify(outputData);
                this.submit();
            }).catch((error) => {
                console.error('Saving failed: ', error);
            });
        });
    }

    // Generic Modal and Form Logic
    const editNoteModal = document.getElementById('editNoteModal');
    const editForm = document.getElementById('editNoteForm');
    const editModalTitle = editNoteModal ? editNoteModal.querySelector('h3') : null;
    const saveEditBtn = document.getElementById('saveEditNoteBtn');
    let editEditorInstance = null;

    // Helper to hide modal
    const hideEditModal = () => {
        if (editNoteModal) {
            editNoteModal.classList.remove('active');
            document.body.classList.remove('overflow-hidden');
            setTimeout(() => editNoteModal.classList.add('hidden'), 300);
        }
    };

    if (document.getElementById('closeEditNoteModal')) {
        document.getElementById('closeEditNoteModal').addEventListener('click', hideEditModal);
    }
    if (document.getElementById('cancelEditNoteBtn')) {
        document.getElementById('cancelEditNoteBtn').addEventListener('click', hideEditModal);
    }

    // Event Delegation for Edit and Suggest buttons
    document.addEventListener('click', async (e) => {
        const editBtn = e.target.closest('.edit-note-btn');
        const suggestBtn = e.target.closest('.suggest-edit-btn');
        const btn = editBtn || suggestBtn;

        if (!btn) return;

        console.log('Note action button clicked:', btn.className);

        const noteId = btn.getAttribute('data-note-id');
        const editUrl = btn.getAttribute('data-edit-url') || (noteId ? `/archives/note/${noteId}/suggest/` : null);
        const dataScript = document.getElementById(noteId);

        if (!editNoteModal || !editForm) {
            console.warn('Edit modal or form not found');
            return;
        }

        // Update modal title based on action
        if (editModalTitle) {
            editModalTitle.innerHTML = editBtn
                ? '<i class="fas fa-edit text-accent mr-2"></i>Edit Community Note'
                : '<i class="fas fa-lightbulb text-vintage-gold mr-2"></i>Suggest Edit';
        }

        let content = {};
        if (dataScript) {
            try {
                content = JSON.parse(dataScript.textContent);
                if (typeof content === 'string') content = JSON.parse(content);
            } catch (err) {
                console.error('Error parsing note JSON:', err);
            }
        }

        // Show modal - using .active for compatibility with modal.css
        editNoteModal.classList.remove('hidden');
        // Force a reflow before adding .active to trigger transition
        void editNoteModal.offsetWidth;
        editNoteModal.classList.add('active');
        document.body.classList.add('overflow-hidden');

        editForm.action = editUrl;

        try {
            if (!editEditorInstance) {
                // Initialize Editor.js
                editEditorInstance = window.IgboEditor.initSimple('editorjs-edit-note', {
                    placeholder: 'Write your context, history, or corrections here...',
                    data: content,
                    autofocus: true,
                    onReady: () => {
                        if (window.EditorToolbar && editEditorInstance) {
                            window.EditorToolbar.init(editEditorInstance, 'editorjs-edit-note', { hasImageTool: false });
                        }
                    }
                });
            } else {
                // Update existing instance
                await editEditorInstance.isReady;
                await editEditorInstance.clear();
                if (content && Object.keys(content).length > 0) {
                    await editEditorInstance.render(content);
                }
            }
        } catch (err) {
            console.error('Editor.js operation failed:', err);
        }
    });

    if (editForm) {
        editForm.addEventListener('submit', function (e) {
            if (!editEditorInstance) return;
            e.preventDefault();

            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Saving...';
            }

            editEditorInstance.save().then((outputData) => {
                const input = document.getElementById('id_content_json_edit_note');
                if (input) {
                    input.value = JSON.stringify(outputData);
                    this.submit();
                }
            }).catch((error) => {
                console.error('Saving failed:', error);
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = 'Save Changes';
                }
            });
        });
    }
});
