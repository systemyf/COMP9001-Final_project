def on_zoom_in(app):
    """
    Zoom in
    """
    app.auto_fit_enabled = False
    if app.zoom_factor < 500:
        app.zoom_factor += 10
        app.update_display_area()
