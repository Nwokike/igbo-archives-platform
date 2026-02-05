(function () {
    'use strict';

    let editor = null;
    let selectedArchive = null;
    let openingBlockIndex = null;
    // FIXED: Variable to track which button was clicked
    let submitAction = null;

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
                // Initialize the custom toolbar
                if (window.EditorToolbar && editor) {
                    window.EditorToolbar.init(editor, 'editor', { hasImageTool: true });
                }
            }
        });
    }

    function initTabs() {
        const tabButtons = document.querySelectorAll('.tab-button[data-img-tab]');
        const uploadBtn = document.getElementById('uploadBtn');
        const insertBtn = document.getElementById('insertArchiveBtn');

        tabButtons.forEach(function (btn) {
            btn.addEventListener('click', function () {
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

        const fieldsToReset = [
            'mediaTitle',
            'mediaArchiveDescription',
            'mediaCategory',
            'mediaOriginalAuthor',
            'mediaCopyrightHolder',
            'mediaCircaDate',
            'mediaDateCreated',
            'mediaLocation',
            'mediaIdentityNumber',
            'mediaOriginalUrl',
            'mediaCaption',
            'mediaAltText'
        ];

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

    // --- NEW HELPER FUNCTION TO COMPOSITE CAPTION ---
    function formatCaption(caption, author, copyright) {
        let parts = [];
        // 1. The main caption
        if (caption && caption.trim()) parts.push(caption.trim());

        // 2. The metadata (Author / Copyright)
        let meta = [];
        if (author && author.trim()) meta.push('Photo by ' + author.trim());
        if (copyright && copyright.trim()) meta.push('© ' + copyright.trim());

        if (meta.length > 0) {
            // Add a separator if there was a caption
            let separator = parts.length > 0 ? ' | ' : '';
            parts.push(separator + meta.join(' '));
        }

        return parts.join('');
    }

    window.uploadAndInsertMedia = function () {
        const mediaType = document.querySelector('input[name="mediaType"]:checked').value;
        const file = document.getElementById('mediaFileInput').files[0];

        const title = document.getElementById('mediaTitle').value.trim();
        const description = document.getElementById('mediaArchiveDescription').value.trim();
        const category = document.getElementById('mediaCategory').value;

        const originalAuthor = document.getElementById('mediaOriginalAuthor').value.trim();
        const copyrightHolder = document.getElementById('mediaCopyrightHolder').value.trim();
        const circaDate = document.getElementById('mediaCircaDate').value.trim();
        const dateCreated = document.getElementById('mediaDateCreated').value;
        const location = document.getElementById('mediaLocation').value.trim();
        const identityNumber = document.getElementById('mediaIdentityNumber').value.trim();
        const originalUrl = document.getElementById('mediaOriginalUrl').value.trim();

        const caption = document.getElementById('mediaCaption').value.trim();
        const altText = document.getElementById('mediaAltText').value.trim();

        if (!file) { showToast('Please select a file', 'error'); return; }
        if (!title) { showToast('Archive Title is required', 'error'); return; }
        if (!description) { showToast('Archive Description is required', 'error'); return; }
        if (!caption) { showToast('Item Caption is required', 'error'); return; }
        if (!altText) { showToast('Item Alt Text is required', 'error'); return; }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('media_type', mediaType);
        formData.append('title', title);
        formData.append('description', description);
        if (category) formData.append('category', category);

        if (originalAuthor) formData.append('original_author', originalAuthor);
        if (copyrightHolder) formData.append('copyright_holder', copyrightHolder);
        if (circaDate) formData.append('circa_date', circaDate);
        if (dateCreated) formData.append('date_created', dateCreated);
        if (location) formData.append('location', location);
        if (identityNumber) formData.append('original_identity_number', identityNumber);
        if (originalUrl) formData.append('original_url', originalUrl);

        formData.append('caption', caption);
        formData.append('alt_text', altText);

        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) formData.append('csrfmiddlewaretoken', csrfToken.value);

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
                    const finalDisplayCaption = formatCaption(caption, originalAuthor, copyrightHolder);

                    if (mediaType === 'image') {
                        editor.blocks.insert('image', {
                            file: { url: data.file.url },
                            caption: finalDisplayCaption,
                            alt: altText,
                            archive_id: data.archive_id,
                            withBorder: false,
                            stretched: false,
                            withBackground: true
                        }, {}, openingBlockIndex, true, true);
                    } else {
                        editor.blocks.insert('paragraph', {
                            text: `<a href="${data.file.url}" target="_blank">View ${mediaType}: ${title}</a> - ${finalDisplayCaption}`
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
            const finalDisplayCaption = formatCaption(
                selectedArchive.caption || selectedArchive.title,
                selectedArchive.original_author,
                selectedArchive.copyright_holder
            );

            editor.blocks.insert('image', {
                file: { url: selectedArchive.thumbnail || selectedArchive.url || '' },
                caption: finalDisplayCaption,
                alt: selectedArchive.alt_text || selectedArchive.title || '',
                archive_id: selectedArchive.id,
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
            // FIXED: Listen for specific button clicks to capture intent
            const submitButtons = form.querySelectorAll('button[name="action"]');
            submitButtons.forEach(btn => {
                btn.addEventListener('click', function () {
                    submitAction = this.value; // Store 'submit' or 'save'
                });
            });

            form.addEventListener('submit', function (e) {
                e.preventDefault();

                // Default to 'save' if undefined
                if (!submitAction) submitAction = 'save';

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
        }
    }

    console.log('Insight editor module loaded');
})();