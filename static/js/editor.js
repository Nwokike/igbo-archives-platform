(function () {
    'use strict';

    window.IgboEditor = {
        instance: null,
        selectedArchive: null,
        selectedFeaturedImage: null,

        init: function (holderId, options) {
            const self = this;
            options = options || {};

            const editorConfig = {
                holder: holderId,
                placeholder: options.placeholder || 'Start writing your content...',
                autofocus: options.autofocus !== false,
                tools: {
                    header: {
                        class: window.Header,
                        inlineToolbar: true,
                        config: {
                            placeholder: 'Enter a heading',
                            levels: [1, 2, 3, 4, 5, 6],
                            defaultLevel: 2
                        }
                    },
                    image: {
                        class: class ModalImageTool {
                            static get toolbox() {
                                return {
                                    title: 'Image',
                                    icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M19 3H5C3.89543 3 3 3.89543 3 5V19C3 20.1046 3.89543 21 5 21H19C20.1046 21 21 20.1046 21 19V5C21 3.89543 20.1046 3 19 3Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M8.5 10C9.32843 10 10 9.32843 10 8.5C10 7.67157 9.32843 7 8.5 7C7.67157 7 7 7.67157 7 8.5C7 9.32843 7.67157 10 8.5 10Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M21 15L16 10L5 21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
                                };
                            }

                            render() {
                                const wrapper = document.createElement('div');
                                wrapper.classList.add('ce-block__content');

                                // Create a placeholder that looks like an empty image block
                                const placeholder = document.createElement('div');
                                placeholder.className = 'cdx-input';
                                placeholder.textContent = 'Select or Upload Image...';
                                placeholder.style.cursor = 'pointer';
                                placeholder.style.color = '#707684';
                                placeholder.style.textAlign = 'center';
                                placeholder.style.padding = '20px';
                                placeholder.style.border = '1px dashed #E8E8EB';
                                placeholder.style.borderRadius = '3px';

                                placeholder.onclick = () => {
                                    if (window.openImageModal) {
                                        window.openImageModal();
                                    }
                                };

                                wrapper.appendChild(placeholder);

                                // Auto-open modal shortly after render
                                setTimeout(() => {
                                    if (window.openImageModal) {
                                        window.openImageModal();
                                    }
                                }, 50);

                                return wrapper;
                            }

                            save(blockContent) {
                                return {
                                    // This custom tool is just a trigger. 
                                    // The modal inserts a standard 'image' block which uses window.ImageTool
                                    // So this block itself doesn't need to save anything valuable 
                                    // because it gets REPLACED by the actual image block.
                                };
                            }
                        }
                    },
                    embed: {
                        class: window.Embed,
                        config: {
                            services: {
                                youtube: true,
                                vimeo: true,
                                twitter: true,
                                instagram: true,
                                facebook: true
                            }
                        }
                    },
                    link: {
                        class: window.LinkTool,
                        config: {
                            endpoint: '/api/fetch-url-meta/'
                        }
                    },
                    delimiter: {
                        class: window.Delimiter
                    },
                    marker: {
                        class: window.Marker,
                        shortcut: 'CMD+SHIFT+M'
                    },
                    code: {
                        class: window.CodeTool
                    }
                },
                data: options.data || {},
                onChange: function (api, event) {
                    if (options.onChange) {
                        options.onChange(api, event);
                    }
                    self.updateFeaturedImageOptions();
                },
                onReady: function () {
                    if (options.onReady) {
                        options.onReady();
                    }
                    console.log('Editor.js initialized successfully');
                }
            };

            this.instance = new EditorJS(editorConfig);
            return this.instance;
        },

        // Simple editor for book reviews - no image/embed tools
        initSimple: function (holderId, options) {
            const self = this;
            options = options || {};

            const editorConfig = {
                holder: holderId,
                placeholder: options.placeholder || 'Start writing your content...',
                autofocus: options.autofocus !== false,
                tools: {
                    header: {
                        class: window.Header,
                        inlineToolbar: true,
                        config: {
                            placeholder: 'Enter a heading',
                            levels: [2, 3, 4],
                            defaultLevel: 2
                        }
                    },
                    link: {
                        class: window.LinkTool,
                        config: {
                            endpoint: '/api/fetch-url-meta/'
                        }
                    },
                    delimiter: {
                        class: window.Delimiter
                    },
                    marker: {
                        class: window.Marker,
                        shortcut: 'CMD+SHIFT+M'
                    },
                    code: {
                        class: window.CodeTool
                    }
                },
                data: options.data || {},
                onChange: function (api, event) {
                    if (options.onChange) {
                        options.onChange(api, event);
                    }
                },
                onReady: function () {
                    if (options.onReady) {
                        options.onReady();
                    }
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
            if (this.instance) {
                return this.instance.save();
            }
            return Promise.resolve({ blocks: [] });
        },

        setData: function (data) {
            if (this.instance && data) {
                return this.instance.render(data);
            }
            return Promise.resolve();
        },

        clear: function () {
            if (this.instance) {
                return this.instance.clear();
            }
            return Promise.resolve();
        },

        isEmpty: function () {
            return this.getData().then(function (data) {
                if (!data.blocks || data.blocks.length === 0) {
                    return true;
                }
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
                                caption: img.alt || '',
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
                            caption: node.alt || '',
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
                        html += '<figure class="editor-image">';
                        html += '<img src="' + imgUrl + '" alt="' + (block.data.caption || '') + '"';
                        let imgClasses = [];
                        if (block.data.stretched) imgClasses.push('stretched');
                        if (block.data.withBorder) imgClasses.push('editor-image-bordered');
                        if (imgClasses.length > 0) html += ' class="' + imgClasses.join(' ') + '"';
                        html += '>';
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
