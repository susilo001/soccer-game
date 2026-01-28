"""Simple AI agent implementation for soccer players."""

import math
import random
from typing import Dict, Any, Tuple
from ai.agents.base_agent import BaseAgent, AgentState, GameState


class SimpleAgent(BaseAgent):
    """Simple rule-based AI agent for soccer players."""
    
    def __init__(self, agent_id: str, team: str, role: str):
        """Initialize the simple AI agent.
        
        Args:
            agent_id: Unique identifier for the agent
            team: Team name ('home' or 'away')
            role: Player role (goalkeeper, defender, midfielder, forward)
        """
        super().__init__(agent_id, team, role)
        
        # AI behavior parameters
        self.aggression = random.uniform(0.3, 0.9)  # How aggressively to pursue ball
        self.positioning_priority = random.uniform(0.2, 0.8)  # How much to prioritize position vs ball
        self.pass_probability = random.uniform(0.1, 0.4)  # Probability of passing vs shooting
        self.reaction_time = random.uniform(0.1, 0.5)  # Decision reaction time
        
        # Role-specific adjustments
        self._adjust_for_role()
        
        # Decision state
        self.last_decision_time = 0.0
        self.current_target = None
        self.action_timer = 0.0
        self.formation_position = (0.0, 0.0)  # Assigned formation position
        
    def _adjust_for_role(self):
        """Adjust AI parameters based on player role."""
        if self.role == "goalkeeper":
            self.aggression = 0.2  # Stay in goal
            self.positioning_priority = 0.9  # Prioritize positioning
            self.pass_probability = 0.8  # Pass often, don't shoot
        elif self.role == "defender":
            self.aggression = 0.4
            self.positioning_priority = 0.7
            self.pass_probability = 0.6
        elif self.role == "midfielder":
            self.aggression = 0.6
            self.positioning_priority = 0.5
            self.pass_probability = 0.4
        elif self.role == "forward":
            self.aggression = 0.8
            self.positioning_priority = 0.3
            self.pass_probability = 0.2  # Shoot more often
    
    def set_formation_position(self, x: float, y: float):
        """Set the player's assigned formation position.
        
        Args:
            x: Formation x position
            y: Formation y position
        """
        self.formation_position = (x, y)
    
    def decide_action(self, game_state: GameState) -> Dict[str, Any]:
        """Decide what action to take based on the current game state.
        
        Args:
            game_state: Current state of the game
            
        Returns:
            Dictionary containing action type and parameters
        """
        # Simple decision tree based on distance to ball and role
        ball_distance = self.calculate_distance_to_ball(game_state)
        
        # Check if we're close enough to the ball to interact with it
        if ball_distance <= 1.0:  # Within interaction range
            return self._decide_ball_action(game_state)
        else:
            return self._decide_movement_action(game_state, ball_distance)
    
    def _decide_ball_action(self, game_state: GameState) -> Dict[str, Any]:
        """Decide what to do when close to the ball."""
        
        # Simple shooting/passing logic
        if self.role == "goalkeeper":
            # Goalkeeper: clear the ball away from goal
            if self.team == "home":
                target_x = 30.0  # Kick towards opponent half
            else:
                target_x = -30.0
            target_y = random.uniform(-10.0, 10.0)
            
            return {
                'action': 'kick',
                'target_x': target_x,
                'target_y': target_y,
                'power': 0.8
            }
        
        # For field players, decide between shooting and passing
        teammates = self.get_teammates(game_state)
        
        # Simple shooting logic: if close to goal, shoot
        goal_x = 52.5 if self.team == "home" else -52.5  # Approximate goal positions
        distance_to_goal = abs(self.state.position[0] - goal_x)
        
        if distance_to_goal < 20.0 and random.random() > self.pass_probability:
            # Shoot at goal
            goal_y = random.uniform(-3.0, 3.0)  # Aim within goal
            return {
                'action': 'kick',
                'target_x': goal_x,
                'target_y': goal_y,
                'power': 1.0
            }
        
        # Otherwise, pass to a teammate or dribble
        if teammates and random.random() < 0.7:  # 70% chance to pass
            # Find closest teammate
            best_teammate = min(teammates, 
                              key=lambda t: math.sqrt((t.position[0] - self.state.position[0])**2 + 
                                                    (t.position[1] - self.state.position[1])**2))
            
            return {
                'action': 'kick',
                'target_x': best_teammate.position[0],
                'target_y': best_teammate.position[1],
                'power': 0.6
            }
        else:
            # Dribble towards goal
            return {
                'action': 'move',
                'target_x': goal_x * 0.8,  # Move towards goal
                'target_y': self.state.position[1] + random.uniform(-5.0, 5.0),
                'speed': 0.8
            }
    
    def _decide_movement_action(self, game_state: GameState, ball_distance: float) -> Dict[str, Any]:
        """Decide movement when not close to the ball."""
        
        # Balance between chasing ball and maintaining formation
        ball_priority = self.aggression * (1.0 - self.positioning_priority)
        formation_priority = self.positioning_priority
        
        # Goalkeeper special case: mostly stay near goal
        if self.role == "goalkeeper":
            goal_x = -52.5 if self.team == "home" else 52.5
            goal_y = 0.0
            
            # Move towards ball only if it's very close to goal
            if ball_distance < 15.0:
                target_x = game_state.ball_position[0] * 0.3 + goal_x * 0.7
                target_y = game_state.ball_position[1] * 0.5
            else:
                target_x = goal_x
                target_y = goal_y
        else:
            # Field players: balance ball chasing and formation
            ball_x, ball_y = game_state.ball_position
            form_x, form_y = self.formation_position
            
            # Weighted target between ball and formation position
            target_x = ball_x * ball_priority + form_x * formation_priority
            target_y = ball_y * ball_priority + form_y * formation_priority
        
        return {
            'action': 'move',
            'target_x': target_x,
            'target_y': target_y,
            'speed': min(0.9, ball_priority + 0.3)  # Faster when chasing ball
        }
    
    def update_state(self, new_state: AgentState):
        """Update the agent's internal state.
        
        Args:
            new_state: New state information
        """
        self.state = new_state