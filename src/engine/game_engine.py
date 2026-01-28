"""Game Engine - Core game loop and management."""

import logging
import pygame
from typing import Optional
from config.game.settings import GameSettings

# Game components
from src.rendering.field_renderer import FieldRenderer
from src.rendering.ui_renderer import UIRenderer
from src.entities.ball import Ball
from src.entities.player import Player, PlayerRole
from src.input.input_handler import InputHandler
from game.team.team_manager import TeamManager
from game.rules.goal_detector import GoalDetector


class GameEngine:
    """Main game engine handling the core game loop."""

    def __init__(self, settings: GameSettings):
        """Initialize the game engine.
        
        Args:
            settings: Game configuration settings
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.clock = None
        self.screen = None

        # Initialize pygame
        pygame.init()
        self._initialize_display()

        # Create subsystems
        self.input = InputHandler()
        self.field_renderer = FieldRenderer(self.settings.display, self.settings.field)
        self.ui_renderer = UIRenderer(self.settings.display.width, self.settings.display.height)

        # World objects
        self.ball = Ball(0.0, 0.0)

        # Create full AI teams
        self.home_team = TeamManager("home", "4-4-2")
        self.away_team = TeamManager("away", "4-3-3")

        # Create goal detector
        self.goal_detector = GoalDetector(
            field_length=self.settings.field.length,
            field_width=self.settings.field.width,
            goal_width=self.settings.field.goal_width
        )

        # Cached field bounds
        self.field_bounds = self.field_renderer.get_field_bounds()

        # Spectator mode settings
        self.game_speed = 1.0  # 1.0 = normal speed
        self.show_debug_info = True
        self.paused = False
        
        # Kickoff state management (replace threading)
        self._kickoff_state = "none"  # none, preparing, ready, active
        self._kickoff_timer = 0.0
        self._kickoff_preparation_time = 2.0  # 2 seconds to prepare
        self._kickoff_pass_delay = 1.0  # 1 second after preparation

        # Start the match with initial kick-off (home team starts)
        self._setup_initial_kickoff()

    def _initialize_display(self):
        """Initialize the pygame display."""
        try:
            if self.settings.display.fullscreen:
                self.screen = pygame.display.set_mode(
                    (self.settings.display.width, self.settings.display.height),
                    pygame.FULLSCREEN
                )
            else:
                self.screen = pygame.display.set_mode(
                    (self.settings.display.width, self.settings.display.height)
                )

            pygame.display.set_caption(self.settings.display.title)
            self.clock = pygame.time.Clock()
            self.logger.info("Display initialized successfully")

        except pygame.error as e:
            self.logger.error(f"Failed to initialize display: {e}")
            raise

    def run(self):
        """Main game loop."""
        self.logger.info("Starting game loop")
        self.running = True

        try:
            while self.running:
                dt = self.clock.tick(self.settings.display.fps) / 1000.0  # Delta time in seconds

                self._handle_events()
                self._update(dt)
                self._render()

        except Exception as e:
            self.logger.error(f"Error in game loop: {e}", exc_info=True)
        finally:
            self._cleanup()

    def _handle_events(self):
        """Handle pygame events."""
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_F11:
                    self._toggle_fullscreen()
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    self.game_speed = min(5.0, self.game_speed + 0.5)
                elif event.key == pygame.K_MINUS:
                    self.game_speed = max(0.1, self.game_speed - 0.5)
                elif event.key == pygame.K_r:
                    self._reset_match()
                elif event.key == pygame.K_d:
                    self.show_debug_info = not self.show_debug_info

        # Update input handler state
        self.input.update(events)

    def _update(self, dt: float):
        """Update game state.
        
        Args:
            dt: Delta time since last frame
        """
        try:
            if self.paused:
                return

            # Apply game speed multiplier
            effective_dt = dt * self.game_speed

            # Update kickoff state
            self._update_kickoff_state(effective_dt)
            
            # Check kick-off state and pass it to teams
            kickoff_info = {
                'active': self._kickoff_state in ["preparing", "ready", "active"],
                'team': getattr(self, '_kickoff_team', None),
                'timer': self._kickoff_timer,
                'state': self._kickoff_state
            }

            # Update teams (AI vs AI) with kick-off awareness
            self.home_team.update_team_ai(effective_dt, self.ball, self.away_team.get_players(), self.field_bounds,
                                          kickoff_info)
            self.away_team.update_team_ai(effective_dt, self.ball, self.home_team.get_players(), self.field_bounds,
                                          kickoff_info)

            # Update ball physics
            self.ball.update(effective_dt, self.field_bounds)

            # Check for goals
            ball_x, ball_y = self.ball.get_position()

            # Debug: print ball position occasionally (only if debug mode is enabled)
            if self.show_debug_info:
                if hasattr(self, '_debug_counter'):
                    self._debug_counter += 1
                else:
                    self._debug_counter = 0

                if self._debug_counter % 3600 == 0:  # Every 60 seconds at 60fps 
                    print(f"Ball position: ({ball_x:.1f}, {ball_y:.1f}), Speed: {self.ball.get_speed():.1f}")
                    print(
                        f"Goal zones: Home at x<={self.goal_detector.home_goal_line:.1f}, Away at x>={self.goal_detector.away_goal_line:.1f}")
                    print(f"Goal width: y between ±{self.goal_detector.half_goal + 0.5:.1f}")

            goal = self.goal_detector.check_goal(ball_x, ball_y, self.ball.last_touched_by)

            if goal:
                self.logger.info(f"GOAL! {goal.scoring_team} team scores! Score: {self.goal_detector.get_score_string()}")
                # Reset ball to center after goal
                self.ball.set_position(0.0, 0.0)
                self.ball.stop()

                # Give kick-off to the team that conceded (defending team)
                self._setup_kickoff(goal.scoring_team)

            # Update goal detector (for celebration timer)
            self.goal_detector.update(effective_dt)
            
        except Exception as e:
            self.logger.error(f"Error in game update: {e}", exc_info=True)
            # Don't crash the game, just log the error

    def _render(self):
        """Render the current frame."""
        try:
            # Draw field
            self.field_renderer.render(self.screen)

            # Draw ball
            self.ball.render(self.screen, self.field_renderer)

            # Draw all players from both teams
            for player in self.home_team.get_players():
                player.render(self.screen, self.field_renderer)
            for player in self.away_team.get_players():
                player.render(self.screen, self.field_renderer)

            # Draw UI elements
            if self.show_debug_info:
                self._render_spectator_ui()
            else:
                self._render_minimal_ui()

            # Flip buffers
            pygame.display.flip()
            
        except Exception as e:
            self.logger.error(f"Error in rendering: {e}", exc_info=True)
            # Try to continue with basic display update
            try:
                pygame.display.flip()
            except:
                pass  # If even basic flip fails, just continue

    def _toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        self.settings.display.fullscreen = not self.settings.display.fullscreen
        self._initialize_display()
        self.logger.info(f"Fullscreen toggled: {self.settings.display.fullscreen}")

    def _update_kickoff_state(self, dt: float):
        """Update kickoff state machine.
        
        Args:
            dt: Delta time in seconds
        """
        if self._kickoff_state == "none":
            return
            
        self._kickoff_timer += dt
        
        if self._kickoff_state == "preparing":
            # Players are moving to positions
            if self._kickoff_timer >= self._kickoff_preparation_time:
                self._kickoff_state = "ready"
                self._kickoff_timer = 0.0
                print(f"⚡ Kickoff ready - {self._kickoff_team} team to kick off")
        
        elif self._kickoff_state == "ready":
            # Brief pause before kick
            if self._kickoff_timer >= self._kickoff_pass_delay:
                self._execute_kickoff_pass()
                self._kickoff_state = "active"
                self._kickoff_timer = 0.0
                
        elif self._kickoff_state == "active":
            # Ball is in play, check if kickoff should end
            if self._kickoff_timer >= 1.0 or self.ball.get_speed() > 2.0:
                self._end_kickoff()
    
    def _execute_kickoff_pass(self):
        """Execute the kickoff pass."""
        if not hasattr(self, '_kickoff_kicker') or not hasattr(self, '_kickoff_receiver'):
            self._end_kickoff()
            return
            
        # Pass toward team's attacking direction
        goal_direction = 1.0 if self._kickoff_team == "home" else -1.0
        
        self.ball.kick(
            goal_direction * 4.0,  # Forward toward goal
            1.0,  # Slight upward (toward receiving player)
            self._kickoff_kicker.player_id
        )
        print(f"⚽ Kick-off: {self._kickoff_kicker.player_id} passes to {self._kickoff_receiver.player_id}")
    
    def _end_kickoff(self):
        """End the kickoff sequence."""
        self._kickoff_state = "none"
        self._kickoff_timer = 0.0
        if hasattr(self, '_kickoff_kicker'):
            delattr(self, '_kickoff_kicker')
        if hasattr(self, '_kickoff_receiver'):
            delattr(self, '_kickoff_receiver')
        print(f"✅ Ball in play!")
        
    def _setup_kickoff(self, scoring_team: str):
        """Set up kick-off after a goal with proper 2-player positioning.
        
        Args:
            scoring_team: Team that just scored ('home' or 'away')
        """
        # The team that conceded gets to kick off
        kick_off_team = "home" if scoring_team == "away" else "away"

        # Reset ALL players to their initial formation positions
        print(f"🔄 Resetting all players to starting positions...")
        self._reset_all_players_to_formation()

        # Set kick-off state
        self._kickoff_state = "preparing"
        self._kickoff_team = kick_off_team
        self._kickoff_timer = 0.0

        # Setup kickoff players
        self._setup_kickoff_players(kick_off_team)
        print(f"🥅 {kick_off_team.upper()} team gets kick-off after conceding goal")
        
    def _setup_kickoff_players(self, kick_off_team: str):
        """Setup players for kickoff.
        
        Args:
            kick_off_team: Team taking the kickoff
        """
        # Find TWO players for kick-off: one midfielder/forward for the kick, one for receiving
        kick_off_players = self.home_team.get_players() if kick_off_team == "home" else self.away_team.get_players()

        from src.entities.player import PlayerRole
        suitable_players = [p for p in kick_off_players if p.role in [PlayerRole.MIDFIELDER, PlayerRole.FORWARD]]

        if len(suitable_players) >= 2:
            # Simplified logic: Use forwards for kick-off (more realistic)
            forwards = [p for p in suitable_players if p.role == PlayerRole.FORWARD]
            midfielders = [p for p in suitable_players if p.role == PlayerRole.MIDFIELDER]

            # Prefer forwards for kick-off
            if len(forwards) >= 2:
                kick_off_player = forwards[0]  # First forward kicks
                receiving_player = forwards[1]  # Second forward receives
            elif len(forwards) >= 1:
                kick_off_player = forwards[0]  # Forward kicks
                receiving_player = midfielders[0] if midfielders else suitable_players[1]  # Midfielder receives
            else:
                # Fallback to any suitable players
                kick_off_player = suitable_players[0]
                receiving_player = suitable_players[1]

            # Ball should be exactly at center (0, 0)
            self.ball.set_position(0.0, 0.0)
            self.ball.stop()
            
            # Position players above and below the ball
            kick_off_player.set_target(0.0, -2.0)  # Below the ball (south)
            receiving_player.set_target(0.0, 2.0)   # Above the ball (north)

            # Move opposing team players to their own half (enforce kick-off rule)
            opposing_players = self.away_team.get_players() if kick_off_team == "home" else self.home_team.get_players()
            self._enforce_kickoff_positions(opposing_players, kick_off_team)

            # Store kick-off players for the sequence
            self._kickoff_kicker = kick_off_player
            self._kickoff_receiver = receiving_player

            print(
                f"👥 Kick-off players: {kick_off_player.player_id} ({kick_off_player.role.value}) → {receiving_player.player_id} ({receiving_player.role.value})")

    def _setup_initial_kickoff(self):
        """Set up the initial kick-off at match start."""
        print(f"🏆 ===== MATCH START =====")
        print(f"🏆 Home Team (4-4-2) vs Away Team (4-3-3)")
        print(f"🏆 Home team wins the toss and kicks off!")

        # Give initial kick-off to home team (traditional)
        # Set a delay before kickoff starts
        self._kickoff_state = "preparing"
        self._kickoff_team = "home"  # Home team kicks off initially
        self._kickoff_timer = -1.0  # Start with -1 second delay for match start
        
        # Setup kickoff players immediately
        self._setup_kickoff_players("home")

    def _enforce_kickoff_positions(self, opposing_players, kick_off_team):
        """Enforce kick-off rule: opposing team must stay in their own half.
        
        Args:
            opposing_players: List of players from opposing team
            kick_off_team: Team that's taking the kick-off
        """
        # Determine which side the opposing team should be on
        opposing_side = 1.0 if kick_off_team == "home" else -1.0

        for player in opposing_players:
            # Check if player is on wrong side of center line
            if (opposing_side > 0 and player.x < 0) or (opposing_side < 0 and player.x > 0):
                # Move player to their own half, maintaining relative position
                buffer = 5.0  # Stay at least 5 meters from center line
                corrected_x = opposing_side * buffer

                # Try to maintain y position but ensure it's reasonable
                corrected_y = max(-25.0, min(25.0, player.y))

                player.set_target(corrected_x, corrected_y)
                print(f"⚠️ Moving {player.player_id} to own half for kick-off: ({corrected_x:.1f}, {corrected_y:.1f})")

    def _reset_all_players_to_formation(self):
        """Reset all players to their initial formation positions."""
        # Get formation positions for both teams
        home_formation = self.home_team.formation.get_positions_for_team("home")
        away_formation = self.away_team.formation.get_positions_for_team("away")

        # Reset home team players
        home_players = self.home_team.get_players()
        self._reset_team_players_to_positions(home_players, home_formation)

        # Reset away team players
        away_players = self.away_team.get_players()
        self._reset_team_players_to_positions(away_players, away_formation)

        print(f"⚙️ Reset {len(home_players + away_players)} players to formation positions")

    def _reset_team_players_to_positions(self, players, formation_positions):
        """Reset a team's players to their formation positions.
        
        Args:
            players: List of player objects
            formation_positions: Dictionary of role -> list of positions
        """
        for player in players:
            role = player.role.value
            if role in formation_positions:
                # Find which position this player should take
                role_positions = formation_positions[role]
                same_role_players = [p for p in players if p.role.value == role]

                try:
                    player_index = same_role_players.index(player)
                    if player_index < len(role_positions):
                        reset_x, reset_y = role_positions[player_index]

                        # Reset player position AND target
                        player.x = reset_x
                        player.y = reset_y
                        player.target_x = reset_x
                        player.target_y = reset_y

                        # Stop player movement
                        player.velocity_x = 0.0
                        player.velocity_y = 0.0
                        player.action = "idle"

                except ValueError:
                    # Fallback: place at center
                    player.x = 0.0
                    player.y = 0.0
                    player.target_x = 0.0
                    player.target_y = 0.0
                    player.velocity_x = 0.0
                    player.velocity_y = 0.0
                    player.action = "idle"

    def _cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up game resources")
        pygame.quit()

    def _render_spectator_ui(self):
        """Render full spectator UI with debug information."""
        # Get representative players for UI info
        home_players = self.home_team.get_players()
        away_players = self.away_team.get_players()

        if home_players and away_players:
            self.ui_renderer.render_game_info(self.screen, self.ball, home_players[0], away_players[0])

        # Score display (prominent)
        score_text = self.goal_detector.get_score_string()
        score_surface = self.ui_renderer.font_large.render(score_text, True, (255, 255, 0))
        score_rect = score_surface.get_rect(center=(self.settings.display.width // 2, 40))

        # Goal celebration overlay
        if self.goal_detector.is_celebrating():
            last_goal = self.goal_detector.get_last_goal()
            if last_goal:
                goal_text = f"GOAL! {last_goal.scoring_team.upper()} TEAM SCORES!"
                goal_surface = self.ui_renderer.font_large.render(goal_text, True, (255, 0, 0))
                goal_rect = goal_surface.get_rect(center=(self.settings.display.width // 2, 80))
                self.screen.blit(goal_surface, goal_rect)

        self.screen.blit(score_surface, score_rect)

        # Spectator controls
        spectator_controls = [
            "SPECTATOR MODE - AI vs AI",
            f"Speed: {self.game_speed:.1f}x (+/- to change)",
            "SPACE - Pause/Resume",
            "R - Reset Match",
            "D - Toggle Debug Info",
            "ESC - Exit",
            "F11 - Fullscreen",
            "",
            f"Home Team: {self.home_team.formation_name} Formation",
            f"Away Team: {self.away_team.formation_name} Formation",
            f"Possession: {'Home' if self.home_team.in_possession else 'Away' if self.away_team.in_possession else 'Loose Ball'}"
        ]

        if self.paused:
            spectator_controls.insert(1, "*** PAUSED ***")

        y_offset = 10
        for i, text in enumerate(spectator_controls):
            if text == "":
                y_offset += 10
                continue

            color = (255, 255, 0) if i == 0 else (255, 0, 0) if "PAUSED" in text else (255, 255, 255)
            font = self.ui_renderer.font_medium if i == 0 else self.ui_renderer.font_small

            text_surface = font.render(text, True, color)
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 18

        # Ball indicator and field center
        self.ui_renderer.render_ball_indicator(self.screen, self.ball, self.field_renderer)
        self.ui_renderer.render_field_center_marker(self.screen, self.field_renderer)

    def _render_minimal_ui(self):
        """Render minimal UI for clean viewing."""
        # Score display (prominent)
        score_text = self.goal_detector.get_score_string()
        score_surface = self.ui_renderer.font_large.render(score_text, True, (255, 255, 0))
        score_rect = score_surface.get_rect(center=(self.settings.display.width // 2, 40))
        self.screen.blit(score_surface, score_rect)

        # Goal celebration overlay
        if self.goal_detector.is_celebrating():
            last_goal = self.goal_detector.get_last_goal()
            if last_goal:
                goal_text = f"GOAL! {last_goal.scoring_team.upper()} TEAM SCORES!"
                goal_surface = self.ui_renderer.font_large.render(goal_text, True, (255, 0, 0))
                goal_rect = goal_surface.get_rect(center=(self.settings.display.width // 2, 80))
                self.screen.blit(goal_surface, goal_rect)

        # Basic controls and pause state
        minimal_controls = []
        if self.paused:
            minimal_controls.append("*** PAUSED ***")
        minimal_controls.extend([
            f"Speed: {self.game_speed:.1f}x",
            "SPACE-Pause +/-Speed D-Debug ESC-Exit"
        ])

        y_offset = 10
        for i, text in enumerate(minimal_controls):
            color = (255, 0, 0) if "PAUSED" in text else (255, 255, 255)
            font = self.ui_renderer.font_small

            text_surface = font.render(text, True, color)
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 20

    def _check_dead_ball_kick(self):
        """Check if ball is completely stuck and give it a random kick."""
        if not hasattr(self, '_stuck_timer'):
            self._stuck_timer = 0.0
            self._last_ball_pos = self.ball.get_position()

        current_pos = self.ball.get_position()
        ball_speed = self.ball.get_speed()

        # Check if ball has barely moved
        distance_moved = math.sqrt(
            (current_pos[0] - self._last_ball_pos[0]) ** 2 +
            (current_pos[1] - self._last_ball_pos[1]) ** 2
        )

        if ball_speed < 0.1 and distance_moved < 0.5:
            self._stuck_timer += 1 / 60.0  # Assuming 60 FPS
        else:
            self._stuck_timer = 0.0
            self._last_ball_pos = current_pos

        # Check if any player is close enough to handle the ball naturally
        closest_player_distance = float('inf')
        for player in self.home_team.get_players() + self.away_team.get_players():
            distance = player.get_distance_to_ball_pos(current_pos[0], current_pos[1])
            closest_player_distance = min(closest_player_distance, distance)

    def _reset_match(self):
        """Reset the match to initial state."""
        self.logger.info("Resetting match...")

        # Reset ball to center
        self.ball.set_position(0.0, 0.0)
        self.ball.stop()

        # Recreate teams (resets positions and states)
        self.home_team = TeamManager("home", "4-4-2")
        self.away_team = TeamManager("away", "4-4-2")

        # Reset score and goals
        self.goal_detector.reset_match()

        # Reset game state
        self.paused = False
        self.game_speed = 1.0

        # Reset stuck timer
        if hasattr(self, '_stuck_timer'):
            self._stuck_timer = 0.0

        # Start the kick-off
        self._setup_initial_kickoff()

    def stop(self):
        """Stop the game engine."""
        self.running = False
