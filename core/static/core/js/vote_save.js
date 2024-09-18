// vote_save.js

document.addEventListener('DOMContentLoaded', function() {
    // CSRF tokenını almak için fonksiyon
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Bu çerez, aradığımız isimle başlıyor mu?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Oy verme butonları
    const voteButtons = document.querySelectorAll('.vote-btn');

    voteButtons.forEach(btn => {
        btn.addEventListener('click', function(event) {
            event.preventDefault();
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
                if (data.votes !== undefined) {
                    if (contentType === 'question') {
                        document.getElementById('question-votes').innerText = data.votes;
                    } else if (contentType === 'answer') {
                        document.getElementById(`answer-votes-${objectId}`).innerText = data.votes;
                    }
                }
            });
        });
    });

    // Kaydetme butonları
    const saveButtons = document.querySelectorAll('.save-btn');

    saveButtons.forEach(btn => {
        btn.addEventListener('click', function(event) {
            event.preventDefault();
            const contentType = this.getAttribute('data-content-type');
            const objectId = this.getAttribute('data-object-id');
            const icon = this.querySelector('i');

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
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                } else if (data.status === 'removed') {
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                }
            });
        });
    });
});
