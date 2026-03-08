(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        var editor = IgboEditor.initSimple('editor', {
            placeholder: 'Edit your book review...',
            autofocus: false
        });

        // Initialize the custom toolbar
        setTimeout(function () {
            if (window.EditorToolbar && editor) {
                window.EditorToolbar.init(editor, 'editor', { hasImageTool: false });
            }
        }, 300);

        // Load existing content
        var existingContentScript = document.getElementById('existing_content');
        if (existingContentScript && existingContentScript.textContent.trim()) {
            try {
                var data = JSON.parse(existingContentScript.textContent);
                if (data && data.blocks) {
                    setTimeout(function () {
                        if (editor && typeof IgboEditor.setData === 'function') {
                            IgboEditor.setData(data).then(function () {
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
                        if (editor && typeof IgboEditor.setData === 'function') {
                            IgboEditor.setData(converted);
                        }
                    }, 500);
                }
            }
        }

        initBookForm(editor);
    });
})();