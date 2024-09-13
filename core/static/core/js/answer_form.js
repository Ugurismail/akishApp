// answer_form.js

document.addEventListener('DOMContentLoaded', function() {
    const insertLinkBtns = document.querySelectorAll('.insert-link-btn');
    const formatBtns = document.querySelectorAll('.format-btn');
    const linkModalElement = document.getElementById('linkModal');
    const linkModal = new bootstrap.Modal(linkModalElement);
    const linkForm = document.getElementById('link-form');
    let currentTextarea = null;

    insertLinkBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            currentTextarea = this.closest('form').querySelector('textarea');
            linkModal.show();
        });
    });

    formatBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            currentTextarea = this.closest('form').querySelector('textarea');
            const format = this.getAttribute('data-format');
            let tag;
            if (format === 'bold') {
                tag = 'strong';
            } else if (format === 'italic') {
                tag = 'em';
            }
            if (tag && currentTextarea) {
                wrapSelectionWithTag(currentTextarea, tag);
                currentTextarea.focus();
            }
        });
    });

    linkForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const url = document.getElementById('link-url').value;
        const text = document.getElementById('link-text').value;
        if (url && text && currentTextarea) {
            const linkMarkup = `<a href="${url}" class="custom-link">${text}</a>`;
            insertAtCursor(currentTextarea, linkMarkup);
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
    }

    function wrapSelectionWithTag(textarea, tag) {
        const startPos = textarea.selectionStart;
        const endPos = textarea.selectionEnd;
        const selectedText = textarea.value.substring(startPos, endPos);
        const beforeValue = textarea.value.substring(0, startPos);
        const afterValue = textarea.value.substring(endPos, textarea.value.length);
        const newText = `<${tag}>${selectedText}</${tag}>`;
        textarea.value = beforeValue + newText + afterValue;
        textarea.selectionStart = startPos;
        textarea.selectionEnd = startPos + newText.length;
    }
});
