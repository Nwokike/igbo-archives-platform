function initViewToggle(gridId, storageKey) {
    var gridBtn = document.getElementById('gridViewBtn');
    var listBtn = document.getElementById('listViewBtn');
    var grid = document.getElementById(gridId);
    
    if (!gridBtn || !listBtn || !grid) return;
    
    function setView(view) {
        if (view === 'list') {
            grid.className = 'space-y-4';
            gridBtn.classList.remove('bg-white', 'text-dark-brown', 'shadow-soft');
            listBtn.classList.add('bg-white', 'text-dark-brown', 'shadow-soft');
        } else {
            grid.className = 'archive-grid';
            listBtn.classList.remove('bg-white', 'text-dark-brown', 'shadow-soft');
            gridBtn.classList.add('bg-white', 'text-dark-brown', 'shadow-soft');
        }
        localStorage.setItem(storageKey, view);
    }
    
    gridBtn.addEventListener('click', function() { setView('grid'); });
    listBtn.addEventListener('click', function() { setView('list'); });
    
    var savedView = localStorage.getItem(storageKey) || 'grid';
    setView(savedView);
}

document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('archiveGrid')) {
        initViewToggle('archiveGrid', 'archivesView');
    }
    if (document.getElementById('insightsGrid')) {
        initViewToggle('insightsGrid', 'insightsView');
    }
    if (document.getElementById('booksGrid')) {
        initViewToggle('booksGrid', 'booksView');
    }
});
