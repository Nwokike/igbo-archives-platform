document.addEventListener('DOMContentLoaded', () => {
    // We attach autocomplete to inputs with these specific IDs
    // Archives/Lore: id_original_author, Book: author
    const authorInputs = [
        document.getElementById('id_original_author'),
        document.getElementById('author')
    ].filter(Boolean);

    // Associated bio textareas
    // Archives/Lore: id_original_author_about, Book: author_about
    const aboutInput = document.getElementById('id_original_author_about') || document.getElementById('author_about');

    if (authorInputs.length === 0 || !aboutInput) return;

    authorInputs.forEach(authorInput => {
        // Prepare DOM for the dropdown
        const container = authorInput.parentElement;
        container.style.position = 'relative';

        const dropdown = document.createElement('div');
        dropdown.className = 'absolute z-50 w-full mt-1 bg-surface border border-border shadow-soft rounded-b-lg max-h-60 overflow-y-auto hidden';
        container.appendChild(dropdown);

        let debounceTimer;

        // Fetch authors on typing
        authorInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            const query = e.target.value.trim();

            if (query.length < 2) {
                dropdown.innerHTML = '';
                dropdown.classList.add('hidden');

                // Allow manual typing in bio if they clear author string
                aboutInput.readOnly = false;
                aboutInput.classList.remove('bg-surface-alt/50', 'text-text-muted', 'cursor-not-allowed');
                return;
            }

            debounceTimer = setTimeout(async () => {
                try {
                    const response = await fetch(`/archives/author-suggestions/?q=${encodeURIComponent(query)}`);
                    const data = await response.json();

                    dropdown.innerHTML = '';

                    if (data.authors && data.authors.length > 0) {
                        data.authors.forEach(author => {
                            const item = document.createElement('div');
                            item.className = 'px-4 py-3 hover:bg-accent/10 cursor-pointer border-b border-border/50 last:border-0 transition-colors';

                            // Highlight matched text
                            const regex = new RegExp(`(${query})`, "gi");
                            const highlightedName = author.name.replace(regex, "<span class='text-accent font-bold'>$1</span>");

                            item.innerHTML = `
                                <div class="font-medium text-text">${highlightedName}</div>
                                ${author.description ? '<div class="text-xs text-text-muted mt-1 truncate"><i class="fas fa-check-circle text-accent/80 mr-1"></i> Bio available in database</div>' : ''}
                            `;

                            // Fill fields on select
                            item.addEventListener('click', () => {
                                authorInput.value = author.name;
                                dropdown.classList.add('hidden');

                                if (author.description) {
                                    aboutInput.value = author.description;
                                    aboutInput.readOnly = true;
                                    aboutInput.classList.add('bg-surface-alt/50', 'text-text-muted', 'cursor-not-allowed');
                                } else {
                                    aboutInput.value = '';
                                    aboutInput.readOnly = false;
                                    // Let the about box know they can type freely
                                    aboutInput.classList.remove('bg-surface-alt/50', 'text-text-muted', 'cursor-not-allowed');
                                    aboutInput.focus();
                                }
                            });

                            dropdown.appendChild(item);
                        });
                        dropdown.classList.remove('hidden');
                    } else {
                        dropdown.classList.add('hidden');
                        // No match -> they are creating a new one -> keep bio field editable
                        aboutInput.readOnly = false;
                        aboutInput.classList.remove('bg-surface-alt/50', 'text-text-muted', 'cursor-not-allowed');
                    }
                } catch (error) {
                    console.error('Error fetching author suggestions:', error);
                }
            }, 300);
        });

        // Hide dropdown on outside click
        document.addEventListener('click', (e) => {
            if (!container.contains(e.target)) {
                dropdown.classList.add('hidden');
            }
        });
    });
});
