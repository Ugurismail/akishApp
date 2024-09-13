// answer_form.js

document.addEventListener('DOMContentLoaded', function() {
    const insertLinkBtn = document.getElementById('insert-link-btn');
    const linkModalElement = document.getElementById('linkModal');
    const linkModal = new bootstrap.Modal(linkModalElement);
    const linkForm = document.getElementById('link-form');
    const answerTextarea = document.getElementById('id_answer_text');

    insertLinkBtn.addEventListener('click', function() {
        linkModal.show();
    });

    linkForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const url = document.getElementById('link-url').value;
        const text = document.getElementById('link-text').value;
        if (url && text) {
            const linkMarkup = `<a href="${url}" class="custom-link">${text}</a>`;
            insertAtCursor(answerTextarea, linkMarkup);
            linkModal.hide();
            linkForm.reset();
        }
    });

    function insertAtCursor(textarea, text) {
        const startPos = textarea.selectionStart;
        const endPos = textarea.selectionEnd;
        const beforeValue = textarea.value.substring(0, startPos);
        const afterValue = textarea.value.substring(endPos, textarea.value.length);
        textarea.value = beforeValue + text + afterValue;
        textarea.selectionStart = textarea.selectionEnd = startPos + text.length;
        textarea.focus();
    }
});
