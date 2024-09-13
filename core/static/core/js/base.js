// base.js

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');

    searchInput.addEventListener('keyup', function() {
        const query = searchInput.value;
        if (query.length > 1) {
            fetch(`/search/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    searchResults.innerHTML = '';
                    if (data.results.length > 0) {
                        const ul = document.createElement('ul');
                        data.results.forEach(item => {
                            const li = document.createElement('li');
                            li.textContent = item.question_text;
                            li.addEventListener('click', function() {
                                window.location.href = `/question/${item.id}/`;
                            });
                            ul.appendChild(li);
                        });
                        searchResults.appendChild(ul);
                    } else {
                        searchResults.innerHTML = '<p>Sonuç bulunamadı.</p>';
                    }
                });
        } else {
            searchResults.innerHTML = '';
        }
    });

    // Arama sonuçları dışında bir yere tıklanınca sonuçları gizle
    document.addEventListener('click', function(event) {
        if (!searchInput.contains(event.target)) {
            searchResults.innerHTML = '';
        }
    });
});
