"""
Game registry system for multi-game Flask application.
"""

from typing import Dict, List, Type
from flask import Blueprint
from .base_game import BaseGame

# Registry of all available games
GAME_REGISTRY: Dict[str, Type[BaseGame]] = {}

def register_game(game_class: Type[BaseGame]) -> None:
    """Register a game class with the system."""
    game_instance = game_class()
    GAME_REGISTRY[game_instance.name] = game_class
    print(f"[GAME_REGISTRY] Registered game: {game_instance.name}")

def get_available_games() -> List[Dict[str, str]]:
    """Get list of all available games with their metadata."""
    games = []
    for name, game_class in GAME_REGISTRY.items():
        game_instance = game_class()
        games.append(game_instance.get_game_info())
    return games

def get_game_blueprint(game_name: str) -> Blueprint:
    """Get the Flask blueprint for a specific game."""
    if game_name not in GAME_REGISTRY:
        raise ValueError(f"Game '{game_name}' not found in registry")
    
    game_class = GAME_REGISTRY[game_name]
    game_instance = game_class()
    return game_instance.create_blueprint()

def load_all_games():
    """Load all games by importing their modules."""
    # Import all game modules to trigger registration
    try:
        from . import mysticgrid
        print(f"[GAME_REGISTRY] Loaded {len(GAME_REGISTRY)} games: {list(GAME_REGISTRY.keys())}")
    except ImportError as e:
        print(f"[GAME_REGISTRY] Error loading games: {e}")
