(function () {
    'use strict';

    var editor = null;
    // FIXED: Variable to track which button was clicked
    var submitAction = null;

    document.addEventListener('DOMContentLoaded', function () {
        editor = IgboEditor.init('editor', {
            placeholder: 'Edit your book review...',
            autofocus: false
        });

        // Initialize the custom toolbar
        setTimeout(function () {
            if (window.EditorToolbar && editor) {
                window.EditorToolbar.init(editor, 'editor', { hasImageTool: false });
            }
        }, 300);

        var existingContentScript = document.getElementById('existing_content');
        if (existingContentScript && existingContentScript.textContent.trim()) {
            try {
                var data = JSON.parse(existingContentScript.textContent);
                if (data && data.blocks) {
                    setTimeout(function () {
                        if (editor) {
                            editor.render(data).then(function () {
                                console.log('Existing content loaded');
                            });
                        }
                    }, 500);
                }
            } catch (e) {
                console.log('Converting HTML content');
                var htmlContent = existingContentScript.textContent;
                if (htmlContent && window.IgboEditor) {
                    var converted = window.IgboEditor.convertHtmlToEditorJS(htmlContent);
                    setTimeout(function () {
                        if (editor) {
                            editor.render(converted);
                        }
                    }, 500);
                }
            }
        }

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

            // Default to 'save' (or whatever default behavior implies) if undefined
            if (!submitAction) submitAction = 'save';

            editor.save().then(function (outputData) {
                if (!outputData.blocks || outputData.blocks.length === 0) {
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