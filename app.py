from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
import json
from datetime import datetime
from server_classes import GameManager, Player, Lobby, GameSession
from debug_utils import debug_function, set_debug, clear_debug_log, get_debug_log_path

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize game manager
game_manager = GameManager()

# Set debug mode (can be controlled via environment variable)
import os
debug_enabled = os.getenv('DEBUG', 'True').lower() == 'true'
set_debug(debug_enabled)

# Print debug log location
if debug_enabled:
    print(f"Debug log will be written to: {get_debug_log_path()}")


@debug_function
@app.route('/')
def index():
    """Landing page."""
    return render_template('index.html')


@debug_function
@app.route('/create_lobby', methods=['POST'])
def create_lobby():
    """Create a new lobby."""
    try:
        data = request.get_json()
        player_name = data.get('player_name', 'Anonymous')
        
        # Create player
        player = game_manager.create_player(name=player_name)
        
        # Create lobby
        lobby_id = game_manager.create_lobby(player.player_id)
        
        if not lobby_id:
            return jsonify({'success': False, 'error': 'Failed to create lobby'}), 500
        
        return jsonify({
            'success': True,
            'lobby_id': lobby_id,
            'player_id': player.player_id,
            'lobby_url': f'/lobby/{lobby_id}'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@debug_function
@app.route('/lobby/<lobby_id>')
def lobby_page(lobby_id):
    """Lobby waiting page."""
    lobby = game_manager.get_lobby_by_id(lobby_id)
    if not lobby:
        return "Lobby not found", 404
    
    return render_template('lobby.html', lobby_id=lobby_id)


@debug_function
@app.route('/game/<game_id>')
def game_page(game_id):
    """Game interface page."""
    game = game_manager.get_game_by_id(game_id)
    if not game:
        return "Game not found", 404
    
    return render_template('game.html', game_id=game_id)


@app.route('/api/lobby/<lobby_id>')
def get_lobby_state(lobby_id):
    """Get lobby state via API."""
    lobby = game_manager.get_lobby_by_id(lobby_id)
    if not lobby:
        return jsonify({'error': 'Lobby not found'}), 404
    
    return jsonify(lobby.get_lobby_state())


@app.route('/api/game/<game_id>')
def get_game_state(game_id):
    """Get game state via API."""
    game = game_manager.get_game_by_id(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    
    player_id = request.args.get('player_id')
    if not player_id:
        return jsonify({'error': 'Player ID required'}), 400
    
    return jsonify(game.get_game_state_for_player(player_id))


@app.route('/api/stats')
def get_stats():
    """Get server statistics."""
    return jsonify(game_manager.get_stats())


@debug_function
@app.route('/api/debug/lobby/<lobby_id>')
def debug_lobby(lobby_id):
    """Debug endpoint to check lobby state."""
    lobby = game_manager.get_lobby_by_id(lobby_id)
    if not lobby:
        return jsonify({'error': 'Lobby not found'}), 404
    
    return jsonify({
        'lobby_id': lobby_id,
        'lobby_exists': True,
        'lobby_state': lobby.get_lobby_state(),
        'all_lobbies': list(game_manager.lobbies.keys()),
        'all_players': list(game_manager.players.keys())
    })


@debug_function
@app.route('/api/debug/clear-log', methods=['POST'])
def clear_debug_log_endpoint():
    """Clear the debug log file."""
    try:
        clear_debug_log()
        return jsonify({'success': True, 'message': 'Debug log cleared'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/game/<game_id>/solve')
@debug_function
def show_solve_page(game_id: str):
    """Show the solve page with clue dependency tree visualization."""
    if game_id not in game_manager.game_sessions:
        return "Game not found", 404
    
    game_session = game_manager.game_sessions[game_id]
    
    # Ensure board and clues are initialized
    game_session._initialize_board_and_clues()
    
    return render_template('solve.html', 
                         game_id=game_id,
                         board=game_session.board,
                         clues=game_session.clues)


# WebSocket Events
@debug_function
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to server'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print(f"Client disconnected: {request.sid}")
    # Clean up player connections
    for player in game_manager.players.values():
        if hasattr(player, 'websocket') and player.websocket == request.sid:
            player.disconnect()
            break


@socketio.on('join_room')
def handle_join_room(data):
    """Handle client joining a room."""
    room = data.get('room')
    if room:
        join_room(room)
        print(f"Client {request.sid} joined room {room}")


@debug_function
@socketio.on('join_lobby')
def handle_join_lobby(data):
    """Handle player joining a lobby."""
    try:
        lobby_id = data.get('lobby_id')
        player_id = data.get('player_id')
        player_name = data.get('player_name', 'Anonymous')
        
        if not lobby_id or not player_id:
            emit('error', {'message': 'Missing lobby_id or player_id'})
            return
        
        # Get or create player
        player = game_manager.get_player(player_id)
        if not player:
            player = game_manager.create_player(player_id=player_id, name=player_name)
        
        # Connect player to WebSocket
        player.connect(request.sid)
        
        # Join lobby
        success = game_manager.join_lobby(lobby_id, player_id)
        
        if success:
            join_room(f"lobby_{lobby_id}")
            emit('lobby_joined', {
                'lobby_id': lobby_id,
                'player_id': player.player_id,
                'lobby_state': game_manager.get_lobby_by_id(lobby_id).get_lobby_state()
            })
            
            # Notify other players in lobby
            lobby_state = game_manager.get_lobby_by_id(lobby_id).get_lobby_state()
            print(f"Emitting player_joined to room lobby_{lobby_id} with {len(lobby_state['players'])} players")
            socketio.emit('player_joined', {
                'player': player.to_dict(),
                'lobby_state': lobby_state
            }, room=f"lobby_{lobby_id}")
        else:
            emit('error', {'message': 'Failed to join lobby'})
    
    except Exception as e:
        emit('error', {'message': str(e)})


@socketio.on('leave_lobby')
def handle_leave_lobby(data):
    """Handle player leaving a lobby."""
    try:
        lobby_id = data.get('lobby_id')
        player_id = data.get('player_id')
        
        if not lobby_id or not player_id:
            emit('error', {'message': 'Missing lobby_id or player_id'})
            return
        
        success = game_manager.leave_lobby(lobby_id, player_id)
        
        if success:
            leave_room(f"lobby_{lobby_id}")
            emit('lobby_left', {'lobby_id': lobby_id})
            
            # Notify other players in lobby
            lobby = game_manager.get_lobby_by_id(lobby_id)
            if lobby:
                socketio.emit('player_left', {
                    'player_id': player_id,
                    'lobby_state': lobby.get_lobby_state()
                }, room=f"lobby_{lobby_id}")
        else:
            emit('error', {'message': 'Failed to leave lobby'})
    
    except Exception as e:
        emit('error', {'message': str(e)})


@debug_function
@socketio.on('start_game')
def handle_start_game(data):
    """Handle starting a game from a lobby."""
    import time
    start_time = time.time()
    print(f"[TIMING] handle_start_game called at: {start_time:.3f}s")
    
    try:
        lobby_id = data.get('lobby_id')
        player_id = data.get('player_id')
        
        if not lobby_id or not player_id:
            emit('error', {'message': 'Missing lobby_id or player_id'})
            return
        
        lobby = game_manager.get_lobby_by_id(lobby_id)
        if not lobby:
            emit('error', {'message': 'Lobby not found'})
            return
        
        if lobby.host_player_id != player_id:
            emit('error', {'message': 'Only the host can start the game'})
            return
        
        if not lobby.can_start_game():
            emit('error', {'message': 'Cannot start game yet'})
            return
        
        # Start the game
        print(f"[TIMING] About to call start_game_from_lobby at: {time.time():.3f}s")
        game_id = game_manager.start_game_from_lobby(lobby_id)
        game_creation_time = time.time()
        print(f"[TIMING] start_game_from_lobby completed at: {game_creation_time:.3f}s (took {game_creation_time - start_time:.3f}s)")
        print(f"DEBUG: Game ID returned: {game_id}")
        
        if game_id:
            print(f"[TIMING] About to emit game_started event at: {time.time():.3f}s")
            # Notify all players in lobby
            socketio.emit('game_started', {
                'game_id': game_id,
                'game_url': f'/game/{game_id}'
            }, room=f"lobby_{lobby_id}")
            emit_time = time.time()
            print(f"[TIMING] game_started event emitted at: {emit_time:.3f}s (took {emit_time - game_creation_time:.3f}s)")
            
            # Move all players to game room
            game = game_manager.get_game_by_id(game_id)
            if game:
                for player in game.players.values():
                    if player.connected:
                        join_room(f"game_{game_id}")
        else:
            print(f"DEBUG: Failed to start game")
            emit('error', {'message': 'Failed to start game'})
    
    except Exception as e:
        emit('error', {'message': str(e)})


@socketio.on('join_game')
def handle_join_game(data):
    """Handle player joining a game."""
    import time
    join_start_time = time.time()
    print(f"[TIMING] handle_join_game called at: {join_start_time:.3f}s")
    
    try:
        game_id = data.get('game_id')
        player_id = data.get('player_id')
        
        if not game_id or not player_id:
            emit('error', {'message': 'Missing game_id or player_id'})
            return
        
        game = game_manager.get_game_by_id(game_id)
        if not game:
            emit('error', {'message': 'Game not found'})
            return
        
        player = game_manager.get_player(player_id)
        if not player:
            emit('error', {'message': 'Player not found'})
            return
        
        # Connect player to WebSocket
        player.connect(request.sid)
        
        # Join game room
        room_name = f"game_{game_id}"
        join_room(room_name)
        join_room_time = time.time()
        print(f"[TIMING] Joined game room at: {join_room_time:.3f}s (took {join_room_time - join_start_time:.3f}s)")
        
        print(f"[TIMING] About to get game state at: {time.time():.3f}s")
        game_state = game.get_game_state_for_player(player_id)
        game_state_time = time.time()
        print(f"[TIMING] Got game state at: {game_state_time:.3f}s (took {game_state_time - join_room_time:.3f}s)")
        
        emit('game_joined', {
            'game_id': game_id,
            'game_state': game_state
        })
        emit_time = time.time()
        print(f"[TIMING] Emitted game_joined at: {emit_time:.3f}s (took {emit_time - game_state_time:.3f}s)")
        
        # Notify other players
        socketio.emit('player_joined_game', {
            'player': player.to_dict(),
            'game_state': game_state
        }, room=f"game_{game_id}")
    
    except Exception as e:
        emit('error', {'message': str(e)})


@debug_function
@socketio.on('submit_solution')
def handle_submit_solution(data):
    """Handle player submitting a solution."""
    try:
        game_id = data.get('game_id')
        player_id = data.get('player_id')
        position = tuple(data.get('position', []))
        guess = data.get('guess', {})
        
        if not all([game_id, player_id, position, guess]):
            emit('error', {'message': 'Missing required data'})
            return
        
        game = game_manager.get_game_by_id(game_id)
        if not game:
            emit('error', {'message': 'Game not found'})
            return
        
        # Submit solution
        result = game.submit_solution(player_id, position, guess)
        
        if result['success']:
            emit('solution_accepted', result)
            
            # Notify all players in game with their individual game states
            for p_id in game.players.keys():
                player_obj = game.players[p_id]
                if player_obj.connected:
                    socketio.emit('cell_solved', {
                        'position': position,
                        'player_id': player_id,
                        'points': result['points'],
                        'game_state': game.get_game_state_for_player(p_id)
                    }, room=player_obj.websocket)
            
            # Check if game is complete
            if result.get('game_complete'):
                socketio.emit('game_complete', {
                    'winner': game.winner.to_dict(),
                    'final_scores': {p.player_id: p.score for p in game.players.values()}
                }, room=f"game_{game_id}")
        else:
            emit('solution_rejected', result)
            
            # Even for rejected solutions, notify all players of the updated game state
            # (turn has advanced, scores may have changed due to penalties)
            for p_id in game.players.keys():
                player_obj = game.players[p_id]
                if player_obj.connected:
                    player_state = game.get_game_state_for_player(p_id)
                    # Emit to the specific player's socket ID instead of the room
                    socketio.emit('game_state_update', player_state, room=player_obj.websocket)
    
    except Exception as e:
        emit('error', {'message': str(e)})




@socketio.on('share_clue')
def handle_share_clue(data):
    """Handle player sharing a clue with another player."""
    try:
        game_id = data.get('game_id')
        from_player_id = data.get('from_player_id')
        to_player_id = data.get('to_player_id')
        clue_data = data.get('clue')  # Now expecting clue object instead of index
        
        if not all([game_id, from_player_id, to_player_id, clue_data]):
            emit('error', {'message': 'Missing required data'})
            return
        
        game = game_manager.get_game_by_id(game_id)
        if not game:
            emit('error', {'message': 'Game not found'})
            return
        
        # Find the clue index in the global clue list
        clue_index = None
        for i, clue in enumerate(game.clues):
            # Handle different clue types
            if clue.clue_type.value == clue_data.get('clue_type'):
                if clue.clue_type.value == 1:  # EXPLICIT
                    if (clue.position == tuple(clue_data.get('position', [])) and
                        clue.attribute == clue_data.get('attribute') and
                        clue.value == clue_data.get('value')):
                        clue_index = i
                        break
                elif clue.clue_type.value == 2:  # GENERAL
                    if (clue.scope == clue_data.get('scope') and
                        clue.scope_index == clue_data.get('scope_index') and
                        clue.count == clue_data.get('count') and
                        clue.value == clue_data.get('value')):
                        clue_index = i
                        break
                elif clue.clue_type.value == 3:  # CONDITIONAL
                    # For conditional clues, we need to match the condition and consequence
                    condition_data = clue_data.get('condition', {})
                    consequence_data = clue_data.get('consequence', {})
                    if (clue.condition and clue.consequence and
                        clue.condition.position == tuple(condition_data.get('position', [])) and
                        clue.condition.attribute == condition_data.get('attribute') and
                        clue.condition.value == condition_data.get('value') and
                        clue.consequence.position == tuple(consequence_data.get('position', [])) and
                        clue.consequence.attribute == consequence_data.get('attribute') and
                        clue.consequence.value == consequence_data.get('value')):
                        clue_index = i
                        break
        
        if clue_index is None:
            emit('error', {'message': 'Clue not found in game'})
            return
        
        result = game.share_clue(from_player_id, to_player_id, clue_index)
        
        if result['success']:
            emit('clue_shared', result)
            
            # Send updated game states to both players
            for p_id in [from_player_id, to_player_id]:
                player_obj = game.players[p_id]
                if player_obj.connected:
                    socketio.emit('game_state_update', game.get_game_state_for_player(p_id), room=player_obj.websocket)
            
            # Notify all players in game about the clue sharing
            socketio.emit('clue_shared_notification', {
                'from_player': result['from_player'],
                'to_player': result['to_player'],
                'clue': result['clue']
            }, room=f"game_{game_id}")
        else:
            emit('clue_share_failed', result)
    
    except Exception as e:
        emit('error', {'message': str(e)})


@socketio.on('get_game_state')
def handle_get_game_state(data):
    """Handle player requesting current game state."""
    try:
        game_id = data.get('game_id')
        player_id = data.get('player_id')
        
        if not game_id or not player_id:
            emit('error', {'message': 'Missing game_id or player_id'})
            return
        
        game = game_manager.get_game_by_id(game_id)
        if not game:
            emit('error', {'message': 'Game not found'})
            return
        
        emit('game_state_response', game.get_game_state_for_player(player_id))
    
    except Exception as e:
        emit('error', {'message': str(e)})


if __name__ == '__main__':
    # Clean up inactive sessions periodically
    import threading
    import time
    import signal
    import sys
    
    def cleanup_sessions():
        while True:
            time.sleep(300)  # Clean up every 5 minutes
            game_manager.cleanup_inactive_sessions()
    
    def signal_handler(sig, frame):
        print('\nShutting down server...')
        # Just exit gracefully - clients will detect disconnection
        sys.exit(0)
    
    # Handle shutdown signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    cleanup_thread = threading.Thread(target=cleanup_sessions, daemon=True)
    cleanup_thread.start()
    
    # Run the app
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
