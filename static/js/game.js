// Game page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const pageLoadTime = performance.now();
    console.log(`[TIMING] Game page loaded at: ${pageLoadTime.toFixed(2)}ms`);
    
    const socketInitTime = performance.now();
    console.log(`[TIMING] Initializing Socket.IO at: ${socketInitTime.toFixed(2)}ms (${(socketInitTime - pageLoadTime).toFixed(2)}ms after page load)`);
    const socket = io();
    const notificationBar = document.getElementById('notification-bar');
    const notificationIcon = notificationBar.querySelector('.notification-icon');
    const notificationMessage = notificationBar.querySelector('.notification-message');
    const cluesContainer = document.getElementById('clues-container');
    const gameBoard = document.getElementById('game-board');
    const playersScores = document.getElementById('players-scores');
    const gameStatus = document.getElementById('game-status');
    const playerScore = document.getElementById('player-score');
    const turnInfo = document.getElementById('turn-info');
    const currentPlayer = document.getElementById('current-player');
    const solutionModal = document.getElementById('solution-modal');
    const solutionForm = document.getElementById('solution-form');
    const cancelSolutionBtn = document.getElementById('cancel-solution');
    const turnActions = document.getElementById('turn-actions');
    const guessCellBtn = document.getElementById('guess-cell-btn');
    const shareClueBtn = document.getElementById('share-clue-btn');
    const clueShareModal = document.getElementById('clue-share-modal');
    const clueShareForm = document.getElementById('clue-share-form');
    const shareClueSelect = document.getElementById('share-clue-select');
    const sharePlayerSelect = document.getElementById('share-player-select');
    const cancelClueShare = document.getElementById('cancel-clue-share');
    const loadingOverlay = document.getElementById('loading-overlay');
    const cluesList = document.getElementById('clues-container');
    
    let playerId = null;
    let gameState = null;
    let selectedCell = null;
    let lastUpdateTime = Date.now();
    let pollingInterval = null;

    // Get player info from sessionStorage
    playerId = sessionStorage.getItem('player_id');
    const playerName = sessionStorage.getItem('player_name') || 'Anonymous';
    
    console.log('Player ID from sessionStorage:', playerId);
    console.log('Player name from sessionStorage:', playerName);
    console.log('Game ID from template:', gameId);
    
    // Show loading overlay initially
    showLoadingOverlay();
    
    // Fallback: Hide loading overlay after 10 seconds if no game state received
    setTimeout(() => {
        hideLoadingOverlay();
    }, 10000);

    // Drag scrolling for clues list
    let isDragging = false;
    let startX = 0;
    let scrollLeft = 0;

    if (cluesList) {
        cluesList.addEventListener('mousedown', (e) => {
            isDragging = true;
            cluesList.style.cursor = 'grabbing';
            startX = e.pageX - cluesList.offsetLeft;
            scrollLeft = cluesList.scrollLeft;
            e.preventDefault();
        });

        cluesList.addEventListener('mouseleave', () => {
            isDragging = false;
            cluesList.style.cursor = 'grab';
        });

        cluesList.addEventListener('mouseup', () => {
            isDragging = false;
            cluesList.style.cursor = 'grab';
        });

        cluesList.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            e.preventDefault();
            const x = e.pageX - cluesList.offsetLeft;
            const walk = (x - startX) * 2; // Scroll speed multiplier
            cluesList.scrollLeft = scrollLeft - walk;
        });

        // Touch support for mobile
        cluesList.addEventListener('touchstart', (e) => {
            isDragging = true;
            startX = e.touches[0].pageX - cluesList.offsetLeft;
            scrollLeft = cluesList.scrollLeft;
        });

        cluesList.addEventListener('touchend', () => {
            isDragging = false;
        });

        cluesList.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            const x = e.touches[0].pageX - cluesList.offsetLeft;
            const walk = (x - startX) * 2;
            cluesList.scrollLeft = scrollLeft - walk;
        });
    }

    // Socket event handlers
    socket.on('connect', function() {
        const connectTime = performance.now();
        console.log(`[TIMING] Connected to server at: ${connectTime.toFixed(2)}ms (${(connectTime - pageLoadTime).toFixed(2)}ms after page load)`);
        showStatus('Connected to game server', 'success');
        
        // Join the game
        const joinEmitTime = performance.now();
        console.log(`[TIMING] Emitting join_game at: ${joinEmitTime.toFixed(2)}ms (${(joinEmitTime - connectTime).toFixed(2)}ms after connect)`);
        socket.emit('join_game', {
            game_id: gameId,
            player_id: playerId
        });
        
        // Start periodic polling as backup (every 5 seconds)
        startPeriodicPolling();
    });
    
    // Add timing for WebSocket connection attempts
    socket.on('connect_error', function(error) {
        const errorTime = performance.now();
        console.log(`[TIMING] WebSocket connection error at: ${errorTime.toFixed(2)}ms (${(errorTime - pageLoadTime).toFixed(2)}ms after page load)`, error);
    });
    
    socket.on('disconnect', function(reason) {
        const disconnectTime = performance.now();
        console.log(`[TIMING] WebSocket disconnected at: ${disconnectTime.toFixed(2)}ms (${(disconnectTime - pageLoadTime).toFixed(2)}ms after page load)`, reason);
        
        // Stop polling
        stopPeriodicPolling();
        
        // Redirect to home after 2 seconds
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
    });

    socket.on('game_joined', function(data) {
        console.log('Joined game:', data);
        gameState = data.game_state;
        updateGameDisplay();
        hideLoadingOverlay(); // Hide loading overlay when game state is received
    });

    socket.on('player_joined_game', function(data) {
        console.log('Player joined game:', data);
        updateGameDisplay();
    });

    socket.on('cell_solved', function(data) {
        console.log('Cell solved event received:', data);
        // Update game state with the new data
        if (data.game_state) {
            gameState = data.game_state;
        }
        updateGameDisplay();
        showStatus(`${data.player_id} solved a cell for ${data.points} points!`, 'info');
        // Hide loading overlay once we have game state
        hideLoadingOverlay();
    });

    socket.on('game_complete', function(data) {
        console.log('Game complete:', data);
        showStatus(`Game Complete! Winner: ${data.winner.name}`, 'success');
        // Disable further interactions
        gameBoard.style.pointerEvents = 'none';
    });

    socket.on('solution_accepted', function(data) {
        console.log('Solution accepted:', data);
        let message = `Correct! +${data.points} points`;
        if (data.penalty > 0) {
            message += ` (penalty: -${data.penalty})`;
        }
        if (data.cell_solved) {
            message += ' - Cell solved!';
        }
        showStatus(message, 'success');
        closeSolutionModal();
        
        // Game state will be updated automatically via cell_solved event
    });

    socket.on('solution_rejected', function(data) {
        console.log('Solution rejected:', data);
        let message = `Incorrect guess`;
        if (data.penalty > 0) {
            message += ` (-${data.penalty} points)`;
        }
        if (data.shape_correct !== undefined && data.number_correct !== undefined) {
            const feedback = [];
            if (data.shape_correct) feedback.push('shape correct');
            if (data.number_correct) feedback.push('number correct');
            if (feedback.length > 0) {
                message += ` (${feedback.join(', ')})`;
            }
        }
        showStatus(message, 'error');
        closeSolutionModal();
        
        // Game state will be updated automatically via game_state_update event
    });


    socket.on('clue_shared', function(data) {
        console.log('Clue shared successfully:', data);
        showStatus(`Clue shared with ${data.to_player}`, 'success');
        updateGameDisplay();
    });

    socket.on('clue_share_failed', function(data) {
        console.log('Clue share failed:', data);
        showStatus(`Failed to share clue: ${data.error}`, 'error');
    });

    socket.on('clue_shared_notification', function(data) {
        console.log('Clue shared notification:', data);
        if (data.to_player === gameState.players.find(p => p.player_id === playerId)?.name) {
            showStatus(`${data.from_player} shared a clue with you!`, 'info');
        }
        updateGameDisplay();
    });

    socket.on('game_state_update', function(data) {
        const gameStateTime = performance.now();
        console.log(`[TIMING] Game state update received at: ${gameStateTime.toFixed(2)}ms (${(gameStateTime - pageLoadTime).toFixed(2)}ms after page load)`);
        console.log('Game state updated:', data);
        console.log('Current turn:', data.current_turn);
        console.log('Is my turn:', data.is_my_turn);
        console.log('My player ID:', playerId);
        console.log('Timestamp:', new Date().toISOString());
        gameState = data;
        lastUpdateTime = Date.now(); // Update timestamp
        updateGameDisplay();
        // Hide loading overlay once we have game state
        hideLoadingOverlay();
    });
    
    socket.on('game_state_response', function(data) {
        console.log('Game state response (from polling):', data);
        gameState = data;
        lastUpdateTime = Date.now(); // Update timestamp
        updateGameDisplay();
        // Hide loading overlay once we have game state
        hideLoadingOverlay();
    });

    // Duplicate handler removed - using the one above

    socket.on('error', function(data) {
        console.error('Socket error:', data);
        showStatus(`Error: ${data.message}`, 'error');
    });
    
    socket.on('server_shutdown', function(data) {
        console.log('Server is shutting down:', data);
        showStatus('Server is shutting down - redirecting to home...', 'error');
        
        // Stop polling
        stopPeriodicPolling();
        
        // Redirect to home after 2 seconds
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
    });

    // Button event handlers
    // Note: requestCluesBtn was removed as clues are now distributed at game start

    cancelSolutionBtn.addEventListener('click', function() {
        closeSolutionModal();
    });

    // Turn action buttons
    guessCellBtn.addEventListener('click', function() {
        showStatus('Click on a cell to guess its contents', 'info');
        // Enable cell clicking for guessing
        enableCellClicking();
    });

    shareClueBtn.addEventListener('click', function() {
        openClueShareModal();
    });

    cancelClueShare.addEventListener('click', function() {
        closeClueShareModal();
    });

    clueShareForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const clueIndex = parseInt(shareClueSelect.value);
        const toPlayerId = sharePlayerSelect.value;
        
        
        if (clueIndex === -1 || !toPlayerId) {
            showStatus('Please select a clue and player', 'error');
            return;
        }
        
        // Get the actual clue object to send to server
        const clueToShare = gameState.clues[clueIndex];
        if (!clueToShare) {
            showStatus('Invalid clue selected', 'error');
            return;
        }
        
        socket.emit('share_clue', {
            game_id: gameId,
            from_player_id: playerId,
            to_player_id: toPlayerId,
            clue: clueToShare  // Send the clue object instead of index
        });
        
        closeClueShareModal();
    });

    solutionForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        console.log('Solution form submitted');
        console.log('Selected cell:', selectedCell);
        console.log('Player ID:', playerId);
        console.log('Game ID:', gameId);
        
        if (!selectedCell) {
            showStatus('No cell selected', 'error');
            return;
        }

        const shape = document.getElementById('solution-shape').value;
        const number = document.getElementById('solution-number').value;

        console.log('Shape:', shape, 'Number:', number);

        // At least one field must be filled
        if (!shape && !number) {
            showStatus('Please select at least a shape or number', 'error');
            return;
        }

        // Prepare the guess object
        const guess = {};
        if (shape) guess.shape = shape;
        if (number) guess.number = parseInt(number);

        console.log('Sending submit_solution with:', {
            game_id: gameId,
            player_id: playerId,
            position: selectedCell,
            guess: guess
        });
        console.log('Submit timestamp:', new Date().toISOString());

        // Don't do immediate UI update - let's fix the root cause instead

        socket.emit('submit_solution', {
            game_id: gameId,
            player_id: playerId,
            position: selectedCell,
            guess: guess
        });
    });

    function updateGameDisplay() {
        if (!gameState) return;

        // Update game status
        // Show a more meaningful status
        if (gameState.game_state === 'playing') {
            gameStatus.textContent = '🎮 Active';
        } else if (gameState.game_state === 'waiting') {
            gameStatus.textContent = '⏳ Waiting';
        } else if (gameState.game_state === 'finished') {
            gameStatus.textContent = '🏁 Finished';
        } else {
            gameStatus.textContent = gameState.game_state;
        }
        
        // Update turn information
        turnInfo.textContent = `Turn: ${gameState.turn_count}`;
        
        // Update current player display
        const currentPlayerName = gameState.players.find(p => p.player_id === gameState.current_turn)?.name || 'Unknown';
        currentPlayer.textContent = `Current Turn: ${currentPlayerName}`;
        
        // Update player score
        playerScore.textContent = `Score: ${gameState.player_score}`;

        // Update game board
        updateGameBoard();

        // Update players scores
        updatePlayersScores();

        // Update clues
        if (gameState.clues) {
            updateCluesDisplay(gameState.clues);
        }

        // Update turn actions UI
        updateTurnActionsUI();
    }

    function updateGameBoard() {
        if (!gameState) return;

        const boardSize = gameState.board_size;
        gameBoard.className = `game-board grid-${boardSize}`;
        gameBoard.innerHTML = '';

        for (let r = 0; r < boardSize; r++) {
            for (let c = 0; c < boardSize; c++) {
                const cell = document.createElement('div');
                cell.className = 'cell';
                cell.dataset.row = r;
                cell.dataset.col = c;

                // Check if cell is solved
                const cellKey = `${r},${c}`;
                if (gameState.solved_cells[cellKey]) {
                    const solvedData = gameState.solved_cells[cellKey];
                    
                    // Only display what was actually revealed
                    let displayText = '';
                    let isFullySolved = false;
                    
                    if (solvedData.revealed.number && solvedData.revealed.shape) {
                        // Both revealed - fully solved
                        displayText = `${solvedData.solution.number}<br>${getShapeEmoji(solvedData.solution.shape)}`;
                        cell.classList.add('solved');
                        isFullySolved = true;
                    } else if (solvedData.revealed.number) {
                        // Only number revealed - partially solved
                        displayText = `${solvedData.solution.number}<br>?`;
                        cell.classList.add('partially-solved');
                    } else if (solvedData.revealed.shape) {
                        // Only shape revealed - partially solved
                        displayText = `?<br>${getShapeEmoji(solvedData.solution.shape)}`;
                        cell.classList.add('partially-solved');
                    }
                    
                    cell.innerHTML = displayText;
                    cell.title = `Solved by ${solvedData.player_id}`;
                    
                    // Make cell clickable if it's only partially solved
                    if (!isFullySolved) {
                        cell.addEventListener('click', function() {
                            console.log('Partially solved cell clicked:', r, c);
                            console.log('Is my turn:', gameState.is_my_turn);
                            if (gameState.is_my_turn) {
                                openSolutionModal(r, c);
                            } else {
                                showStatus('Wait for your turn to guess cells', 'error');
                            }
                        });
                    }
                } else {
                    cell.innerHTML = '?';
                    cell.addEventListener('click', function() {
                        console.log('Cell clicked:', r, c);
                        console.log('Is my turn:', gameState.is_my_turn);
                        if (gameState.is_my_turn) {
                            openSolutionModal(r, c);
                        } else {
                            showStatus('Wait for your turn to guess cells', 'error');
                        }
                    });
                }

                gameBoard.appendChild(cell);
            }
        }
    }

    function updatePlayersScores() {
        if (!gameState) return;

        playersScores.innerHTML = '';
        gameState.players.forEach(player => {
            const div = document.createElement('div');
            div.className = 'player-score';
            div.innerHTML = `
                <strong>${player.name}</strong>: ${player.score} points
                ${player.player_id === playerId ? ' (You)' : ''}
            `;
            playersScores.appendChild(div);
        });
    }

    function updateCluesDisplay(clues) {
        cluesContainer.innerHTML = '';
        
        if (clues.length === 0) {
            cluesContainer.innerHTML = '<p>No clues yet. Click "Get More Clues" to receive clues!</p>';
            return;
        }

        clues.forEach((clue, index) => {
            const clueDiv = document.createElement('div');
            clueDiv.className = 'clue-card';
            
            let clueText = '';
            if (clue.clue_type === 1) { // EXPLICIT
                clueText = `Cell (${clue.position[0]}, ${clue.position[1]}) has ${clue.attribute} = ${clue.value}`;
            } else if (clue.clue_type === 2) { // GENERAL
                clueText = `${clue.scope.charAt(0).toUpperCase() + clue.scope.slice(1)} ${clue.scope_index} has ${clue.count} ${clue.value}s`;
            } else if (clue.clue_type === 3) { // CONDITIONAL
                const condition = clue.condition;
                const consequence = clue.consequence;
                clueText = `If cell (${condition.position[0]}, ${condition.position[1]}) has ${condition.attribute} = ${condition.value}, then cell (${consequence.position[0]}, ${consequence.position[1]}) has ${consequence.attribute} = ${consequence.value}`;
            }
            
            clueDiv.textContent = clueText;
            cluesContainer.appendChild(clueDiv);
        });
    }

    function openSolutionModal(row, col) {
        console.log('Opening solution modal for cell:', row, col);
        selectedCell = [row, col];
        solutionModal.style.display = 'block';
        
        // Reset form
        document.getElementById('solution-shape').value = '';
        document.getElementById('solution-number').value = '';
    }

    function closeSolutionModal() {
        solutionModal.style.display = 'none';
        selectedCell = null;
    }

    function updateTurnActionsUI() {
        if (!gameState) return;

        console.log('DEBUG: updateTurnActionsUI called - is_my_turn:', gameState.is_my_turn, 'game_state:', gameState.game_state);
        
        // Show/hide turn actions based on turn
        if (gameState.is_my_turn && gameState.game_state === 'playing') {
            console.log('DEBUG: Showing turn actions');
            turnActions.style.display = 'block';
        } else {
            console.log('DEBUG: Hiding turn actions');
            turnActions.style.display = 'none';
        }
    }

    function enableCellClicking() {
        // This function is called when "Guess a Cell" button is clicked
        // The cell clicking is already handled in updateGameBoard
        showStatus('Click on any cell to guess its contents', 'info');
    }

    function openClueShareModal() {
        if (!gameState) return;

        // Update clue select options
        shareClueSelect.innerHTML = '<option value="">Choose a clue...</option>';
        if (gameState.clues && gameState.clues.length > 0) {
            gameState.clues.forEach((clue, index) => {
                const option = document.createElement('option');
                option.value = index;
                
                // Generate readable clue text
                let clueText = '';
                if (clue.clue_type === 1) { // EXPLICIT
                    clueText = `Cell (${clue.position[0]}, ${clue.position[1]}) has ${clue.attribute} = ${clue.value}`;
                } else if (clue.clue_type === 2) { // GENERAL
                    clueText = `${clue.scope.charAt(0).toUpperCase() + clue.scope.slice(1)} ${clue.scope_index} has ${clue.count} ${clue.value}s`;
                } else if (clue.clue_type === 3) { // CONDITIONAL
                    const condition = clue.condition;
                    const consequence = clue.consequence;
                    clueText = `If cell (${condition.position[0]}, ${condition.position[1]}) has ${condition.attribute} = ${condition.value}, then cell (${consequence.position[0]}, ${consequence.position[1]}) has ${consequence.attribute} = ${consequence.value}`;
                }
                
                // Truncate long clues for dropdown
                const truncatedText = clueText.length > 60 ? clueText.substring(0, 57) + '...' : clueText;
                option.textContent = truncatedText;
                option.title = clueText; // Full text on hover
                shareClueSelect.appendChild(option);
            });
        } else {
            const option = document.createElement('option');
            option.value = -1;
            option.textContent = 'No clues to share';
            option.disabled = true;
            shareClueSelect.appendChild(option);
        }
        
        // Update player select options
        sharePlayerSelect.innerHTML = '<option value="">Choose a player...</option>';
        gameState.players.forEach(player => {
            if (player.player_id !== playerId) {
                const option = document.createElement('option');
                option.value = player.player_id;
                option.textContent = player.name;
                sharePlayerSelect.appendChild(option);
            }
        });

        clueShareModal.style.display = 'block';
    }

    function closeClueShareModal() {
        clueShareModal.style.display = 'none';
        shareClueSelect.value = '';
        sharePlayerSelect.value = '';
    }

    function getShapeEmoji(shape) {
        const shapeMap = {
            'circle': '🟢',
            'square': '🟦',
            'star': '⭐',
            'heart': '❤️'
        };
        return shapeMap[shape] || '?';
    }

    function showStatus(message, type) {
        // Set the notification content
        notificationMessage.textContent = message;
        
        // Set the icon based on type
        const icons = {
            success: '✅',
            error: '❌',
            info: 'ℹ️',
            warning: '⚠️'
        };
        notificationIcon.textContent = icons[type] || 'ℹ️';
        
        // Set the notification type
        notificationBar.className = `notification-bar ${type}`;
        
        // Show the notification
        notificationBar.style.display = 'block';
        setTimeout(() => {
            notificationBar.classList.add('show');
        }, 10);
        
        // Auto-hide after delay
        const delay = type === 'error' ? 5000 : 3000;
        setTimeout(() => {
            closeNotification();
        }, delay);
    }

    // Global function for closing notifications
    window.closeNotification = function() {
        notificationBar.classList.remove('show');
        setTimeout(() => {
            notificationBar.style.display = 'none';
        }, 300);
    };

    // Polling functions for backup updates and connection monitoring
    function startPeriodicPolling() {
        // Poll every 5 seconds as backup
        pollingInterval = setInterval(() => {
            const timeSinceLastUpdate = Date.now() - lastUpdateTime;
            
            // If no updates for 10 seconds, request fresh state
            if (timeSinceLastUpdate > 10000) {
                console.log('No updates for 10+ seconds, requesting fresh game state...');
                socket.emit('get_game_state', {
                    game_id: gameId,
                    player_id: playerId
                });
            }
        }, 5000);
    }
    
    function stopPeriodicPolling() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
    }
    
    // Clean up on page unload
    window.addEventListener('beforeunload', function() {
        stopPeriodicPolling();
    });
    
    function showLoadingOverlay() {
        if (loadingOverlay) {
            loadingOverlay.style.display = 'flex';
        }
    }
    
    function hideLoadingOverlay() {
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
    }

    // Game state will be loaded automatically when joining the game
});

// Solve button functionality
function showSolvePage() {
    const gameId = window.location.pathname.split('/').pop();
    window.open(`/game/${gameId}/solve`, '_blank');
}
