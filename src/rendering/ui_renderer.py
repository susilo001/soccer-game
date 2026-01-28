"""UI renderer for game information and debugging displays."""

import pygame
from typing import List, Tuple


class UIRenderer:
    """Renders UI elements like score, controls, and debug info."""
    
    def __init__(self, display_width: int, display_height: int):
        """Initialize the UI renderer.
        
        Args:
            display_width: Screen width in pixels
            display_height: Screen height in pixels
        """
        self.display_width = display_width
        self.display_height = display_height
        
        # Initialize fonts
        pygame.font.init()
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
        
        # Colors
        self.text_color = (255, 255, 255)
        self.background_color = (0, 0, 0, 128)  # Semi-transparent black
        
    def render_controls(self, screen: pygame.Surface):
        """Render control instructions.
        
        Args:
            screen: Pygame surface to render on
        """
        controls_text = [
            "CONTROLS:",
            "WASD - Move Player (Blue)",
            "Mouse - Aim",
            "SPACE - Kick Ball",
            "ESC - Exit",
            "F11 - Fullscreen"
        ]
        
        y_offset = 10
        for i, text in enumerate(controls_text):
            color = (255, 255, 0) if i == 0 else self.text_color
            font = self.font_medium if i == 0 else self.font_small
            
            text_surface = font.render(text, True, color)
            screen.blit(text_surface, (10, y_offset))
            y_offset += 20
    
    def render_game_info(self, screen: pygame.Surface, ball, player1, player2):
        """Render game state information.
        
        Args:
            screen: Pygame surface to render on
            ball: Ball object
            player1: Player 1 object
            player2: Player 2 object (AI)
        """
        # Ball position
        ball_x, ball_y = ball.get_position()
        ball_speed = ball.get_speed()
        
        # Player positions
        p1_x, p1_y = player1.get_position()
        p2_x, p2_y = player2.get_position()
        
        info_text = [
            f"Ball: ({ball_x:.1f}, {ball_y:.1f}) Speed: {ball_speed:.1f}",
            f"Player (Blue): ({p1_x:.1f}, {p1_y:.1f}) Energy: {player1.energy:.0f}%",
            f"AI (Red): ({p2_x:.1f}, {p2_y:.1f}) Energy: {player2.energy:.0f}%",
            f"Distance to Ball: P1={player1.get_distance_to_ball(ball):.1f}m, AI={player2.get_distance_to_ball(ball):.1f}m"
        ]
        
        # Create semi-transparent background
        info_height = len(info_text) * 20 + 10
        info_surface = pygame.Surface((400, info_height))
        info_surface.set_alpha(128)
        info_surface.fill((0, 0, 0))
        screen.blit(info_surface, (10, self.display_height - info_height - 10))
        
        # Render text
        y_offset = self.display_height - info_height
        for text in info_text:
            text_surface = self.font_small.render(text, True, self.text_color)
            screen.blit(text_surface, (15, y_offset))
            y_offset += 20
    
    def render_ball_indicator(self, screen: pygame.Surface, ball, field_renderer):
        """Render a ball position indicator at screen edge if ball is off-screen.
        
        Args:
            screen: Pygame surface to render on
            ball: Ball object
            field_renderer: Field renderer for coordinate conversion
        """
        ball_screen_x, ball_screen_y = field_renderer.world_to_screen(ball.x, ball.y)
        
        # Check if ball is visible on screen
        margin = 50
        if (ball_screen_x < margin or ball_screen_x > self.display_width - margin or
            ball_screen_y < margin or ball_screen_y > self.display_height - margin):
            
            # Draw arrow pointing to ball from center of screen
            center_x = self.display_width // 2
            center_y = self.display_height // 2
            
            # Calculate direction to ball
            dx = ball_screen_x - center_x
            dy = ball_screen_y - center_y
            distance = (dx**2 + dy**2)**0.5
            
            if distance > 0:
                # Normalize and scale
                dx /= distance
                dy /= distance
                
                # Position arrow at screen edge
                arrow_distance = min(center_x - 30, center_y - 30)
                arrow_x = center_x + dx * arrow_distance
                arrow_y = center_y + dy * arrow_distance
                
                # Draw arrow
                pygame.draw.circle(screen, (255, 255, 0), (int(arrow_x), int(arrow_y)), 8)
                pygame.draw.circle(screen, (255, 0, 0), (int(arrow_x), int(arrow_y)), 6)
                
                # Draw distance text
                world_distance = ((ball.x)**2 + (ball.y)**2)**0.5
                distance_text = self.font_small.render(f"{world_distance:.1f}m", True, (255, 255, 255))
                screen.blit(distance_text, (int(arrow_x) - 15, int(arrow_y) - 25))
    
    def render_field_center_marker(self, screen: pygame.Surface, field_renderer):
        """Render a small marker at the field center for reference.
        
        Args:
            screen: Pygame surface to render on
            field_renderer: Field renderer for coordinate conversion
        """
        center_screen_x, center_screen_y = field_renderer.world_to_screen(0, 0)
        
        # Draw cross at center
        size = 5
        pygame.draw.line(screen, (255, 255, 0), 
                         (center_screen_x - size, center_screen_y), 
                         (center_screen_x + size, center_screen_y), 2)
        pygame.draw.line(screen, (255, 255, 0), 
                         (center_screen_x, center_screen_y - size), 
                         (center_screen_x, center_screen_y + size), 2)
