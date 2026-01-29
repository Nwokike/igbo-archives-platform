function updateFileInput() {
    var typeSelect = document.getElementById('id_archive_type');
    if (!typeSelect) return;

    var type = typeSelect.value;
    var sections = ['imageUploadSection', 'videoUploadSection', 'documentUploadSection', 'audioUploadSection', 'featuredImageSection'];
    sections.forEach(function (s) {
        var el = document.getElementById(s);
        if (el) el.classList.add('hidden');
    });

    if (type === 'image') {
        document.getElementById('imageUploadSection').classList.remove('hidden');
    } else if (type === 'video') {
        document.getElementById('videoUploadSection').classList.remove('hidden');
        document.getElementById('featuredImageSection').classList.remove('hidden');
    } else if (type === 'document') {
        document.getElementById('documentUploadSection').classList.remove('hidden');
    } else if (type === 'audio') {
        document.getElementById('audioUploadSection').classList.remove('hidden');
        document.getElementById('featuredImageSection').classList.remove('hidden');
    }
}

// Metadata suggestions
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

// Initialize on load and add change event listener
document.addEventListener('DOMContentLoaded', function () {
    var typeSelect = document.getElementById('id_archive_type');
    if (typeSelect) {
        updateFileInput();
        typeSelect.addEventListener('change', updateFileInput);
    }

    // Setup metadata autocomplete
    setupAutocomplete('id_original_author', 'author-list', 'author');
    setupAutocomplete('id_circa_date', 'date-list', 'date');
});

function validateFileSize(input, maxMB) {
    var errorDiv = document.getElementById('uploadError');
    if (input.files[0] && input.files[0].size > maxMB * 1024 * 1024) {
        errorDiv.textContent = 'File is too large. Maximum size is ' + maxMB + 'MB.';
        errorDiv.classList.remove('hidden');
        input.value = '';
    } else {
        errorDiv.classList.add('hidden');
    }
}
