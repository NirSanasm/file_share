document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('file-upload');
    const dropZone = document.getElementById('drop-zone');
    const pasteBtn = document.getElementById('paste-btn');
    const textArea = document.getElementById('paste-content');
    const fileInfo = document.getElementById('file-info');

    let selectedFile = null;

    // File Input Change
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });
    }

    // Drag and Drop
    if (dropZone) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
        });

        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                handleFileSelect(files[0]);
            }
        });

        dropZone.addEventListener('click', () => {
            fileInput.click();
        });
    }

    function handleFileSelect(file) {
        selectedFile = file;
        fileInfo.textContent = `Selected: ${file.name} (${formatBytes(file.size)})`;
        textArea.disabled = true;
        textArea.placeholder = "File selected. Clear file to paste text.";
        dropZone.style.borderColor = 'var(--accent-color)';
    }

    // Paste Action
    if (pasteBtn) {
        pasteBtn.addEventListener('click', async () => {
            if (!textArea.value.trim() && !selectedFile) {
                showToast('Please enter text or select a file.');
                return;
            }

            pasteBtn.disabled = true;
            pasteBtn.textContent = 'Uploading...';

            const formData = new FormData();

            if (selectedFile) {
                formData.append('file', selectedFile);
            } else {
                formData.append('text', textArea.value);
            }

            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    window.location.href = data.url;
                } else {
                    const err = await response.text();
                    showToast('Error: ' + err);
                    pasteBtn.disabled = false;
                    pasteBtn.textContent = 'Create Paste';
                }
            } catch (error) {
                console.error('Error:', error);
                showToast('Upload failed.');
                pasteBtn.disabled = false;
                pasteBtn.textContent = 'Create Paste';
            }
        });
    }

    // Format bytes
    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    // Toast Notification
    function showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        document.body.appendChild(toast);

        // Trigger reflow
        toast.offsetHeight;

        toast.classList.add('show');

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }
});

// Copy to clipboard functionality for view page
function copyToClipboard() {
    const content = document.querySelector('.code-block') ? document.querySelector('.code-block').innerText : window.location.href;
    navigator.clipboard.writeText(content).then(() => {
        const btn = document.querySelector('.btn-primary');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<span>&#10003;</span> Copied!';
        setTimeout(() => {
            btn.innerHTML = originalText;
        }, 2000);
    });
}
