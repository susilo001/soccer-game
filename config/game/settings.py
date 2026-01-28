"""Game settings and configuration."""

import os
from dataclasses import dataclass
from typing import Tuple


@dataclass
class DisplaySettings:
    """Display and rendering settings."""
    width: int = 1200
    height: int = 800
    fps: int = 60
    fullscreen: bool = False
    title: str = "Soccer Game AI"


@dataclass
class FieldSettings:
    """Soccer field dimensions and properties."""
    length: float = 105.0  # meters
    width: float = 68.0    # meters
    goal_width: float = 7.32
    goal_height: float = 2.44
    penalty_area_length: float = 16.5
    penalty_area_width: float = 40.3
    center_circle_radius: float = 9.15


@dataclass
class GameplaySettings:
    """Gameplay rules and timing."""
    match_duration: int = 90  # minutes
    half_time_duration: int = 45
    players_per_team: int = 11
    max_substitutions: int = 5
    injury_time_enabled: bool = True


@dataclass
class AISettings:
    """AI agent configuration."""
    difficulty_level: str = "medium"  # easy, medium, hard, expert
    learning_enabled: bool = True
    training_mode: bool = False
    agent_type: str = "neural_network"  # neural_network, rule_based, hybrid


class GameSettings:
    """Main game settings container."""
    
    def __init__(self):
        self.display = DisplaySettings()
        self.field = FieldSettings()
        self.gameplay = GameplaySettings()
        self.ai = AISettings()
        
        # Load environment variables if available
        self._load_from_env()
    
    def _load_from_env(self):
        """Load settings from environment variables."""
        if os.getenv("GAME_WIDTH"):
            self.display.width = int(os.getenv("GAME_WIDTH"))
        if os.getenv("GAME_HEIGHT"):
            self.display.height = int(os.getenv("GAME_HEIGHT"))
        if os.getenv("GAME_FPS"):
            self.display.fps = int(os.getenv("GAME_FPS"))
        if os.getenv("AI_DIFFICULTY"):
            self.ai.difficulty_level = os.getenv("AI_DIFFICULTY")
    
    def to_dict(self) -> dict:
        """Convert settings to dictionary."""
        return {
            "display": self.display.__dict__,
            "field": self.field.__dict__,
            "gameplay": self.gameplay.__dict__,
            "ai": self.ai.__dict__
        }