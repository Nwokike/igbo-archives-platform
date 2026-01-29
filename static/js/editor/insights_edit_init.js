(function () {
    document.addEventListener('DOMContentLoaded', function () {
        var existingContent = document.getElementById('existing_content');
        if (existingContent && existingContent.value) {
            try {
                var data = JSON.parse(existingContent.value);
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
                var htmlContent = existingContent.value;
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
