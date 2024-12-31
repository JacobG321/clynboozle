import pygame
from typing import Tuple, Optional

class ResponsiveLayout:
    def __init__(self, display_manager):
        self.display_manager = display_manager
        self.update_scale_factors()
        # Track mouse state
        self.mouse_pos = (0, 0)
        self.mouse_pressed = False
    
    def update_scale_factors(self):
        """Update scale factors based on current screen dimensions"""
        self.screen_width = self.display_manager.current_width
        self.screen_height = self.display_manager.current_height
        
        # Calculate base font sizes relative to screen height
        self.base_font_size = int(self.screen_height * 0.04)  # 4% of screen height
        self.small_font_size = int(self.base_font_size * 0.75)
    
    def get_font(self, size_multiplier: float = 1.0) -> pygame.font.Font:
        """Get a scaled font based on screen size"""
        return pygame.font.Font(None, int(self.base_font_size * size_multiplier))
    
    def update_mouse_state(self, pos, pressed):
        """Update current mouse position and state"""
        # Scale the mouse position to match our coordinate system
        scaled_x, scaled_y = self.display_manager.unscale_pos(pos[0], pos[1])
        self.mouse_pos = (scaled_x, scaled_y)
        self.mouse_pressed = pressed
        
        # Store previous frame's press state to detect transitions
        if not hasattr(self, 'prev_pressed'):
            self.prev_pressed = False
            
        # Detect press and release events
        self.just_pressed = pressed and not self.prev_pressed
        self.just_released = not pressed and self.prev_pressed
        self.prev_pressed = pressed
    
    def adjust_color(self, color: Tuple[int, int, int], amount: int) -> Tuple[int, int, int]:
        """Lighten or darken a color by the given amount"""
        return tuple(min(255, max(0, c + amount)) for c in color)
    
    def draw_button(self, rect: pygame.Rect, color: Tuple[int, int, int], 
                    text: str, text_color: Tuple[int, int, int],
                    pressed: bool = False, hovered: bool = False):
        """Draw a button with enhanced hover and press effects"""
        SHADOW_OFFSET = 4
        PRESS_OFFSET = 3
        
        # Original position for reference
        original_y = rect.y
        
        # Shadow effect (only when not pressed)
        if not pressed:
            shadow_rect = rect.copy()
            shadow_rect.y += SHADOW_OFFSET
            pygame.draw.rect(self.display_manager.screen, (0, 0, 0, 128), 
                            shadow_rect, border_radius=8)
        
        # Button background
        button_rect = rect.copy()
        if pressed:
            button_rect.y += PRESS_OFFSET  # Move down when pressed
            button_color = self.adjust_color(color, -40)  # Darker when pressed
            # Add a darker inner shadow when pressed
            inner_shadow = button_rect.copy()
            inner_shadow.y -= 1
            pygame.draw.rect(self.display_manager.screen, 
                            self.adjust_color(color, -60),
                            inner_shadow, border_radius=8)
        elif hovered:
            button_color = self.adjust_color(color, 30)  # Lighter when hovered
            # Add a subtle glow effect when hovered
            glow_rect = button_rect.copy()
            glow_rect.inflate_ip(4, 4)
            pygame.draw.rect(self.display_manager.screen, 
                            self.adjust_color(color, 50),
                            glow_rect, border_radius=10)
        else:
            button_color = color
        
        # Draw the main button
        pygame.draw.rect(self.display_manager.screen, button_color, 
                        button_rect, border_radius=8)
        
        # Add a subtle top highlight for 3D effect
        highlight_rect = button_rect.copy()
        highlight_rect.height = 2
        pygame.draw.rect(self.display_manager.screen,
                        self.adjust_color(button_color, 30),
                        highlight_rect, border_radius=8)
        
        # Text with shadow
        font = self.get_font()
        if pressed:
            text_color = self.adjust_color(text_color, -30)
        text_surface = font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=button_rect.center)
        
        # Draw text shadow when not pressed
        if not pressed:
            shadow_text_rect = text_rect.copy()
            shadow_text_rect.y += 1
            shadow_surface = font.render(text, True, (0, 0, 0, 128))
            self.display_manager.screen.blit(shadow_surface, shadow_text_rect)
        
        # Draw main text
        self.display_manager.screen.blit(text_surface, text_rect)
        
        return button_rect
    
    def create_centered_button(self, 
                             y_percent: float, 
                             width_percent: float, 
                             height_percent: float, 
                             color: Tuple[int, int, int], 
                             text: str, 
                             text_color: Tuple[int, int, int] = (255, 255, 255)) -> pygame.Rect:
        """Create a button centered horizontally at given vertical position"""
        width = int(self.screen_width * width_percent)
        height = int(self.screen_height * height_percent)
        y = int(self.screen_height * y_percent)
        x = int((self.screen_width - width) / 2)
        
        button_rect = pygame.Rect(x, y, width, height)
        
        # Check if mouse is over button
        hovered = button_rect.collidepoint(self.mouse_pos)
        pressed = hovered and self.mouse_pressed
        
        return self.draw_button(button_rect, color, text, text_color, pressed, hovered)
    
    def create_positioned_button(self,
                               x_percent: float,
                               y_percent: float,
                               width_percent: float,
                               height_percent: float,
                               color: Tuple[int, int, int],
                               text: str,
                               text_color: Tuple[int, int, int] = (255, 255, 255)) -> pygame.Rect:
        """Create a button at specific position using percentages"""
        width = int(self.screen_width * width_percent)
        height = int(self.screen_height * height_percent)
        x = int(self.screen_width * x_percent)
        y = int(self.screen_height * y_percent)
        
        button_rect = pygame.Rect(x, y, width, height)
        
        # Check if mouse is over button
        hovered = button_rect.collidepoint(self.mouse_pos)
        pressed = hovered and self.mouse_pressed
        
        return self.draw_button(button_rect, color, text, text_color, pressed, hovered)
    
    def draw_text_centered(self, 
                          y_percent: float, 
                          text: str, 
                          color: Tuple[int, int, int] = (0, 0, 0),
                          size_multiplier: float = 1.0):
        """Draw centered text at given vertical position"""
        font = self.get_font(size_multiplier)
        text_surface = font.render(text, True, color)
        x = (self.screen_width - text_surface.get_width()) / 2
        y = self.screen_height * y_percent
        self.display_manager.screen.blit(text_surface, (x, y))
    
    def create_input_field(self,
                          y_percent: float,
                          width_percent: float,
                          height_percent: float,
                          text: str = '',
                          label: Optional[str] = None) -> pygame.Rect:
        """Create a centered input field with optional label"""
        width = int(self.screen_width * width_percent)
        height = int(self.screen_height * height_percent)
        x = int((self.screen_width - width) / 2)
        y = int(self.screen_height * y_percent)
        
        input_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.display_manager.screen, (128, 128, 128), input_rect)
        
        if label:
            font = self.get_font(0.75)
            label_surface = font.render(label, True, (0, 0, 0))
            label_y = y - label_surface.get_height() - 5
            self.display_manager.screen.blit(label_surface, (x, label_y))
        
        if text:
            font = self.get_font()
            text_surface = font.render(text, True, (0, 0, 0))
            text_rect = text_surface.get_rect(center=input_rect.center)
            self.display_manager.screen.blit(text_surface, text_rect)
        
        return input_rect
    
    def create_grid_buttons(self,
                          items: list,
                          start_y_percent: float,
                          button_width_percent: float,
                          button_height_percent: float,
                          color: Tuple[int, int, int],
                          spacing_percent: float = 0.02) -> list:
        """Create a grid of buttons with text from items list"""
        buttons = []
        current_x_percent = spacing_percent
        current_y_percent = start_y_percent
        
        for item in items:
            # Check if we need to start a new row
            if current_x_percent + button_width_percent > 1.0:
                current_x_percent = spacing_percent
                current_y_percent += button_height_percent + spacing_percent
            
            button_rect = self.create_positioned_button(
                current_x_percent,
                current_y_percent,
                button_width_percent,
                button_height_percent,
                color,
                str(item)
            )
            buttons.append((button_rect, item))
            
            current_x_percent += button_width_percent + spacing_percent
        
        return buttons