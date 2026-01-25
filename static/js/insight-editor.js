(function () {
    'use strict';

    let editor = null;
    let selectedArchive = null;
    let openingBlockIndex = null;

    document.addEventListener('DOMContentLoaded', function () {
        initEditor();
        initTabs();
        initArchiveSearch();
        initFormSubmission();
    });

    function initEditor() {
        editor = IgboEditor.init('editor', {
            placeholder: 'Start writing your insight... Use the + button to add images, headers, and more!',
            autofocus: true,
            onChange: function () {
                IgboEditor.updateFeaturedImageOptions();
            },
            onReady: function () {
                console.log('Insight editor ready');
            }
        });
    }

    function initTabs() {
        // FIXED: Selector changed to avoid conflict with global tabs.js
        const tabButtons = document.querySelectorAll('.tab-button[data-img-tab]');
        const uploadBtn = document.getElementById('uploadBtn');
        const insertBtn = document.getElementById('insertArchiveBtn');

        tabButtons.forEach(function (btn) {
            btn.addEventListener('click', function () {
                // FIXED: Using data-img-tab instead of data-tab
                const tabId = this.dataset.imgTab;

                tabButtons.forEach(function (b) { b.classList.remove('active'); });
                this.classList.add('active');

                // Explicitly manage hidden classes to override any global css conflicts
                document.querySelectorAll('#imageModal .tab-panel').forEach(function (p) {
                    p.classList.remove('active');
                    p.classList.add('hidden');
                });

                const activePanel = document.getElementById(tabId + '-panel');
                if (activePanel) {
                    activePanel.classList.add('active');
                    activePanel.classList.remove('hidden');
                }

                if (tabId === 'upload') {
                    uploadBtn.classList.remove('hidden');
                    insertBtn.classList.add('hidden');
                } else {
                    uploadBtn.classList.add('hidden');
                    insertBtn.classList.remove('hidden');
                    loadArchives();
                }
            });
        });
    }

    function initArchiveSearch() {
        const searchInput = document.getElementById('archiveSearch');
        if (searchInput) {
            let debounceTimer;
            searchInput.addEventListener('input', function () {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(function () {
                    loadArchives();
                }, 300);
            });
        }
    }

    function loadArchives() {
        const search = document.getElementById('archiveSearch').value || '';
        const url = '/api/archive-media-browser/?search=' + encodeURIComponent(search) + '&type=image';
        const grid = document.getElementById('archiveGrid');
        const insertBtn = document.getElementById('insertArchiveBtn');

        if (!grid) return;

        grid.innerHTML = '<div class="col-span-full flex justify-center py-8"><i class="fas fa-spinner fa-spin text-2xl text-vintage-gold"></i></div>';

        fetch(url)
            .then(function (response) { return response.json(); })
            .then(function (data) {
                grid.innerHTML = '';
                selectedArchive = null;
                insertBtn.classList.add('hidden');

                if (data.archives && data.archives.length > 0) {
                    data.archives.forEach(function (archive) {
                        const item = document.createElement('div');
                        item.className = 'archive-item';
                        const imgUrl = archive.thumbnail || archive.url || '';
                        item.innerHTML =
                            '<img src="' + imgUrl + '" alt="' + (archive.alt_text || archive.title || '') + '" loading="lazy">' +
                            '<div class="archive-item-title">' + (archive.title || 'Untitled') + '</div>';

                        item.addEventListener('click', function () {
                            document.querySelectorAll('.archive-item').forEach(function (el) {
                                el.classList.remove('selected');
                            });
                            item.classList.add('selected');
                            selectedArchive = archive;
                            insertBtn.classList.remove('hidden');
                        });

                        grid.appendChild(item);
                    });
                } else {
                    grid.innerHTML = '<p class="col-span-full text-center text-vintage-beaver py-8">No image archives found</p>';
                }
            })
            .catch(function (error) {
                console.error('Error loading archives:', error);
                grid.innerHTML = '<p class="col-span-full text-center text-red-600 py-8">Error loading archives</p>';
            });
    }

    window.openImageModal = function (index) {
        const modal = document.getElementById('imageModal');
        openingBlockIndex = index;
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
            loadArchives();
        }
    };

    window.closeImageModal = function () {
        const modal = document.getElementById('imageModal');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }

        document.getElementById('imageFileInput').value = '';
        document.getElementById('imageCaption').value = '';
        document.getElementById('imageDescription').value = '';
        selectedArchive = null;
        document.querySelectorAll('.archive-item').forEach(function (item) {
            item.classList.remove('selected');
        });
        document.getElementById('insertArchiveBtn').classList.add('hidden');
    };

    window.uploadAndInsertImage = function () {
        const file = document.getElementById('imageFileInput').files[0];
        const caption = document.getElementById('imageCaption').value.trim();
        const description = document.getElementById('imageDescription').value.trim();

        if (!file) {
            showToast('Please select an image file', 'error');
            return;
        }
        if (!caption) {
            showToast('Caption with copyright/source info is required', 'error');
            return;
        }
        if (!description) {
            showToast('Image description (alt text) is required', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('image', file);
        formData.append('caption', caption);
        formData.append('description', description);

        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) {
            formData.append('csrfmiddlewaretoken', csrfToken.value);
        }

        const uploadBtn = document.getElementById('uploadBtn');
        const originalText = uploadBtn.innerHTML;
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';

        fetch('/api/upload-image/', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        })
            .then(function (response) { return response.json(); })
            .then(function (data) {
                if (data.success === 1) {
                    // FIXED: Now passing 'alt' (description) to the editor block
                    // Using index and replace true to swap the placeholder
                    editor.blocks.insert('image', {
                        file: { url: data.file.url },
                        caption: caption,
                        alt: description,
                        withBorder: false,
                        stretched: false,
                        withBackground: true
                    }, {}, openingBlockIndex, true, true);
                    closeImageModal();
                    showToast('Image uploaded successfully', 'success');
                    IgboEditor.updateFeaturedImageOptions();
                } else {
                    showToast('Upload failed: ' + (data.error || 'Unknown error'), 'error');
                }
            })
            .catch(function (error) {
                showToast('Upload failed: ' + error.message, 'error');
            })
            .finally(function () {
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = originalText;
            });
    };

    window.insertSelectedArchive = function () {
        if (selectedArchive) {
            // Insert image with archive metadata for linking
            editor.blocks.insert('image', {
                file: { url: selectedArchive.thumbnail || selectedArchive.url || '' },
                caption: selectedArchive.caption || selectedArchive.title || '',
                alt: selectedArchive.alt_text || selectedArchive.title || '',
                archive_id: selectedArchive.id,  // For linking to archive detail
                archive_slug: selectedArchive.slug || null,
                withBorder: false,
                stretched: false,
                withBackground: true
            }, {}, openingBlockIndex, true, true);
            closeImageModal();
            showToast('Image inserted successfully', 'success');
            IgboEditor.updateFeaturedImageOptions();
        }
    };

    function initFormSubmission() {
        const form = document.getElementById('insightForm');
        if (form) {
            form.addEventListener('submit', function (e) {
                e.preventDefault();

                editor.save().then(function (outputData) {
                    if (!outputData.blocks || outputData.blocks.length === 0) {
                        showToast('Please add some content before submitting.', 'error');
                        return;
                    }

                    const hasContent = outputData.blocks.some(function (block) {
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

                    const images = outputData.blocks.filter(function (b) { return b.type === 'image'; });
                    const featuredInput = document.getElementById('featured_image_url');
                    if (images.length > 0 && !featuredInput.value) {
                        featuredInput.value = images[0].data.file.url;
                    }

                    form.submit();
                }).catch(function (error) {
                    console.error('Error saving editor content:', error);
                    showToast('Error saving content. Please try again.', 'error');
                });
            });
        }
    }

    console.log('Insight editor module loaded');
})();
