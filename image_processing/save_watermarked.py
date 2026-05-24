"""Save watermarked image module"""

import os
import sys
from tkinter import messagebox, simpledialog
from PIL import Image, ImageDraw, ImageFont


def on_save_watermarked_image(app):
    """
    Save current image with watermark to desktop/WatermarkImgs folder
    
    Args:
        app: WatermarkSealApp application instance
    """
    if not app.image_list:
        messagebox.showwarning("No Image", "Please open an image first!")
        return
    
    # Get current image path
    current_file = app.image_list[app.current_index]
    path = app.image_paths.get(current_file)
    
    if not path or not os.path.exists(path):
        messagebox.showerror("File Not Found", f"Cannot find image file: {current_file}")
        return
    
    try:
        # Open original image
        img = Image.open(path)
        
        # Apply rotation if needed
        if app.rotation_angle != 0:
            img = img.rotate(-app.rotation_angle, expand=True)
        
        # Convert to RGBA for watermark
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        
        # Ask user for watermark text
        watermark_text = simpledialog.askstring(
            "Watermark Text", 
            "Enter watermark text:", 
            initialvalue="WatermarkSeal"
        )
        
        if not watermark_text:
            return
        
        # Create watermark layer
        watermark_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(watermark_layer)
        
        # Calculate font size based on image size
        font_size = max(20, int(min(img.size) * 0.05))
        
        # Load font
        try:
            if sys.platform.startswith('win'):
                font = ImageFont.truetype("msyh.ttc", font_size)
            elif sys.platform.startswith('darwin'):
                font = ImageFont.truetype("PingFang.ttc", font_size)
            else:
                font = ImageFont.truetype("DejaVuSans.ttf", font_size)
        except OSError:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except OSError:
                font = ImageFont.load_default()
        
        # Draw watermark at center
        draw.text(
            (img.size[0] / 2, img.size[1] / 2), 
            watermark_text, 
            fill=(14, 165, 233, 128), 
            anchor="mm", 
            font=font
        )
        
        # Composite watermark layer
        img = Image.alpha_composite(img, watermark_layer)
        
        # Create output directory on desktop
        desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        output_dir = os.path.join(desktop, 'WatermarkImgs')
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate output filename
        base_name = os.path.splitext(current_file)[0]
        ext = os.path.splitext(current_file)[1]
        output_filename = f"{base_name}_watermarked{ext}"
        output_path = os.path.join(output_dir, output_filename)
        
        # Handle duplicate filenames
        counter = 1
        while os.path.exists(output_path):
            output_filename = f"{base_name}_watermarked_{counter}{ext}"
            output_path = os.path.join(output_dir, output_filename)
            counter += 1
        
        # Save image (convert to RGB for JPEG)
        if ext.lower() in ['.jpg', '.jpeg']:
            img = img.convert('RGB')
            img.save(output_path, 'JPEG', quality=95)
        else:
            img.save(output_path)
        
        messagebox.showinfo(
            "Success", 
            f"Watermarked image saved successfully!\n\nLocation: {output_path}"
        )
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save watermarked image: {str(e)}")
