"""
MysticGrid game implementation.
"""

from flask import Blueprint
from typing import Dict, Any
from games.base_game import BaseGame
from .routes import mysticgrid_bp, register_socket_handlers, game_manager

class MysticGridGame(BaseGame):
    """MysticGrid game implementation."""
    
    @property
    def name(self) -> str:
        """Unique identifier for the game."""
        return "mysticgrid"
    
    @property
    def display_name(self) -> str:
        """Human-readable name for the game."""
        return "MysticGrid"
    
    @property
    def description(self) -> str:
        """Short description of the game."""
        return "A collaborative multiplayer puzzle game where players work together to solve a mystical grid using logical clues!"
    
    @property
    def url_prefix(self) -> str:
        """URL prefix for the game routes."""
        return "/mysticgrid"
    
    @property
    def icon(self) -> str:
        """Icon/emoji for the game in the catalog."""
        return "🔮"
    
    def create_blueprint(self) -> Blueprint:
        """Create and return the Flask blueprint for this game."""
        return mysticgrid_bp
    
    def get_game_info(self) -> Dict[str, Any]:
        """Get detailed information about the game for the catalog."""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'url_prefix': self.url_prefix,
            'icon': self.icon,
            'features': [
                "Multiplayer Support",
                "Real-time Gameplay", 
                "Logic Puzzles",
                "No Login Required",
                "Collaborative Solving"
            ],
            'rules': [
                "Each cell contains a shape (🟢🟦⭐❤️) and a number (1-4)",
                "You receive clues to help solve the puzzle",
                "Correct solutions earn points",
                "Work together to solve all cells!"
            ],
            'stats': self.get_stats()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current game statistics."""
        return game_manager.get_stats()
    
    def register_socket_handlers(self, socketio):
        """Register socket handlers with the main socketio instance."""
        register_socket_handlers(socketio)
