// vote_save.js

document.addEventListener('DOMContentLoaded', function() {
    const voteButtons = document.querySelectorAll('.vote-btn');
    const saveButtons = document.querySelectorAll('.save-btn');

    voteButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const contentType = this.getAttribute('data-content-type');
            const objectId = this.getAttribute('data-object-id');
            const value = this.getAttribute('data-value');

            fetch('/vote/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `content_type=${contentType}&object_id=${objectId}&value=${value}`,
            })
            .then(response => response.json())
            .then(data => {
                if (contentType === 'question') {
                    document.getElementById('question-votes').textContent = data.votes;
                } else if (contentType === 'answer') {
                    document.getElementById(`answer-votes-${objectId}`).textContent = data.votes;
                }
            });
        });
    });

    saveButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const contentType = this.getAttribute('data-content-type');
            const objectId = this.getAttribute('data-object-id');

            fetch('/save-item/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `content_type=${contentType}&object_id=${objectId}`,
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'saved') {
                    btn.innerHTML = '<i class="fa-solid fa-bookmark"></i> Kaydedildi';
                } else if (data.status === 'removed') {
                    btn.innerHTML = '<i class="fa-solid fa-bookmark"></i> Kaydet';
                }
            });
        });
    });

    // CSRF tokenını almak için yardımcı fonksiyon
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                // Bu çerez istenen çerez mi?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
