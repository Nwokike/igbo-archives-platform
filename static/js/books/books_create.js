(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        var editor = IgboEditor.initSimple('editor', {
            placeholder: 'Start writing your book review... Share your thoughts about the book!',
            autofocus: false
        });

        // Initialize the custom toolbar (without image tool for books)
        setTimeout(function () {
            if (window.EditorToolbar && editor) {
                window.EditorToolbar.init(editor, 'editor', { hasImageTool: false });
            }
        }, 300);

        initBookForm(editor);
    });
})();