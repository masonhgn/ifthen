"""
Base game class that all games must inherit from.
"""

from abc import ABC, abstractmethod
from flask import Blueprint
from typing import Dict, Any

class BaseGame(ABC):
    """Base class that all games must inherit from."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the game (e.g., 'mysticgrid')."""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for the game (e.g., 'MysticGrid')."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Short description of the game."""
        pass
    
    @property
    @abstractmethod
    def url_prefix(self) -> str:
        """URL prefix for the game routes (e.g., '/mysticgrid')."""
        pass
    
    @property
    @abstractmethod
    def icon(self) -> str:
        """Icon/emoji for the game in the catalog."""
        pass
    
    @abstractmethod
    def create_blueprint(self) -> Blueprint:
        """Create and return the Flask blueprint for this game."""
        pass
    
    @abstractmethod
    def get_game_info(self) -> Dict[str, Any]:
        """Get detailed information about the game for the catalog."""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current game statistics (optional override)."""
        return {
            'active_players': 0,
            'active_games': 0,
            'total_players': 0
        }
