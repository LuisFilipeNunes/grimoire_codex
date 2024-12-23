function cleanFolder() {
    fetch('/clean_folder', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Folder cleaned:', data);
        window.location.href = '/'
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
