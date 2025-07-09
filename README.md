# Natural Quadrant Zoom Viewer (bad quality copy)

A Python-based image viewer that provides smooth, natural zooming into quadrants of images with animated transitions. Perfect for exploring hierarchical image data, maps, or any content that can be divided into quadrants at different zoom levels.

## Features

- 🔍 **Smooth zoom animations** - Natural zoom in/out transitions with easing
- 🎯 **Quadrant-based navigation** - Divide images into 4 quadrants for exploration
- 🖱️ **Intuitive mouse controls** - Hover to highlight, scroll to zoom
- 📁 **Hierarchical image loading** - Automatic loading of nested quadrant images
- 🎨 **Visual feedback** - Real-time quadrant highlighting and animation states
- 🔄 **Seamless navigation** - Smooth transitions between zoom levels

## Installation

1. Clone or download the script
https://github.com/jero98772/Map_engine_copy

2. Install dependencies:
```bash
pip install Pillow matplotlib numpy
```

## Usage

### Basic Usage
```bash
python main.py
```

### Custom Root Image
```python
viewer = QuadrantZoomViewer("my_image.png")
viewer.run()
```

## Controls

| Action | Control |
|--------|---------|
| **Navigate** | Move mouse over quadrants |
| **Zoom In** | Scroll up over highlighted quadrant |
| **Zoom Out** | Scroll down |

## File Structure

The viewer uses a hierarchical naming convention for images inside folder data:

```
root.png              # Main/root image
root_0.png           # Top-left quadrant of root
root_1.png           # Top-right quadrant of root  
root_2.png           # Bottom-left quadrant of root
root_3.png           # Bottom-right quadrant of root
root_0_0.png         # Top-left of top-left quadrant
root_0_1.png         # Top-right of top-left quadrant
root_0_2.png         # Bottom-left of top-left quadrant
root_0_3.png         # Bottom-right of top-left quadrant
root_1_2_3.png       # Bottom-right of bottom-left of top-right
```

### Quadrant Numbering System

```
┌─────┬─────┐
│  0  │  1  │
├─────┼─────┤
│  2  │  3  │
└─────┴─────┘
```

- **0**: Top-left quadrant
- **1**: Top-right quadrant
- **2**: Bottom-left quadrant
- **3**: Bottom-right quadrant

## How It Works

1. **Start**: Load the root image (e.g., `root.png`)
2. **Highlight**: Move mouse over quadrants to see yellow highlighting
3. **Zoom In**: Scroll up to smoothly zoom into the highlighted quadrant
4. **Load**: At maximum zoom, the corresponding quadrant image loads automatically
5. **Explore**: Continue navigating deeper into sub-quadrants
6. **Zoom Out**: Scroll down to smoothly return to the parent level

## Example Use Cases

- **Map Exploration**: Navigate through map tiles at different zoom levels
- **Medical Imaging**: Explore high-resolution medical scans by region
- **Satellite Imagery**: Zoom into different areas of satellite photos
- **Art/Photography**: Examine fine details in high-resolution artwork
- **Scientific Data**: Explore large datasets divided into regions
- **Game Development**: Navigate through game world tiles

## Technical Details

- **Animation**: 20 frames at 20 FPS for smooth transitions
- **Easing**: Uses ease-in-out function for natural motion
- **Placeholder Images**: Automatically generates colored quadrant placeholders for missing images
- **Error Handling**: Gracefully handles missing image files
- **Memory Efficient**: Loads only the current image, not the entire hierarchy

## Animation Behavior

The viewer provides a natural zoom experience:

1. **Zoom In Animation**:
   - Current image view smoothly zooms into selected quadrant
   - At maximum zoom, new quadrant image loads and displays
   - Grid and labels hidden during animation for clean experience

2. **Zoom Out Animation**:
   - Current view smoothly zooms out to show parent image
   - Returns to full parent image view
   - Grid and labels reappear after animation

## Customization

### Change Root Image
```python
viewer = QuadrantZoomViewer("root.jpg")
```

### Modify Animation Settings
```python
# In the class __init__ method:
self.animation_frames = 30  # More frames = smoother animation
```

### Custom Placeholder Colors
Modify the `create_placeholder_image()` method to change quadrant colors.

## Troubleshooting

### Missing Images
- The viewer will create colored placeholder images for missing files
- Check console output for "Image not found" messages
- Ensure your image files follow the naming convention exactly

### Performance Issues
- Large images may cause slower animations
- Consider resizing images to reasonable dimensions (e.g., 1024x1024)
- Reduce `animation_frames` for faster transitions

### Mouse Responsiveness
- Ensure your mouse is over the image area when scrolling
- Grid lines help identify quadrant boundaries
- Yellow highlighting confirms quadrant selection

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the viewer.

## Future Enhancements

- Support for different image formats
- Configurable animation speeds
- Keyboard shortcuts for direct quadrant navigation
- Zoom level indicators
- Breadcrumb navigation
- Support for non-square images