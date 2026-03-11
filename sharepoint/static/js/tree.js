// Folder tree interactivity

function toggleFolder(icon) {
    const li = icon.closest('.tree-item');
    const children = li.querySelector('.tree-children');
    if (children) {
        children.classList.toggle('d-none');
        icon.classList.toggle('collapsed');
    }
}

// Initialize: expand all folders by default
document.addEventListener('DOMContentLoaded', function() {
    // All children are visible by default; no collapsed class needed

    // Drag-and-drop for documents (future enhancement placeholder)
    const docRows = document.querySelectorAll('.engagement-table tbody tr[draggable]');
    const treeNodes = document.querySelectorAll('.tree-node[data-folder-id]');

    treeNodes.forEach(node => {
        node.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.style.backgroundColor = '#d6e4f0';
        });
        node.addEventListener('dragleave', function(e) {
            this.style.backgroundColor = '';
        });
        node.addEventListener('drop', function(e) {
            e.preventDefault();
            this.style.backgroundColor = '';
            const docId = e.dataTransfer.getData('text/plain');
            const folderId = this.dataset.folderId;
            if (docId && folderId) {
                moveDocument(docId, folderId);
            }
        });
    });
});

function moveDocument(docId, folderId) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/document/' + docId + '/move';

    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'folder_id';
    input.value = folderId;
    form.appendChild(input);

    document.body.appendChild(form);
    form.submit();
}
