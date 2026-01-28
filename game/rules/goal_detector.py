"""Goal detection and scoring system for soccer game."""

from typing import Tuple, Optional
from dataclasses import dataclass
import time


@dataclass
class Goal:
    """Represents a goal scored."""
    scoring_team: str
    time_scored: float
    ball_position: Tuple[float, float]
    scorer_id: Optional[str] = None


class GoalDetector:
    """Detects when goals are scored and manages scoring."""
    
    def __init__(self, field_length: float = 105.0, field_width: float = 68.0, 
                 goal_width: float = 7.32):
        """Initialize goal detector.
        
        Args:
            field_length: Length of the field in meters
            field_width: Width of the field in meters  
            goal_width: Width of the goal in meters
        """
        self.field_length = field_length
        self.field_width = field_width
        self.goal_width = goal_width
        
        # Calculate goal boundaries
        self.half_field = field_length / 2
        self.half_goal = goal_width / 2
        
        # Goal lines (simplified - just check if ball crosses goal line)
        self.home_goal_line = -self.half_field  # Left goal line
        self.away_goal_line = self.half_field   # Right goal line
        
        # Score tracking
        self.home_score = 0
        self.away_score = 0
        self.goals_scored = []
        
        # Goal celebration state
        self.goal_just_scored = False
        self.celebration_timer = 0.0
        self.celebration_duration = 3.0  # 3 seconds
        self.last_goal = None
    
    def check_goal(self, ball_x: float, ball_y: float, ball_last_touched_by: Optional[str] = None) -> Optional[Goal]:
        """Check if ball position constitutes a goal.
        
        Args:
            ball_x: Ball x position
            ball_y: Ball y position
            ball_last_touched_by: ID of player who last touched the ball
            
        Returns:
            Goal object if goal was scored, None otherwise
        """
        goal = None
        
        # Check if ball is within goal width (between goal posts) - make it more generous
        goal_width_buffer = self.half_goal + 0.5  # Add 0.5m buffer for easier scoring
        
        # Debug: print when ball is very close to goal (reduce spam)
        if abs(ball_y) <= goal_width_buffer and (ball_x <= self.home_goal_line + 0.5 or ball_x >= self.away_goal_line - 0.5):
            if not hasattr(self, '_last_near_goal_debug') or (time.time() - self._last_near_goal_debug) > 2.0:
                print(f"Ball near goal: ({ball_x:.1f}, {ball_y:.1f}) | Goal width: ±{goal_width_buffer:.1f} | Goal lines: {self.home_goal_line:.1f}, {self.away_goal_line:.1f}")
                self._last_near_goal_debug = time.time()
        
        if abs(ball_y) <= goal_width_buffer:
            # Make goal detection more generous - reduce the goal line threshold by 1 meter
            home_goal_threshold = self.home_goal_line + 1.0  # -51.5 instead of -52.5
            away_goal_threshold = self.away_goal_line - 1.0  # 51.5 instead of 52.5
            
            # Check home goal (left side) - away team scores
            if ball_x <= home_goal_threshold:
                goal = Goal(
                    scoring_team="away",
                    time_scored=time.time(),
                    ball_position=(ball_x, ball_y),
                    scorer_id=ball_last_touched_by
                )
                self.away_score += 1
                print(f"🥅 GOAL! Away team scores! Ball at ({ball_x:.1f}, {ball_y:.1f}) - Score: {self.get_score_string()}")
            
            # Check away goal (right side) - home team scores  
            elif ball_x >= away_goal_threshold:
                goal = Goal(
                    scoring_team="home", 
                    time_scored=time.time(),
                    ball_position=(ball_x, ball_y),
                    scorer_id=ball_last_touched_by
                )
                self.home_score += 1
                print(f"🥅 GOAL! Home team scores! Ball at ({ball_x:.1f}, {ball_y:.1f}) - Score: {self.get_score_string()}")
        
        if goal:
            self.goals_scored.append(goal)
            self.goal_just_scored = True
            self.celebration_timer = self.celebration_duration
            self.last_goal = goal
            
        return goal
    
    def _point_in_goal_zone(self, x: float, y: float, goal_zone: Tuple[float, float, float, float]) -> bool:
        """Check if a point is within a goal zone.
        
        Args:
            x: Point x coordinate
            y: Point y coordinate
            goal_zone: Goal zone boundaries (x_min, x_max, y_min, y_max)
            
        Returns:
            True if point is in goal zone
        """
        x_min, x_max, y_min, y_max = goal_zone
        return x_min <= x <= x_max and y_min <= y <= y_max
    
    def update(self, dt: float):
        """Update goal celebration timer.
        
        Args:
            dt: Delta time in seconds
        """
        if self.goal_just_scored:
            self.celebration_timer -= dt
            if self.celebration_timer <= 0:
                self.goal_just_scored = False
                self.celebration_timer = 0.0
    
    def get_score(self) -> Tuple[int, int]:
        """Get current score.
        
        Returns:
            Tuple of (home_score, away_score)
        """
        return self.home_score, self.away_score
    
    def get_score_string(self) -> str:
        """Get formatted score string.
        
        Returns:
            Score string like "Home 2 - 1 Away"
        """
        return f"Home {self.home_score} - {self.away_score} Away"
    
    def is_celebrating(self) -> bool:
        """Check if currently in goal celebration mode.
        
        Returns:
            True if celebrating a goal
        """
        return self.goal_just_scored
    
    def get_last_goal(self) -> Optional[Goal]:
        """Get the most recently scored goal.
        
        Returns:
            Last goal scored, or None
        """
        return self.last_goal
    
    def reset_celebration(self):
        """Reset celebration state (for manual control)."""
        self.goal_just_scored = False
        self.celebration_timer = 0.0
    
    def reset_match(self):
        """Reset the match score and goals."""
        self.home_score = 0
        self.away_score = 0
        self.goals_scored.clear()
        self.goal_just_scored = False
        self.celebration_timer = 0.0
        self.last_goal = None
    
    def get_goal_zones_for_rendering(self) -> Tuple[Tuple[float, float, float, float], 
                                                   Tuple[float, float, float, float]]:
        """Get goal zone boundaries for rendering/debugging.
        
        Returns:
            Tuple of (home_goal_zone, away_goal_zone)
        """
        return self.home_goal_zone, self.away_goal_zone