// Lobby page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    const statusMessage = document.getElementById('status-message');
    const playersList = document.getElementById('players-list');
    const startGameBtn = document.getElementById('start-game-btn');
    const leaveLobbyBtn = document.getElementById('leave-lobby-btn');
    const lobbyUrl = document.getElementById('lobby-url');
    const nameModal = document.getElementById('name-modal');
    const nameForm = document.getElementById('name-form');
    const lobbyInfo = document.getElementById('lobby-info');
    
    let playerId = null;
    let playerName = null;
    let isHost = false;

    // Set up lobby URL
    lobbyUrl.value = window.location.href;
    
    // Copy link functionality
    const copyLinkBtn = document.getElementById('copy-link-btn');
    copyLinkBtn.addEventListener('click', function() {
        lobbyUrl.select();
        lobbyUrl.setSelectionRange(0, 99999); // For mobile devices
        
        try {
            document.execCommand('copy');
            showStatus('Link copied to clipboard!', 'success');
        } catch (err) {
            // Fallback for modern browsers
            navigator.clipboard.writeText(lobbyUrl.value).then(() => {
                showStatus('Link copied to clipboard!', 'success');
            }).catch(() => {
                showStatus('Failed to copy link', 'error');
            });
        }
    });

    // Check if player already has a name (from main page)
    const existingName = sessionStorage.getItem('player_name');
    const existingId = sessionStorage.getItem('player_id');
    
    if (existingName && existingId) {
        // Player came from main page, use existing info
        playerName = existingName;
        playerId = existingId;
        showLobbyInterface();
        // Don't try to join lobby immediately - wait for socket connection
        // and check if we're already in the lobby
    } else {
        // Player came directly to lobby URL, show name input
        showNameInput();
    }

    // Name form handler
    nameForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(nameForm);
        playerName = formData.get('player_name');
        
        if (playerName) {
            // Generate a new player ID
            playerId = 'player_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('player_name', playerName);
            sessionStorage.setItem('player_id', playerId);
            
            showLobbyInterface();
        }
    });

    // Socket event handlers
    socket.on('connect', function() {
        console.log('Connected to server');
        showStatus('Connected to server', 'success');
        
        // Only join lobby if we have player info
        if (playerId && playerName) {
            // First check if we're already in the lobby
            checkLobbyState();
        }
    });

    socket.on('lobby_joined', function(data) {
        console.log('Joined lobby:', data);
        // Don't overwrite playerId - it should already be set correctly
        // Only update sessionStorage if the server returned a different ID
        if (data.player_id && data.player_id !== playerId) {
            console.log('Server returned different player ID, updating:', data.player_id);
            playerId = data.player_id;
            sessionStorage.setItem('player_id', playerId);
        }
        updateLobbyState(data.lobby_state);
    });

    socket.on('player_joined', function(data) {
        console.log('Player joined event received:', data);
        console.log('Current player ID:', playerId);
        console.log('Joining player ID:', data.player.player_id);
        
        // Only show the message if it's not us joining
        if (data.player.player_id !== playerId) {
            showStatus(`${data.player.name} joined the lobby`, 'info');
        }
        
        updateLobbyState(data.lobby_state);
    });

    socket.on('player_left', function(data) {
        console.log('Player left:', data);
        updateLobbyState(data.lobby_state);
        showStatus('A player left the lobby', 'info');
    });

    socket.on('game_started', function(data) {
        const gameStartedTime = performance.now();
        console.log(`[TIMING] Game started event received at: ${gameStartedTime.toFixed(2)}ms`);
        console.log('Game started:', data);
        showStatus('Game starting...', 'success');
        
        // Redirect to game page immediately
        const redirectTime = performance.now();
        console.log(`[TIMING] Redirecting to game page at: ${redirectTime.toFixed(2)}ms (${(redirectTime - gameStartedTime).toFixed(2)}ms after game_started event)`);
        window.location.href = data.game_url;
    });

    socket.on('error', function(data) {
        console.error('Socket error:', data);
        showStatus(`Error: ${data.message}`, 'error');
        
        // Reset start game button if there was an error
        startGameBtn.disabled = false;
        
        const startBtnText = document.getElementById('start-btn-text');
        const startBtnLoading = document.getElementById('start-btn-loading');
        
        if (startBtnText && startBtnLoading) {
            startBtnText.style.display = 'inline';
            startBtnLoading.style.display = 'none';
        } else {
            // Fallback: reset button text
            startGameBtn.textContent = 'Start Game';
        }
    });

    // Button event handlers
    startGameBtn.addEventListener('click', function() {
        if (isHost) {
            const startTime = performance.now();
            console.log(`[TIMING] Start Game button clicked at: ${startTime.toFixed(2)}ms`);
            
            // Show loading state
            startGameBtn.disabled = true;
            
            // Safely update loading state elements
            const startBtnText = document.getElementById('start-btn-text');
            const startBtnLoading = document.getElementById('start-btn-loading');
            
            if (startBtnText && startBtnLoading) {
                startBtnText.style.display = 'none';
                startBtnLoading.style.display = 'inline';
            } else {
                // Fallback: just change button text
                startGameBtn.textContent = 'Starting...';
            }
            
            const emitTime = performance.now();
            console.log(`[TIMING] About to emit start_game at: ${emitTime.toFixed(2)}ms (${(emitTime - startTime).toFixed(2)}ms after click)`);
            
            socket.emit('start_game', {
                lobby_id: lobbyId,
                player_id: playerId
            });
        }
    });

    leaveLobbyBtn.addEventListener('click', function() {
        socket.emit('leave_lobby', {
            lobby_id: lobbyId,
            player_id: playerId
        });
        
        // Redirect to home page
        setTimeout(() => {
            window.location.href = '/';
        }, 1000);
    });

    function updateLobbyState(lobbyState) {
        console.log('Updating lobby state:', lobbyState);
        
        // Update players list
        playersList.innerHTML = '';
        lobbyState.players.forEach(player => {
            const li = document.createElement('li');
            li.textContent = player.name;
            if (player.player_id === lobbyState.host_player_id) {
                li.textContent += ' (Host)';
                li.style.fontWeight = 'bold';
            }
            playersList.appendChild(li);
        });

        // Update host status
        isHost = lobbyState.host_player_id === playerId;
        console.log('Is host:', isHost, 'Can start:', lobbyState.can_start);
        
        // Update start game button
        startGameBtn.disabled = !lobbyState.can_start || !isHost;
        
        if (isHost) {
            startGameBtn.textContent = lobbyState.can_start ? 'Start Game' : 'Waiting for Players';
        } else {
            startGameBtn.textContent = 'Only Host Can Start';
        }
    }

    function showStatus(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${type}`;
        statusMessage.style.display = 'block';
        
        // Auto-hide info messages
        if (type === 'info') {
            setTimeout(() => {
                statusMessage.style.display = 'none';
            }, 3000);
        }
    }

    // Helper functions
    function showNameInput() {
        nameModal.style.display = 'flex';
        lobbyInfo.style.display = 'none';
    }

    function showLobbyInterface() {
        nameModal.style.display = 'none';
        lobbyInfo.style.display = 'block';
        
        // Join lobby if socket is connected
        if (socket.connected) {
            joinLobby();
        }
    }

    function checkLobbyState() {
        // First, try to get the current lobby state via API
        fetch(`/mysticgrid/api/lobby/${lobbyId}`)
            .then(response => response.json())
            .then(data => {
                console.log('Lobby state:', data);
                
                // Check if we're already in the lobby
                const playerInLobby = data.players.some(p => p.player_id === playerId);
                
                if (playerInLobby) {
                    // We're already in the lobby, just update the display
                    console.log('Player already in lobby, updating display');
                    updateLobbyState(data);
                    showStatus('Connected to lobby', 'success');
                    
                    // Make sure we're in the WebSocket room for real-time updates
                    socket.emit('join_room', { room: `lobby_${lobbyId}` });
                } else {
                    // We're not in the lobby, try to join
                    console.log('Player not in lobby, attempting to join');
                    joinLobby();
                }
            })
            .catch(error => {
                console.error('Error checking lobby state:', error);
                // Fallback: try to join anyway
                joinLobby();
            });
    }

    function joinLobby() {
        socket.emit('join_lobby', {
            lobby_id: lobbyId,
            player_id: playerId,
            player_name: playerName
        });
    }

    // Handle page unload
    window.addEventListener('beforeunload', function() {
        if (playerId) {
            socket.emit('leave_lobby', {
                lobby_id: lobbyId,
                player_id: playerId
            });
        }
    });
});