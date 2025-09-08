"""
Multi-Game Flask Application
Main application that serves a game catalog and hosts multiple games.
"""

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
import json
import os
from datetime import datetime
import threading
import time

# Import shared utilities
from shared.debug_utils import debug_function, set_debug, clear_debug_log, get_debug_log_path

# Import game registry system
from games import load_all_games, get_available_games, get_game_blueprint

# Initialize Flask app
app = Flask(__name__, 
           template_folder='shared/templates',
           static_folder='static')

# Use environment variable for secret key, fallback to generated key for development
import secrets
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Initialize socketio with proper cors configuration for deployment
default_origins = [
    'http://localhost:5000',
    'http://127.0.0.1:5000',
    'http://localhost:3000',  # common react dev port
    'http://127.0.0.1:3000',
    'http://localhost:8080',  # common vue dev port
    'http://127.0.0.1:8080'
]
allowed_origins = os.getenv('ALLOWED_ORIGINS', ','.join(default_origins)).split(',')
socketio = SocketIO(app, cors_allowed_origins=allowed_origins)

# Set debug mode (can be controlled via environment variable)
debug_enabled = os.getenv('DEBUG', 'True').lower() == 'true'
set_debug(debug_enabled)

# Load all games and register their blueprints
load_all_games()

# Register all game blueprints
for game_info in get_available_games():
    try:
        blueprint = get_game_blueprint(game_info['name'])
        app.register_blueprint(blueprint)
        print(f"[APP] Registered blueprint for game: {game_info['name']}")
    except Exception as e:
        print(f"[APP] Error registering blueprint for {game_info['name']}: {e}")

# Register socket handlers for all games
from games.mysticgrid import register_socket_handlers
register_socket_handlers(socketio)

# Main homepage route
@app.route('/')
def home():
    """Main homepage."""
    return render_template('catalog.html')

# Games page route
@app.route('/games')
def games():
    """Games page with game cards."""
    games = get_available_games()
    return render_template('games.html', games=games)

# API routes
@app.route('/api/games')
def api_games():
    """API endpoint to get available games."""
    return jsonify(get_available_games())

@app.route('/api/stats')
def api_stats():
    """API endpoint to get overall server statistics."""
    all_stats = {}
    for game_info in get_available_games():
        try:
            blueprint = get_game_blueprint(game_info['name'])
            # Get stats from each game (this would need to be implemented in each game)
            all_stats[game_info['name']] = {
                'active_players': 0,
                'active_games': 0,
                'total_players': 0
            }
        except Exception as e:
            print(f"[API] Error getting stats for {game_info['name']}: {e}")
            all_stats[game_info['name']] = {
                'active_players': 0,
                'active_games': 0,
                'total_players': 0
            }
    
    return jsonify(all_stats)

# Debug routes
@app.route('/api/debug/clear-log', methods=['POST'])
def clear_debug_log_endpoint():
    """Clear the debug log file."""
    try:
        clear_debug_log()
        return jsonify({'success': True, 'message': 'Debug log cleared'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/debug/log')
def get_debug_log():
    """Get the debug log content."""
    try:
        log_path = get_debug_log_path()
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                content = f.read()
            return jsonify({'success': True, 'content': content})
        else:
            return jsonify({'success': True, 'content': 'Debug log is empty'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Set up periodic cleanup (this would need to be coordinated across all games)
def periodic_cleanup():
    """Run cleanup tasks every 30 minutes."""
    while True:
        try:
            time.sleep(1800)  # 30 minutes
            print("[CLEANUP] Running periodic cleanup...")
            # Each game would handle its own cleanup
            print("[CLEANUP] Cleanup completed")
        except Exception as e:
            print(f"[CLEANUP] Error during cleanup: {e}")

# Start cleanup thread
cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()

# Global socket handlers (for cross-game functionality if needed)
@socketio.on('connect')
def handle_global_connect():
    """Handle global client connection."""
    print(f"[GLOBAL_SOCKET] Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_global_disconnect():
    """Handle global client disconnection."""
    print(f"[GLOBAL_SOCKET] Client disconnected: {request.sid}")

if __name__ == '__main__':
    print("[APP] Starting Multi-Game Flask Application...")
    print(f"[APP] Available games: {[game['name'] for game in get_available_games()]}")
    print(f"[APP] Debug mode: {debug_enabled}")
    
    # Run the application
    socketio.run(app, 
                host=os.getenv('HOST', '0.0.0.0'),
                port=int(os.getenv('PORT', 5000)),
                debug=debug_enabled)
