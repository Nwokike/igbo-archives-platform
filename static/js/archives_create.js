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

// Initialize on load and add change event listener
document.addEventListener('DOMContentLoaded', function () {
    var typeSelect = document.getElementById('id_archive_type');
    if (typeSelect) {
        updateFileInput();
        typeSelect.addEventListener('change', updateFileInput);
    }
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
