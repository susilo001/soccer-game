"""Player entity with movement, controls, and rendering."""
import random
import pygame
import math
from typing import Tuple, Optional
from enum import Enum


class PlayerRole(Enum):
    """Player roles on the field."""
    GOALKEEPER = "goalkeeper"
    DEFENDER = "defender"
    MIDFIELDER = "midfielder"
    FORWARD = "forward"


class Player:
    """Soccer player with movement and basic AI."""

    def __init__(self, player_id: str, team: str, role: PlayerRole, x: float = 0.0, y: float = 0.0):
        """Initialize the player.
        
        Args:
            player_id: Unique identifier for the player
            team: Team name ('home' or 'away')
            role: Player role
            x: Initial x position in world coordinates (meters)
            y: Initial y position in world coordinates (meters)
        """
        self.player_id = player_id
        self.team = team
        self.role = role

        # Position and movement
        self.x = x
        self.y = y
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.facing_angle = 0.0  # Radians, 0 = facing right

        # Physical properties
        self.radius = 0.4  # Player radius in meters
        self.max_speed = self._get_max_speed_for_role()
        self.acceleration = 8.0  # m/s²
        self.deceleration = 12.0  # m/s²

        # Player state
        self.has_ball = False
        self.energy = 100.0  # 0-100
        self.is_controlled = False  # True if controlled by human player

        # Visual properties
        self.colors = self._get_team_colors()
        self.jersey_color, self.shorts_color = self.colors

        # AI/Control state
        self.target_x = x
        self.target_y = y
        self.action = "idle"  # idle, moving, kicking, etc.

    def render(self, screen: pygame.Surface, field_renderer):
        """Render the player on screen.

        Args:
            screen: Pygame surface to render on
            field_renderer: Field renderer for coordinate conversion
        """
        # Convert world coordinates to screen coordinates
        screen_x, screen_y = field_renderer.world_to_screen(self.x, self.y)
        screen_radius = max(8, int(self.radius * field_renderer.scale))

        # Draw player shadow
        shadow_offset = 2
        pygame.draw.circle(
            screen,
            (50, 50, 50),  # Dark gray shadow
            (screen_x + shadow_offset, screen_y + shadow_offset),
            screen_radius
        )

        # Draw player body (jersey)
        pygame.draw.circle(screen, self.jersey_color, (screen_x, screen_y), screen_radius)
        pygame.draw.circle(screen, (0, 0, 0), (screen_x, screen_y), screen_radius, 2)

        # Draw shorts (smaller circle at bottom)
        shorts_radius = screen_radius // 2
        shorts_y = screen_y + screen_radius // 2
        pygame.draw.circle(screen, self.shorts_color, (screen_x, shorts_y), shorts_radius)

        # Draw facing direction indicator
        direction_length = screen_radius + 5
        end_x = screen_x + int(direction_length * math.cos(self.facing_angle))
        end_y = screen_y + int(direction_length * math.sin(self.facing_angle))
        pygame.draw.line(screen, (255, 255, 255), (screen_x, screen_y), (end_x, end_y), 2)

        # Draw player ID
        if screen_radius > 10:
            font = pygame.font.Font(None, max(16, screen_radius))
            text = font.render(self.player_id[-1], True, (255, 255, 255))  # Last character of ID
            text_rect = text.get_rect(center=(screen_x, screen_y))
            screen.blit(text, text_rect)

        # Draw energy bar if low
        if self.energy < 50:
            bar_width = screen_radius * 2
            bar_height = 4
            bar_x = screen_x - bar_width // 2
            bar_y = screen_y - screen_radius - 10

            # Background bar
            pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))

            # Energy bar
            energy_width = int(bar_width * (self.energy / 100.0))
            energy_color = (255, 0, 0) if self.energy < 25 else (255, 255, 0)
            pygame.draw.rect(screen, energy_color, (bar_x, bar_y, energy_width, bar_height))

        # Draw target position if moving (for debugging AI)
        if self.action == "moving" and not self.is_controlled:
            target_screen_x, target_screen_y = field_renderer.world_to_screen(self.target_x, self.target_y)
            pygame.draw.circle(screen, (255, 255, 0), (target_screen_x, target_screen_y), 3)
            pygame.draw.line(screen, (255, 255, 0), (screen_x, screen_y), (target_screen_x, target_screen_y), 1)

    def update(self, dt: float, field_bounds: Tuple[float, float, float, float]):
        """Update player movement and state.

        Args:
            dt: Delta time in seconds
            field_bounds: (min_x, max_x, min_y, max_y) in meters
        """
        # Update energy (simple recovery when not moving fast)
        speed = math.sqrt(self.velocity_x ** 2 + self.velocity_y ** 2)
        if speed < 2.0:
            self.energy = min(100.0, self.energy + 20.0 * dt)  # Recover energy
        else:
            self.energy = max(0.0, self.energy - speed * 2.0 * dt)  # Consume energy

        # Apply velocity to position
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt

        # Keep player within field bounds
        min_x, max_x, min_y, max_y = field_bounds
        self.x = max(min_x + self.radius, min(max_x - self.radius, self.x))
        self.y = max(min_y + self.radius, min(max_y - self.radius, self.y))

        # Update facing direction based on velocity
        if abs(self.velocity_x) > 0.1 or abs(self.velocity_y) > 0.1:
            self.facing_angle = math.atan2(self.velocity_y, self.velocity_x)

    def kick_ball(self, ball, target_x: float = None, target_y: float = None, power: float = 0.5):
        """Kick the ball towards a target or in facing direction.

        Args:
            ball: Ball object to kick
            target_x: Target x coordinate (optional)
            target_y: Target y coordinate (optional)
            power: Kick power (0.0 to 1.0)
        """
        # Check if ball is close enough to kick
        ball_x, ball_y = ball.get_position()
        distance_to_ball = math.sqrt((ball_x - self.x) ** 2 + (ball_y - self.y) ** 2)

        if distance_to_ball <= self.radius + ball.radius + 0.5:  # Within kicking range
            if target_x is not None and target_y is not None:
                # Kick towards target
                kick_direction_x = target_x - ball_x
                kick_direction_y = target_y - ball_y
            else:
                # Kick in facing direction
                kick_direction_x = math.cos(self.facing_angle)
                kick_direction_y = math.sin(self.facing_angle)

            # Normalize kick direction
            kick_magnitude = math.sqrt(kick_direction_x ** 2 + kick_direction_y ** 2)
            if kick_magnitude > 0:
                kick_direction_x /= kick_magnitude
                kick_direction_y /= kick_magnitude

            # Apply kick force (scaled by power and player energy)
            max_kick_force = 15.0  # Maximum kick force
            energy_factor = max(0.3, self.energy / 100.0)  # Minimum 30% power when tired
            kick_force = max_kick_force * power * energy_factor

            ball.kick(
                kick_direction_x * kick_force,
                kick_direction_y * kick_force,
                self.player_id
            )

            # Consume energy for kicking
            self.energy = max(0.0, self.energy - 5.0 * power)
            self.action = "kicking"

            return True
        return False

    def pass_ball(self, ball, teammate, power: float = 0.5):
        """Pass the ball to a teammate.

        Args:
            ball: Ball object
            teammate: Player object to receive the ball
            power: Pass power (0.0 to 1.0)
        """
        return self.kick_ball(ball, teammate.x, teammate.y, power)

    def tackle(self, opponent, ball) -> bool:
        """Attempt to tackle an opponent to steal the ball.

        Args:
            opponent: Opponent Player object
            ball: Ball object

        Returns:
            True if tackle was successful, False otherwise
        """
        distance = math.sqrt((opponent.x - self.x) ** 2 + (opponent.y - self.y) ** 2)

        if distance <= self.radius * 2:  # within tackling range
            success_chance = 0.7 if self.energy > 20 else 0.4
            if random.random() < success_chance:
                # Steal the ball
                opponent.has_ball = False
                self.has_ball = True
                ball.set_position(self.x, self.y)  # stick ball to player
                self.action = "tackling"
                return True
        return False

    def shoot(self, ball, goal_x: float, goal_y: float, power: float = 1.0):
        """Shoot the ball towards the goal."""
        return self.kick_ball(ball, goal_x, goal_y, power)

    def _get_max_speed_for_role(self) -> float:
        """Get maximum speed based on player role."""
        speeds = {
            PlayerRole.GOALKEEPER: 6.0,  # Slower, focused on positioning
            PlayerRole.DEFENDER: 7.0,  # Moderate speed, endurance focused
            PlayerRole.MIDFIELDER: 8.5,  # Balanced speed and endurance
            PlayerRole.FORWARD: 9.0  # Fastest, for attacks
        }
        return speeds.get(self.role, 7.5)

    def _get_team_colors(self) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
        """Get team colors (jersey, shorts)."""
        if self.team == "home":
            if self.role == PlayerRole.GOALKEEPER:
                return (255, 255, 0), (0, 0, 0)  # Yellow jersey, black shorts
            else:
                return (0, 100, 200), (255, 255, 255)  # Blue jersey, white shorts
        else:  # away team
            if self.role == PlayerRole.GOALKEEPER:
                return (255, 165, 0), (0, 0, 0)  # Orange jersey, black shorts
            else:
                return (200, 0, 0), (0, 0, 0)  # Red jersey, black shorts

    def move_towards_target(self, dt: float):
        """Move towards the current target position."""
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        
        # Use squared distance to avoid expensive sqrt when possible
        distance_squared = dx ** 2 + dy ** 2
        
        if distance_squared > 0.25:  # Only move if reasonably far from target (0.5^2 = 0.25)
            # Only calculate sqrt when we actually need to move
            distance = math.sqrt(distance_squared)
            
            # Normalize direction
            direction_x = dx / distance
            direction_y = dy / distance

            # Calculate desired velocity with energy consideration
            energy_factor = max(0.3, self.energy / 100.0)  # Slow down when tired
            desired_speed = min(self.max_speed * energy_factor, distance * 2.0)  # Slow down when close
            desired_velocity_x = direction_x * desired_speed
            desired_velocity_y = direction_y * desired_speed

            # Apply acceleration/deceleration
            acceleration = self.acceleration * dt

            # Update velocity towards desired velocity
            vel_diff_x = desired_velocity_x - self.velocity_x
            vel_diff_y = desired_velocity_y - self.velocity_y

            if abs(vel_diff_x) > acceleration:
                self.velocity_x += acceleration * (1 if vel_diff_x > 0 else -1)
            else:
                self.velocity_x = desired_velocity_x

            if abs(vel_diff_y) > acceleration:
                self.velocity_y += acceleration * (1 if vel_diff_y > 0 else -1)
            else:
                self.velocity_y = desired_velocity_y
        else:
            # Close to target, decelerate
            deceleration = self.deceleration * dt

            if abs(self.velocity_x) > deceleration:
                self.velocity_x -= deceleration * (1 if self.velocity_x > 0 else -1)
            else:
                self.velocity_x = 0

            if abs(self.velocity_y) > deceleration:
                self.velocity_y -= deceleration * (1 if self.velocity_y > 0 else -1)
            else:
                self.velocity_y = 0

    def set_target(self, x: float, y: float):
        """Set target position for AI movement.
        
        Args:
            x: Target x coordinate
            y: Target y coordinate
        """
        self.target_x = x
        self.target_y = y
        self.action = "moving"

    def apply_input(self, input_x: float, input_y: float, dt: float):
        """Apply direct input for player control.
        
        Args:
            input_x: Input in x direction (-1 to 1)
            input_y: Input in y direction (-1 to 1)
            dt: Delta time in seconds
        """
        # Normalize input
        input_magnitude = math.sqrt(input_x ** 2 + input_y ** 2)
        if input_magnitude > 1.0:
            input_x /= input_magnitude
            input_y /= input_magnitude
            input_magnitude = 1.0

        # Calculate desired velocity
        desired_velocity_x = input_x * self.max_speed
        desired_velocity_y = input_y * self.max_speed

        # Apply acceleration or deceleration
        if input_magnitude > 0.1:
            # Accelerating
            acceleration = self.acceleration * dt
            vel_diff_x = desired_velocity_x - self.velocity_x
            vel_diff_y = desired_velocity_y - self.velocity_y

            if abs(vel_diff_x) > acceleration:
                self.velocity_x += acceleration * (1 if vel_diff_x > 0 else -1)
            else:
                self.velocity_x = desired_velocity_x

            if abs(vel_diff_y) > acceleration:
                self.velocity_y += acceleration * (1 if vel_diff_y > 0 else -1)
            else:
                self.velocity_y = desired_velocity_y
        else:
            # Decelerating
            deceleration = self.deceleration * dt

            if abs(self.velocity_x) > deceleration:
                self.velocity_x -= deceleration * (1 if self.velocity_x > 0 else -1)
            else:
                self.velocity_x = 0

            if abs(self.velocity_y) > deceleration:
                self.velocity_y -= deceleration * (1 if self.velocity_y > 0 else -1)
            else:
                self.velocity_y = 0

    def get_position(self) -> Tuple[float, float]:
        """Get current player position."""
        return self.x, self.y

    def get_distance_to_ball(self, ball) -> float:
        """Get distance to the ball."""
        ball_x, ball_y = ball.get_position()
        return math.sqrt((ball_x - self.x) ** 2 + (ball_y - self.y) ** 2)

    def get_distance_to_ball_pos(self, ball_x: float, ball_y: float) -> float:
        """Get distance to a ball position."""
        return math.sqrt((ball_x - self.x) ** 2 + (ball_y - self.y) ** 2)
