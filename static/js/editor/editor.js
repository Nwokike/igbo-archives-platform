(function () {
    'use strict';

    window.IgboEditor = {
        instance: null,
        selectedArchive: null,
        selectedFeaturedImage: null,

        // Helper to generate consistent captions (Title | Author | Copyright)
        formatCaption: function(caption, author, copyright) {
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
        },

        init: function (holderId, options) {
            const self = this;
            options = options || {};

            const editorConfig = {
                holder: holderId,
                placeholder: options.placeholder || 'Start writing your content...',
                autofocus: options.autofocus !== false,
                tools: {
                    image: {
                        class: class ModalImageTool {
                            constructor({ data, api }) {
                                this.data = data;
                                this.api = api;
                                this.wrapper = undefined;
                                this.settings = [
                                    {
                                        name: 'withBorder',
                                        icon: `<svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path d="M15.8 10.592v2.043h2.35v2.138H15.8v2.232h-2.25v-2.232h-2.4v-2.138h2.4v-2.28h2.25v.237h1.15-1.15zM1.9 8.455v-3.42c0-1.154.985-2.09 2.2-2.09h4.2v2.137H4.15c-.22 0-.4.187-.4.418v3.42H1.9zm0 2.137h1.9v3.42c0 .231.18.418.4.418h4.2v2.137H4.15c-1.215 0-2.2-.936-2.2-2.09v-3.885zm6.1 6.877V15.7h2.25v1.772H8zM14.05 5.09H8V2.945h6.05c1.215 0 2.2.936 2.2 2.09v4.18h-2.25V5.508c0-.231-.18-.418-.4-.418z"/></svg>`,
                                        title: 'Add Border'
                                    },
                                    {
                                        name: 'stretched',
                                        icon: `<svg width="17" height="10" viewBox="0 0 17 10" xmlns="http://www.w3.org/2000/svg"><path d="M13.568 5.925H4.056l1.703 1.703a1.125 1.125 0 0 1-1.59 1.591L.962 6.014A1.069 1.069 0 0 1 .588 4.26L4.38.469a1.069 1.069 0 0 1 1.759 1.511L4.056 3.975h9.512l-1.703-1.703a1.125 1.125 0 0 1 1.59-1.591l3.207 3.207a1.069 1.069 0 0 1 .374 1.754L13.26 9.249a1.069 1.069 0 0 1-1.759-1.511l2.067-2.067z"/></svg>`,
                                        title: 'Stretch Image'
                                    },
                                    {
                                        name: 'withBackground',
                                        icon: `<svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path d="M10.043 8.265l3.183-3.183h-2.924L4.75 10.636v2.923l4.15-4.15v2.351l-2.158 2.159H8.9v2.137H4.75v-3.903l.971-.971-3.062-3.062h3.448l3.936 3.095zM18.1 10.93v3.238c0 .971-.828 1.757-1.849 1.757h-3.14l-4.71-4.71h.236c2.478 0 4.295-.922 5.253-2.664.67-1.219.782-2.326.33-3.084-.366-.615-.992-.885-1.722-.885-.145 0-.285.01-.421.033l-1.353.221-1.228-1.228c.459-.148.966-.23 1.503-.23 1.944 0 3.873.864 4.876 2.548 1.442 2.42 1.049 4.908 2.225 4.908h.001z"/></svg>`,
                                        title: 'Boxed Layout'
                                    }
                                ];
                            }

                            static get toolbox() {
                                return {
                                    title: 'Image',
                                    icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M19 3H5C3.89543 3 3 3.89543 3 5V19C3 20.1046 3.89543 21 5 21H19C20.1046 21 21 20.1046 21 19V5C21 3.89543 20.1046 3 19 3Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M8.5 10C9.32843 10 10 9.32843 10 8.5C10 7.67157 9.32843 7 8.5 7C7.67157 7 7 7.67157 7 8.5C7 9.32843 7.67157 10 8.5 10Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M21 15L16 10L5 21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
                                };
                            }

                            renderSettings() {
                                const wrapper = document.createElement('div');
                                this.settings.forEach(tune => {
                                    let button = document.createElement('div');
                                    button.classList.add('cdx-settings-button');
                                    button.innerHTML = tune.icon;
                                    button.title = tune.title;

                                    if (this.data[tune.name]) {
                                        button.classList.add('cdx-settings-button--active');
                                    }

                                    button.addEventListener('click', () => {
                                        this._toggleTune(tune.name);
                                        button.classList.toggle('cdx-settings-button--active');
                                    });

                                    wrapper.appendChild(button);
                                });
                                return wrapper;
                            }

                            _toggleTune(tune) {
                                this.data[tune] = !this.data[tune];
                                this._acceptTune(tune);
                            }

                            _acceptTune(tune) {
                                if (this.wrapper) {
                                    const imgContainer = this.wrapper.querySelector('.image-tool');
                                    if (imgContainer) {
                                        imgContainer.classList.toggle(`image-tool--${tune}`, !!this.data[tune]);
                                    }
                                }
                            }

                            render() {
                                this.wrapper = document.createElement('div');
                                this.wrapper.classList.add('ce-block__content');

                                if (this.data && this.data.file && this.data.file.url) {
                                    const imgContainer = document.createElement('div');
                                    imgContainer.classList.add('cdx-block', 'image-tool', 'image-tool--filled');

                                    // Default to boxed (withBackground) if not specified
                                    if (this.data.withBackground === undefined) this.data.withBackground = true;

                                    if (this.data.stretched) imgContainer.classList.add('image-tool--stretched');
                                    if (this.data.withBorder) imgContainer.classList.add('image-tool--withBorder');
                                    if (this.data.withBackground) imgContainer.classList.add('image-tool--withBackground');

                                    const imgWrapper = document.createElement('div');
                                    imgWrapper.classList.add('image-tool__image');

                                    const img = document.createElement('img');
                                    img.classList.add('image-tool__image-picture');
                                    img.src = this.data.file.url;

                                    // Use description/alt as the actual HTML alt attribute
                                    const altText = this.data.alt || this.data.description || '';
                                    img.alt = altText;

                                    // Consolidate 'description' into 'alt' for future saves
                                    this.data.alt = altText;

                                    imgWrapper.appendChild(img);
                                    imgContainer.appendChild(imgWrapper);

                                    const caption = document.createElement('div');
                                    caption.classList.add('cdx-input', 'image-tool__caption');
                                    caption.contentEditable = true;
                                    caption.dataset.placeholder = 'Enter a caption...';

                                    // Only show the actual caption text
                                    caption.innerHTML = this.data.caption || '';

                                    caption.addEventListener('input', () => {
                                        this.data.caption = caption.innerHTML;
                                    });

                                    // Append caption AFTER imgWrapper
                                    imgContainer.appendChild(caption);
                                    this.wrapper.appendChild(imgContainer);

                                    return this.wrapper;
                                }

                                const placeholder = document.createElement('div');
                                placeholder.className = 'cdx-input';
                                placeholder.textContent = 'Select or Upload Image...';
                                placeholder.style.cssText = 'cursor: pointer; color: #707684; text-align: center; padding: 20px; border: 1px dashed #E8E8EB; border-radius: 3px;';

                                placeholder.onclick = () => {
                                    const index = this.api.blocks.getCurrentBlockIndex();
                                    if (window.openImageModal) window.openImageModal(index);
                                };

                                this.wrapper.appendChild(placeholder);
                                return this.wrapper;
                            }

                            save(blockContent) {
                                return {
                                    file: { url: (this.data.file && this.data.file.url) ? this.data.file.url : '' },
                                    caption: this.data.caption || '',
                                    alt: this.data.alt || this.data.description || '',
                                    archive_id: this.data.archive_id || null,  // Preserve archive ID
                                    archive_slug: this.data.archive_slug || null,  // Preserve archive slug
                                    withBorder: !!this.data.withBorder,
                                    stretched: !!this.data.stretched,
                                    withBackground: !!this.data.withBackground
                                };
                            }
                        }
                    },
                    paragraph: {
                        // FIXED: Removed 'class: window.Paragraph' to prevent Editor crash
                        inlineToolbar: true
                    },
                    header: {
                        class: window.Header,
                        inlineToolbar: true,
                        config: {
                            placeholder: 'Enter a heading',
                            levels: [1, 2, 3, 4, 5, 6],
                            defaultLevel: 2
                        }
                    },
                    list: {
                        class: window.List,
                        inlineToolbar: true,
                        config: {
                            defaultStyle: 'unordered'
                        }
                    },
                    quote: {
                        class: window.Quote,
                        inlineToolbar: true,
                        config: {
                            quotePlaceholder: 'Enter a quote',
                            captionPlaceholder: 'Quote author',
                        },
                    },
                    embed: {
                        class: window.Embed,
                        config: {
                            services: {
                                youtube: true,
                                vimeo: true,
                                twitter: true
                            }
                        }
                    },
                    link: {
                        class: window.LinkTool,
                        config: { endpoint: '/api/fetch-url-meta/' }
                    },
                    delimiter: { class: window.Delimiter },
                    marker: { class: window.Marker, shortcut: 'CMD+SHIFT+M' },
                    code: { class: window.CodeTool }
                },
                data: options.data || {},
                onChange: function (api, event) {
                    if (options.onChange) options.onChange(api, event);
                    self.updateFeaturedImageOptions();
                },
                onReady: function () {
                    if (options.onReady) options.onReady();
                }
            };

            this.instance = new EditorJS(editorConfig);
            return this.instance;
        },

        // Simple editor for book reviews (no image tool)
        initSimple: function (holderId, options) {
            const self = this;
            options = options || {};

            // Dynamically build tools to prevent crashes if scripts are missing
            const tools = {
                paragraph: {
                    inlineToolbar: true
                }
            };

            if (window.Header) {
                tools.header = {
                    class: window.Header,
                    inlineToolbar: true,
                    config: {
                        placeholder: 'Enter a heading',
                        levels: [2, 3, 4],
                        defaultLevel: 2
                    }
                };
            }

            if (window.List) {
                tools.list = {
                    class: window.List,
                    inlineToolbar: true,
                    config: {
                        defaultStyle: 'unordered'
                    }
                };
            }

            if (window.Quote) {
                tools.quote = {
                    class: window.Quote,
                    inlineToolbar: true,
                    config: {
                        quotePlaceholder: 'Enter a quote',
                        captionPlaceholder: 'Quote author',
                    },
                };
            }

            if (window.LinkTool) {
                tools.link = {
                    class: window.LinkTool,
                    config: { endpoint: '/api/fetch-url-meta/' }
                };
            }

            if (window.Delimiter) tools.delimiter = { class: window.Delimiter };
            if (window.Marker) tools.marker = { class: window.Marker, shortcut: 'CMD+SHIFT+M' };
            if (window.CodeTool) tools.code = { class: window.CodeTool };

            const editorConfig = {
                holder: holderId,
                placeholder: options.placeholder || 'Start writing your content...',
                autofocus: options.autofocus !== false,
                tools: tools,
                data: options.data || {},
                onChange: function (api, event) {
                    if (options.onChange) options.onChange(api, event);
                },
                onReady: function () {
                    if (options.onReady) options.onReady();
                    console.log('Simple Editor.js initialized successfully');
                }
            };

            this.instance = new EditorJS(editorConfig);
            return this.instance;
        },

        uploadImage: function (file) {
            const self = this;
            return new Promise(function (resolve, reject) {
                const formData = new FormData();
                formData.append('image', file);

                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
                if (csrfToken) {
                    formData.append('csrfmiddlewaretoken', csrfToken.value);
                }

                fetch('/api/upload-image/', {
                    method: 'POST',
                    body: formData,
                    credentials: 'same-origin'
                })
                    .then(function (response) { return response.json(); })
                    .then(function (data) {
                        if (data.success === 1) {
                            resolve({
                                success: 1,
                                file: {
                                    url: data.file.url,
                                    caption: data.file.caption || '',
                                    alt: data.file.alt || ''
                                }
                            });
                        } else {
                            reject(data.error || 'Upload failed');
                        }
                    })
                    .catch(function (error) {
                        reject(error.message || 'Upload failed');
                    });
            });
        },

        getData: function () {
            if (this.instance) return this.instance.save();
            return Promise.resolve({ blocks: [] });
        },

        setData: function (data) {
            if (this.instance && data) return this.instance.render(data);
            return Promise.resolve();
        },

        clear: function () {
            if (this.instance) return this.instance.clear();
            return Promise.resolve();
        },

        isEmpty: function () {
            return this.getData().then(function (data) {
                if (!data.blocks || data.blocks.length === 0) return true;
                const hasContent = data.blocks.some(function (block) {
                    if (block.type === 'paragraph') {
                        return block.data.text && block.data.text.trim().length > 0;
                    }
                    return true;
                });
                return !hasContent;
            });
        },

        getImages: function () {
            return this.getData().then(function (data) {
                const images = [];
                if (data.blocks) {
                    data.blocks.forEach(function (block) {
                        if (block.type === 'image' && block.data && block.data.file && block.data.file.url) {
                            images.push({
                                url: block.data.file.url,
                                caption: block.data.caption || ''
                            });
                        }
                    });
                }
                return images;
            });
        },

        updateFeaturedImageOptions: function () {
            const self = this;
            const featuredSection = document.getElementById('featuredImageSection');
            const featuredGrid = document.getElementById('featuredImageGrid');
            const featuredInput = document.getElementById('featured_image_url');

            if (!featuredSection || !featuredGrid) return;

            this.getImages().then(function (images) {
                if (images.length === 0) {
                    featuredSection.style.display = 'none';
                    return;
                }

                featuredSection.style.display = 'block';
                featuredGrid.innerHTML = '';

                images.forEach(function (img, index) {
                    const option = document.createElement('div');
                    option.className = 'featured-option';

                    const isSelected = (index === 0 && !self.selectedFeaturedImage) ||
                        img.url === self.selectedFeaturedImage;

                    if (isSelected) {
                        option.classList.add('selected');
                        self.selectedFeaturedImage = img.url;
                        if (featuredInput) {
                            featuredInput.value = img.url;
                        }
                    }

                    option.innerHTML =
                        '<img src="' + img.url + '" alt="Image ' + (index + 1) + '">' +
                        (isSelected ? '<span class="featured-badge">Featured</span>' : '');

                    option.addEventListener('click', function () {
                        document.querySelectorAll('.featured-option').forEach(function (opt) {
                            opt.classList.remove('selected');
                            const badge = opt.querySelector('.featured-badge');
                            if (badge) badge.remove();
                        });

                        option.classList.add('selected');
                        const badge = document.createElement('span');
                        badge.className = 'featured-badge';
                        badge.textContent = 'Featured';
                        option.appendChild(badge);

                        self.selectedFeaturedImage = img.url;
                        if (featuredInput) {
                            featuredInput.value = img.url;
                        }
                    });

                    featuredGrid.appendChild(option);
                });
            });
        },

        openArchiveSelector: function (callback) {
            const self = this;
            const modal = document.getElementById('archiveModal');
            if (!modal) {
                console.error('Archive modal not found');
                return;
            }
            modal.classList.add('active');
            this.loadArchives('');
            this.archiveCallback = callback;
        },

        closeArchiveSelector: function () {
            const modal = document.getElementById('archiveModal');
            if (modal) {
                modal.classList.remove('active');
            }
            this.selectedArchive = null;
            this.archiveCallback = null;
        },

        loadArchives: function (search) {
            const self = this;
            const url = '/api/archive-media-browser/?search=' + encodeURIComponent(search) + '&type=image';
            const grid = document.getElementById('archiveGrid');

            if (!grid) return;

            grid.innerHTML = '<div class="flex justify-center py-8"><i class="fas fa-spinner fa-spin text-2xl text-vintage-gold"></i></div>';

            fetch(url)
                .then(function (response) { return response.json(); })
                .then(function (data) {
                    grid.innerHTML = '';

                    if (data.archives && data.archives.length > 0) {
                        data.archives.forEach(function (archive) {
                            const item = document.createElement('div');
                            item.className = 'archive-item';
                            item.dataset.archiveId = archive.id;
                            item.innerHTML =
                                '<img src="' + archive.thumbnail + '" alt="' + (archive.alt_text || archive.title) + '">' +
                                '<div class="archive-item-title">' + archive.title + '</div>';

                            item.addEventListener('click', function () {
                                document.querySelectorAll('.archive-item').forEach(function (el) {
                                    el.classList.remove('selected');
                                });
                                item.classList.add('selected');
                                self.selectedArchive = archive;

                                const insertBtn = document.getElementById('insertArchiveBtn');
                                if (insertBtn) {
                                    insertBtn.style.display = 'inline-flex';
                                }
                            });

                            grid.appendChild(item);
                        });
                    } else {
                        grid.innerHTML = '<p class="text-center text-muted py-8">No image archives found</p>';
                    }
                })
                .catch(function (error) {
                    console.error('Error loading archives:', error);
                    grid.innerHTML = '<p class="text-center text-red-600 py-8">Error loading archives</p>';
                });
        },

        insertSelectedArchive: function () {
            if (this.selectedArchive && this.archiveCallback) {
                this.archiveCallback(this.selectedArchive);
            }
            this.closeArchiveSelector();
        },

        convertHtmlToEditorJS: function (htmlContent) {
            const blocks = [];
            const div = document.createElement('div');
            div.innerHTML = htmlContent;

            const children = div.childNodes;
            for (let i = 0; i < children.length; i++) {
                const node = children[i];

                if (node.nodeType === Node.TEXT_NODE) {
                    const text = node.textContent.trim();
                    if (text) {
                        blocks.push({
                            type: 'paragraph',
                            data: { text: text }
                        });
                    }
                    continue;
                }

                if (node.nodeType !== Node.ELEMENT_NODE) continue;

                const tagName = node.tagName.toLowerCase();

                if (/^h[1-6]$/.test(tagName)) {
                    blocks.push({
                        type: 'header',
                        data: {
                            text: node.innerHTML,
                            level: parseInt(tagName.charAt(1))
                        }
                    });
                } else if (tagName === 'p') {
                    const img = node.querySelector('img');
                    if (img) {
                        blocks.push({
                            type: 'image',
                            data: {
                                file: { url: img.src },
                                caption: img.title || '', // Mapping title to caption
                                alt: img.alt || '', // Mapping alt correctly
                                withBorder: false,
                                stretched: false,
                                withBackground: false
                            }
                        });
                    } else {
                        const text = node.innerHTML.trim();
                        if (text) {
                            blocks.push({
                                type: 'paragraph',
                                data: { text: text }
                            });
                        }
                    }
                } else if (tagName === 'img') {
                    blocks.push({
                        type: 'image',
                        data: {
                            file: { url: node.src },
                            caption: node.title || '',
                            alt: node.alt || '',
                            withBorder: false,
                            stretched: false,
                            withBackground: false
                        }
                    });
                } else if (tagName === 'ul' || tagName === 'ol') {
                    const items = [];
                    node.querySelectorAll('li').forEach(function (li) {
                        items.push(li.innerHTML);
                    });
                    blocks.push({
                        type: 'list',
                        data: {
                            style: tagName === 'ol' ? 'ordered' : 'unordered',
                            items: items
                        }
                    });
                } else if (tagName === 'blockquote') {
                    blocks.push({
                        type: 'quote',
                        data: {
                            text: node.innerHTML,
                            caption: '',
                            alignment: 'left'
                        }
                    });
                } else if (tagName === 'pre') {
                    blocks.push({
                        type: 'code',
                        data: {
                            code: node.textContent
                        }
                    });
                } else if (tagName === 'hr') {
                    blocks.push({
                        type: 'delimiter',
                        data: {}
                    });
                } else {
                    const text = node.innerHTML.trim();
                    if (text) {
                        blocks.push({
                            type: 'paragraph',
                            data: { text: text }
                        });
                    }
                }
            }

            return {
                time: Date.now(),
                blocks: blocks,
                version: '2.28.2'
            };
        },

        renderToHtml: function (editorData) {
            if (!editorData || !editorData.blocks) {
                return '';
            }

            let html = '';
            editorData.blocks.forEach(function (block) {
                switch (block.type) {
                    case 'header':
                        const level = block.data.level || 2;
                        html += '<h' + level + '>' + block.data.text + '</h' + level + '>';
                        break;

                    case 'paragraph':
                        html += '<p>' + block.data.text + '</p>';
                        break;

                    case 'image':
                        const imgUrl = block.data.file ? block.data.file.url : block.data.url;
                        // UPDATED: Use the saved 'alt' field for the image tag
                        const altText = block.data.alt || block.data.description || block.data.caption || '';
                        const archiveSlug = block.data.archive_slug;

                        html += '<figure class="editor-image">';

                        // Wrap image in archive link if archive_slug exists
                        if (archiveSlug) {
                            html += '<a href="/archives/' + archiveSlug + '/" class="archive-image-link" title="View in Archives">';
                        }

                        html += '<img src="' + imgUrl + '" alt="' + altText + '"';
                        let imgClasses = [];
                        if (block.data.stretched) imgClasses.push('stretched');
                        if (block.data.withBorder) imgClasses.push('editor-image-bordered');
                        if (imgClasses.length > 0) html += ' class="' + imgClasses.join(' ') + '"';
                        html += '>';

                        if (archiveSlug) {
                            html += '</a>';
                        }

                        if (block.data.caption) {
                            html += '<figcaption>' + block.data.caption + '</figcaption>';
                        }
                        html += '</figure>';
                        break;

                    case 'list':
                        const tag = block.data.style === 'ordered' ? 'ol' : 'ul';
                        html += '<' + tag + '>';
                        block.data.items.forEach(function (item) {
                            if (typeof item === 'string') {
                                html += '<li>' + item + '</li>';
                            } else if (item.content) {
                                html += '<li>' + item.content + '</li>';
                            }
                        });
                        html += '</' + tag + '>';
                        break;

                    case 'quote':
                        html += '<blockquote>';
                        html += '<p>' + block.data.text + '</p>';
                        if (block.data.caption) {
                            html += '<cite>' + block.data.caption + '</cite>';
                        }
                        html += '</blockquote>';
                        break;

                    case 'code':
                        html += '<pre><code>' + block.data.code + '</code></pre>';
                        break;

                    case 'delimiter':
                        html += '<hr>';
                        break;

                    case 'embed':
                        html += '<div class="embed-container">';
                        html += '<iframe src="' + block.data.embed + '" allowfullscreen></iframe>';
                        if (block.data.caption) {
                            html += '<p class="embed-caption">' + block.data.caption + '</p>';
                        }
                        html += '</div>';
                        break;

                    case 'table':
                        html += '<table class="editor-table">';
                        if (block.data.withHeadings && block.data.content.length > 0) {
                            html += '<thead><tr>';
                            block.data.content[0].forEach(function (cell) {
                                html += '<th>' + cell + '</th>';
                            });
                            html += '</tr></thead>';
                            html += '<tbody>';
                            for (let i = 1; i < block.data.content.length; i++) {
                                html += '<tr>';
                                block.data.content[i].forEach(function (cell) {
                                    html += '<td>' + cell + '</td>';
                                });
                                html += '</tr>';
                            }
                            html += '</tbody>';
                        } else {
                            html += '<tbody>';
                            block.data.content.forEach(function (row) {
                                html += '<tr>';
                                row.forEach(function (cell) {
                                    html += '<td>' + cell + '</td>';
                                });
                                html += '</tr>';
                            });
                            html += '</tbody>';
                        }
                        html += '</table>';
                        break;

                    case 'warning':
                        html += '<div class="warning-block">';
                        html += '<strong>' + (block.data.title || 'Warning') + '</strong>';
                        html += '<p>' + block.data.message + '</p>';
                        html += '</div>';
                        break;

                    default:
                        if (block.data && block.data.text) {
                            html += '<p>' + block.data.text + '</p>';
                        }
                }
            });

            return html;
        }
    };
})();