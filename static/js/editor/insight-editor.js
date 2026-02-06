(function () {
    'use strict';

    let editor = null;
    let selectedArchive = null;
    let openingBlockIndex = null;
    let submitAction = null;

    document.addEventListener('DOMContentLoaded', function () {
        initEditor();
        initTabs();
        initArchiveSearch();
        initFormSubmission();
    });

    function initEditor() {
        console.log('Initializing Insight Editor...');
        editor = IgboEditor.init('editor', {
            placeholder: 'Start writing your insight... Use the + button to add images, headers, and more!',
            autofocus: true,
            onChange: function () {
                console.log('Editor content changed. Updating featured image options...');
                try {
                    IgboEditor.updateFeaturedImageOptions();
                } catch (e) {
                    console.error('Error in onChange listener:', e);
                }
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
                    if (uploadBtn) uploadBtn.classList.remove('hidden');
                    if (insertBtn) insertBtn.classList.add('hidden');
                } else {
                    if (uploadBtn) uploadBtn.classList.add('hidden');
                    if (insertBtn) insertBtn.classList.remove('hidden');
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
        const searchInput = document.getElementById('archiveSearch');
        const search = searchInput ? searchInput.value : '';
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
                if (insertBtn) insertBtn.classList.add('hidden');

                if (data.archives && data.archives.length > 0) {
                    data.archives.forEach(function (archive) {
                        const item = document.createElement('div');
                        item.className = 'archive-item';

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
                            if (insertBtn) insertBtn.classList.remove('hidden');
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
        console.log('Opening Image Modal at index:', index);
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

        const imageRadio = document.querySelector('input[name="mediaType"][value="image"]');
        if (imageRadio) {
            imageRadio.checked = true;
            if (window.updateMediaUploadUI) window.updateMediaUploadUI();
        }

        selectedArchive = null;
        document.querySelectorAll('.archive-item').forEach(function (item) {
            item.classList.remove('selected');
        });
        const insertBtn = document.getElementById('insertArchiveBtn');
        if (insertBtn) insertBtn.classList.add('hidden');
    };

    window.updateMediaUploadUI = function () {
        const typeEl = document.querySelector('input[name="mediaType"]:checked');
        const mediaType = typeEl ? typeEl.value : 'image';
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

    function formatCaption(caption, author, copyright) {
        let parts = [];
        if (caption && caption.trim()) parts.push(caption.trim());

        let meta = [];
        if (author && author.trim()) meta.push('Photo by ' + author.trim());
        if (copyright && copyright.trim()) meta.push('© ' + copyright.trim());

        if (meta.length > 0) {
            let separator = parts.length > 0 ? ' | ' : '';
            parts.push(separator + meta.join(' '));
        }

        return parts.join('');
    }

    window.uploadAndInsertMedia = function () {
        const typeEl = document.querySelector('input[name="mediaType"]:checked');
        const mediaType = typeEl ? typeEl.value : 'image';
        const fileInput = document.getElementById('mediaFileInput');
        const file = fileInput ? fileInput.files[0] : null;

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
        const originalText = uploadBtn ? uploadBtn.innerHTML : '';
        if (uploadBtn) {
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
        }

        console.log('Sending upload request to /api/upload-media/...');

        fetch('/api/upload-media/', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        })
            .then(function (response) {
                console.log('Upload HTTP Response:', response.status);
                return response.json();
            })
            .then(function (data) {
                console.log('Received API JSON data:', data);
                if (data.success === 1) {
                    const finalDisplayCaption = formatCaption(caption, originalAuthor, copyrightHolder);
                    console.log('Preparing to insert block...', {
                        mediaType,
                        index: openingBlockIndex,
                        url: data.file.url
                    });

                    try {
                        if (mediaType === 'image') {
                            const insertIndex = openingBlockIndex !== null ? openingBlockIndex : undefined;
                            editor.blocks.insert('image', {
                                file: { url: data.file.url },
                                caption: finalDisplayCaption,
                                alt: altText,
                                archive_id: data.archive_id,
                                withBorder: false,
                                stretched: false,
                                withBackground: true
                            }, {}, insertIndex, true);
                            console.log('Image block inserted successfully');
                        } else {
                            const insertIndex = openingBlockIndex !== null ? openingBlockIndex : undefined;
                            editor.blocks.insert('paragraph', {
                                text: `<a href="${data.file.url}" target="_blank">View ${mediaType}: ${title}</a> - ${finalDisplayCaption}`
                            }, {}, insertIndex, true);
                            console.log('Paragraph block (for media) inserted successfully');
                        }
                    } catch (insertErr) {
                        console.error('CRITICAL: Error during editor.blocks.insert:', insertErr);
                    }

                    closeImageModal();
                    showToast(mediaType.charAt(0).toUpperCase() + mediaType.slice(1) + ' uploaded and inserted successfully', 'success');
                    if (IgboEditor.updateFeaturedImageOptions) IgboEditor.updateFeaturedImageOptions();
                } else {
                    console.error('API returned error success state:', data);
                    showToast('Upload failed: ' + (data.error || 'Unknown error'), 'error');
                }
            })
            .catch(function (error) {
                console.error('Fetch/JSON Error:', error);
                showToast('Upload failed: ' + error.message, 'error');
            })
            .finally(function () {
                if (uploadBtn) {
                    uploadBtn.disabled = false;
                    uploadBtn.innerHTML = originalText;
                }
            });
    };

    window.insertSelectedArchive = function () {
        if (selectedArchive) {
            console.log('Inserting selected archive:', selectedArchive.id);
            const finalDisplayCaption = formatCaption(
                selectedArchive.caption || selectedArchive.title,
                selectedArchive.original_author,
                selectedArchive.copyright_holder
            );

            try {
                const insertIndex = openingBlockIndex !== null ? openingBlockIndex : undefined;
                editor.blocks.insert('image', {
                    file: { url: selectedArchive.thumbnail || selectedArchive.url || '' },
                    caption: finalDisplayCaption,
                    alt: selectedArchive.alt_text || selectedArchive.title || '',
                    archive_id: selectedArchive.id,
                    archive_slug: selectedArchive.slug || null,
                    withBorder: false,
                    stretched: false,
                    withBackground: true
                }, {}, insertIndex, true);
                console.log('Archive image inserted successfully');
            } catch (e) {
                console.error('Error inserting archive block:', e);
            }

            closeImageModal();
            showToast('Image inserted successfully', 'success');
            if (IgboEditor.updateFeaturedImageOptions) IgboEditor.updateFeaturedImageOptions();
        }
    };

    function initFormSubmission() {
        const form = document.getElementById('insightForm');
        if (form) {
            const submitButtons = form.querySelectorAll('button[name="action"]');
            submitButtons.forEach(btn => {
                btn.addEventListener('click', function () {
                    submitAction = this.value;
                });
            });

            form.addEventListener('submit', function (e) {
                e.preventDefault();

                if (!submitAction) submitAction = 'save';

                console.log('Saving editor content for form submission...');
                editor.save().then(function (outputData) {
                    console.log('Editor Save Output:', outputData);
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

                    const contentJsonInput = document.getElementById('content_json');
                    if (contentJsonInput) contentJsonInput.value = JSON.stringify(outputData);

                    const images = outputData.blocks.filter(function (b) { return b.type === 'image'; });
                    const featuredInput = document.getElementById('featured_image_url');
                    if (images.length > 0 && featuredInput && !featuredInput.value) {
                        featuredInput.value = images[0].data.file.url;
                    }

                    let actionInput = form.querySelector('input[name="action"]');
                    if (!actionInput) {
                        actionInput = document.createElement('input');
                        actionInput.type = 'hidden';
                        actionInput.name = 'action';
                        form.appendChild(actionInput);
                    }
                    actionInput.value = submitAction;

                    console.log('Submitting form with action:', submitAction);
                    form.submit();
                }).catch(function (error) {
                    console.error('Error saving editor content during submit:', error);
                    showToast('Error saving content. Please try again.', 'error');
                });
            });
        }
    }

    console.log('Insight editor module loaded');
})();