"""Reinforcement Learning AI agent that actually learns from experience."""

import numpy as np
import random
import json
import os
from typing import Dict, Any, Tuple, List
from collections import defaultdict, deque
from ai.agents.base_agent import BaseAgent, AgentState, GameState


class QLearningAgent(BaseAgent):
    """Q-Learning agent that learns from soccer experience."""
    
    def __init__(self, agent_id: str, team: str, role: str, 
                 learning_rate: float = 0.1, discount_factor: float = 0.95, 
                 epsilon: float = 0.3, epsilon_decay: float = 0.995):
        """Initialize the Q-Learning agent.
        
        Args:
            agent_id: Unique identifier for the agent
            team: Team name ('home' or 'away')
            role: Player role
            learning_rate: How fast to learn (alpha)
            discount_factor: Future reward importance (gamma)  
            epsilon: Exploration probability
            epsilon_decay: How fast epsilon decreases
        """
        super().__init__(agent_id, team, role)
        
        # Q-Learning parameters
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = 0.05
        
        # Q-table: state -> action -> value
        self.q_table = defaultdict(lambda: defaultdict(float))
        
        # Experience replay for better learning
        self.experience_memory = deque(maxlen=1000)
        self.last_state = None
        self.last_action = None
        self.last_reward = 0.0
        
        # Action space
        self.actions = [
            'chase_ball',
            'move_to_position',
            'shoot_goal',
            'pass_forward',
            'pass_side',
            'defend_position',
            'clear_ball'
        ]
        
        # Learning statistics
        self.total_rewards = 0.0
        self.games_played = 0
        self.goals_contributed = 0
        self.successful_passes = 0
        self.total_actions = 0
        
    def get_state_representation(self, game_state: GameState) -> str:
        """Convert complex game state to learnable state string.
        
        Args:
            game_state: Current game state
            
        Returns:
            String representation of state for Q-table
        """
        # Simplify state to key features
        ball_x, ball_y = game_state.ball_position
        my_x, my_y = self.state.position
        
        # Discretize positions (reduce state space)
        ball_zone_x = int((ball_x + 52.5) // 21)  # 0-4 zones across field
        ball_zone_y = int((ball_y + 34) // 13.6)  # 0-4 zones down field
        my_zone_x = int((my_x + 52.5) // 21)
        my_zone_y = int((my_y + 34) // 13.6)
        
        # Distance to ball (discretized)
        ball_distance = self.calculate_distance_to_ball(game_state)
        distance_category = min(4, int(ball_distance // 5))  # 0-4 categories
        
        # Ball possession
        possession = 'our_ball' if game_state.ball_position[0] * (1 if self.team == 'home' else -1) > 0 else 'their_ball'
        
        # Energy level
        energy_level = 'high' if self.state.energy > 70 else 'medium' if self.state.energy > 30 else 'low'
        
        return f"{self.role}_{ball_zone_x}_{ball_zone_y}_{my_zone_x}_{my_zone_y}_{distance_category}_{possession}_{energy_level}"
    
    def decide_action(self, game_state: GameState) -> Dict[str, Any]:
        """Decide action using Q-learning with exploration.
        
        Args:
            game_state: Current game state
            
        Returns:
            Action dictionary
        """
        current_state = self.get_state_representation(game_state)
        
        # Store previous experience for learning
        if self.last_state is not None and self.last_action is not None:
            self.learn_from_experience(self.last_state, self.last_action, 
                                     self.last_reward, current_state)
        
        # Choose action using epsilon-greedy
        if random.random() < self.epsilon:
            # Explore: choose random action
            action_name = random.choice(self.actions)
        else:
            # Exploit: choose best known action
            action_values = self.q_table[current_state]
            if not action_values:
                # No experience with this state, choose random
                action_name = random.choice(self.actions)
            else:
                action_name = max(action_values.items(), key=lambda x: x[1])[0]
        
        # Convert action name to actual action
        action_dict = self.convert_action_to_dict(action_name, game_state)
        
        # Store for next learning step
        self.last_state = current_state
        self.last_action = action_name
        self.last_reward = self.calculate_immediate_reward(game_state)
        self.total_actions += 1
        
        # Decay exploration over time
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
        
        return action_dict
    
    def convert_action_to_dict(self, action_name: str, game_state: GameState) -> Dict[str, Any]:
        """Convert action name to actual action dictionary.
        
        Args:
            action_name: Name of the action to take
            game_state: Current game state
            
        Returns:
            Action dictionary
        """
        ball_x, ball_y = game_state.ball_position
        my_x, my_y = self.state.position
        
        # Goal positions
        goal_x = 52.0 if self.team == "home" else -52.0
        
        if action_name == 'chase_ball':
            return {
                'action': 'move',
                'target_x': ball_x,
                'target_y': ball_y,
                'speed': 1.0
            }
        
        elif action_name == 'move_to_position':
            # Move to formation position
            form_x = getattr(self, 'formation_x', 0.0)
            form_y = getattr(self, 'formation_y', 0.0)
            return {
                'action': 'move',
                'target_x': form_x,
                'target_y': form_y,
                'speed': 0.7
            }
        
        elif action_name == 'shoot_goal':
            return {
                'action': 'kick',
                'target_x': goal_x,
                'target_y': random.uniform(-2.0, 2.0),
                'power': 1.0
            }
        
        elif action_name == 'pass_forward':
            return {
                'action': 'kick',
                'target_x': ball_x + (goal_x - ball_x) * 0.3,
                'target_y': ball_y,
                'power': 0.7
            }
        
        elif action_name == 'pass_side':
            return {
                'action': 'kick',
                'target_x': ball_x + random.uniform(-10, 10),
                'target_y': ball_y + random.uniform(-15, 15),
                'power': 0.6
            }
        
        elif action_name == 'defend_position':
            # Move between ball and own goal
            own_goal_x = -52.0 if self.team == "home" else 52.0
            defend_x = (ball_x + own_goal_x) * 0.5
            defend_y = ball_y * 0.3
            return {
                'action': 'move',
                'target_x': defend_x,
                'target_y': defend_y,
                'speed': 0.8
            }
        
        elif action_name == 'clear_ball':
            return {
                'action': 'kick',
                'target_x': goal_x * 0.5,
                'target_y': ball_y + (-20 if ball_y > 0 else 20),
                'power': 0.9
            }
        
        # Fallback
        return {
            'action': 'move',
            'target_x': ball_x,
            'target_y': ball_y,
            'speed': 0.5
        }
    
    def calculate_immediate_reward(self, game_state: GameState) -> float:
        """Calculate reward for current state/action.
        
        Args:
            game_state: Current game state
            
        Returns:
            Reward value
        """
        reward = 0.0
        
        # Distance to ball reward (closer is better for most roles)
        ball_distance = self.calculate_distance_to_ball(game_state)
        if self.role != "goalkeeper":
            reward += max(0, 10 - ball_distance) * 0.01  # Small positive for being near ball
        
        # Position reward (stay in reasonable area)
        my_x, my_y = self.state.position
        if abs(my_x) < 55 and abs(my_y) < 35:  # Stay on field
            reward += 0.05
        else:
            reward -= 0.1  # Penalty for going off field
        
        # Energy management
        if self.state.energy < 20:
            reward -= 0.02  # Small penalty for being tired
        
        # Role-specific rewards
        if self.role == "goalkeeper":
            # Goalkeeper should stay near goal
            goal_x = -52.0 if self.team == "home" else 52.0
            distance_to_goal = abs(my_x - goal_x)
            reward += max(0, 20 - distance_to_goal) * 0.001
        
        return reward
    
    def learn_from_experience(self, state: str, action: str, reward: float, next_state: str):
        """Update Q-table based on experience.
        
        Args:
            state: Previous state
            action: Action taken
            reward: Reward received
            next_state: New state after action
        """
        # Q-learning update formula:
        # Q(s,a) = Q(s,a) + α[r + γ*max(Q(s',a')) - Q(s,a)]
        
        current_q = self.q_table[state][action]
        
        # Find maximum Q-value for next state
        next_state_values = self.q_table[next_state]
        max_next_q = max(next_state_values.values()) if next_state_values else 0.0
        
        # Update Q-value
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        
        self.q_table[state][action] = new_q
        
        # Store experience for potential replay
        self.experience_memory.append((state, action, reward, next_state))
        
        # Update statistics
        self.total_rewards += reward
    
    def update_performance_metrics(self, action_result: Dict[str, Any]):
        """Override to add learning-specific metrics.
        
        Args:
            action_result: Result of the last action
        """
        super().update_performance_metrics(action_result)
        
        # Learning-specific rewards
        if action_result.get('goal_scored'):
            self.goals_contributed += 1
            self.last_reward += 100.0  # Big reward for goals!
        
        if action_result.get('assist'):
            self.goals_contributed += 1
            self.last_reward += 50.0   # Good reward for assists
        
        if action_result.get('pass_completed'):
            self.successful_passes += 1
            self.last_reward += 5.0    # Small reward for successful passes
        
        if action_result.get('ball_lost'):
            self.last_reward -= 10.0   # Penalty for losing ball
    
    def get_learning_stats(self) -> Dict[str, float]:
        """Get learning-specific statistics.
        
        Returns:
            Dictionary of learning metrics
        """
        return {
            'total_rewards': self.total_rewards,
            'average_reward': self.total_rewards / max(1, self.total_actions),
            'games_played': self.games_played,
            'goals_contributed': self.goals_contributed,
            'successful_passes': self.successful_passes,
            'epsilon': self.epsilon,
            'q_table_size': len(self.q_table),
            'experience_memory_size': len(self.experience_memory)
        }
    
    def save_q_table(self, filename: str = None):
        """Save Q-table to file for persistence.
        
        Args:
            filename: File to save to (default: agent_id.json)
        """
        if filename is None:
            filename = f"q_table_{self.agent_id}_{self.team}_{self.role}.json"
        
        # Convert defaultdict to regular dict for JSON serialization
        q_dict = {state: dict(actions) for state, actions in self.q_table.items()}
        
        try:
            os.makedirs("ai_models", exist_ok=True)
            filepath = os.path.join("ai_models", filename)
            
            with open(filepath, 'w') as f:
                json.dump({
                    'q_table': q_dict,
                    'stats': self.get_learning_stats(),
                    'parameters': {
                        'learning_rate': self.learning_rate,
                        'discount_factor': self.discount_factor,
                        'epsilon': self.epsilon
                    }
                }, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save Q-table: {e}")
    
    def load_q_table(self, filename: str = None):
        """Load Q-table from file.
        
        Args:
            filename: File to load from (default: agent_id.json)
        """
        if filename is None:
            filename = f"q_table_{self.agent_id}_{self.team}_{self.role}.json"
        
        try:
            filepath = os.path.join("ai_models", filename)
            
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Load Q-table
                loaded_q_table = data.get('q_table', {})
                for state, actions in loaded_q_table.items():
                    for action, value in actions.items():
                        self.q_table[state][action] = value
                
                # Load parameters if available
                params = data.get('parameters', {})
                self.epsilon = params.get('epsilon', self.epsilon)
                
                print(f"Loaded Q-table with {len(self.q_table)} states for {self.agent_id}")
            
        except Exception as e:
            print(f"Warning: Could not load Q-table: {e}")
    
    def update_state(self, new_state: AgentState):
        """Update agent state and potentially save learning progress.
        
        Args:
            new_state: New agent state
        """
        super().update_state(new_state)
        
        # Periodically save Q-table (every 100 actions)
        if self.total_actions > 0 and self.total_actions % 100 == 0:
            self.save_q_table()
