(function () {
    document.addEventListener('DOMContentLoaded', function () {
        var existingContentScript = document.getElementById('existing_content');
        if (existingContentScript && existingContentScript.textContent.trim()) {
            try {
                var data = JSON.parse(existingContentScript.textContent);
                if (data && data.blocks) {
                    setTimeout(function () {
                        if (window.IgboEditor && window.IgboEditor.instance) {
                            window.IgboEditor.instance.render(data).then(function () {
                                console.log('Existing content loaded');
                                window.IgboEditor.updateFeaturedImageOptions();
                            });
                        }
                    }, 500);
                }
            } catch (e) {
                console.log('Could not parse existing content as JSON, converting from HTML');
                var htmlContent = existingContentScript.textContent;
                if (htmlContent && window.IgboEditor) {
                    var converted = window.IgboEditor.convertHtmlToEditorJS(htmlContent);
                    setTimeout(function () {
                        if (window.IgboEditor.instance) {
                            window.IgboEditor.instance.render(converted).then(function () {
                                console.log('Content converted from HTML');
                                window.IgboEditor.updateFeaturedImageOptions();
                            });
                        }
                    }, 500);
                }
            }
        }
    });
})();
