import os
from PIL import Image


def on_fit_view(app, called_from_resize=False):
    """
    fit the img to the view
    """
    if not called_from_resize:
        app.rotation_angle = 0
        app.auto_fit_enabled = True  # Re-activate auto-fit state
        
    if not app.image_list:
        app.zoom_factor = 100
        app.update_display_area()
        return
        
    current_file = app.image_list[app.current_index]
    path = app.image_paths.get(current_file)
    
    try:
        # Get original image dimensions
        if path and os.path.exists(path):
            img = Image.open(path)
        else:
            # File does not exist, cannot calculate fit ratio
            app.zoom_factor = 100
            app.update_display_area()
            return
        
        # If there is rotation, we need to get the bounding box dimensions after rotation to calculate fit! Avoid overflow after rotation
        if app.rotation_angle != 0:
            img = img.rotate(-app.rotation_angle, expand=True)
            
        img_w, img_h = img.size
        
        # Get actual width and height of current display area Frame
        frame_w = app.display_frame.winfo_width()
        frame_h = app.display_frame.winfo_height()
        
        # Handle default value of 1 before rendering
        if frame_w <= 1:
            frame_w = 800
        frame_h -= 30  # Leave room for status bar
        if frame_h <= 1:
            frame_h = 500
        
        # Reserve 40 pixels padding
        target_w = frame_w - 40
        target_h = frame_h - 40
        
        # Calculate ratio
        ratio_w = target_w / img_w
        ratio_h = target_h / img_h
        best_ratio = min(ratio_w, ratio_h)
        
        # Convert ratio to zoom_factor percentage (limited between 10% and 500%)
        app.zoom_factor = max(10, min(500, int(best_ratio * 100)))
    except Exception:
        app.zoom_factor = 100
        
    app.update_display_area()
