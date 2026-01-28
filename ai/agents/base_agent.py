"""Base AI Agent class for soccer players."""

import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class AgentState:
    """Current state of an AI agent."""
    position: Tuple[float, float]
    velocity: Tuple[float, float]
    energy: float
    has_ball: bool
    team: str
    role: str  # goalkeeper, defender, midfielder, forward


@dataclass
class GameState:
    """Current state of the game."""
    ball_position: Tuple[float, float]
    ball_velocity: Tuple[float, float]
    players: Dict[str, AgentState]
    score: Tuple[int, int]
    time_remaining: float
    game_phase: str  # kickoff, play, corner, freekick, etc.


class BaseAgent(ABC):
    """Base class for all AI agents in the soccer game."""
    
    def __init__(self, agent_id: str, team: str, role: str):
        """Initialize the AI agent.
        
        Args:
            agent_id: Unique identifier for the agent
            team: Team name ('home' or 'away')
            role: Player role (goalkeeper, defender, midfielder, forward)
        """
        self.agent_id = agent_id
        self.team = team
        self.role = role
        self.state = AgentState(
            position=(0.0, 0.0),
            velocity=(0.0, 0.0),
            energy=100.0,
            has_ball=False,
            team=team,
            role=role
        )
        
        # Learning and memory
        self.experience_buffer = []
        self.performance_metrics = {
            'goals': 0,
            'assists': 0,
            'passes_completed': 0,
            'passes_attempted': 0,
            'tackles_won': 0,
            'tackles_attempted': 0,
            'distance_covered': 0.0
        }
    
    @abstractmethod
    def decide_action(self, game_state: GameState) -> Dict[str, Any]:
        """Decide what action to take based on the current game state.
        
        Args:
            game_state: Current state of the game
            
        Returns:
            Dictionary containing action type and parameters
            Example: {'action': 'move', 'direction': (1.0, 0.0), 'speed': 0.8}
        """
        pass
    
    @abstractmethod
    def update_state(self, new_state: AgentState):
        """Update the agent's internal state.
        
        Args:
            new_state: New state information
        """
        pass
    
    def calculate_distance_to_ball(self, game_state: GameState) -> float:
        """Calculate distance from agent to ball.
        
        Args:
            game_state: Current game state
            
        Returns:
            Distance to ball in meters
        """
        dx = game_state.ball_position[0] - self.state.position[0]
        dy = game_state.ball_position[1] - self.state.position[1]
        return np.sqrt(dx**2 + dy**2)
    
    def calculate_distance_to_position(self, target_pos: Tuple[float, float]) -> float:
        """Calculate distance from agent to a target position.
        
        Args:
            target_pos: Target position (x, y)
            
        Returns:
            Distance to target in meters
        """
        dx = target_pos[0] - self.state.position[0]
        dy = target_pos[1] - self.state.position[1]
        return np.sqrt(dx**2 + dy**2)
    
    def get_teammates(self, game_state: GameState) -> List[AgentState]:
        """Get list of teammate states.
        
        Args:
            game_state: Current game state
            
        Returns:
            List of teammate agent states
        """
        return [
            player for player_id, player in game_state.players.items()
            if player.team == self.team and player_id != self.agent_id
        ]
    
    def get_opponents(self, game_state: GameState) -> List[AgentState]:
        """Get list of opponent states.
        
        Args:
            game_state: Current game state
            
        Returns:
            List of opponent agent states
        """
        return [
            player for player in game_state.players.values()
            if player.team != self.team
        ]
    
    def update_performance_metrics(self, action_result: Dict[str, Any]):
        """Update performance tracking metrics.
        
        Args:
            action_result: Result of the last action taken
        """
        if action_result.get('goal_scored'):
            self.performance_metrics['goals'] += 1
        if action_result.get('assist'):
            self.performance_metrics['assists'] += 1
        if action_result.get('pass_completed'):
            self.performance_metrics['passes_completed'] += 1
        if action_result.get('pass_attempted'):
            self.performance_metrics['passes_attempted'] += 1
        if action_result.get('tackle_won'):
            self.performance_metrics['tackles_won'] += 1
        if action_result.get('tackle_attempted'):
            self.performance_metrics['tackles_attempted'] += 1
        if action_result.get('distance_moved'):
            self.performance_metrics['distance_covered'] += action_result['distance_moved']
    
    def get_performance_summary(self) -> Dict[str, float]:
        """Get summary of agent's performance.
        
        Returns:
            Dictionary of performance metrics
        """
        summary = self.performance_metrics.copy()
        
        # Calculate derived metrics
        if summary['passes_attempted'] > 0:
            summary['pass_accuracy'] = summary['passes_completed'] / summary['passes_attempted']
        else:
            summary['pass_accuracy'] = 0.0
            
        if summary['tackles_attempted'] > 0:
            summary['tackle_success_rate'] = summary['tackles_won'] / summary['tackles_attempted']
        else:
            summary['tackle_success_rate'] = 0.0
            
        return summary