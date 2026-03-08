/**
 * Books Editor - Shared form submission logic.
 * Used by both books_create.js and books_edit.js.
 */
function initBookForm(editor) {
    var submitAction = null;
    var form = document.getElementById('bookForm');
    if (!form) return;

    // Capture which action button was clicked
    var submitButtons = form.querySelectorAll('button[name="action"]');
    submitButtons.forEach(function (btn) {
        btn.addEventListener('click', function () {
            submitAction = this.value;
        });
    });

    form.addEventListener('submit', function (e) {
        e.preventDefault();
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

            var actionInput = form.querySelector('input[name="action"]');
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
}
