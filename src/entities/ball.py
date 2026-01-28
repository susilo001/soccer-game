"""Soccer ball entity with physics and rendering."""

import pygame
import math
from typing import Tuple


class Ball:
    """Soccer ball with realistic physics."""
    
    def __init__(self, x: float = 0.0, y: float = 0.0):
        """Initialize the ball.
        
        Args:
            x: Initial x position in world coordinates (meters)
            y: Initial y position in world coordinates (meters)
        """
        # Position and velocity
        self.x = x
        self.y = y
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        
        # Physical properties
        self.radius = 0.11  # FIFA regulation: 21-22 cm diameter, so ~11 cm radius
        self.mass = 0.43  # FIFA regulation: 410-450 grams
        self.friction = 0.7  # Ground friction coefficient
        self.bounce = 0.6  # Bounce factor when hitting walls
        
        # Visual properties
        self.color = (255, 255, 255)  # White
        self.outline_color = (0, 0, 0)  # Black outline
        
        # Ball state
        self.is_moving = False
        self.last_touched_by = None  # Player ID who last touched the ball
    
    def update(self, dt: float, field_bounds: Tuple[float, float, float, float]):
        """Update ball physics.
        
        Args:
            dt: Delta time in seconds
            field_bounds: (min_x, max_x, min_y, max_y) in meters
        """
        # Apply friction
        speed = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
        if speed > 0.1:  # Minimum speed threshold
            friction_force = self.friction * dt
            speed_reduction = min(friction_force, speed)
            
            # Reduce velocity proportionally
            velocity_factor = (speed - speed_reduction) / speed
            self.velocity_x *= velocity_factor
            self.velocity_y *= velocity_factor
            
            self.is_moving = True
        else:
            # Stop the ball if moving very slowly
            self.velocity_x = 0.0
            self.velocity_y = 0.0
            self.is_moving = False
        
        # Update position
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        
        # Handle field boundaries with bounce
        min_x, max_x, min_y, max_y = field_bounds
        
        # Horizontal boundaries
        if self.x - self.radius < min_x:
            self.x = min_x + self.radius
            self.velocity_x = -self.velocity_x * self.bounce
        elif self.x + self.radius > max_x:
            self.x = max_x - self.radius
            self.velocity_x = -self.velocity_x * self.bounce
        
        # Vertical boundaries
        if self.y - self.radius < min_y:
            self.y = min_y + self.radius
            self.velocity_y = -self.velocity_y * self.bounce
        elif self.y + self.radius > max_y:
            self.y = max_y - self.radius
            self.velocity_y = -self.velocity_y * self.bounce
    
    def kick(self, force_x: float, force_y: float, kicker_id: str = None):
        """Apply a force to the ball (kick it).
        
        Args:
            force_x: Force in x direction (N⋅s impulse)
            force_y: Force in y direction (N⋅s impulse)
            kicker_id: ID of the player who kicked the ball
        """
        # Convert force to velocity (F⋅dt = m⋅Δv, assuming dt=1)
        self.velocity_x += force_x / self.mass
        self.velocity_y += force_y / self.mass
        
        # Cap maximum velocity (realistic ball speed)
        max_velocity = 30.0  # ~108 km/h maximum
        current_speed = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
        if current_speed > max_velocity:
            scale = max_velocity / current_speed
            self.velocity_x *= scale
            self.velocity_y *= scale
        
        self.last_touched_by = kicker_id
        self.is_moving = True
    
    def get_position(self) -> Tuple[float, float]:
        """Get current ball position.
        
        Returns:
            Tuple of (x, y) in world coordinates
        """
        return self.x, self.y
    
    def get_velocity(self) -> Tuple[float, float]:
        """Get current ball velocity.
        
        Returns:
            Tuple of (velocity_x, velocity_y) in m/s
        """
        return self.velocity_x, self.velocity_y
    
    def get_speed(self) -> float:
        """Get current ball speed.
        
        Returns:
            Speed in m/s
        """
        return math.sqrt(self.velocity_x**2 + self.velocity_y**2)
    
    def set_position(self, x: float, y: float):
        """Set ball position.
        
        Args:
            x: New x position in world coordinates
            y: New y position in world coordinates
        """
        self.x = x
        self.y = y
    
    def stop(self):
        """Stop the ball immediately."""
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.is_moving = False
    
    def render(self, screen: pygame.Surface, field_renderer):
        """Render the ball on screen.
        
        Args:
            screen: Pygame surface to render on
            field_renderer: Field renderer for coordinate conversion
        """
        # Convert world coordinates to screen coordinates
        screen_x, screen_y = field_renderer.world_to_screen(self.x, self.y)
        screen_radius = max(8, int(self.radius * field_renderer.scale))  # Increased minimum size
        
        # Draw ball shadow (slightly offset)
        shadow_offset = 2
        pygame.draw.circle(
            screen,
            (50, 50, 50),  # Dark gray shadow
            (screen_x + shadow_offset, screen_y + shadow_offset),
            screen_radius
        )
        
        # Draw ball
        pygame.draw.circle(screen, self.color, (screen_x, screen_y), screen_radius)
        pygame.draw.circle(screen, self.outline_color, (screen_x, screen_y), screen_radius, 2)
        
        # Draw ball pattern (simple cross pattern)
        if screen_radius > 5:
            # Draw cross lines on the ball
            line_length = screen_radius - 2
            pygame.draw.line(
                screen,
                self.outline_color,
                (screen_x - line_length, screen_y),
                (screen_x + line_length, screen_y),
                1
            )
            pygame.draw.line(
                screen,
                self.outline_color,
                (screen_x, screen_y - line_length),
                (screen_x, screen_y + line_length),
                1
            )
        
        # Draw velocity indicator if ball is moving fast
        if self.is_moving and self.get_speed() > 2.0:
            velocity_scale = 10  # Scale factor for velocity visualization
            end_x = screen_x + int(self.velocity_x * velocity_scale)
            end_y = screen_y + int(self.velocity_y * velocity_scale)
            
            pygame.draw.line(
                screen,
                (255, 0, 0),  # Red velocity indicator
                (screen_x, screen_y),
                (end_x, end_y),
                2
            )
            
            # Draw arrowhead
            if abs(end_x - screen_x) > 5 or abs(end_y - screen_y) > 5:
                arrow_size = 5
                angle = math.atan2(end_y - screen_y, end_x - screen_x)
                
                # Arrow points
                arrow_x1 = end_x - arrow_size * math.cos(angle - math.pi/6)
                arrow_y1 = end_y - arrow_size * math.sin(angle - math.pi/6)
                arrow_x2 = end_x - arrow_size * math.cos(angle + math.pi/6)
                arrow_y2 = end_y - arrow_size * math.sin(angle + math.pi/6)
                
                pygame.draw.line(screen, (255, 0, 0), (end_x, end_y), (arrow_x1, arrow_y1), 2)
                pygame.draw.line(screen, (255, 0, 0), (end_x, end_y), (arrow_x2, arrow_y2), 2)
    
    def distance_to_point(self, x: float, y: float) -> float:
        """Calculate distance from ball center to a point.
        
        Args:
            x: Point x coordinate
            y: Point y coordinate
            
        Returns:
            Distance in meters
        """
        dx = self.x - x
        dy = self.y - y
        return math.sqrt(dx**2 + dy**2)
    
    def is_near_position(self, x: float, y: float, threshold: float = 1.0) -> bool:
        """Check if ball is near a specific position.
        
        Args:
            x: Target x coordinate
            y: Target y coordinate
            threshold: Distance threshold in meters
            
        Returns:
            True if ball is within threshold distance
        """
        return self.distance_to_point(x, y) <= threshold