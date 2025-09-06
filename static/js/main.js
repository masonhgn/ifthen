// Main page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const createLobbyForm = document.getElementById('create-lobby-form');
    const joinLobbyForm = document.getElementById('join-lobby-form');
    const statusMessage = document.getElementById('status-message');

    // Create lobby form handler
    createLobbyForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(createLobbyForm);
        const playerName = formData.get('player_name');
        
        try {
            showStatus('Creating lobby...', 'info');
            
            const response = await fetch('/create_lobby', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    player_name: playerName
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showStatus('Lobby created successfully!', 'success');
                
                // Store player info in sessionStorage
                sessionStorage.setItem('player_id', data.player_id);
                sessionStorage.setItem('player_name', playerName);
                
                // Redirect to lobby page
                setTimeout(() => {
                    window.location.href = data.lobby_url;
                }, 1500);
            } else {
                showStatus(`Error: ${data.error}`, 'error');
            }
        } catch (error) {
            showStatus(`Error: ${error.message}`, 'error');
        }
    });

    // Join lobby form handler
    joinLobbyForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(joinLobbyForm);
        const lobbyId = formData.get('lobby_id');
        const playerName = formData.get('player_name');
        
        try {
            showStatus('Joining lobby...', 'info');
            
            // Store player info in sessionStorage
            sessionStorage.setItem('player_name', playerName);
            
            // Redirect to lobby page
            window.location.href = `/lobby/${lobbyId}`;
            
        } catch (error) {
            showStatus(`Error: ${error.message}`, 'error');
        }
    });

    function showStatus(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${type}`;
        statusMessage.style.display = 'block';
        
        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => {
                statusMessage.style.display = 'none';
            }, 3000);
        }
    }
});
