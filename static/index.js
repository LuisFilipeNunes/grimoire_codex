function searchDecklist() {
    const button = document.getElementById('searchButton');
    const buttonText = document.getElementById('buttonText');
    const spinner = document.getElementById('loadingSpinner');
    
    buttonText.style.display = 'none';
    spinner.style.display = 'inline-block';
    button.disabled = true;

    let decklist = document.getElementById('decklistSearch').value;
    let deckName = document.getElementById('deckName').value;

    if (hasWhitespace(deckName)) {
        showNotification('Deck name cannot be empty or only whitespace!');
        buttonText.style.display = 'inline-block';
        spinner.style.display = 'none';
        button.disabled = false;
        return;
    }

    if (!decklist) {
        showNotification('Please enter a decklist!!');
        buttonText.style.display = 'inline-block';
        spinner.style.display = 'none';
        button.disabled = false;
        return;
    }

    

    sendDecklistToServer(decklist, deckName);
}

function showNotification(message) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}


function hasWhitespace(str) {
    return /\s/.test(str);
}

function sendDecklistToServer(decklist, deckName) {
    const trimmedDeckName = deckName ? deckName.trim() : '';
    fetch('/search_decklist', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'decklist=' + encodeURIComponent(decklist) + '&deckName=' + encodeURIComponent(trimmedDeckName)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
        window.location.href = '/ready_decks';
    })
    .catch(error => {
        const buttonText = document.getElementById('buttonText');
        const spinner = document.getElementById('loadingSpinner');
        const button = document.getElementById('searchButton');
        
        buttonText.style.display = 'inline-block';
        spinner.style.display = 'none';
        button.disabled = false;
    });
}
