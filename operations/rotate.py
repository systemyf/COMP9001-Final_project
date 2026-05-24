
def on_rotate(app):
    """
    Rotate image
    """
    app.rotation_angle = (app.rotation_angle + 90) % 360
    app.update_display_area()
