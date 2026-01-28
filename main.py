#!/usr/bin/env python3
"""
Soccer Game - Main Entry Point
A Python-based soccer game with AI agents.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.engine.game_engine import GameEngine
from config.game.settings import GameSettings
import logging

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('game.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main function to start the soccer game."""
    try:
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting Soccer Game...")
        
        # Initialize game settings
        settings = GameSettings()
        
        # Create and run the game engine
        engine = GameEngine(settings)
        engine.run()
        
    except KeyboardInterrupt:
        logger.info("Game interrupted by user")
    except Exception as e:
        logger.error(f"Game crashed: {e}", exc_info=True)
    finally:
        logger.info("Game shutting down...")

if __name__ == "__main__":
    main()