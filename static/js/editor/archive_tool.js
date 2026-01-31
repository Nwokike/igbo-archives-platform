/**
 * ArchiveTool for Editor.js
 * Enables importing existing archives directly into the editor content.
 */
class ArchiveTool {
    static get toolbox() {
        return {
            title: 'Import Archive',
            icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 6H20M4 12H20M4 18H20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>' 
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
            const img = document.createElement('img');
            img.src = this.data.url;
            img.style.maxWidth = '100%';
            this.wrapper.appendChild(img);
            return this.wrapper;
        }

        // Placeholder that triggers the modal
        const placeholder = document.createElement('div');
        placeholder.className = 'cdx-input';
        placeholder.textContent = 'Select an archive to import...';
        placeholder.style.cursor = 'pointer';
        placeholder.onclick = () => this.openModal();

        this.wrapper.appendChild(placeholder);

        // Auto-open if it's a fresh block
        setTimeout(() => {
            if (!this.data || !this.data.url) {
                this.openModal();
            }
        }, 50);

        return this.wrapper;
    }

    openModal() {
        if (window.IgboEditor) {
            const modal = document.getElementById('imageModal');
            if (modal) {
                modal.classList.add('active');

                // Switch to Archive Tab
                const tabs = modal.querySelectorAll('.tab-button');
                const panels = modal.querySelectorAll('.tab-panel');

                tabs.forEach(t => t.classList.remove('active'));
                panels.forEach(p => p.classList.remove('active'));

                const archiveTab = modal.querySelector('[data-img-tab="archive"]'); // Updated selector to match HTML
                const archivePanel = document.getElementById('archive-panel');

                if (archiveTab) archiveTab.classList.add('active');
                if (archivePanel) {
                    archivePanel.classList.add('active');
                    archivePanel.classList.remove('hidden'); // Ensure visibility helper is toggled
                }

                // Trigger load
                if (window.IgboEditor.loadArchives) {
                    window.IgboEditor.loadArchives('');
                }

                // Define the callback for when an item is clicked in the modal
                window.IgboEditor.archiveCallback = (archive) => {
                    const currentBlockIndex = this.api.blocks.getCurrentBlockIndex();
                    
                    // We delete the temporary "Import Archive" block and replace it with a real Image block
                    this.api.blocks.delete(currentBlockIndex);
                    
                    // Use the helper to format the caption consistently
                    let caption = archive.caption || archive.title;
                    if (window.IgboEditor.formatCaption) {
                        caption = window.IgboEditor.formatCaption(
                            caption,
                            archive.original_author,
                            archive.copyright_holder
                        );
                    }

                    this.api.blocks.insert('image', {
                        file: { url: archive.thumbnail || archive.image || archive.url },
                        caption: caption,
                        alt: archive.alt_text || archive.title || '',
                        archive_id: archive.id,
                        archive_slug: archive.slug || null,
                        withBorder: false,
                        withBackground: false,
                        stretched: false
                    }, {}, currentBlockIndex);
                    
                    // Close modal handled by the item click listener in insight-editor.js usually, 
                    // but we ensure clean state here.
                    window.IgboEditor.closeArchiveSelector();
                };
            }
        }
    }

    save(blockContent) {
        return {
            url: blockContent.querySelector('img') ? blockContent.querySelector('img').src : ''
        };
    }
}

window.ArchiveTool = ArchiveTool;