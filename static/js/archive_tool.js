/**
 * ArchiveTool for Editor.js
 */
class ArchiveTool {
    static get toolbox() {
        return {
            title: 'Import Archive',
            icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 6H20M4 12H20M4 18H20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>' // Simple list icon for now, or maybe a database icon
        };
    }

    constructor({ data, api, config }) {
        this.data = data;
        this.api = api;
        this.config = config;
        this.wrapper = undefined;
    }

    render() {
        this.wrapper = document.createElement('div');
        this.wrapper.classList.add('cdx-block');

        // If we already have data, render an image block style or placeholder
        if (this.data && this.data.url) {
            // Render as image preview
            const img = document.createElement('img');
            img.src = this.data.url;
            img.style.maxWidth = '100%';
            this.wrapper.appendChild(img);
            return this.wrapper;
        }

        // Otherwise, trigger the modal logic. 
        // Since render is synchronous, we create a placeholder and trigger UI after.
        const placeholder = document.createElement('div');
        placeholder.className = 'cdx-input';
        placeholder.textContent = 'Select an archive to import...';
        placeholder.style.cursor = 'pointer';
        placeholder.onclick = () => this.openModal();

        this.wrapper.appendChild(placeholder);

        // Auto-open if it's a fresh block
        setTimeout(() => {
            this.openModal();
        }, 50);

        return this.wrapper;
    }

    openModal() {
        // Use the existing IgboEditor.openArchiveSelector
        if (window.IgboEditor) {
            // Open the image modal and switch to archive tab
            const modal = document.getElementById('imageModal');
            if (modal) {
                modal.classList.add('active');

                // Switch tabs
                const tabs = modal.querySelectorAll('.tab-button');
                const panels = modal.querySelectorAll('.tab-panel');

                tabs.forEach(t => t.classList.remove('active'));
                panels.forEach(p => p.classList.remove('active'));

                const archiveTab = modal.querySelector('[data-tab="archive"]');
                const archivePanel = document.getElementById('archive-panel');

                if (archiveTab) archiveTab.classList.add('active');
                if (archivePanel) archivePanel.classList.add('active');

                // Trigger load
                window.IgboEditor.loadArchives('');

                // Override the insert button behavior for this specific instance
                const insertBtn = document.getElementById('insertArchiveBtn');
                const originalOnClick = insertBtn.onclick;

                // Define the one-time insertion logic
                const handleInsert = () => {
                    const selected = window.IgboEditor.selectedArchive;
                    if (selected) {
                        // Replace this block with an image block
                        const currentBlockIndex = this.api.blocks.getCurrentBlockIndex();

                        this.api.blocks.insert('image', {
                            file: { url: selected.thumbnail || selected.image },
                            caption: selected.title + ' - ' + (selected.description || ''),
                            withBorder: false,
                            withBackground: false,
                            stretched: false
                        }, {}, currentBlockIndex, true); // replace: true is not a standard arg in all versions, but we can delete and insert.

                        // Actually, generic Editor.js doesn't support 'replace' in insert easily.
                        // We can delete current block and insert new one.
                        this.api.blocks.delete(currentBlockIndex);
                    }

                    // Reset UI
                    window.IgboEditor.closeArchiveSelector();

                    // Restore button behavior (cleanup)
                    // insertBtn.onclick = originalOnClick; // This might be tricky if event listeners are bound via attributes.
                    // Since the existing modal uses onclick="insertSelectedArchive()", we can just hook into the global assignment if we want,
                    // OR rely on IgboEditor.archiveCallback.
                };

                // Use the callback mechanism we already have in editor.js
                window.IgboEditor.archiveCallback = (archive) => {
                    const currentBlockIndex = this.api.blocks.getCurrentBlockIndex();
                    this.api.blocks.delete(currentBlockIndex);
                    this.api.blocks.insert('image', {
                        file: { url: archive.thumbnail || archive.image },
                        caption: archive.title + ' - ' + (archive.description || ''),
                        withBorder: false,
                        withBackground: false,
                        stretched: false
                    }, {}, currentBlockIndex);
                };

                // We don't need to override the button click if `insertSelectedArchive` calls `window.IgboEditor.insertSelectedArchive()` which calls `this.archiveCallback`.
                // Let's verify `editor.js` logic.
                // Yes: insertSelectedArchive calls this.archiveCallback.
            }
        }
    }

    save(blockContent) {
        return {
            // If for some reason we save the archive block itself
            url: blockContent.querySelector('img') ? blockContent.querySelector('img').src : ''
        };
    }
}

window.ArchiveTool = ArchiveTool;
