fetch('http://localhost:5000/api/start')

function startCrawler() {
    fetch('/api/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        alert(data.status);
        location.reload();
    })
    .catch(error => console.error('Error:', error));
}

function stopCrawler() {
    fetch('/api/stop', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        alert(data.status);
        location.reload();
    })
    .catch(error => console.error('Error:', error));
}
