(function () {
    'use strict';

    var editor = null;
    // FIXED: Variable to track which button was clicked
    var submitAction = null;

    document.addEventListener('DOMContentLoaded', function () {
        // Use simple editor config for books - no image tool
        editor = IgboEditor.initSimple('editor', {
            placeholder: 'Start writing your book review... Share your thoughts about the book!',
            autofocus: false
        });

        // Initialize the custom toolbar (without image tool for books)
        setTimeout(function () {
            if (window.EditorToolbar && editor) {
                window.EditorToolbar.init(editor, 'editor', { hasImageTool: false });
            }
        }, 300);

        const form = document.getElementById('bookForm');
        if (!form) return;

        // FIXED: Listen for specific button clicks to capture intent
        const submitButtons = form.querySelectorAll('button[name="action"]');
        submitButtons.forEach(btn => {
            btn.addEventListener('click', function () {
                submitAction = this.value; // Store 'submit' or 'save'
            });
        });

        form.addEventListener('submit', function (e) {
            e.preventDefault();

            // Default to 'save' if triggered by Enter key without button click
            if (!submitAction) submitAction = 'save';

            editor.save().then(function (outputData) {
                if (!outputData.blocks || outputData.blocks.length === 0) {
                    showToast('Please add some content before submitting.', 'error');
                    return;
                }

                var hasContent = outputData.blocks.some(function (block) {
                    if (block.type === 'paragraph') {
                        return block.data.text && block.data.text.trim().length > 0;
                    }
                    return true;
                });

                if (!hasContent) {
                    showToast('Please add some content before submitting.', 'error');
                    return;
                }

                document.getElementById('content_json').value = JSON.stringify(outputData);

                // FIXED: Inject the captured action into the form before submitting
                let actionInput = form.querySelector('input[name="action"]');
                if (!actionInput) {
                    actionInput = document.createElement('input');
                    actionInput.type = 'hidden';
                    actionInput.name = 'action';
                    form.appendChild(actionInput);
                }
                actionInput.value = submitAction;

                form.submit();
            }).catch(function (error) {
                console.error('Error saving editor content:', error);
                showToast('Error saving content. Please try again.', 'error');
            });
        });
    });

    // showToast is handled globally by main.js
})();