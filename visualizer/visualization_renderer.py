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
            self.font = pygame.font.Font(None, 32)
            
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
            
        try:
            # Fill background
            self.screen.fill((250, 250, 250))
            
            # Calculate center and scale based on current canvas size
            center_x = self.current_canvas_size / 2
            center_y = self.current_canvas_size / 2
            
            # Dynamic scale factor based on canvas size - import dynamically to get updated value
            from .config import SCALE_FACTOR
            dynamic_scale = SCALE_FACTOR * (self.current_canvas_size / 800)  # 800 is the original SCREEN_WIDTH
            
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
            
            # Standard pygame display update
            pygame.display.flip()
            pygame.event.pump()
                
        except Exception as e:
            print(f"Error rendering frame: {e}")
            import traceback
            traceback.print_exc()
    
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
                # Draw line and important point
                pygame.draw.line(self.screen, (255, 0, 255), (center_x, center_y),
                               (x_coord, y_coord), 2)
                pygame.draw.circle(self.screen, (255, 0, 0), (x_coord, y_coord), 3)
            else:
                pygame.draw.circle(self.screen, (0, 0, 0), (x_coord, y_coord), 2)
    
    def _draw_car(self, center_x, center_y):
        """Draw the car representation"""
        car_radius = max(6, int(12 * (self.current_canvas_size / 800)))
        pygame.draw.circle(self.screen, (252, 132, 3), (center_x, center_y), car_radius)
    
    def _draw_forward_direction(self, center_x, center_y, car_line_length):
        """Draw forward direction line (blue)"""
        pygame.draw.line(self.screen, (0, 0, 255), (center_x, center_y),
                        (center_x + car_line_length, center_y), 3)
    
    def _draw_current_velocity(self, distances, center_x, center_y, car_line_length, augmented_mode):
        """Draw current velocity direction line (green)"""
        try:
            turn_value = float(distances[360])
            if augmented_mode:
                turn_value = -turn_value
            
            # Apply configurable direction ratio mapping
            angle_degrees = (turn_value / self.direction_ratio_max_angular) * self.direction_ratio_max_degree
            angle_radians = angle_degrees * math.pi / 180
            
            x = math.cos(angle_radians) * car_line_length
            y = math.sin(angle_radians) * car_line_length
            
            pygame.draw.line(self.screen, (0, 255, 0), (center_x, center_y),
                           (center_x + x, center_y - y), 3)
        except (ValueError, TypeError):
            pass
    
    def _draw_previous_velocity(self, prev_angular_velocity, center_x, center_y, car_line_length, augmented_mode):
        """Draw previous velocity direction line (red)"""
        try:
            prev_turn_value = prev_angular_velocity
            if augmented_mode:
                prev_turn_value = -prev_turn_value
                
            # Apply configurable direction ratio mapping
            prev_angle_degrees = (prev_turn_value / self.direction_ratio_max_angular) * self.direction_ratio_max_degree
            prev_angle_radians = prev_angle_degrees * math.pi / 180
            
            prev_x = math.cos(prev_angle_radians) * car_line_length
            prev_y = math.sin(prev_angle_radians) * car_line_length
            
            pygame.draw.line(self.screen, (255, 0, 0), (center_x, center_y),
                           (center_x + prev_x, center_y - prev_y), 2)
        except (ValueError, TypeError):
            pass
    
    def _draw_ai_prediction(self, distances, center_x, center_y, car_line_length, 
                          augmented_mode, data_manager, pred_turn_var):
        """Draw AI prediction direction line (orange)"""
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
                    
                    pygame.draw.line(self.screen, (255, 165, 0), (center_x, center_y),
                                   (center_x + ai_x, center_y - ai_y), 3)
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
