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
        const typeFilter = document.getElementById('archiveTypeFilter');

        if (searchInput) {
            let debounceTimer;
            searchInput.addEventListener('input', function () {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(function () {
                    loadArchives();
                }, 300);
            });
        }

        if (typeFilter) {
            typeFilter.addEventListener('change', function () {
                loadArchives();
            });
        }
    }

    function loadArchives() {
        const search = document.getElementById('archiveSearch').value || '';
        const typeFilter = document.getElementById('archiveTypeFilter');
        const mediaType = typeFilter ? typeFilter.value : 'image';
        const url = '/api/archive-media-browser/?search=' + encodeURIComponent(search) + '&type=' + mediaType;
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

                        // Different display based on media type
                        let mediaPreview = '';
                        if (mediaType === 'image') {
                            const imgUrl = archive.thumbnail || archive.url || '';
                            mediaPreview = '<img src="' + imgUrl + '" alt="' + (archive.alt_text || archive.title || '') + '" loading="lazy">';
                        } else if (mediaType === 'video') {
                            mediaPreview = '<div class="archive-item-icon"><i class="fas fa-video text-3xl text-blue-500"></i></div>';
                        } else if (mediaType === 'audio') {
                            mediaPreview = '<div class="archive-item-icon"><i class="fas fa-music text-3xl text-green-500"></i></div>';
                        }

                        item.innerHTML = mediaPreview + '<div class="archive-item-title">' + (archive.title || 'Untitled') + '</div>';

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
                    grid.innerHTML = '<p class="col-span-full text-center text-vintage-beaver py-8">No ' + mediaType + ' archives found</p>';
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

        // Reset all form fields
        const fileInput = document.getElementById('mediaFileInput');
        if (fileInput) fileInput.value = '';

        const fieldsToReset = ['mediaTitle', 'mediaCaption', 'mediaDescription',
            'mediaLocation', 'mediaCircaDate', 'mediaCopyrightHolder',
            'mediaOriginalUrl', 'mediaTags'];
        fieldsToReset.forEach(function (id) {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });

        const categorySelect = document.getElementById('mediaCategory');
        if (categorySelect) categorySelect.selectedIndex = 0;

        // Reset radio buttons to image
        const imageRadio = document.querySelector('input[name="mediaType"][value="image"]');
        if (imageRadio) {
            imageRadio.checked = true;
            updateMediaUploadUI();
        }

        selectedArchive = null;
        document.querySelectorAll('.archive-item').forEach(function (item) {
            item.classList.remove('selected');
        });
        document.getElementById('insertArchiveBtn').classList.add('hidden');
    };

    // Update UI when media type changes
    window.updateMediaUploadUI = function () {
        const mediaType = document.querySelector('input[name="mediaType"]:checked').value;
        const fileInput = document.getElementById('mediaFileInput');
        const fileLabel = document.getElementById('fileInputLabel');
        const fileHelp = document.getElementById('fileInputHelp');

        const config = {
            image: {
                accept: 'image/*',
                label: 'Select Image File',
                help: 'Accepted: JPG, PNG, WEBP (Max 5MB)'
            },
            video: {
                accept: 'video/*',
                label: 'Select Video File',
                help: 'Accepted: MP4, WEBM, OGG (Max 50MB)'
            },
            audio: {
                accept: 'audio/*',
                label: 'Select Audio File',
                help: 'Accepted: MP3, WAV, OGG, M4A (Max 10MB)'
            }
        };

        const c = config[mediaType] || config.image;
        if (fileInput) fileInput.accept = c.accept;
        if (fileLabel) fileLabel.textContent = c.label;
        if (fileHelp) fileHelp.textContent = c.help;
    };

    window.uploadAndInsertMedia = function () {
        const mediaType = document.querySelector('input[name="mediaType"]:checked').value;
        const file = document.getElementById('mediaFileInput').files[0];
        const title = document.getElementById('mediaTitle').value.trim();
        const caption = document.getElementById('mediaCaption').value.trim();
        const description = document.getElementById('mediaDescription').value.trim();

        // Optional fields
        const category = document.getElementById('mediaCategory').value;
        const location = document.getElementById('mediaLocation').value.trim();
        const circaDate = document.getElementById('mediaCircaDate').value.trim();
        const copyrightHolder = document.getElementById('mediaCopyrightHolder').value.trim();
        const originalUrl = document.getElementById('mediaOriginalUrl').value.trim();
        const tags = document.getElementById('mediaTags').value.trim();

        // Validation
        if (!file) {
            showToast('Please select a file', 'error');
            return;
        }
        if (!title) {
            showToast('Title is required', 'error');
            return;
        }
        if (!caption) {
            showToast('Caption with copyright/source info is required', 'error');
            return;
        }
        if (!description) {
            showToast('Description (alt text) is required', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('media_type', mediaType);
        formData.append('title', title);
        formData.append('caption', caption);
        formData.append('description', description);

        // Optional fields
        if (category) formData.append('category', category);
        if (location) formData.append('location', location);
        if (circaDate) formData.append('circa_date', circaDate);
        if (copyrightHolder) formData.append('copyright_holder', copyrightHolder);
        if (originalUrl) formData.append('original_url', originalUrl);
        if (tags) formData.append('tags', tags);

        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) {
            formData.append('csrfmiddlewaretoken', csrfToken.value);
        }

        const uploadBtn = document.getElementById('uploadBtn');
        const originalText = uploadBtn.innerHTML;
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';

        fetch('/api/upload-media/', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        })
            .then(function (response) { return response.json(); })
            .then(function (data) {
                if (data.success === 1) {
                    // Insert appropriate block based on media type
                    const blockType = mediaType === 'image' ? 'image' :
                        (mediaType === 'video' ? 'embed' : 'embed');

                    if (mediaType === 'image') {
                        editor.blocks.insert('image', {
                            file: { url: data.file.url },
                            caption: caption,
                            alt: description,
                            archive_id: data.archive_id,
                            withBorder: false,
                            stretched: false,
                            withBackground: true
                        }, {}, openingBlockIndex, true, true);
                    } else {
                        // For video/audio, insert as embed or raw HTML
                        editor.blocks.insert('paragraph', {
                            text: '<a href="' + data.file.url + '" target="_blank">' + title + '</a> - ' + caption
                        }, {}, openingBlockIndex, true, true);
                    }

                    closeImageModal();
                    showToast(mediaType.charAt(0).toUpperCase() + mediaType.slice(1) + ' uploaded successfully', 'success');
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
