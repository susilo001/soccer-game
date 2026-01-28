"""Input handler for player controls and game interactions."""

import pygame
from typing import Dict, Tuple, Optional


class InputHandler:
    """Handles keyboard and mouse input for the game."""
    
    def __init__(self):
        """Initialize the input handler."""
        self.keys_pressed = set()
        self.keys_just_pressed = set()
        self.keys_just_released = set()
        
        self.mouse_pos = (0, 0)
        self.mouse_buttons = set()
        self.mouse_just_clicked = set()
        self.mouse_just_released = set()
        
        # Player controls configuration
        self.player1_controls = {
            'up': pygame.K_w,
            'down': pygame.K_s,
            'left': pygame.K_a,
            'right': pygame.K_d,
            'kick': pygame.K_SPACE,
            'pass': pygame.K_e,
            'sprint': pygame.K_LSHIFT
        }
        
        self.player2_controls = {
            'up': pygame.K_UP,
            'down': pygame.K_DOWN,
            'left': pygame.K_LEFT,
            'right': pygame.K_RIGHT,
            'kick': pygame.K_RETURN,
            'pass': pygame.K_RSHIFT,
            'sprint': pygame.K_RCTRL
        }
    
    def update(self, events):
        """Update input state based on pygame events.
        
        Args:
            events: List of pygame events
        """
        # Clear just pressed/released sets
        self.keys_just_pressed.clear()
        self.keys_just_released.clear()
        self.mouse_just_clicked.clear()
        self.mouse_just_released.clear()
        
        # Process events
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key not in self.keys_pressed:
                    self.keys_just_pressed.add(event.key)
                self.keys_pressed.add(event.key)
                
            elif event.type == pygame.KEYUP:
                if event.key in self.keys_pressed:
                    self.keys_just_released.add(event.key)
                    self.keys_pressed.remove(event.key)
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button not in self.mouse_buttons:
                    self.mouse_just_clicked.add(event.button)
                self.mouse_buttons.add(event.button)
                
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button in self.mouse_buttons:
                    self.mouse_just_released.add(event.button)
                    self.mouse_buttons.remove(event.button)
                    
            elif event.type == pygame.MOUSEMOTION:
                self.mouse_pos = event.pos
    
    def get_player_input(self, player_id: int) -> Dict[str, bool]:
        """Get input state for a specific player.
        
        Args:
            player_id: Player ID (1 or 2)
            
        Returns:
            Dictionary with input states for the player
        """
        controls = self.player1_controls if player_id == 1 else self.player2_controls
        
        return {
            'up': controls['up'] in self.keys_pressed,
            'down': controls['down'] in self.keys_pressed,
            'left': controls['left'] in self.keys_pressed,
            'right': controls['right'] in self.keys_pressed,
            'kick': controls['kick'] in self.keys_just_pressed,
            'kick_held': controls['kick'] in self.keys_pressed,
            'pass': controls['pass'] in self.keys_just_pressed,
            'sprint': controls['sprint'] in self.keys_pressed
        }
    
    def get_movement_vector(self, player_id: int) -> Tuple[float, float]:
        """Get normalized movement vector for a player.
        
        Args:
            player_id: Player ID (1 or 2)
            
        Returns:
            Tuple of (x, y) movement vector (-1 to 1 range)
        """
        input_state = self.get_player_input(player_id)
        
        x = 0.0
        y = 0.0
        
        if input_state['left']:
            x -= 1.0
        if input_state['right']:
            x += 1.0
        if input_state['up']:
            y -= 1.0
        if input_state['down']:
            y += 1.0
        
        # Apply sprint modifier
        if input_state['sprint']:
            x *= 1.5  # 50% speed boost when sprinting
            y *= 1.5
        
        return x, y
    
    def is_key_pressed(self, key: int) -> bool:
        """Check if a key is currently pressed.
        
        Args:
            key: Pygame key constant
            
        Returns:
            True if key is pressed
        """
        return key in self.keys_pressed
    
    def is_key_just_pressed(self, key: int) -> bool:
        """Check if a key was just pressed this frame.
        
        Args:
            key: Pygame key constant
            
        Returns:
            True if key was just pressed
        """
        return key in self.keys_just_pressed
    
    def is_key_just_released(self, key: int) -> bool:
        """Check if a key was just released this frame.
        
        Args:
            key: Pygame key constant
            
        Returns:
            True if key was just released
        """
        return key in self.keys_just_released
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position.
        
        Returns:
            Tuple of (x, y) screen coordinates
        """
        return self.mouse_pos
    
    def is_mouse_button_pressed(self, button: int) -> bool:
        """Check if a mouse button is currently pressed.
        
        Args:
            button: Mouse button (1=left, 2=middle, 3=right)
            
        Returns:
            True if button is pressed
        """
        return button in self.mouse_buttons
    
    def is_mouse_button_just_clicked(self, button: int) -> bool:
        """Check if a mouse button was just clicked this frame.
        
        Args:
            button: Mouse button (1=left, 2=middle, 3=right)
            
        Returns:
            True if button was just clicked
        """
        return button in self.mouse_just_clicked
    
    def get_world_mouse_position(self, field_renderer) -> Optional[Tuple[float, float]]:
        """Get mouse position in world coordinates.
        
        Args:
            field_renderer: Field renderer for coordinate conversion
            
        Returns:
            Tuple of (x, y) world coordinates, or None if outside field
        """
        try:
            world_x, world_y = field_renderer.screen_to_world(self.mouse_pos[0], self.mouse_pos[1])
            
            # Check if within field bounds
            field_bounds = field_renderer.get_field_bounds()
            min_x, max_x, min_y, max_y = field_bounds
            
            if min_x <= world_x <= max_x and min_y <= world_y <= max_y:
                return world_x, world_y
            else:
                return None
        except:
            return None