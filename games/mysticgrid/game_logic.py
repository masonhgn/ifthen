import uuid
import json
import threading
from datetime import datetime
from typing import Dict, Optional, Any
from .board_logic import Board, Cell, Clue
from shared.debug_utils import debug_method, debug_function


class Player:
    """Represents a connected player in the game system."""
    
    @debug_method
    def __init__(self, player_id: str = None, name: str = None):
        self.player_id = player_id or str(uuid.uuid4())
        self.name = name or f"Player_{self.player_id[:8]}"
        self.websocket = None
        self.current_lobby_id = None
        self.current_game_id = None
        self.connected = False
        self.joined_at = datetime.now()
    
    @debug_method
    def connect(self, websocket):
        """Connect player to a WebSocket."""
        self.websocket = websocket
        self.connected = True
    
    @debug_method
    def disconnect(self):
        """Disconnect player from WebSocket."""
        self.websocket = None
        self.connected = False
    
    @debug_method
    def send_message(self, message: dict):
        """Send a message to the player via WebSocket."""
        if self.websocket and self.connected:
            try:
                self.websocket.emit('message', message)
            except Exception as e:
                print(f"Error sending message to player {self.player_id}: {e}")
                self.disconnect()
    
    
    @debug_method
    def to_dict(self) -> dict:
        """Convert player to dictionary for JSON serialization."""
        return {
            'player_id': self.player_id,
            'name': self.name,
            'connected': self.connected,
            'current_lobby_id': self.current_lobby_id,
            'current_game_id': self.current_game_id
        }


class Lobby:
    """Represents a waiting room for players before a game starts."""
    
    @debug_method
    def __init__(self, lobby_id: str, host_player_id: str):
        self.lobby_id = lobby_id
        self.host_player_id = host_player_id
        self.players: Dict[str, Player] = {}
        self.max_players = 4
        self.game_settings = {"board_size": 3}
        self.created_at = datetime.now()
        self.status = "waiting"  # waiting, starting, started
    
    @debug_method
    def add_player(self, player: Player) -> bool:
        """Add a player to the lobby."""
        if len(self.players) >= self.max_players:
            return False
        
        if player.player_id in self.players:
            return False
        
        self.players[player.player_id] = player
        player.current_lobby_id = self.lobby_id
        return True
    
    @debug_method
    def remove_player(self, player_id: str) -> bool:
        """Remove a player from the lobby."""
        if player_id in self.players:
            player = self.players[player_id]
            player.current_lobby_id = None
            del self.players[player_id]
            
            # If host leaves, assign new host
            if player_id == self.host_player_id and self.players:
                self.host_player_id = next(iter(self.players.keys()))
            
            return True
        return False
    
    @debug_method
    def can_start_game(self) -> bool:
        """Check if the lobby can start a game."""
        return len(self.players) >= 1 and self.status == "waiting"
    
    @debug_method
    def start_game(self) -> Optional[str]:
        """Start a game from this lobby."""
        if not self.can_start_game():
            return None
        
        self.status = "started"
        # Return a game session ID (will be created by GameManager)
        return f"game_{self.lobby_id}_{int(datetime.now().timestamp())}"
    
    @debug_method
    def get_lobby_state(self) -> dict:
        """Get current lobby state for clients."""
        return {
            'lobby_id': self.lobby_id,
            'host_player_id': self.host_player_id,
            'players': [player.to_dict() for player in self.players.values()],
            'max_players': self.max_players,
            'game_settings': self.game_settings,
            'status': self.status,
            'can_start': self.can_start_game()
        }


class GameSession:
    """Represents an active game session."""
    
    @debug_method
    def __init__(self, session_id: str, board_size: int = 3):
        self.session_id = session_id
        self.board_size = board_size
        self.board = None  # Lazy initialization
        self.clues = None  # Lazy initialization
        self.players: Dict[str, Player] = {}
        self.game_state = "waiting"  # waiting, playing, finished
        self.current_turn = None
        self.turn_count = 0
        self.max_turns = 50  # Shared turn pool - adjust difficulty here
        self.player_turns: Dict[str, int] = {}  # player_id -> turn count
        self.solved_cells: Dict[tuple, dict] = {}  # (r,c) -> {"player_id": str, "solution": Cell}
        self.revealed_clues: Dict[str, list] = {}  # player_id -> list of clue indices
        self.shared_clues: Dict[str, list] = {}  # player_id -> list of clues shared with them
        self.created_at = datetime.now()
        self.game_start_time = None  # When the game actually starts
        self.game_duration = 900  # 15 minutes in seconds
        self.clues_distributed = False  # Track if clues have been distributed
        self._initialization_lock = threading.Lock()  # Thread safety for initialization
    
    @debug_method
    def add_player(self, player: Player) -> bool:
        """Add a player to the game session."""
        if player.player_id in self.players:
            return False
        
        self.players[player.player_id] = player
        player.current_game_id = self.session_id
        self.revealed_clues[player.player_id] = []
        self.shared_clues[player.player_id] = []
        self.player_turns[player.player_id] = 0
        
        # If this is the first player, they become the current turn
        if self.current_turn is None:
            self.current_turn = player.player_id
        
        return True
    
    @debug_method
    def _initialize_board_and_clues(self):
        """Lazy initialization of board and clues with thread safety."""
        if self.board is None:
            with self._initialization_lock:
                # Double-check pattern to prevent race conditions
                if self.board is None:
                    import time
                    board_start_time = time.time()
                    print(f"[TIMING] About to create board at: {board_start_time:.3f}s")
                    self.board = Board(self.board_size)
                    board_time = time.time()
                    print(f"[TIMING] Board created at: {board_time:.3f}s (took {board_time - board_start_time:.3f}s)")
                    
                    print(f"[TIMING] About to generate clues at: {time.time():.3f}s")
                    self.clues = self.board.generate_all_clues()
                    clues_time = time.time()
                    print(f"[TIMING] Clues generated at: {clues_time:.3f}s (took {clues_time - board_time:.3f}s)")
                    print(f"[TIMING] Total board+clues initialization: {clues_time - board_start_time:.3f}s")
    
    @debug_method
    def start_game(self) -> bool:
        """Start the game if conditions are met."""
        if len(self.players) < 1 or self.game_state != "waiting":
            return False
        
        # Initialize board and clues when starting the game
        self._initialize_board_and_clues()
        
        # Distribute clues among players
        self.distribute_clues()
        
        self.game_state = "playing"
        self.game_start_time = datetime.now()
        return True
    
    @debug_method
    def distribute_clues(self):
        """Distribute clues uniquely among players at game start."""
        if self.clues_distributed:
            return
        
        with self._initialization_lock:
            # Double-check pattern to prevent race conditions
            if self.clues_distributed:
                return
            
            # Ensure board and clues are initialized
            self._initialize_board_and_clues()
            
            import random
            
            # Calculate clues per player (aim for 6-8 clues each for better solvability)
            num_players = len(self.players)
            total_clues = len(self.clues)
            clues_per_player = max(6, total_clues // num_players)
            
            print(f"DEBUG: Distributing {total_clues} total clues among {num_players} players ({clues_per_player} each)")
            
            # Shuffle all clue indices
            all_clue_indices = list(range(total_clues))
            random.shuffle(all_clue_indices)
            
            # Distribute clues to each player
            player_ids = list(self.players.keys())
            for i, player_id in enumerate(player_ids):
                start_idx = i * clues_per_player
                end_idx = min(start_idx + clues_per_player, total_clues)
                
                # Give this player their clues
                self.revealed_clues[player_id] = all_clue_indices[start_idx:end_idx]
                print(f"DEBUG: Player {i+1} gets {len(self.revealed_clues[player_id])} clues")
                
                # If this is the last player and there are remaining clues, give them the extras
                if i == len(player_ids) - 1 and end_idx < total_clues:
                    self.revealed_clues[player_id].extend(all_clue_indices[end_idx:])
                    print(f"DEBUG: Player {i+1} gets {len(all_clue_indices[end_idx:])} extra clues")
            
            self.clues_distributed = True
    
    @debug_method
    def _remove_redundant_clues(self, row: int, col: int, shape: str, number: int):
        """Remove clues that are now redundant because the cell is revealed on the board."""
        if not self.clues:
            return
        
        # Find clues that are now redundant
        redundant_clue_indices = []
        
        for i, clue in enumerate(self.clues):
            is_redundant = False
            
            if clue.clue_type.value == 1:  # EXPLICIT
                # If this clue is about the exact cell that was just solved
                if clue.position == (row, col):
                    if clue.attribute == "shape" and clue.value == shape:
                        is_redundant = True
                    elif clue.attribute == "number" and clue.value == number:
                        is_redundant = True
            
            elif clue.clue_type.value == 2:  # GENERAL
                # For general clues, we need to check if this cell's reveal makes the clue redundant
                # This is more complex - for now, we'll be conservative and not remove general clues
                # as they might still be useful for other cells
                pass
            
            elif clue.clue_type.value == 3:  # CONDITIONAL
                # Check if the condition or consequence is about the solved cell
                if clue.condition and clue.condition.position == (row, col):
                    if clue.condition.attribute == "shape" and clue.condition.value == shape:
                        is_redundant = True
                    elif clue.condition.attribute == "number" and clue.condition.value == number:
                        is_redundant = True
                
                if clue.consequence and clue.consequence.position == (row, col):
                    if clue.consequence.attribute == "shape" and clue.consequence.value == shape:
                        is_redundant = True
                    elif clue.consequence.attribute == "number" and clue.consequence.value == number:
                        is_redundant = True
            
            if is_redundant:
                redundant_clue_indices.append(i)
        
        # Remove redundant clues from all players
        for player_id in self.players:
            # Remove from revealed clues
            self.revealed_clues[player_id] = [
                idx for idx in self.revealed_clues[player_id] 
                if idx not in redundant_clue_indices
            ]
            # Remove from shared clues
            self.shared_clues[player_id] = [
                idx for idx in self.shared_clues[player_id] 
                if idx not in redundant_clue_indices
            ]
    
    @debug_method
    def submit_solution(self, player_id: str, position: tuple, guess: dict) -> dict:
        """Submit a solution for a cell position."""
        print(f"[DEBUG] submit_solution called - game_state: {self.game_state}, player_id: {player_id}, current_turn: {self.current_turn}")
        
        if self.game_state != "playing":
            print(f"[DEBUG] Game not in playing state: {self.game_state}")
            # TEMPORARY FIX: Allow submission even when game_state is "finished" for debugging
            if self.game_state == "finished":
                print(f"[DEBUG] Allowing submission despite finished state for debugging")
            else:
                return {"success": False, "error": "Game not in playing state"}
        
        if player_id not in self.players:
            print(f"[DEBUG] Player not in game: {player_id}")
            return {"success": False, "error": "Player not in game"}
        
        if player_id != self.current_turn:
            print(f"[DEBUG] Not player's turn: {player_id} != {self.current_turn}")
            return {"success": False, "error": "Not your turn"}
        
        # Ensure board and clues are initialized
        self._initialize_board_and_clues()
        
        r, c = position
        # Check if cell is fully solved (both shape and number revealed)
        if (r, c) in self.solved_cells:
            existing = self.solved_cells[(r, c)]
            print(f"[DEBUG] Cell ({r}, {c}) already in solved_cells: shape_revealed={existing['revealed']['shape']}, number_revealed={existing['revealed']['number']}")
            if existing["revealed"]["shape"] and existing["revealed"]["number"]:
                print(f"[DEBUG] Cell ({r}, {c}) is fully solved, rejecting guess")
                return {"success": False, "error": "Cell already fully solved"}
            else:
                print(f"[DEBUG] Cell ({r}, {c}) is partially solved, allowing update")
        
        # Validate the guess
        actual_cell = self.board.board[r][c]
        guessed_shape = guess.get('shape')
        guessed_number = guess.get('number')
        
        # Check what was guessed correctly
        shape_correct = guessed_shape is None or actual_cell.shape == guessed_shape
        number_correct = guessed_number is None or actual_cell.number == guessed_number
        
        # Check if solution is correct
        success = False
        
        if shape_correct and number_correct:
            # Both correct (or both not guessed)
            if guessed_shape and guessed_number:
                # Complete correct guess
                success = True
                self.solved_cells[(r, c)] = {
                    "player_id": player_id,
                    "solution": {
                        "shape": actual_cell.shape,
                        "number": actual_cell.number
                    },
                    "revealed": {
                        "shape": True,
                        "number": True
                    },
                    "solved_at": datetime.now().isoformat()
                }
            else:
                # Partial guess, both parts correct
                success = True
                # Update existing entry or create new one
                if (r, c) in self.solved_cells:
                    # Update existing partial solution
                    existing = self.solved_cells[(r, c)]
                    existing["revealed"]["shape"] = existing["revealed"]["shape"] or (guessed_shape is not None)
                    existing["revealed"]["number"] = existing["revealed"]["number"] or (guessed_number is not None)
                    existing["solved_at"] = datetime.now().isoformat()
                else:
                    # Create new partial solution
                    self.solved_cells[(r, c)] = {
                        "player_id": player_id,
                        "solution": {
                            "shape": actual_cell.shape,
                            "number": actual_cell.number
                        },
                        "revealed": {
                            "shape": guessed_shape is not None,
                            "number": guessed_number is not None
                        },
                        "solved_at": datetime.now().isoformat()
                    }
        
        # Remove redundant clues if cell was solved
        if success:
            self._remove_redundant_clues(r, c, actual_cell.shape, actual_cell.number)
        
        # Move to next turn
        print(f"[DEBUG] About to call next_turn() - success: {success}")
        self.next_turn()
        print(f"[DEBUG] After next_turn() - current_turn: {self.current_turn}")
        
        # Calculate game metrics (needed for return values)
        total_cells = self.board.size * self.board.size
        # Count only fully solved cells (both shape and number revealed)
        cells_solved = sum(1 for cell_data in self.solved_cells.values() 
                          if cell_data["revealed"]["shape"] and cell_data["revealed"]["number"])
        turns_remaining = self.max_turns - self.turn_count
        time_remaining = self.get_time_remaining()
        
        print(f"[DEBUG] Game metrics calculated:")
        print(f"  - max_turns: {self.max_turns}")
        print(f"  - turn_count: {self.turn_count}")
        print(f"  - turns_remaining: {turns_remaining}")
        print(f"  - total_cells: {total_cells}")
        print(f"  - cells_solved (fully): {cells_solved}")
        print(f"  - total_solved_cells (partial+full): {len(self.solved_cells)}")
        print(f"  - time_remaining: {time_remaining}")
        
        # Check if game is complete (all cells solved, turns exhausted, or time up)
        # Only check if game is still in playing state
        if self.game_state == "playing":
            print(f"[DEBUG] Game completion check:")
            print(f"  - total_cells: {total_cells}")
            print(f"  - cells_solved: {cells_solved}")
            print(f"  - turns_remaining: {turns_remaining}")
            print(f"  - time_remaining: {time_remaining}")
            print(f"  - current game_state: {self.game_state}")
            print(f"  - turn_count: {self.turn_count}")
            print(f"  - max_turns: {self.max_turns}")
            print(f"  - game_start_time: {self.game_start_time}")
            print(f"  - solved_cells count: {len(self.solved_cells)}")
            print(f"  - board size: {self.board.size if self.board else 'None'}")
            
            if cells_solved >= total_cells:
                print(f"[DEBUG] Game finished: All cells solved ({cells_solved}/{total_cells})")
                self.game_state = "finished"
            elif turns_remaining <= 0:
                print(f"[DEBUG] Game finished: No turns remaining ({turns_remaining})")
                self.game_state = "finished"
            elif time_remaining <= 0:
                print(f"[DEBUG] Game finished: Time up ({time_remaining})")
                self.game_state = "finished"
            else:
                print(f"[DEBUG] Game continues - not finished yet")
        else:
            print(f"[DEBUG] Skipping game completion check - game state is: {self.game_state}")
        
        if success:
            return {
                "success": True, 
                "game_complete": self.game_state == "finished",
                "cell_solved": (r, c) in self.solved_cells,
                "cells_remaining": total_cells - cells_solved,
                "turns_remaining": turns_remaining,
                "time_remaining": time_remaining
            }
        else:
            return {
                "success": False, 
                "error": "Incorrect guess", 
                "shape_correct": shape_correct,
                "number_correct": number_correct,
                "cells_remaining": total_cells - cells_solved,
                "turns_remaining": turns_remaining,
                "time_remaining": time_remaining
            }
    
    
    @debug_method
    def get_time_remaining(self) -> int:
        """Get remaining time in seconds."""
        if not self.game_start_time or self.game_state != "playing":
            return self.game_duration
        
        elapsed = (datetime.now() - self.game_start_time).total_seconds()
        remaining = max(0, self.game_duration - elapsed)
        return int(remaining)
    
    @debug_method
    def next_turn(self):
        """Move to the next player's turn."""
        print(f"[DEBUG] next_turn called - current_turn: {self.current_turn}, players: {list(self.players.keys())}")
        
        if not self.players:
            print(f"[DEBUG] No players, returning")
            return
        
        player_ids = list(self.players.keys())
        current_index = player_ids.index(self.current_turn) if self.current_turn in player_ids else 0
        next_index = (current_index + 1) % len(player_ids)
        old_turn = self.current_turn
        self.current_turn = player_ids[next_index]
        
        # Increment turn count only when a turn is actually completed
        # This represents the number of completed turns, not the current turn number
        self.turn_count += 1
        self.player_turns[self.current_turn] += 1
        
        print(f"[DEBUG] Turn advanced: {old_turn} -> {self.current_turn}, turn_count: {self.turn_count}")
    
    @debug_method
    def share_clue(self, from_player_id: str, to_player_id: str, clue_index: int) -> dict:
        """Share a clue from one player to another."""
        if self.game_state != "playing":
            return {"success": False, "error": "Game not in playing state"}
        
        if from_player_id not in self.players or to_player_id not in self.players:
            return {"success": False, "error": "Invalid player"}
        
        if from_player_id == to_player_id:
            return {"success": False, "error": "Cannot share clue with yourself"}
        
        if from_player_id != self.current_turn:
            return {"success": False, "error": "Not your turn"}
        
        # Ensure board and clues are initialized
        self._initialize_board_and_clues()
        
        if clue_index < 0 or clue_index >= len(self.clues):
            return {"success": False, "error": "Invalid clue index"}
        
        # Check if the player has this clue (either revealed or shared)
        player_has_clue = (clue_index in self.revealed_clues[from_player_id] or 
                          clue_index in self.shared_clues[from_player_id])
        if not player_has_clue:
            return {"success": False, "error": "You don't have this clue"}
        
        # Check if the clue is already shared with the target player
        if clue_index in self.shared_clues[to_player_id]:
            return {"success": False, "error": "This clue is already shared with this player"}
        
        # Share the clue
        # Add to receiver's shared clues (they keep their original clues)
        self.shared_clues[to_player_id].append(clue_index)
        
        # Remove the clue from the sender's revealed clues (they no longer have it)
        if clue_index in self.revealed_clues[from_player_id]:
            self.revealed_clues[from_player_id].remove(clue_index)
        elif clue_index in self.shared_clues[from_player_id]:
            self.shared_clues[from_player_id].remove(clue_index)
        
        # Move to next turn
        self.next_turn()
        
        return {
            "success": True,
            "clue": self.clues[clue_index].to_dict(),
            "from_player": self.players[from_player_id].name,
            "to_player": self.players[to_player_id].name
        }
    
    @debug_method
    def get_game_state_for_player(self, player_id: str) -> dict:
        """Get game state for a specific player."""
        import time
        state_start_time = time.time()
        print(f"[TIMING] get_game_state_for_player called at: {state_start_time:.3f}s")
        
        # Ensure board and clues are initialized when first accessed
        print(f"[TIMING] About to initialize board and clues at: {time.time():.3f}s")
        self._initialize_board_and_clues()
        init_time = time.time()
        print(f"[TIMING] Board and clues initialized at: {init_time:.3f}s (took {init_time - state_start_time:.3f}s)")
        
        # If clues haven't been distributed yet, do it now
        if not self.clues_distributed:
            print(f"[TIMING] About to distribute clues at: {time.time():.3f}s")
            self.distribute_clues()
            distribute_time = time.time()
            print(f"[TIMING] Clues distributed at: {distribute_time:.3f}s (took {distribute_time - init_time:.3f}s)")
        
        # Initialize player turns if not done yet
        for p_id in self.players:
            if p_id not in self.player_turns:
                self.player_turns[p_id] = 0
        
        # Ensure current_turn is set if not already set
        if self.current_turn is None and self.players:
            self.current_turn = list(self.players.keys())[0]
            print(f"[DEBUG] Set current_turn to first player: {self.current_turn}")
        
        # Get all clues available to this player (revealed + shared)
        print(f"[TIMING] About to process clues at: {time.time():.3f}s")
        all_clue_indices = set(self.revealed_clues.get(player_id, []))
        all_clue_indices.update(self.shared_clues.get(player_id, []))
        player_clues = [self.clues[i].to_dict() for i in sorted(all_clue_indices)]
        clues_time = time.time()
        print(f"[TIMING] Clues processed at: {clues_time:.3f}s (took {clues_time - state_start_time:.3f}s)")
        
        solved_cells_dict = {f"{r},{c}": data for (r, c), data in self.solved_cells.items()}
        
        # Pre-compute player data to avoid multiple to_dict() calls
        players_data = [p.to_dict() for p in self.players.values()]
        
        # Calculate collaborative metrics
        total_cells = self.board.size * self.board.size
        # Count only fully solved cells (both shape and number revealed)
        cells_solved = sum(1 for cell_data in self.solved_cells.values() 
                          if cell_data["revealed"]["shape"] and cell_data["revealed"]["number"])
        cells_remaining = total_cells - cells_solved
        turns_remaining = self.max_turns - self.turn_count
        time_remaining = self.get_time_remaining()
        
        # Calculate is_my_turn
        is_my_turn = self.current_turn == player_id
        
        result = {
            'session_id': self.session_id,
            'game_state': self.game_state,
            'board_size': self.board.size,
            'players': players_data,
            'current_turn': self.current_turn,
            'turn_count': self.turn_count,
            'max_turns': self.max_turns,
            'turns_remaining': turns_remaining,
            'time_remaining': time_remaining,
            'cells_solved': cells_solved,
            'cells_remaining': cells_remaining,
            'total_cells': total_cells,
            'player_turns': self.player_turns.get(player_id, 0),
            'solved_cells': solved_cells_dict,
            'clues': player_clues,
            'is_my_turn': is_my_turn
        }
        
        # Debug logging for turn information
        print(f"[DEBUG] Game state for player {player_id}:")
        print(f"  - current_turn: {self.current_turn}")
        print(f"  - is_my_turn: {is_my_turn}")
        print(f"  - game_state: {self.game_state}")
        print(f"  - players: {[p.player_id for p in self.players.values()]}")
        print(f"  - turn_count: {self.turn_count}")
        print(f"  - max_turns: {self.max_turns}")
        print(f"  - cells_solved: {len(self.solved_cells)}")
        print(f"  - total_cells: {total_cells}")
        print(f"  - time_remaining: {time_remaining}")
        
        final_time = time.time()
        print(f"[TIMING] get_game_state_for_player completed at: {final_time:.3f}s (total time: {final_time - state_start_time:.3f}s)")
        return result


class GameManager:
    """Central coordinator for managing lobbies and game sessions."""
    
    @debug_method
    def __init__(self):
        self.lobbies: Dict[str, Lobby] = {}
        self.game_sessions: Dict[str, GameSession] = {}
        self.players: Dict[str, Player] = {}
        self._cleanup_lock = threading.Lock()  # Thread safety for cleanup
    
    @debug_method
    def create_player(self, player_id: str = None, name: str = None) -> Player:
        """Create a new player."""
        player = Player(player_id=player_id, name=name)
        self.players[player.player_id] = player
        return player
    
    @debug_method
    def get_player(self, player_id: str) -> Optional[Player]:
        """Get a player by ID."""
        return self.players.get(player_id)
    
    @debug_method
    def create_lobby(self, host_player_id: str) -> Optional[str]:
        """Create a new lobby."""
        if host_player_id not in self.players:
            return None
        
        lobby_id = f"lobby_{str(uuid.uuid4())[:8]}"
        lobby = Lobby(lobby_id, host_player_id)
        
        # Add host to lobby
        host = self.players[host_player_id]
        lobby.add_player(host)
        
        self.lobbies[lobby_id] = lobby
        return lobby_id
    
    @debug_method
    def join_lobby(self, lobby_id: str, player_id: str) -> bool:
        """Join a player to a lobby."""
        if lobby_id not in self.lobbies or player_id not in self.players:
            return False
        
        lobby = self.lobbies[lobby_id]
        player = self.players[player_id]
        
        return lobby.add_player(player)
    
    @debug_method
    def leave_lobby(self, lobby_id: str, player_id: str) -> bool:
        """Remove a player from a lobby."""
        if lobby_id not in self.lobbies:
            return False
        
        lobby = self.lobbies[lobby_id]
        success = lobby.remove_player(player_id)
        
        # Clean up empty lobbies
        if not lobby.players:
            del self.lobbies[lobby_id]
        
        return success
    
    @debug_method
    def start_game_from_lobby(self, lobby_id: str) -> Optional[str]:
        """Start a game from a lobby."""
        print(f"DEBUG: start_game_from_lobby called with lobby_id: {lobby_id}")
        if lobby_id not in self.lobbies:
            print(f"DEBUG: Lobby {lobby_id} not found in lobbies")
            return None
        
        lobby = self.lobbies[lobby_id]
        print(f"DEBUG: Found lobby with {len(lobby.players)} players")
        game_id = lobby.start_game()
        print(f"DEBUG: lobby.start_game() returned: {game_id}")
        
        if not game_id:
            print(f"DEBUG: lobby.start_game() returned None")
            return None
        
        # Create game session (lazy initialization - no board generation yet)
        print(f"DEBUG: Creating game session with board size: {lobby.game_settings['board_size']}")
        game_session = GameSession(game_id, lobby.game_settings["board_size"])
        
        # Add all lobby players to game
        print(f"DEBUG: Adding {len(lobby.players)} players to game session")
        for player in lobby.players.values():
            game_session.add_player(player)
        
        # Initialize the game (this will set up turn order, etc.)
        # But board/clues will be generated lazily when first accessed
        game_session.game_state = "playing"
        game_session.game_start_time = datetime.now()  # Set start time when game begins
        game_session.current_turn = list(game_session.players.keys())[0]  # Set first player as current turn
        print(f"DEBUG: Set current turn to: {game_session.current_turn}")
        print(f"DEBUG: Set game_state to: {game_session.game_state}")
        print(f"DEBUG: Game session created with {len(game_session.players)} players")
        
        # Store game session
        self.game_sessions[game_id] = game_session
        print(f"DEBUG: Stored game session, total games: {len(self.game_sessions)}")
        
        # Clean up lobby
        del self.lobbies[lobby_id]
        print(f"DEBUG: Cleaned up lobby, returning game_id: {game_id}")
        
        return game_id
    
    @debug_method
    def get_lobby_by_id(self, lobby_id: str) -> Optional[Lobby]:
        """Get a lobby by ID."""
        return self.lobbies.get(lobby_id)
    
    @debug_method
    def get_game_by_id(self, game_id: str) -> Optional[GameSession]:
        """Get a game session by ID."""
        return self.game_sessions.get(game_id)
    
    @debug_method
    def cleanup_inactive_sessions(self):
        """Clean up inactive lobbies and games."""
        current_time = datetime.now()
        
        # Clean up old lobbies (older than 1 hour)
        inactive_lobbies = [
            lobby_id for lobby_id, lobby in self.lobbies.items()
            if (current_time - lobby.created_at).seconds > 3600
        ]
        
        for lobby_id in inactive_lobbies:
            del self.lobbies[lobby_id]
        
        # Clean up finished games (older than 30 minutes)
        inactive_games = [
            game_id for game_id, game in self.game_sessions.items()
            if game.game_state == "finished" and 
            (current_time - game.created_at).seconds > 1800
        ]
        
        for game_id in inactive_games:
            del self.game_sessions[game_id]
    
    def get_stats(self) -> dict:
        """Get server statistics."""
        return {
            'active_lobbies': len(self.lobbies),
            'active_games': len(self.game_sessions),
            'total_players': len(self.players),
            'connected_players': sum(1 for p in self.players.values() if p.connected)
        }
    
    @debug_method
    def cleanup_finished_games(self):
        """Clean up finished games and inactive players."""
        with self._cleanup_lock:
            # Clean up finished games
            finished_games = []
            for game_id, game in self.game_sessions.items():
                if game.game_state == "finished":
                    # Check if game has been finished for more than 1 hour
                    if game.game_start_time:
                        time_since_finish = datetime.now() - game.game_start_time
                        if time_since_finish.total_seconds() > 3600:  # 1 hour
                            finished_games.append(game_id)
            
            for game_id in finished_games:
                print(f"[CLEANUP] Removing finished game: {game_id}")
                del self.game_sessions[game_id]
            
            # Clean up inactive players (disconnected for more than 2 hours)
            inactive_players = []
            for player_id, player in self.players.items():
                if not player.connected:
                    time_since_join = datetime.now() - player.joined_at
                    if time_since_join.total_seconds() > 7200:  # 2 hours
                        inactive_players.append(player_id)
            
            for player_id in inactive_players:
                print(f"[CLEANUP] Removing inactive player: {player_id}")
                del self.players[player_id]
            
            if finished_games or inactive_players:
                print(f"[CLEANUP] Cleaned up {len(finished_games)} games and {len(inactive_players)} players")
    
    @debug_method
    def cleanup_empty_lobbies(self):
        """Clean up empty lobbies."""
        with self._cleanup_lock:
            empty_lobbies = [lobby_id for lobby_id, lobby in self.lobbies.items() if not lobby.players]
            for lobby_id in empty_lobbies:
                print(f"[CLEANUP] Removing empty lobby: {lobby_id}")
                del self.lobbies[lobby_id]
            
            if empty_lobbies:
                print(f"[CLEANUP] Cleaned up {len(empty_lobbies)} empty lobbies")