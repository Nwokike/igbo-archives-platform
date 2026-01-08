(function () {
    'use strict';

    var editor = null;

    document.addEventListener('DOMContentLoaded', function () {
        editor = IgboEditor.init('editor', {
            placeholder: 'Edit your book review...',
            autofocus: false
        });

        var existingContent = document.getElementById('existing_content');
        if (existingContent && existingContent.value) {
            try {
                var data = JSON.parse(existingContent.value);
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
                var htmlContent = existingContent.value;
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

        document.getElementById('bookForm').addEventListener('submit', function (e) {
            e.preventDefault();

            editor.save().then(function (outputData) {
                if (!outputData.blocks || outputData.blocks.length === 0) {
                    showToast('Please add some content before submitting.', 'error');
                    return;
                }

                document.getElementById('content_json').value = JSON.stringify(outputData);
                e.target.submit();
            }).catch(function (error) {
                console.error('Error saving editor content:', error);
                showToast('Error saving content. Please try again.', 'error');
            });
        });
    });

    // showToast is handled globally by main.js
})();
