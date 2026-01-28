"""Team manager for coordinating AI players and formations."""

import math
import time
from typing import List, Dict, Tuple, Optional
from src.entities.player import Player, PlayerRole
from ai.agents.base_agent import AgentState, GameState

# -------------------
# Constants
# -------------------
BALL_INTERACT_DIST = 1.2
POSSESSION_DIST = 2.0
RETRIEVAL_COOLDOWN = 2.0

ROLE_MAP = {
    "goalkeeper": PlayerRole.GOALKEEPER,
    "defender": PlayerRole.DEFENDER,
    "midfielder": PlayerRole.MIDFIELDER,
    "forward": PlayerRole.FORWARD,
}

class Formation:
    """Represents a team formation with player positions."""

    def __init__(self, name: str, positions: Dict[str, List[Tuple[float, float]]]):
        """Initialize formation.
        
        Args:
            name: Formation name (e.g., "4-4-2")
            positions: Dictionary mapping roles to list of (x, y) positions
        """
        self.name = name
        self.positions = positions

    def get_positions_for_team(self, team: str) -> Dict[str, List[Tuple[float, float]]]:
        """Get positions adjusted for team side.
        
        Args:
            team: "home" or "away"
            
        Returns:
            Dictionary of role positions adjusted for team side
        """
        if team == "home":
            return self.positions

        return {
            role: [(-x, -y) for x, y in pos_list]
            for role, pos_list in self.positions.items()
        }


class FormationManager:
    """Manages different football formations."""

    def __init__(self):
        """Initialize with standard formations."""
        self.formations = {}
        self._create_standard_formations()

    def _create_standard_formations(self):
        """Create standard soccer formations."""

        # 4-4-2 Formation (most common)
        self.formations["4-4-2"] = Formation("4-4-2", {
            "goalkeeper": [(-45.0, 0.0)],
            "defender": [(-35.0, -15.0), (-35.0, -5.0), (-35.0, 5.0), (-35.0, 15.0)],
            "midfielder": [(-15.0, -18.0), (-15.0, -6.0), (-15.0, 6.0), (-15.0, 18.0)],
            "forward": [(-5.0, -8.0), (-5.0, 8.0)]
        })

        # 4-3-3 Formation (attacking)
        self.formations["4-3-3"] = Formation("4-3-3", {
            "goalkeeper": [(-45.0, 0.0)],
            "defender": [(-35.0, -15.0), (-35.0, -5.0), (-35.0, 5.0), (-35.0, 15.0)],
            "midfielder": [(-20.0, -12.0), (-20.0, 0.0), (-20.0, 12.0)],
            "forward": [(-5.0, -15.0), (-5.0, 0.0), (-5.0, 15.0)]
        })

        # 3-5-2 Formation (midfield heavy)
        self.formations["3-5-2"] = Formation("3-5-2", {
            "goalkeeper": [(-45.0, 0.0)],
            "defender": [(-35.0, -10.0), (-35.0, 0.0), (-35.0, 10.0)],
            "midfielder": [(-25.0, -20.0), (-25.0, -10.0), (-25.0, 0.0), (-25.0, 10.0), (-25.0, 20.0)],
            "forward": [(-8.0, -8.0), (-8.0, 8.0)]
        })

    def get_formation(self, name: str) -> Formation:
        """Get formation by name."""
        return self.formations.get(name, self.formations["4-4-2"])

    def list_formations(self) -> List[str]:
        """Get list of available formation names."""
        return list(self.formations.keys())


class TeamManager:
    """Manages a team of AI players with formation and coordination."""

    def __init__(self, team_name: str, formation_name: str = "4-4-2"):
        """Initialize team manager.
        
        Args:
            team_name: "home" or "away"
            formation_name: Formation to use
        """
        self.team_name = team_name
        self.formation_manager = FormationManager()
        
        # Initialize players list first
        self.players: List[Player] = []
        
        # Set formation and create team
        self.change_formation(formation_name)
        self._create_team()

        self.in_possession = False
        self.ball_carrier: Optional[Player] = None
        self.team_strategy = "balanced"

        self.last_retrieval_time = 0.0
        self.retrieval_cooldown = RETRIEVAL_COOLDOWN


    def _create_team(self):
        """Create team players based on formation."""
        positions = self.formation.get_positions_for_team(self.team_name)
        player_id = 0

        for role_name, pos_list in positions.items():
            role = ROLE_MAP[role_name]
            for x, y in pos_list:
                player_id += 1
                player = Player(
                    player_id=f"{self.team_name[0].upper()}{player_id}",
                    team=self.team_name,
                    role=role,
                    x=x, y=y,
                )
                player.is_controlled = False
                self.players.append(player)

    def update_formation_positions(self, ball_position: Tuple[float, float], ball_needs_retrieval: bool = False):
        """Update formation positions based on ball position and game phase.
        
        Args:
            ball_position: Current ball position (x, y)
            ball_needs_retrieval: Whether ball needs to be retrieved
        """
        if not ball_position or not self.players:
            return
            
        try:
            ball_x, ball_y = ball_position
            base_positions = self.formation.get_positions_for_team(self.team_name)

            # If ball needs retrieval, find closest player to send
            if ball_needs_retrieval:
                closest_player = None
                closest_distance = float('inf')

                for player in self.players:
                    if player.role != PlayerRole.GOALKEEPER:  # Don't send goalkeeper
                        distance = player.get_distance_to_ball_pos(ball_x, ball_y)
                        if distance < closest_distance:
                            closest_distance = distance
                            closest_player = player

                # Send closest player to retrieve ball
                if closest_player:
                    closest_player.set_target(ball_x, ball_y)
                    # Reduced debug output - only print occasionally
                    if hasattr(self, '_last_retrieval_debug_time'):
                        import time
                        if time.time() - self._last_retrieval_debug_time > 5.0:
                            print(f"[{self.team_name}] Ball retrieval: {closest_player.player_id} going to get ball at ({ball_x:.1f}, {ball_y:.1f})")
                            self._last_retrieval_debug_time = time.time()
                    else:
                        import time
                        self._last_retrieval_debug_time = time.time()
                        print(f"[{self.team_name}] Ball retrieval: {closest_player.player_id} going to get ball at ({ball_x:.1f}, {ball_y:.1f})")

            # Adjust formation based on ball position
            for player in self.players:
                role = player.role.value
                if role in base_positions:
                    # Find which position this player should take
                    role_positions = base_positions[role]
                    same_role_players = [p for p in self.players if p.role.value == role]

                    try:
                        player_index = same_role_players.index(player)
                        if player_index < len(role_positions):
                            base_x, base_y = role_positions[player_index]

                            # Skip formation positioning if this player is retrieving ball
                            if ball_needs_retrieval:
                                closest_player = min(self.players,
                                                     key=lambda p: p.get_distance_to_ball_pos(ball_x, ball_y)
                                                     if p.role != PlayerRole.GOALKEEPER else float('inf'))
                                if player == closest_player:
                                    continue  # Already set target above

                            # Better formation discipline - only closest players chase ball
                            if role != "goalkeeper":
                                # Find distance to ball
                                ball_distance = math.sqrt((ball_x - base_x) ** 2 + (ball_y - base_y) ** 2)

                                # Only chase ball if you're one of the closest players
                                should_chase_ball = not ball_needs_retrieval and ball_distance < 15.0 and (
                                        self.in_possession or
                                        (not self.in_possession and ball_distance < 8.0)
                                )

                                if should_chase_ball:
                                    # Move toward ball with some formation bias
                                    formation_weight = 0.2
                                    target_x = base_x * formation_weight + ball_x * (1 - formation_weight)
                                    target_y = base_y * formation_weight + ball_y * (1 - formation_weight)
                                else:
                                    # Stay in formation position with slight ball awareness
                                    ball_awareness = 0.1
                                    target_x = base_x * (1 - ball_awareness) + ball_x * ball_awareness
                                    target_y = base_y * (1 - ball_awareness) + ball_y * ball_awareness

                                # Keep players within reasonable bounds
                                field_bounds = (-50.0, 50.0, -30.0, 30.0)
                                target_x = max(field_bounds[0], min(field_bounds[1], target_x))
                                target_y = max(field_bounds[2], min(field_bounds[3], target_y))

                                player.set_target(target_x, target_y)
                            else:
                                # Goalkeeper: more reactive to ball position
                                goal_x = base_x
                                goal_y = ball_y * 0.5  # Follow ball more closely
                                goal_y = max(-8.0, min(8.0, goal_y))  # Wider goal area movement
                                player.set_target(goal_x, goal_y)
                    except ValueError:
                        # Fallback: move toward ball
                        player.set_target(ball_x, ball_y)
                    
        except Exception as e:
            print(f"Warning: Error updating formation positions for {self.team_name}: {e}")

    def update_team_ai(self, dt: float, ball, opponent_players: List[Player],
                       field_bounds: Tuple[float, float, float, float], kickoff_info: dict = None):
        """Update AI decision making for all team players.
        
        Args:
            dt: Delta time
            ball: Ball object
            opponent_players: List of opponent players
            field_bounds: Field boundaries
            kickoff_info: Information about active kick-off state
        """
        if not ball or not self.players:
            return
            
        try:
            ball_pos = ball.get_position()

            # Handle kick-off state
            if kickoff_info and kickoff_info.get('active', False):
                self._handle_kickoff_behavior(kickoff_info, ball_pos)
                # During kick-off, use minimal AI to avoid interference
                for player in self.players:
                    player.move_towards_target(dt)
                    player.update(dt, field_bounds)
                return

            # Update time tracking
            import time
            current_time = time.time()

            # Update ball possession status
            self._update_possession_status(ball, opponent_players)

            # Check if ball needs retrieval (stuck situation) with cooldown
            ball_needs_retrieval = self._check_ball_retrieval_needed(ball, opponent_players, current_time)

            # Update formation positions
            self.update_formation_positions(ball_pos, ball_needs_retrieval)

            # Update individual player AI
            for player in self.players:
                if player:  # Validate player exists
                    self._update_player_ai(player, dt, ball, field_bounds, ball_needs_retrieval)
                    player.update(dt, field_bounds)
                    
        except Exception as e:
            print(f"Warning: Error in team AI update for {self.team_name}: {e}")

    def _update_possession_status(self, ball, opponent_players: List[Player]):
        """Update which team has ball possession."""
        ball_pos = ball.get_position()

        # Find closest player to ball
        closest_distance = float('inf')
        closest_player = None

        # Check our players
        for player in self.players:
            distance = player.get_distance_to_ball(ball)
            if distance < closest_distance:
                closest_distance = distance
                closest_player = player

        # Check opponent players
        for player in opponent_players:
            distance = player.get_distance_to_ball(ball)
            if distance < closest_distance:
                closest_distance = distance
                closest_player = player

        # Update possession
        if closest_player and closest_distance < 2.0:
            if closest_player in self.players:
                self.in_possession = True
                self.ball_carrier = closest_player
            else:
                self.in_possession = False
                self.ball_carrier = None
        else:
            self.in_possession = False
            self.ball_carrier = None

    def _check_ball_retrieval_needed(self, ball, opponent_players: List[Player], current_time: float) -> bool:
        """Check if ball is stuck and needs retrieval.
        
        Args:
            ball: Ball object
            opponent_players: List of opponent players
            current_time: Current timestamp
            
        Returns:
            True if ball needs to be retrieved by closest player
        """
        # Check cooldown first - longer cooldown to prevent spam
        if current_time - self.last_retrieval_time < (self.retrieval_cooldown * 2):
            return False

        # If ball is moving, no retrieval needed
        ball_speed = ball.get_speed()
        if ball_speed > 1.0:  # Any significant movement
            return False

        # Find closest player from both teams
        ball_pos = ball.get_position()
        closest_distance = float('inf')
        closest_is_ours = False

        # Check our players first
        for player in self.players:
            distance = player.get_distance_to_ball(ball)
            if distance < closest_distance:
                closest_distance = distance
                closest_is_ours = True

        # Check opponent players
        for player in opponent_players:
            distance = player.get_distance_to_ball(ball)
            if distance < closest_distance:
                closest_distance = distance
                closest_is_ours = False

        # Only retrieve if we're the closest team and ball is truly stuck
        if not closest_is_ours:
            return False

        # Much more conservative ball retrieval conditions:
        ball_x, ball_y = ball_pos
        near_edge = abs(ball_x) > 45 or abs(ball_y) > 30  # Near field edges
        
        needs_retrieval = (
                (closest_distance > 12.0 and ball_speed < 0.1) or  # Very far and completely stopped
                (near_edge and closest_distance > 8.0 and ball_speed < 0.5)  # Stuck near edge
        )

        if needs_retrieval:
            # Only print debug info occasionally to avoid spam
            if not hasattr(self, '_last_retrieval_need_debug') or (current_time - self._last_retrieval_need_debug) > 10.0:
                print(
                    f"[{self.team_name}] Ball retrieval needed: speed={ball_speed:.1f}, closest_dist={closest_distance:.1f}, pos=({ball_x:.1f},{ball_y:.1f})")
                self._last_retrieval_need_debug = current_time
            self.last_retrieval_time = current_time  # Set cooldown

        return needs_retrieval

    def _handle_kickoff_behavior(self, kickoff_info: dict, ball_pos: Tuple[float, float]):
        """Handle team behavior during kick-off.
        
        Args:
            kickoff_info: Dictionary with kick-off state information
            ball_pos: Current ball position
        """
        kickoff_team = kickoff_info.get('team')
        kickoff_state = kickoff_info.get('state', 'none')

        if kickoff_team == self.team_name:
            # This is the kick-off team - players should stay ready but not interfere
            # The designated kick-off players are already positioned by the engine
            if kickoff_state in ['preparing', 'ready']:
                # During preparation, non-kickoff players should maintain formation
                for player in self.players:
                    # Only move to formation if not designated kickoff player
                    # (kickoff players are handled by the engine)
                    distance_to_ball = player.get_distance_to_ball_pos(ball_pos[0], ball_pos[1])
                    if distance_to_ball > 5.0:  # Not close to center circle
                        self._move_to_formation_position_simple(player)
        else:
            # This is the opposing team - enforce they stay in their own half
            center_line_buffer = 5.0
            team_side = 1.0 if self.team_name == "away" else -1.0

            for player in self.players:
                # Check if player is violating kick-off rule (crossed center line)
                if (team_side > 0 and player.x < center_line_buffer) or (
                        team_side < 0 and player.x > -center_line_buffer):
                    # Move player back to their own half
                    safe_x = team_side * center_line_buffer
                    safe_y = max(-25.0, min(25.0, player.y))  # Keep reasonable y position
                    player.set_target(safe_x, safe_y)

    def _update_player_ai(self, player: Player, dt: float, ball, field_bounds: Tuple,
                          ball_needs_retrieval: bool = False):
        """Update AI for individual player."""
        if not player or not ball:
            return
            
        try:
            # Cache ball position to avoid repeated calls
            ball_x, ball_y = ball.get_position()
            ball_distance = player.get_distance_to_ball_pos(ball_x, ball_y)

            # Smarter AI: only closest players actively chase ball
            if ball_distance < 1.2:  # Very close - kick the ball!
                self._handle_ball_interaction(player, ball)
            elif ball_needs_retrieval or (
                    ball_distance < 5.0 and player.role in [PlayerRole.FORWARD, PlayerRole.MIDFIELDER]):
                # If ball needs retrieval OR normal chase conditions
                player.set_target(ball_x, ball_y)
                player.move_towards_target(dt)
            else:
                # Use formation position (set by formation system)
                player.move_towards_target(dt)
                
        except Exception as e:
            print(f"Warning: Error in player AI for {player.player_id}: {e}")

    def _handle_ball_interaction(self, player: Player, ball):
        """Handle player interaction when close to ball."""
        if not player or not ball:
            return
            
        try:
            ball_x, ball_y = ball.get_position()

            # Determine opponent goal direction (using actual field bounds)
            if self.team_name == "home":
                opponent_goal_x = 52.0  # Away goal (right side)
                own_goal_x = -52.0  # Home goal (left side)
            else:
                opponent_goal_x = -52.0  # Home goal (left side)
                own_goal_x = 52.0  # Away goal (right side)

            # Debug output
            # print(f"{player.player_id} ({self.team_name}) kicking ball from ({ball_x:.1f}, {ball_y:.1f}) toward goal at {opponent_goal_x}")

            if player.role == PlayerRole.GOALKEEPER:
                # Goalkeeper: clear the ball toward opponent half
                clear_x = opponent_goal_x * 0.5
                clear_y = ball_y + (-10.0 if ball_y > 0 else 10.0)
                success = player.kick_ball(ball, target_x=clear_x, target_y=clear_y, power=0.9)

            elif player.role == PlayerRole.FORWARD:
                # Forward: shoot directly at goal center with some variation
                goal_y = (hash(player.player_id) % 5 - 2) * 1.5  # -3 to +3 range
                success = player.kick_ball(ball, target_x=opponent_goal_x, target_y=goal_y, power=1.0)

            else:
                # Midfielders and defenders: either pass forward or shoot if close
                distance_to_goal = abs(ball_x - opponent_goal_x)

                if distance_to_goal < 25.0:  # Close enough to shoot
                    goal_y = ball_y * 0.5  # Aim toward goal with slight centering
                    success = player.kick_ball(ball, target_x=opponent_goal_x, target_y=goal_y, power=1.0)
                else:  # Pass forward
                    advance_x = ball_x + (opponent_goal_x - ball_x) * 0.5
                    advance_y = ball_y * 0.7
                    success = player.kick_ball(ball, target_x=advance_x, target_y=advance_y, power=0.8)
                
        except Exception as e:
            # Log error but don't crash - just skip this interaction
            print(f"Warning: Error in ball interaction for {player.player_id}: {e}")

    def get_players(self) -> List[Player]:
        """Get list of all team players."""
        return self.players

    def change_formation(self, formation_name: str):
        """Change team formation.
        
        Args:
            formation_name: New formation name
        """
        self.formation_name = formation_name
        self.formation = self.formation_manager.get_formation(formation_name)
        # Update player positions
        ball_pos = (0.0, 0.0)  # Use center as default
        self.update_formation_positions(ball_pos)

    def find_nearest_player(self, ball) -> Optional[Player]:
        """Find nearest player to the ball."""
        nearest = None
        min_dist = float("inf")
        bx, by = ball.get_position()

        for p in self.players:
            dist = p.get_distance_to_ball_pos(bx, by)
            if dist < min_dist:
                min_dist = dist
                nearest = p

        return nearest



    def _move_to_formation_position(self, player: Player, dt: float, field_bounds):
        """Send player back to default formation position."""
        default_pos = self.formation.get_positions_for_team(self.team_name)[
            player.role.value
        ]
        if default_pos:
            # For simplicity, just send to first assigned spot
            tx, ty = default_pos[0]
            player.set_target(tx, ty)
            player.move_towards_target(dt)
            
    def _move_to_formation_position_simple(self, player: Player):
        """Send player to formation position without movement update."""
        default_pos = self.formation.get_positions_for_team(self.team_name)[
            player.role.value
        ]
        if default_pos:
            # For simplicity, just send to first assigned spot
            tx, ty = default_pos[0]
            player.set_target(tx, ty)
