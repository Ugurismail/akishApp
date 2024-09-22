// vote_save.js

document.addEventListener('DOMContentLoaded', function() {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

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
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `content_type=${contentType}&object_id=${objectId}&value=${value}`,
            })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text) });
                }
                return response.json();
            })
            .then(data => {
                if (data.upvotes !== undefined && data.downvotes !== undefined) {
                    if (contentType === 'question') {
                        document.getElementById('question-upvotes').innerText = data.upvotes;
                        document.getElementById('question-downvotes').innerText = data.downvotes;
                    } else if (contentType === 'answer') {
                        document.getElementById(`answer-upvotes-${objectId}`).innerText = data.upvotes;
                        document.getElementById(`answer-downvotes-${objectId}`).innerText = data.downvotes;
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
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
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `content_type=${contentType}&object_id=${objectId}`,
            })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text) });
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'saved') {
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                } else if (data.status === 'removed') {
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
});
