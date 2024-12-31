import pygame
from typing import Tuple, Dict

class DisplayManager:
    def __init__(self):
        # Get the display info
        display_info = pygame.display.Info()
        self.native_width = display_info.current_w
        self.native_height = display_info.current_h
        
        # Base design resolution (what you're currently using)
        self.base_width = 800
        self.base_height = 600
        
        # Set initial scale factors
        self.scale_x = 1.0
        self.scale_y = 1.0
        
        # Initialize the display
        self.update_display_size()
    
    def update_display_size(self, custom_width=None, custom_height=None):
        """Update the display size and scaling factors."""
        if custom_width and custom_height:
            self.current_width = custom_width
            self.current_height = custom_height
        else:
            # Default to 80% of screen size if no custom size
            self.current_width = int(self.native_width * 0.8)
            self.current_height = int(self.native_height * 0.8)
        
        # Update scale factors
        self.scale_x = self.current_width / self.base_width
        self.scale_y = self.current_height / self.base_height
        
        # Set the new display mode
        self.screen = pygame.display.set_mode((self.current_width, self.current_height), pygame.RESIZABLE)
        return self.screen
    
    def scale_rect(self, rect: pygame.Rect) -> pygame.Rect:
        """Scale a rectangle according to current display size."""
        return pygame.Rect(
            rect.x * self.scale_x,
            rect.y * self.scale_y,
            rect.width * self.scale_x,
            rect.height * self.scale_y
        )
    
    def scale_pos(self, x: float, y: float) -> Tuple[float, float]:
        """Scale a position according to current display size."""
        return (x * self.scale_x, y * self.scale_y)
    
    def unscale_pos(self, x: float, y: float) -> Tuple[float, float]:
        """Convert screen coordinates back to design coordinates."""
        return (x / self.scale_x, y / self.scale_y)
    
    def get_scaled_font(self, base_size: int) -> pygame.font.Font:
        """Get a font scaled to current display size."""
        scaled_size = int(base_size * min(self.scale_x, self.scale_y))
        return pygame.font.Font(None, scaled_size)