"""
MysticGrid game module.
"""

from .mysticgrid_game import MysticGridGame
from .routes import register_socket_handlers
from .. import register_game

# Create game instance
mysticgrid_game = MysticGridGame()

# Register the game
register_game(MysticGridGame)

# Export the game class for registration
__all__ = ['MysticGridGame', 'mysticgrid_game', 'register_socket_handlers']
