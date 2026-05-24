def on_zoom_out(app):
    """
    Zoom out
    """
    app.auto_fit_enabled = False
    if app.zoom_factor > 10:
        app.zoom_factor -= 10
        app.update_display_area()
