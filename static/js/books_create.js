(function () {
    'use strict';

    var editor = null;

    document.addEventListener('DOMContentLoaded', function () {
        // Use simple editor config for books - no image tool
        editor = IgboEditor.initSimple('editor', {
            placeholder: 'Start writing your book review... Share your thoughts about the book!',
            autofocus: false
        });

        document.getElementById('bookForm').addEventListener('submit', function (e) {
            e.preventDefault();

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
                e.target.submit();
            }).catch(function (error) {
                console.error('Error saving editor content:', error);
                showToast('Error saving content. Please try again.', 'error');
            });
        });
    });

    // showToast is handled globally by main.js
})();
