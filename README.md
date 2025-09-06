# IfThen Logic Game

A multiplayer logic puzzle game where players solve a grid using logical clues!

## Features

- **Multiplayer Support**: Create lobbies and play with friends
- **Real-time Gameplay**: WebSocket-based communication for instant updates
- **Logic Puzzles**: Three types of clues (explicit, general, conditional)
- **No Login Required**: Just create a lobby and share the link

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Server**:
   ```bash
   python3 start_server.py
   ```
   Or directly:
   ```bash
   python3 app.py
   ```

3. **Open Your Browser**:
   Go to `http://localhost:5000`

4. **Test the Implementation**:
   ```bash
   python3 test_server.py
   ```

## Debug Mode

The server includes comprehensive debug logging that shows function calls, arguments, and return values.

### Enable/Disable Debug Mode

**Option 1: Environment Variable**
```bash
# Enable debug mode (default)
DEBUG=True python3 start_server.py

# Disable debug mode
DEBUG=False python3 start_server.py
```

**Option 2: Programmatically**
```python
from debug_utils import set_debug

# Enable debug mode
set_debug(True)

# Disable debug mode
set_debug(False)
```

### Debug Output Example

When debug mode is enabled, you'll see output like:
```
[14:23:45.123] 🔍 CALL: GameSession.submit_solution(player_id='player_abc123', position=(1, 2), guess={'shape': 'circle', 'number': 3})
[14:23:45.124] ✅ RETURN: GameSession.submit_solution() -> {
  "success": true,
  "points": 10,
  "penalty": 0,
  "cell_solved": true
}
```

### Debug Log File

When debug mode is enabled, all debug output is written to `debug.log` in the project root. This file is automatically cleared each time you start the server.

**View the debug log:**
```bash
# View the entire log
cat debug.log

# Follow the log in real-time
tail -f debug.log

# View the last 50 lines
tail -n 50 debug.log
```

**Clear the debug log manually:**
```bash
# Via API endpoint
curl -X POST http://localhost:5000/api/debug/clear-log

# Or delete the file directly
rm debug.log
```

### Demo Script

Run the debug demo to see the decorators in action:
```bash
python3 debug_demo.py
```

## How to Play

1. **Create a Lobby**: Enter your name and click "Create Lobby"
2. **Share the Link**: Send the lobby URL to friends
3. **Start the Game**: Once players join, the host can start the game
4. **Solve the Puzzle**: Use the clues to determine what goes in each cell
5. **Submit Solutions**: Click on cells to submit your answers

## Game Rules

- Each cell contains a shape (🟢🟦⭐❤️) and a number (1-4)
- You receive clues to help solve the puzzle
- Correct solutions earn points
- First to solve all cells wins!

## Architecture

The game uses a clean separation of concerns:

- **`game.py`**: Core game logic (Board, Cell, Clue classes)
- **`server_classes.py`**: Server-side game management (Player, Lobby, GameSession, GameManager)
- **`app.py`**: Flask server with WebSocket support
- **`templates/`**: HTML pages for the web interface
- **`static/`**: CSS and JavaScript for the frontend

## Development Status

✅ Core game logic implemented  
✅ Server classes implemented  
✅ Flask server with WebSocket support  
✅ Frontend interface created  
✅ Basic testing framework  

## Next Steps

- Add more game modes
- Implement player authentication
- Add game history and statistics
- Improve mobile responsiveness
- Add sound effects and animations
