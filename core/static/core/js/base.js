document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');

    searchInput.addEventListener('input', function() {
        const query = this.value.trim();

        if (query.length > 1) {
            fetch(`/search/?q=${encodeURIComponent(query)}&ajax=1`)
                .then(response => response.json())
                .then(data => {
                    searchResults.innerHTML = '';
                    data.results.forEach(result => {
                        const item = document.createElement('a');
                        item.href = `/question/${result.id}/`;
                        item.classList.add('list-group-item', 'list-group-item-action');
                        item.textContent = result.question_text;
                        searchResults.appendChild(item);
                    });
                });
        } else {
            searchResults.innerHTML = '';
        }
    });

    // Close search results when clicking outside
    document.addEventListener('click', function(event) {
        if (!searchInput.contains(event.target)) {
            searchResults.innerHTML = '';
        }
    });
});
