"""Soccer field renderer with proper markings."""

import pygame
import math
from config.game.settings import FieldSettings, DisplaySettings


class FieldRenderer:
    """Renders the soccer field with proper markings."""
    
    def __init__(self, display_settings: DisplaySettings, field_settings: FieldSettings):
        """Initialize the field renderer.
        
        Args:
            display_settings: Display configuration
            field_settings: Field dimensions and properties
        """
        self.display = display_settings
        self.field = field_settings
        
        # Colors
        self.field_color = (34, 139, 34)  # Forest green
        self.line_color = (255, 255, 255)  # White
        self.goal_color = (255, 255, 255)  # White
        
        # Calculate scaling factors to fit field on screen
        self.scale_x = (self.display.width * 0.9) / self.field.length
        self.scale_y = (self.display.height * 0.9) / self.field.width
        self.scale = min(self.scale_x, self.scale_y)  # Use smaller scale to maintain aspect ratio
        
        # Field dimensions in pixels
        self.field_width_px = self.field.length * self.scale
        self.field_height_px = self.field.width * self.scale
        
        # Field offset to center it on screen
        self.field_offset_x = (self.display.width - self.field_width_px) // 2
        self.field_offset_y = (self.display.height - self.field_height_px) // 2
    
    def world_to_screen(self, world_x: float, world_y: float) -> tuple:
        """Convert world coordinates to screen coordinates.
        
        Args:
            world_x: X coordinate in world space (meters)
            world_y: Y coordinate in world space (meters)
            
        Returns:
            Tuple of (screen_x, screen_y)
        """
        screen_x = self.field_offset_x + (world_x + self.field.length / 2) * self.scale
        screen_y = self.field_offset_y + (world_y + self.field.width / 2) * self.scale
        return int(screen_x), int(screen_y)
    
    def screen_to_world(self, screen_x: int, screen_y: int) -> tuple:
        """Convert screen coordinates to world coordinates.
        
        Args:
            screen_x: X coordinate on screen
            screen_y: Y coordinate on screen
            
        Returns:
            Tuple of (world_x, world_y) in meters
        """
        world_x = (screen_x - self.field_offset_x) / self.scale - self.field.length / 2
        world_y = (screen_y - self.field_offset_y) / self.scale - self.field.width / 2
        return world_x, world_y
    
    def render(self, screen: pygame.Surface):
        """Render the complete soccer field.
        
        Args:
            screen: Pygame surface to render on
        """
        # Clear screen with field color
        screen.fill(self.field_color)
        
        # Draw field background (slightly darker green for the playing area)
        field_rect = pygame.Rect(
            self.field_offset_x,
            self.field_offset_y,
            self.field_width_px,
            self.field_height_px
        )
        pygame.draw.rect(screen, (20, 120, 20), field_rect)
        
        # Draw field markings
        self._draw_field_lines(screen)
        self._draw_center_circle(screen)
        self._draw_penalty_areas(screen)
        self._draw_goals(screen)
        self._draw_corner_arcs(screen)
    
    def _draw_field_lines(self, screen: pygame.Surface):
        """Draw the outer field lines and center line."""
        # Field boundary
        field_rect = pygame.Rect(
            self.field_offset_x,
            self.field_offset_y,
            self.field_width_px,
            self.field_height_px
        )
        pygame.draw.rect(screen, self.line_color, field_rect, 2)
        
        # Center line
        center_x = self.field_offset_x + self.field_width_px // 2
        pygame.draw.line(
            screen,
            self.line_color,
            (center_x, self.field_offset_y),
            (center_x, self.field_offset_y + self.field_height_px),
            2
        )
    
    def _draw_center_circle(self, screen: pygame.Surface):
        """Draw the center circle."""
        center_x = self.field_offset_x + self.field_width_px // 2
        center_y = self.field_offset_y + self.field_height_px // 2
        radius = int(self.field.center_circle_radius * self.scale)
        
        pygame.draw.circle(screen, self.line_color, (center_x, center_y), radius, 2)
        
        # Center spot
        pygame.draw.circle(screen, self.line_color, (center_x, center_y), 3)
    
    def _draw_penalty_areas(self, screen: pygame.Surface):
        """Draw penalty areas and penalty spots."""
        penalty_width = self.field.penalty_area_width * self.scale
        penalty_length = self.field.penalty_area_length * self.scale
        
        # Left penalty area
        left_penalty_rect = pygame.Rect(
            self.field_offset_x,
            self.field_offset_y + (self.field_height_px - penalty_width) // 2,
            penalty_length,
            penalty_width
        )
        pygame.draw.rect(screen, self.line_color, left_penalty_rect, 2)
        
        # Right penalty area
        right_penalty_rect = pygame.Rect(
            self.field_offset_x + self.field_width_px - penalty_length,
            self.field_offset_y + (self.field_height_px - penalty_width) // 2,
            penalty_length,
            penalty_width
        )
        pygame.draw.rect(screen, self.line_color, right_penalty_rect, 2)
        
        # Penalty spots (11 meters from goal line)
        penalty_spot_distance = 11.0 * self.scale
        
        # Left penalty spot
        left_spot_x = self.field_offset_x + penalty_spot_distance
        center_y = self.field_offset_y + self.field_height_px // 2
        pygame.draw.circle(screen, self.line_color, (int(left_spot_x), int(center_y)), 3)
        
        # Right penalty spot
        right_spot_x = self.field_offset_x + self.field_width_px - penalty_spot_distance
        pygame.draw.circle(screen, self.line_color, (int(right_spot_x), int(center_y)), 3)
    
    def _draw_goals(self, screen: pygame.Surface):
        """Draw the goals."""
        goal_width = self.field.goal_width * self.scale
        goal_height = 8  # Goal depth in pixels (for visual representation)
        
        # Left goal
        left_goal_y = self.field_offset_y + (self.field_height_px - goal_width) // 2
        left_goal_rect = pygame.Rect(
            self.field_offset_x - goal_height,
            left_goal_y,
            goal_height,
            goal_width
        )
        pygame.draw.rect(screen, self.goal_color, left_goal_rect, 2)
        
        # Right goal
        right_goal_rect = pygame.Rect(
            self.field_offset_x + self.field_width_px,
            left_goal_y,
            goal_height,
            goal_width
        )
        pygame.draw.rect(screen, self.goal_color, right_goal_rect, 2)
    
    def _draw_corner_arcs(self, screen: pygame.Surface):
        """Draw corner arcs."""
        corner_radius = int(1.0 * self.scale)  # 1 meter radius
        
        corners = [
            (self.field_offset_x, self.field_offset_y),  # Top-left
            (self.field_offset_x + self.field_width_px, self.field_offset_y),  # Top-right
            (self.field_offset_x, self.field_offset_y + self.field_height_px),  # Bottom-left
            (self.field_offset_x + self.field_width_px, self.field_offset_y + self.field_height_px)  # Bottom-right
        ]
        
        # Draw quarter circles at each corner
        for i, (corner_x, corner_y) in enumerate(corners):
            # Determine the arc angles based on corner position
            if i == 0:  # Top-left
                start_angle = 0
                end_angle = math.pi / 2
            elif i == 1:  # Top-right
                start_angle = math.pi / 2
                end_angle = math.pi
            elif i == 2:  # Bottom-left
                start_angle = -math.pi / 2
                end_angle = 0
            else:  # Bottom-right
                start_angle = math.pi
                end_angle = 3 * math.pi / 2
            
            # Draw arc using multiple line segments
            num_segments = 10
            for j in range(num_segments):
                angle1 = start_angle + (end_angle - start_angle) * j / num_segments
                angle2 = start_angle + (end_angle - start_angle) * (j + 1) / num_segments
                
                x1 = corner_x + corner_radius * math.cos(angle1)
                y1 = corner_y + corner_radius * math.sin(angle1)
                x2 = corner_x + corner_radius * math.cos(angle2)
                y2 = corner_y + corner_radius * math.sin(angle2)
                
                pygame.draw.line(screen, self.line_color, (x1, y1), (x2, y2), 1)
    
    def get_field_bounds(self) -> tuple:
        """Get the field boundaries in world coordinates.
        
        Returns:
            Tuple of (min_x, max_x, min_y, max_y) in meters
        """
        return (
            -self.field.length / 2,
            self.field.length / 2,
            -self.field.width / 2,
            self.field.width / 2
        )