"""
Pygame visualization and rendering for the LiDAR Visualizer
"""

import pygame
import math
import os
from .config import LIDAR_RESOLUTION, DECISIVE_FRAME_POSITIONS
from .ai_model import is_ai_model_loaded, get_ai_prediction


class VisualizationRenderer:
    """Handles pygame rendering and visualization"""
    
    def __init__(self, canvas_size=680):
        self.current_canvas_size = canvas_size
        self.screen = None
        self.clock = None
        self.font = None
        # Direction ratio configuration
        self.direction_ratio_max_degree = 45.0
        self.direction_ratio_max_angular = 1.0
        # Dynamic robot distances for circles and step indicator
        self.robot_distances = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]

    def update_robot_distances(self, data_manager=None):
        """Recalculate robot_distances based on current config step or data file/environment."""
        try:
            from .config import CO_CENTRIC_CIRCLE_STEP
            step = CO_CENTRIC_CIRCLE_STEP
            # Always use the user-defined step for co-centric circles
            min_dist = step
            max_dist = step * 10
            self.robot_distances = [round(min_dist * (i + 1), 3) for i in range(10)]
        except Exception:
            self.robot_distances = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]
    
    def init_pygame(self, canvas):
        """Initialize pygame with proper embedding"""
        try:
            # Get the tkinter canvas window ID for embedding
            canvas.update()
            
            # Set environment variables for pygame embedding
            embed_info = canvas.winfo_id()
            os.environ['SDL_WINDOWID'] = str(embed_info)
            if os.name == 'posix':  # Linux/Unix
                os.environ['SDL_VIDEODRIVER'] = 'x11'
            
            # Initialize pygame
            pygame.init()
            
            # Create pygame surface with dynamic size
            self.screen = pygame.display.set_mode([self.current_canvas_size, self.current_canvas_size])
            self.clock = pygame.time.Clock()
            
            # Initialize fonts - try different sizes for different uses
            try:
                self.font = pygame.font.Font(None, 24)  # Main font for labels
                self.small_font = pygame.font.Font(None, 18)  # Smaller font for distance markers
                self.title_font = pygame.font.Font(None, 32)  # Title font
            except:
                # Fallback to default font
                self.font = pygame.font.Font(None, 24)
                self.small_font = pygame.font.Font(None, 18)
                self.title_font = pygame.font.Font(None, 32)
            
            return True
        except Exception as e:
            print(f"Error initializing pygame: {e}")
            return False
    
    def update_canvas_size(self, new_size):
        """Update the pygame canvas size"""
        try:
            self.current_canvas_size = new_size
            if hasattr(self, 'screen') and self.screen:
                self.screen = pygame.display.set_mode([self.current_canvas_size, self.current_canvas_size])
        except Exception as e:
            print(f"Error updating pygame canvas size: {e}")
    
    def render_frame(self, distances, augmented_mode, prev_angular_velocity, 
                    show_current_vel, show_prev_vel, show_pred_vel, show_forward_dir,
                    data_manager, pred_turn_var):
        """Render the current lidar frame"""
        if not hasattr(self, 'screen') or not self.screen:
            print("ERROR: No pygame screen available for rendering!")
            return
            
        # Update robot_distances dynamically based on data_manager
        self.update_robot_distances(data_manager)

        # Fill background with dark theme
        self.screen.fill((45, 45, 45))  # Dark gray background

        # Calculate center and scale based on current canvas size
        center_x = self.current_canvas_size / 2
        center_y = self.current_canvas_size / 2 - 37  # Move visualization up by 37 pixels

        # Dynamic scale factor based on canvas size - import dynamically to get updated value
        from .config import SCALE_FACTOR
        dynamic_scale = SCALE_FACTOR * (self.current_canvas_size / 800)  # 800 is the original SCREEN_WIDTH

        # Draw polar coordinate grid
        self._draw_polar_grid(center_x, center_y, dynamic_scale)

        # Draw distance circles centered on robot
        self._draw_robot_distance_circles(center_x, center_y, dynamic_scale)

        # Render lidar points
        self._render_lidar_points(distances, center_x, center_y, dynamic_scale, augmented_mode)

        # Draw car
        self._draw_car(center_x, center_y)

        # Draw direction lines
        car_line_length = max(20, int(40 * (self.current_canvas_size / 800)))

        # Forward direction (blue line)
        if show_forward_dir:
            self._draw_forward_direction(center_x, center_y, car_line_length)

        # Current velocity (green line)
        if show_current_vel:
            self._draw_current_velocity(distances, center_x, center_y, car_line_length, augmented_mode)

        # Previous velocity (red line)
        if show_prev_vel:
            self._draw_previous_velocity(prev_angular_velocity, center_x, center_y, car_line_length, augmented_mode)

        # AI prediction (orange line)
        if show_pred_vel:
            self._draw_ai_prediction(distances, center_x, center_y, car_line_length, 
                                   augmented_mode, data_manager, pred_turn_var)
        else:
            # Update prediction text even when visualization is disabled
            self._update_prediction_text_only(distances, augmented_mode, data_manager, pred_turn_var)

        # Draw step indicator for co-centric circles in the bottom right corner
        self._draw_step_indicator(dynamic_scale)

        # Standard pygame display update
        pygame.display.flip()
        pygame.event.pump()
    def _draw_step_indicator(self, dynamic_scale):
        """Draw the step indicator for co-centric circles in the bottom right corner"""
        try:
            from .config import AUGMENTATION_UNIT, CO_CENTRIC_CIRCLE_STEP
            step_val_m = CO_CENTRIC_CIRCLE_STEP
            if AUGMENTATION_UNIT == "mm":
                step_val = int(step_val_m * 1000)
                step_text = f"Step: {step_val} mm"
            else:
                step_text = f"Step: {step_val_m:.3f} m"
            font_to_use = self.small_font if hasattr(self, 'small_font') and self.small_font else self.font
            if font_to_use:
                text_surface = font_to_use.render(step_text, True, (150, 150, 150))  # Gray
                text_rect = text_surface.get_rect()
                pad_x, pad_y = 12, 120
                x = self.current_canvas_size - text_rect.width - pad_x
                y = self.current_canvas_size - text_rect.height - pad_y
                self.screen.blit(text_surface, (x, y))
        except Exception:
            pass
    
    def _draw_robot_distance_circles(self, center_x, center_y, dynamic_scale):
        """Draw concentric circles centered on robot to show distance ranges"""
        max_radius = min(center_x, center_y) * 0.85  # Match the grid boundary

        # Colors for robot-centered distance circles (gray like in reference image)
        robot_circle_color = (120, 120, 120)  # Medium gray for regular circles
        robot_circle_major_color = (140, 140, 140)  # Slightly brighter gray for major circles
        label_color = (160, 160, 160)  # Light gray for labels

        # Use dynamic robot_distances
        major_distances = [0.5, 1.0, 1.5, 2.0]  # Major circles every 0.5m (can be improved to be dynamic too)

        # Draw robot-centered distance circles
        from .config import AUGMENTATION_UNIT
        for distance in self.robot_distances:
            # If unit is mm, convert to meters for visualization; if m, use as-is
            if AUGMENTATION_UNIT == "mm":
                radius = distance * 1000 * dynamic_scale
            else:
                radius = distance * dynamic_scale
            if radius <= max_radius and radius > 5:  # Make sure even small circles are visible
                # Use different styling for major vs minor circles
                is_major = distance in major_distances

                if is_major:
                    # Major circles - more visible
                    color = robot_circle_major_color
                    line_width = 2
                else:
                    # Minor circles - more subtle
                    color = robot_circle_color
                    line_width = 1

                # Draw the circle
                pygame.draw.circle(self.screen, color, (int(center_x), int(center_y)), int(radius), line_width)

                # Add distance labels for major circles only, positioned at 45° angle
                if is_major and hasattr(self, 'small_font') and self.small_font:
                    # Position label at 45 degrees (northeast)
                    label_angle = math.radians(45)
                    label_x = center_x + radius * math.cos(label_angle)
                    label_y = center_y - radius * math.sin(label_angle)

                    # Format distance label
                    label_text = f"{distance:.1f}m"

                    text_surface = self.small_font.render(label_text, True, label_color)
                    text_rect = text_surface.get_rect()

                    # Position the label slightly outside the circle
                    label_x -= text_rect.width // 2
                    label_y -= text_rect.height // 2

                    # Ensure label stays within screen bounds
                    label_x = max(5, min(label_x, self.current_canvas_size - text_rect.width - 5))
                    label_y = max(35, min(label_y, self.current_canvas_size - text_rect.height - 5))

                    # Add a subtle background for better readability
                    background_rect = pygame.Rect(label_x - 2, label_y - 1, text_rect.width + 4, text_rect.height + 2)
                    pygame.draw.rect(self.screen, (20, 20, 20), background_rect)

                    self.screen.blit(text_surface, (label_x, label_y))

    def _draw_title(self):
        """Draw the visualization title"""
        if hasattr(self, 'title_font') and self.title_font:
            title_text = "LiDAR Scan Data"
            text_surface = self.title_font.render(title_text, True, (200, 200, 200))
            text_rect = text_surface.get_rect()
            title_x = (self.current_canvas_size - text_rect.width) // 2
            title_y = 10
            self.screen.blit(text_surface, (title_x, title_y))

    def _draw_polar_grid(self, center_x, center_y, dynamic_scale):
        """Draw polar coordinate grid with distance circles and angle lines"""
        max_radius = min(center_x, center_y) * 0.85  # Use 85% of available space to leave room for labels
        
        # Grid colors
        grid_color = (70, 70, 70)  # Darker gray for grid lines
        major_grid_color = (100, 100, 100)  # Lighter gray for major grid lines
        label_color = (180, 180, 180)  # Brighter gray for labels
        
        # Calculate appropriate distance intervals based on scale
        # Determine what distance would fill about 80% of the display
        max_display_distance = max_radius / dynamic_scale * 0.8
        
        # Choose appropriate intervals
        if max_display_distance > 20:
            distance_intervals = [5, 10, 15, 20, 25, 30]
        elif max_display_distance > 10:
            distance_intervals = [2, 4, 6, 8, 10, 12, 14, 16]
        else:
            distance_intervals = [1, 2, 3, 4, 5, 6, 7, 8]
        
        # Draw concentric circles for distance indicators
        for i, distance in enumerate(distance_intervals):
            radius = distance * dynamic_scale
            if radius <= max_radius:
                # Use major grid color for every other circle
                color = major_grid_color if i % 2 == 1 else grid_color
                line_width = 2 if i % 2 == 1 else 1
                pygame.draw.circle(self.screen, color, (int(center_x), int(center_y)), int(radius), line_width)
                
                # Draw distance labels using smaller font
                font_to_use = self.small_font if hasattr(self, 'small_font') and self.small_font else self.font
                if font_to_use and i % 2 == 1:  # Only label major circles
                    label_text = f"{distance}m"
                    text_surface = font_to_use.render(label_text, True, label_color)
                    text_rect = text_surface.get_rect()
                    label_x = center_x + radius - text_rect.width // 2
                    label_y = center_y - text_rect.height // 2 - 3
                    if label_x > 5 and label_y > 35 and label_x + text_rect.width < self.current_canvas_size - 5:
                        self.screen.blit(text_surface, (label_x, label_y))
        
        # Draw radial lines for angle indicators
        angles = [0, 45, 90, 135, 180, 225, 270, 315]  # Degrees
        for i, angle in enumerate(angles):
            angle_rad = math.radians(angle)
            end_x = center_x + max_radius * math.cos(angle_rad)
            end_y = center_y - max_radius * math.sin(angle_rad)  # Negative because pygame y-axis is flipped
            
            # Use major grid color for cardinal directions (0°, 90°, 180°, 270°)
            color = major_grid_color if angle % 90 == 0 else grid_color
            line_width = 2 if angle % 90 == 0 else 1
            pygame.draw.line(self.screen, color, (center_x, center_y), (end_x, end_y), line_width)
            
            # Draw angle labels
            font_to_use = self.small_font if hasattr(self, 'small_font') and self.small_font else self.font
            if font_to_use:
                label_text = f"{angle}°"
                text_surface = font_to_use.render(label_text, True, label_color)
                text_rect = text_surface.get_rect()
                
                # Position labels slightly outside the grid
                label_radius = max_radius + 25
                label_x = center_x + label_radius * math.cos(angle_rad) - text_rect.width // 2
                label_y = center_y - label_radius * math.sin(angle_rad) - text_rect.height // 2
                
                # Ensure labels stay within screen bounds
                label_x = max(5, min(label_x, self.current_canvas_size - text_rect.width - 5))
                label_y = max(35, min(label_y, self.current_canvas_size - text_rect.height - 5))  # Account for title
                
                self.screen.blit(text_surface, (label_x, label_y))

    def _render_lidar_points(self, distances, center_x, center_y, dynamic_scale, augmented_mode):
        """Render the lidar points"""
        for x in range(LIDAR_RESOLUTION):
            try:
                distance_value = float(distances[x])
                if math.isinf(distance_value) or math.isnan(distance_value) or distance_value <= 0:
                    continue
            except (ValueError, TypeError):
                continue
                
            a = distance_value * dynamic_scale
            
            # Use standard coordinates - the data itself has been flipped if needed
            x_coord = math.cos(x / 180 * math.pi) * a + center_x
            y_coord = -math.sin(x / 180 * math.pi) * a + center_y
            
            if x in DECISIVE_FRAME_POSITIONS:
                # Draw line and important point - magenta for decisive positions
                pygame.draw.line(self.screen, (255, 120, 255), (center_x, center_y),
                               (x_coord, y_coord), 2)
                
                # Get decisive point radii from config
                from .config import DECISIVE_POINT_RADIUS, DECISIVE_POINT_CENTER_RADIUS
                pygame.draw.circle(self.screen, (255, 80, 80), (x_coord, y_coord), DECISIVE_POINT_RADIUS)
                # Add a bright center dot
                pygame.draw.circle(self.screen, (255, 200, 200), (x_coord, y_coord), DECISIVE_POINT_CENTER_RADIUS)
            else:
                # Regular LiDAR points in bright green with better visibility
                from .config import NORMAL_POINT_RADIUS, NORMAL_POINT_CENTER_RADIUS
                pygame.draw.circle(self.screen, (100, 255, 100), (x_coord, y_coord), NORMAL_POINT_RADIUS)
                # Add a darker center for better definition
                pygame.draw.circle(self.screen, (50, 200, 50), (x_coord, y_coord), NORMAL_POINT_CENTER_RADIUS)
    
    def _draw_car(self, center_x, center_y):
        """Draw the car representation"""
        car_radius = max(8, int(16 * (self.current_canvas_size / 800)))
        # Draw car as orange circle with black outline
        pygame.draw.circle(self.screen, (255, 140, 0), (center_x, center_y), car_radius)
        pygame.draw.circle(self.screen, (200, 200, 200), (center_x, center_y), car_radius, 2)
    
    def _draw_forward_direction(self, center_x, center_y, car_line_length):
        """Draw forward direction line (bright blue)"""
        pygame.draw.line(self.screen, (100, 150, 255), (center_x, center_y),
                        (center_x + car_line_length, center_y), 4)
    
    def _draw_current_velocity(self, distances, center_x, center_y, car_line_length, augmented_mode):
        """Draw current velocity direction line (bright green)"""
        try:
            turn_value = float(distances[360])
            if augmented_mode:
                turn_value = -turn_value
            
            # Apply configurable direction ratio mapping
            angle_degrees = (turn_value / self.direction_ratio_max_angular) * self.direction_ratio_max_degree
            angle_radians = angle_degrees * math.pi / 180
            
            x = math.cos(angle_radians) * car_line_length
            y = math.sin(angle_radians) * car_line_length
            
            pygame.draw.line(self.screen, (100, 255, 100), (center_x, center_y),
                           (center_x + x, center_y - y), 4)
        except (ValueError, TypeError):
            pass
    
    def _draw_previous_velocity(self, prev_angular_velocity, center_x, center_y, car_line_length, augmented_mode):
        """Draw previous velocity direction line (bright red)"""
        try:
            prev_turn_value = prev_angular_velocity
            if augmented_mode:
                prev_turn_value = -prev_turn_value
                
            # Apply configurable direction ratio mapping
            prev_angle_degrees = (prev_turn_value / self.direction_ratio_max_angular) * self.direction_ratio_max_degree
            prev_angle_radians = prev_angle_degrees * math.pi / 180
            
            prev_x = math.cos(prev_angle_radians) * car_line_length
            prev_y = math.sin(prev_angle_radians) * car_line_length
            
            pygame.draw.line(self.screen, (255, 100, 100), (center_x, center_y),
                           (center_x + prev_x, center_y - prev_y), 3)
        except (ValueError, TypeError):
            pass
    
    def _draw_ai_prediction(self, distances, center_x, center_y, car_line_length, 
                          augmented_mode, data_manager, pred_turn_var):
        """Draw AI prediction direction line (bright orange)"""
        try:
            if is_ai_model_loaded():
                # Get AI prediction for current frame
                current_frame = data_manager.pointer
                ai_prediction = get_ai_prediction(distances[:360], current_frame)
                
                if ai_prediction is not None:
                    ai_turn_value = float(ai_prediction)
                    if augmented_mode:
                        ai_turn_value = -ai_turn_value
                    
                    # Update AI prediction display
                    pred_turn_var.set(f"{ai_turn_value:.2f}")
                    
                    # Apply configurable direction ratio mapping
                    ai_angle_degrees = (ai_turn_value / self.direction_ratio_max_angular) * self.direction_ratio_max_degree
                    ai_angle_radians = ai_angle_degrees * math.pi / 180
                    
                    ai_x = math.cos(ai_angle_radians) * car_line_length
                    ai_y = math.sin(ai_angle_radians) * car_line_length
                    
                    pygame.draw.line(self.screen, (255, 200, 100), (center_x, center_y),
                                   (center_x + ai_x, center_y - ai_y), 4)
                else:
                    pred_turn_var.set("--")
            else:
                pred_turn_var.set("--")
        except (ValueError, TypeError, Exception):
            pred_turn_var.set("--")
    
    def _update_prediction_text_only(self, distances, augmented_mode, data_manager, pred_turn_var):
        """Update AI prediction text when visualization is disabled"""
        try:
            if is_ai_model_loaded():
                current_frame = data_manager.pointer
                ai_prediction = get_ai_prediction(distances[:360], current_frame)
                if ai_prediction is not None:
                    ai_turn_value = float(ai_prediction)
                    if augmented_mode:
                        ai_turn_value = -ai_turn_value
                    pred_turn_var.set(f"{ai_turn_value:.2f}")
                else:
                    pred_turn_var.set("--")
            else:
                pred_turn_var.set("--")
        except:
            pred_turn_var.set("--")
    
    def set_direction_ratio(self, max_degree, max_angular):
        """Set the direction ratio configuration"""
        self.direction_ratio_max_degree = max_degree
        self.direction_ratio_max_angular = max_angular
    
    def cleanup(self):
        """Cleanup pygame resources"""
        try:
            if hasattr(self, 'screen') and self.screen:
                pygame.quit()
        except Exception as e:
            print(f"Error cleaning up pygame: {e}")
