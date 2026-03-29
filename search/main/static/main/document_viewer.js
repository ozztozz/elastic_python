console.log('document_viewer.js loaded');
// main/static/main/document_viewer.js
// Adds modal document viewer functionality

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.open-doc-viewer').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const modalId = btn.getAttribute('data-modal-id');
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.remove('hidden');
                // Scroll to matched sentence
                const matchedSentence = btn.getAttribute('data-snippet');
                if (matchedSentence) {
                    const contentDiv = modal.querySelector('.overflow-auto');
                    if (contentDiv) {
                        // Normalize whitespace for matching
                        const normSentence = matchedSentence.replace(/\s+/g, ' ').trim();
                        let found = false;
                        console.log('Trying to scroll to sentence:', normSentence);
                        const allSentences = contentDiv.querySelectorAll('.fulltext-sentence');
                        console.log('Number of .fulltext-sentence elements:', allSentences.length);
                        allSentences.forEach(function(el, idx) {
                            const elNorm = el.textContent.replace(/\s+/g, ' ').trim();
                            console.log('Sentence', idx, ':', elNorm);
                            if (elNorm.includes(normSentence)) {
                                console.log('Match found, scrolling to:', elNorm);
                                el.scrollIntoView({behavior: 'smooth', block: 'center'});
                                // Highlight the matched sentence
                                el.style.backgroundColor = '#fff59d'; // light yellow
                                setTimeout(function() {
                                    el.style.transition = 'background-color 1.5s';
                                    el.style.backgroundColor = '';
                                }, 2000);
                                found = true;
                            }
                        });
                        // Fallback: search in the raw text and scroll to the first occurrence
                        if (!found) {
                            const idx = contentDiv.textContent.replace(/\s+/g, ' ').indexOf(normSentence);
                            if (idx !== -1) {
                                // Estimate scroll position by ratio
                                console.log('No element match, fallback scroll to index:', idx);
                                const ratio = idx / contentDiv.textContent.length;
                                contentDiv.scrollTop = ratio * contentDiv.scrollHeight;
                            } else {
                                console.log('No match found for sentence in modal content.');
                            }
                        }
                    }
                }
            }
        });
    });
    document.querySelectorAll('.close-doc-viewer').forEach(function(btn) {
        btn.addEventListener('click', function() {
            btn.closest('.doc-viewer-modal').classList.add('hidden');
        });
    });
});
