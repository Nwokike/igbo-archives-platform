function initViewToggle(gridId, storageKey) {
    var gridBtn = document.getElementById('gridViewBtn');
    var listBtn = document.getElementById('listViewBtn');
    var grid = document.getElementById(gridId);

    if (!gridBtn || !listBtn || !grid) return;

    function setView(view) {
        if (view === 'list') {
            grid.className = 'grid grid-cols-1 gap-3';
            grid.setAttribute('data-view', 'list');
            gridBtn.classList.remove('active', 'bg-white', 'dark:bg-surface-dark', 'text-accent', 'shadow-sm');
            listBtn.classList.add('active', 'bg-white', 'dark:bg-surface-dark', 'text-accent', 'shadow-sm');
        } else {
            grid.className = 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4';
            grid.setAttribute('data-view', 'grid');
            listBtn.classList.remove('active', 'bg-white', 'dark:bg-surface-dark', 'text-accent', 'shadow-sm');
            gridBtn.classList.add('active', 'bg-white', 'dark:bg-surface-dark', 'text-accent', 'shadow-sm');
        }
        try {
            localStorage.setItem(storageKey, view);
        } catch (storageError) {
            // Silently fail if localStorage is blocked by tracking prevention
        }
    }

    gridBtn.addEventListener('click', function () { setView('grid'); });
    listBtn.addEventListener('click', function () { setView('list'); });

    let savedView = 'grid';
    try {
        savedView = localStorage.getItem(storageKey) || 'grid';
    } catch (storageError) {
        // Silently fail if localStorage is blocked by tracking prevention
    }
    setView(savedView);
}

document.addEventListener('DOMContentLoaded', function () {
    if (document.getElementById('archiveGrid')) {
        initViewToggle('archiveGrid', 'archivesView');
    }
    if (document.getElementById('loreGrid')) {
        initViewToggle('loreGrid', 'loreView');
    }
    if (document.getElementById('booksGrid')) {
        initViewToggle('booksGrid', 'booksView');
    }
});
