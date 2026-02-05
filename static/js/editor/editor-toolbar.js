/**
 * Editor Toolbar - Provides quick-access buttons above the Editor.js instance
 * Creates a WordPress-like toolbar with common formatting options
 */
(function () {
    'use strict';

    window.EditorToolbar = {
        editor: null,
        container: null,

        /**
         * Initialize the toolbar
         * @param {EditorJS} editorInstance - The Editor.js instance
         * @param {string} editorHolderId - The ID of the editor container
         * @param {Object} options - Configuration options
         */
        init: function (editorInstance, editorHolderId, options) {
            this.editor = editorInstance;
            options = options || {};

            var editorHolder = document.getElementById(editorHolderId);
            if (!editorHolder) {
                console.warn('EditorToolbar: Editor holder not found');
                return;
            }

            // Create toolbar container
            this.container = document.createElement('div');
            this.container.className = 'editor-toolbar';
            this.container.id = 'editor-toolbar';

            // Define toolbar buttons
            var buttons = [
                { icon: 'fa-heading', title: 'Add Header (H2)', action: this.insertHeader.bind(this, 2), label: 'H2' },
                { icon: 'fa-heading', title: 'Add Subheader (H3)', action: this.insertHeader.bind(this, 3), label: 'H3', small: true },
                { type: 'divider' },
                { icon: 'fa-paragraph', title: 'Add Paragraph', action: this.insertParagraph.bind(this) },
                { icon: 'fa-list-ul', title: 'Add Bulleted List', action: this.insertList.bind(this, 'unordered') },
                { icon: 'fa-list-ol', title: 'Add Numbered List', action: this.insertList.bind(this, 'ordered') },
                { type: 'divider' },
                { icon: 'fa-quote-left', title: 'Add Quote', action: this.insertQuote.bind(this) },
                { icon: 'fa-code', title: 'Add Code Block', action: this.insertCode.bind(this) },
                { icon: 'fa-minus', title: 'Add Divider', action: this.insertDelimiter.bind(this) },
            ];

            // Add image button if image tool is available
            if (options.hasImageTool !== false) {
                buttons.splice(6, 0, { type: 'divider' });
                buttons.splice(7, 0, { icon: 'fa-image', title: 'Add Image', action: this.insertImage.bind(this), highlight: true });
            }

            // Build toolbar HTML
            buttons.forEach(function (btn) {
                if (btn.type === 'divider') {
                    var divider = document.createElement('span');
                    divider.className = 'editor-toolbar-divider';
                    this.container.appendChild(divider);
                } else {
                    var button = document.createElement('button');
                    button.type = 'button';
                    button.className = 'editor-toolbar-btn' + (btn.highlight ? ' editor-toolbar-btn-primary' : '') + (btn.small ? ' editor-toolbar-btn-small' : '');
                    button.title = btn.title;
                    button.innerHTML = '<i class="fas ' + btn.icon + '"></i>' + (btn.label ? '<span class="editor-toolbar-label">' + btn.label + '</span>' : '');
                    button.addEventListener('click', btn.action);
                    this.container.appendChild(button);
                }
            }.bind(this));

            // Insert toolbar before editor
            editorHolder.parentNode.insertBefore(this.container, editorHolder);

            console.log('EditorToolbar initialized');
        },

        insertHeader: function (level) {
            if (!this.editor) return;
            this.editor.blocks.insert('header', { text: '', level: level });
            this.focusLastBlock();
        },

        insertParagraph: function () {
            if (!this.editor) return;
            this.editor.blocks.insert('paragraph', { text: '' });
            this.focusLastBlock();
        },

        insertList: function (style) {
            if (!this.editor) return;
            this.editor.blocks.insert('list', { style: style, items: [''] });
            this.focusLastBlock();
        },

        insertQuote: function () {
            if (!this.editor) return;
            this.editor.blocks.insert('quote', { text: '', caption: '' });
            this.focusLastBlock();
        },

        insertCode: function () {
            if (!this.editor) return;
            this.editor.blocks.insert('code', { code: '' });
            this.focusLastBlock();
        },

        insertDelimiter: function () {
            if (!this.editor) return;
            this.editor.blocks.insert('delimiter', {});
            // Add a paragraph after delimiter for continued writing
            this.editor.blocks.insert('paragraph', { text: '' });
            this.focusLastBlock();
        },

        insertImage: function () {
            // Check if there's a custom image modal function (for insights)
            if (typeof window.openImageModal === 'function') {
                window.openImageModal();
            } else if (typeof window.showMediaModal === 'function') {
                window.showMediaModal();
            } else {
                // Use default Editor.js image if available
                if (!this.editor) return;
                this.editor.blocks.insert('image', {
                    file: { url: '' },
                    caption: '',
                    withBorder: false,
                    stretched: false,
                    withBackground: false
                });
                this.focusLastBlock();
            }
        },

        focusLastBlock: function () {
            var self = this;
            setTimeout(function () {
                if (self.editor && self.editor.caret) {
                    var lastBlockIndex = self.editor.blocks.getBlocksCount() - 1;
                    self.editor.caret.setToBlock(lastBlockIndex, 'start');
                }
            }, 100);
        }
    };
})();
