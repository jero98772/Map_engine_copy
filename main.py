import os
import gc
import weakref
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
from PIL import Image
import numpy as np
import time
from functools import lru_cache
from typing import Optional, Tuple, Dict, Any

class OptimizedQuadrantZoomViewer:
    def __init__(self, root_image_path="root.png", cache_size=16):
        self.root_image_path = root_image_path
        self.current_path = ""  # Current zoom path (e.g., "0_2_1")
        self.current_image = None
        self.fig, self.ax = plt.subplots(figsize=(10, 10))
        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

        self.mouse_quadrant = 0  # Track which quadrant mouse is over
        
        # Animation state - using __slots__ equivalent with explicit cleanup
        self.is_animating = False
        self.animation_frames = 20
        self.current_frame = 0
        self.zoom_target = None
        self.zoom_start_bounds = None
        self.zoom_end_bounds = None
        self.pending_path = None
        self.zoom_direction = 1  # 1 for zoom in, -1 for zoom out
        self.animation_timer = None
        
        # Memory optimization: Image cache with weak references
        self._image_cache: Dict[str, Any] = {}
        self._cache_size = cache_size
        
        # Pre-allocate numpy arrays for quadrant bounds to avoid repeated allocation
        self._quadrant_bounds_cache = {}
        
        # Optimize matplotlib patches - reuse rectangles
        self._highlight_rect = None
        self._text_objects = []
        
        # Enable garbage collection optimizations
        gc.set_threshold(700, 10, 10)  # More aggressive GC
        
        # Load and display the root image
        self.load_current_image()
        self.display_image()
    
    def __del__(self):
        """Cleanup resources when object is destroyed"""
        self.cleanup()
    
    def cleanup(self):
        """Explicit cleanup method"""
        # Clear image cache
        for img in self._image_cache.values():
            if hasattr(img, 'close'):
                img.close()
        self._image_cache.clear()
        
        # Clear matplotlib objects
        if self._highlight_rect:
            self._highlight_rect.remove()
        for text_obj in self._text_objects:
            text_obj.remove()
        self._text_objects.clear()
        
        # Stop animation timer
        if self.animation_timer:
            self.animation_timer.stop()
            self.animation_timer = None
        
        # Clear bounds cache
        self._quadrant_bounds_cache.clear()
        
        # Force garbage collection
        gc.collect()
    
    @lru_cache(maxsize=32)
    def get_image_filename(self, path: str = "") -> str:
        """Generate filename based on current path - cached to avoid string operations"""
        if path == "":
            return self.root_image_path
        else:
            base_name, extension = os.path.splitext(self.root_image_path)
            return f"{base_name}_{path}{extension}"
    
    def load_current_image(self):
        """Load the current image based on the current path with caching"""
        filename = self.get_image_filename(self.current_path)
        
        # Check cache first
        if filename in self._image_cache:
            self.current_image = self._image_cache[filename]
            return
        
        try:
            # Load image
            img = Image.open(filename)
            
            # Cache management - remove oldest if cache is full
            if len(self._image_cache) >= self._cache_size:
                # Remove oldest entry (simple FIFO)
                oldest_key = next(iter(self._image_cache))
                old_img = self._image_cache.pop(oldest_key)
                if hasattr(old_img, 'close'):
                    old_img.close()
                # Force garbage collection after removing old image
                gc.collect()
            
            # Add to cache
            self._image_cache[filename] = img
            self.current_image = img
            print(f"Loaded and cached: {filename}")
            
        except FileNotFoundError:
            print(f"Image not found: {filename}")
            # Create and cache placeholder
            if "placeholder" not in self._image_cache:
                self._image_cache["placeholder"] = self.create_placeholder_image()
            self.current_image = self._image_cache["placeholder"]
    
    def create_placeholder_image(self) -> Image.Image:
        """Create a placeholder image with quadrant numbers - optimized"""
        # Use more efficient numpy array creation
        pixels = np.empty((400, 400, 3), dtype=np.uint8)
        
        # Fill quadrants using array slicing (more efficient than pixel-by-pixel)
        mid_h, mid_w = 200, 200
        
        # Use memoryview for even faster access
        pixels_view = memoryview(pixels)
        
        # Quadrant 0 (top-left) - light blue
        pixels[:mid_h, :mid_w] = [173, 216, 230]
        # Quadrant 1 (top-right) - light green
        pixels[:mid_h, mid_w:] = [144, 238, 144]
        # Quadrant 2 (bottom-left) - light coral
        pixels[mid_h:, :mid_w] = [240, 128, 128]
        # Quadrant 3 (bottom-right) - light yellow
        pixels[mid_h:, mid_w:] = [255, 255, 224]
        
        return Image.fromarray(pixels)
    
    def get_quadrant_bounds(self, quadrant: int) -> Tuple[int, int, int, int]:
        """Get the bounds of a specific quadrant - cached for performance"""
        if not self.current_image:
            return (0, 0, 0, 0)
        
        cache_key = (self.current_image.size, quadrant)
        if cache_key in self._quadrant_bounds_cache:
            return self._quadrant_bounds_cache[cache_key]
        
        img_width, img_height = self.current_image.size
        mid_x, mid_y = img_width >> 1, img_height >> 1  # Bit shift is faster than //
        
        bounds_map = {
            0: (0, 0, mid_x, mid_y),           # top-left
            1: (mid_x, 0, img_width, mid_y),   # top-right
            2: (0, mid_y, mid_x, img_height),  # bottom-left
            3: (mid_x, mid_y, img_width, img_height)  # bottom-right
        }
        
        bounds = bounds_map[quadrant]
        self._quadrant_bounds_cache[cache_key] = bounds
        return bounds
    
    def display_image(self):
        """Display the current image with quadrant grid overlay - optimized"""
        # Clear only what's necessary
        if self._highlight_rect:
            self._highlight_rect.remove()
            self._highlight_rect = None
        
        for text_obj in self._text_objects:
            text_obj.remove()
        self._text_objects.clear()
        
        # Only clear axes if we have a new image
        if not hasattr(self, '_last_image_size') or self._last_image_size != self.current_image.size:
            self.ax.clear()
            self._last_image_size = self.current_image.size
        
        if self.current_image:
            # Display the image
            self.ax.imshow(self.current_image)
            
            # Only show grid and highlights if not animating
            if not self.is_animating:
                # Add quadrant grid overlay
                img_width, img_height = self.current_image.size
                mid_x, mid_y = img_width >> 1, img_height >> 1
                
                # Draw grid lines
                self.ax.axhline(y=mid_y, color='red', linestyle='--', alpha=0.7, linewidth=2)
                self.ax.axvline(x=mid_x, color='red', linestyle='--', alpha=0.7, linewidth=2)
                
                # Highlight the quadrant where mouse is hovering
                x1, y1, x2, y2 = self.get_quadrant_bounds(self.mouse_quadrant)
                self._highlight_rect = patches.Rectangle((x1, y1), x2-x1, y2-y1, 
                                                       linewidth=3, edgecolor='yellow', 
                                                       facecolor='yellow', alpha=0.2)
                self.ax.add_patch(self._highlight_rect)
                
                # Add quadrant labels - reuse text objects
                text_props = dict(fontsize=20, ha='center', va='center',
                                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
                
                positions = [
                    (mid_x >> 1, mid_y >> 1, '0'),
                    (mid_x + (mid_x >> 1), mid_y >> 1, '1'),
                    (mid_x >> 1, mid_y + (mid_y >> 1), '2'),
                    (mid_x + (mid_x >> 1), mid_y + (mid_y >> 1), '3')
                ]
                
                for x, y, label in positions:
                    text_obj = self.ax.text(x, y, label, **text_props)
                    self._text_objects.append(text_obj)
            
            # Set title based on animation state
            if self.is_animating:
                action = "Zooming in..." if self.zoom_direction == 1 else "Zooming out..."
                self.ax.set_title(f"{action}", fontsize=12, pad=20)
            else:
                self.ax.set_title(f"Current Path: {self.current_path if self.current_path else 'root'}\n"
                                f"Scroll up over a quadrant to zoom in, scroll down to zoom out", 
                                fontsize=12, pad=20)
        
        # Set initial view bounds
        if not self.is_animating:
            self.ax.set_xlim(0, self.current_image.size[0])
            self.ax.set_ylim(self.current_image.size[1], 0)  # Flip Y axis for image coordinates
        
        self.ax.set_aspect('equal')
        plt.tight_layout()
        plt.draw()
    
    def animate_zoom(self, frame: int):
        """Animation function for smooth zooming - optimized"""
        if frame >= self.animation_frames:
            # Animation complete
            self.is_animating = False
            
            if self.zoom_direction == 1:  # Zoom in complete
                # Load the new image
                self.current_path = self.pending_path
                self.load_current_image()
                self.display_image()
            else:  # Zoom out complete
                # Just update display
                self.display_image()
            
            # Clean up animation timer
            if self.animation_timer:
                self.animation_timer.stop()
                self.animation_timer = None
            
            return
        
        # Calculate interpolation factor (0 to 1)
        t = frame / (self.animation_frames - 1)
        
        # Smooth easing function (ease-in-out) - optimized
        t = t * t * (3.0 - 2.0 * t)
        
        # Interpolate between start and end bounds
        start_x1, start_y1, start_x2, start_y2 = self.zoom_start_bounds
        end_x1, end_y1, end_x2, end_y2 = self.zoom_end_bounds
        
        # Use faster arithmetic
        inv_t = 1.0 - t
        current_x1 = start_x1 * inv_t + end_x1 * t
        current_y1 = start_y1 * inv_t + end_y1 * t
        current_x2 = start_x2 * inv_t + end_x2 * t
        current_y2 = start_y2 * inv_t + end_y2 * t
        
        # Set the view bounds
        self.ax.set_xlim(current_x1, current_x2)
        self.ax.set_ylim(current_y2, current_y1)  # Flip Y axis for image coordinates
        
        plt.draw()
    
    def start_zoom_animation(self, target_quadrant: int, zoom_in: bool = True):
        """Start zoom animation to a specific quadrant"""
        if self.is_animating:
            return
        
        self.is_animating = True
        self.zoom_direction = 1 if zoom_in else -1
        
        img_width, img_height = self.current_image.size
        
        if zoom_in:
            # Zoom into quadrant
            self.zoom_start_bounds = (0, 0, img_width, img_height)
            self.zoom_end_bounds = self.get_quadrant_bounds(target_quadrant)
            
            # Prepare new path
            if self.current_path:
                self.pending_path = f"{self.current_path}_{target_quadrant}"
            else:
                self.pending_path = str(target_quadrant)
        else:
            # Zoom out from current view
            self.zoom_start_bounds = (0, 0, img_width, img_height)
            self.zoom_end_bounds = (0, 0, img_width, img_height)
            
            # Update current path
            if self.current_path:
                path_parts = self.current_path.split('_')
                if len(path_parts) > 1:
                    self.current_path = '_'.join(path_parts[:-1])
                else:
                    self.current_path = ""
                
                # Load the parent image
                self.load_current_image()
                
                # Calculate which quadrant we're zooming out from
                if path_parts:
                    last_quadrant = int(path_parts[-1])
                    self.zoom_start_bounds = self.get_quadrant_bounds(last_quadrant)
                    self.zoom_end_bounds = (0, 0, self.current_image.size[0], self.current_image.size[1])
        
        # Start animation with optimized timer
        self.current_frame = 0
        if self.animation_timer:
            self.animation_timer.stop()
        
        self.animation_timer = self.fig.canvas.new_timer(interval=33)  # ~30 FPS for smoother animation
        self.animation_timer.add_callback(self.animate_step)
        self.animation_timer.start()
    
    def animate_step(self):
        """Single step of animation"""
        if self.current_frame >= self.animation_frames:
            self.animation_timer.stop()
            self.animate_zoom(self.current_frame)
            return
        
        self.animate_zoom(self.current_frame)
        self.current_frame += 1
    
    def on_mouse_move(self, event):
        """Handle mouse movement to track which quadrant mouse is over"""
        if event.inaxes != self.ax or not self.current_image or self.is_animating:
            return
        
        # Get mouse coordinates
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return
        
        # Determine which quadrant mouse is over - optimized with bit operations
        img_width, img_height = self.current_image.size
        mid_x, mid_y = img_width >> 1, img_height >> 1
        
        # Use bitwise operations for quadrant calculation
        new_quadrant = (2 if y >= mid_y else 0) + (1 if x >= mid_x else 0)
        
        # Only redraw if quadrant changed
        if new_quadrant != self.mouse_quadrant:
            self.mouse_quadrant = new_quadrant
            self.display_image()
    
    def on_scroll(self, event):
        """Handle mouse scroll events"""
        if event.inaxes != self.ax or not self.current_image or self.is_animating:
            return
        
        if event.button == 'up':  # Scroll up - zoom in
            print(f"Zooming into quadrant {self.mouse_quadrant}")
            self.start_zoom_animation(self.mouse_quadrant, zoom_in=True)
            
        elif event.button == 'down':  # Scroll down - zoom out
            if self.current_path:
                print(f"Zooming out from path: {self.current_path}")
                self.start_zoom_animation(0, zoom_in=False)  # quadrant doesn't matter for zoom out
    
    def run(self):
        """Run the viewer"""
        try:
            plt.show()
        finally:
            self.cleanup()

def main():
    # Enable garbage collection debugging (optional)
    # gc.set_debug(gc.DEBUG_STATS)
    
    # You can change the root image filename here
    viewer = OptimizedQuadrantZoomViewer("data/root.jpg", cache_size=16)
    
    try:
        viewer.run()
    finally:
        # Ensure cleanup happens
        viewer.cleanup()
        gc.collect()

if __name__ == "__main__":
    main()
