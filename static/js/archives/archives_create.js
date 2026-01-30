document.addEventListener('DOMContentLoaded', function () {
    const itemCountSelect = document.getElementById('id_item_count');
    const itemRows = document.querySelectorAll('.item-row');

    // 1. Logic to Show/Hide Item Rows based on Dropdown
    function updateItemCount() {
        const count = parseInt(itemCountSelect.value) || 1;
        
        itemRows.forEach((row, index) => {
            if (index < count) {
                row.classList.remove('hidden');
                // Optional: Scroll to new item if it was just revealed
                // if (row.classList.contains('hidden')) row.scrollIntoView({ behavior: 'smooth' });
            } else {
                row.classList.add('hidden');
                // Clear inputs in hidden rows to prevent validation errors? 
                // Better to handle in backend or let user keep data if they toggle back.
            }
        });
    }

    if (itemCountSelect) {
        itemCountSelect.addEventListener('change', updateItemCount);
        // Initial run in case of edit mode or validation error return
        updateItemCount(); 
    }

    // 2. Logic to Show/Hide File Inputs based on Item Type
    function updateFileInputs(selectElement) {
        const row = selectElement.closest('.item-row');
        const type = selectElement.value;
        const fileGroups = row.querySelectorAll('.file-group');

        // Hide all first
        fileGroups.forEach(group => group.classList.add('hidden'));

        // Show specific one
        if (type) {
            const specificGroup = row.querySelector(`.type-${type}`);
            if (specificGroup) {
                specificGroup.classList.remove('hidden');
            }
        }
    }

    // Attach listeners to all Type Selectors
    const typeSelects = document.querySelectorAll('.item-type-select');
    typeSelects.forEach(select => {
        select.addEventListener('change', function() {
            updateFileInputs(this);
        });
        
        // Initial run to set correct state
        updateFileInputs(select);
    });

    // 3. Autocomplete Logic (Preserved from previous version)
    setupAutocomplete('id_original_author', 'author-list', 'author');
    setupAutocomplete('id_circa_date', 'date-list', 'date');
});

// Helper for Autocomplete
function setupAutocomplete(inputId, datalistId, fieldName) {
    const input = document.getElementById(inputId);
    const datalist = document.getElementById(datalistId);
    if (!input || !datalist) return;

    input.addEventListener('input', function () {
        const query = this.value;
        if (query.length < 2) return;

        fetch(`/archives/suggestions/?q=${encodeURIComponent(query)}&field=${fieldName}`)
            .then(response => response.json())
            .then(data => {
                datalist.innerHTML = '';
                data.results.forEach(item => {
                    const option = document.createElement('option');
                    option.value = item;
                    datalist.appendChild(option);
                });
            })
            .catch(err => console.error('Error fetching suggestions:', err));
    });
}