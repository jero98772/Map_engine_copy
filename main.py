import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
from PIL import Image
import numpy as np
import time

class QuadrantZoomViewer:
    def __init__(self, root_image_path="root.png"):
        self.root_image_path = root_image_path
        self.current_path = ""  # Current zoom path (e.g., "0_2_1")
        self.current_image = None
        self.fig, self.ax = plt.subplots(figsize=(10, 10))
        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.mouse_quadrant = 0  # Track which quadrant mouse is over
        
        # Animation state
        self.is_animating = False
        self.animation_frames = 20
        self.current_frame = 0
        self.zoom_target = None
        self.zoom_start_bounds = None
        self.zoom_end_bounds = None
        self.pending_path = None
        self.zoom_direction = 1  # 1 for zoom in, -1 for zoom out
        
        # Load and display the root image
        self.load_current_image()
        self.display_image()
        
    def get_image_filename(self, path=""):
        """Generate filename based on current path"""
        if path == "":
            return self.root_image_path
        else:
            base_name = self.root_image_path.split('.')[0]
            extension = self.root_image_path.split('.')[-1]
            return f"{base_name}_{path}.{extension}"
    
    def load_current_image(self):
        """Load the current image based on the current path"""
        filename = self.get_image_filename(self.current_path)
        
        try:
            self.current_image = Image.open(filename)
            print(f"Loaded: {filename}")
        except FileNotFoundError:
            print(f"Image not found: {filename}")
            # Create a placeholder image with quadrant labels
            self.current_image = self.create_placeholder_image()
    
    def create_placeholder_image(self):
        """Create a placeholder image with quadrant numbers"""
        img = Image.new('RGB', (400, 400), color='lightgray')
        
        # You could add text here using PIL's ImageDraw if needed
        # For simplicity, we'll just use colored quadrants
        pixels = np.array(img)
        
        # Color the quadrants differently
        h, w = pixels.shape[:2]
        mid_h, mid_w = h // 2, w // 2
        
        # Quadrant 0 (top-left) - light blue
        pixels[:mid_h, :mid_w] = [173, 216, 230]
        # Quadrant 1 (top-right) - light green
        pixels[:mid_h, mid_w:] = [144, 238, 144]
        # Quadrant 2 (bottom-left) - light coral
        pixels[mid_h:, :mid_w] = [240, 128, 128]
        # Quadrant 3 (bottom-right) - light yellow
        pixels[mid_h:, mid_w:] = [255, 255, 224]
        
        return Image.fromarray(pixels)
    
    def get_quadrant_bounds(self, quadrant):
        """Get the bounds of a specific quadrant"""
        img_width, img_height = self.current_image.size
        mid_x, mid_y = img_width // 2, img_height // 2
        
        bounds = {
            0: (0, 0, mid_x, mid_y),           # top-left
            1: (mid_x, 0, img_width, mid_y),   # top-right
            2: (0, mid_y, mid_x, img_height),  # bottom-left
            3: (mid_x, mid_y, img_width, img_height)  # bottom-right
        }
        
        return bounds[quadrant]
    
    def display_image(self):
        """Display the current image with quadrant grid overlay"""
        self.ax.clear()
        
        if self.current_image:
            # Display the image
            self.ax.imshow(self.current_image)
            
            # Only show grid and highlights if not animating
            if not self.is_animating:
                # Add quadrant grid overlay
                img_width, img_height = self.current_image.size
                mid_x, mid_y = img_width // 2, img_height // 2
                
                # Draw grid lines
                self.ax.axhline(y=mid_y, color='red', linestyle='--', alpha=0.7, linewidth=2)
                self.ax.axvline(x=mid_x, color='red', linestyle='--', alpha=0.7, linewidth=2)
                
                # Highlight the quadrant where mouse is hovering
                x1, y1, x2, y2 = self.get_quadrant_bounds(self.mouse_quadrant)
                highlight_rect = patches.Rectangle((x1, y1), x2-x1, y2-y1, 
                                                 linewidth=3, edgecolor='yellow', 
                                                 facecolor='yellow', alpha=0.2)
                self.ax.add_patch(highlight_rect)
                
                # Add quadrant labels
                self.ax.text(mid_x//2, mid_y//2, '0', fontsize=20, ha='center', va='center', 
                            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
                self.ax.text(mid_x + mid_x//2, mid_y//2, '1', fontsize=20, ha='center', va='center',
                            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
                self.ax.text(mid_x//2, mid_y + mid_y//2, '2', fontsize=20, ha='center', va='center',
                            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
                self.ax.text(mid_x + mid_x//2, mid_y + mid_y//2, '3', fontsize=20, ha='center', va='center',
                            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
            
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
    
    def animate_zoom(self, frame):
        """Animation function for smooth zooming"""
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
            
            return
        
        # Calculate interpolation factor (0 to 1)
        t = frame / (self.animation_frames - 1)
        
        # Smooth easing function (ease-in-out)
        t = t * t * (3 - 2 * t)
        
        # Interpolate between start and end bounds
        start_x1, start_y1, start_x2, start_y2 = self.zoom_start_bounds
        end_x1, end_y1, end_x2, end_y2 = self.zoom_end_bounds
        
        current_x1 = start_x1 + (end_x1 - start_x1) * t
        current_y1 = start_y1 + (end_y1 - start_y1) * t
        current_x2 = start_x2 + (end_x2 - start_x2) * t
        current_y2 = start_y2 + (end_y2 - start_y2) * t
        
        # Set the view bounds
        self.ax.set_xlim(current_x1, current_x2)
        self.ax.set_ylim(current_y2, current_y1)  # Flip Y axis for image coordinates
        
        plt.draw()
    
    def start_zoom_animation(self, target_quadrant, zoom_in=True):
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
                self.pending_path = self.current_path + f"_{target_quadrant}"
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
        
        # Start animation
        self.current_frame = 0
        self.animation_timer = self.fig.canvas.new_timer(interval=50)  # 50ms = 20 FPS
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
        
        # Determine which quadrant mouse is over
        img_width, img_height = self.current_image.size
        mid_x, mid_y = img_width // 2, img_height // 2
        
        if x < mid_x and y < mid_y:
            new_quadrant = 0  # top-left
        elif x >= mid_x and y < mid_y:
            new_quadrant = 1  # top-right
        elif x < mid_x and y >= mid_y:
            new_quadrant = 2  # bottom-left
        else:
            new_quadrant = 3  # bottom-right
        
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
    
    def on_key_press(self, event):
        """Handle key press events"""
        if self.is_animating:
            return
            
        if event.key == 'b':  # Go back
            if self.current_path:
                print(f"Going back from path: {self.current_path}")
                self.start_zoom_animation(0, zoom_in=False)
        elif event.key == 'q':  # Quit
            plt.close()
    
    def run(self):
        """Start the viewer"""
        print("Natural Quadrant Zoom Viewer")
        print("Instructions:")
        print("- Move mouse over quadrants to highlight them")
        print("- Scroll up over a quadrant to zoom in with animation")
        print("- Scroll down to zoom out with animation")
        print("- Press 'b' to go back to previous level")
        print("- Press 'q' to quit")
        print(f"Looking for images with pattern: {self.root_image_path.split('.')[0]}_[path].{self.root_image_path.split('.')[-1]}")
        print("Example: root.png, root_0.png, root_0_2.png, root_0_2_1.png")
        
        plt.show()

def main():
    # You can change the root image filename here
    viewer = QuadrantZoomViewer("data/root.jpg")
    viewer.run()

if __name__ == "__main__":
    main()