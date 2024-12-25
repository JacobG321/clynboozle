import pygame
from typing import Tuple, Optional

class ResponsiveLayout:
    def __init__(self, display_manager):
        self.display_manager = display_manager
        self.update_scale_factors()
    
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
        pygame.draw.rect(self.display_manager.screen, color, button_rect)
        
        font = self.get_font()
        text_surface = font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=button_rect.center)
        self.display_manager.screen.blit(text_surface, text_rect)
        
        return button_rect
    
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
        pygame.draw.rect(self.display_manager.screen, color, button_rect)
        
        font = self.get_font()
        text_surface = font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=button_rect.center)
        self.display_manager.screen.blit(text_surface, text_rect)
        
        return button_rect
    
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