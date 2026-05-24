def on_prev_image(app):
    """
    back to last img
    """
    if not app.image_list:
        return
    if app.current_index > 0:
        app.current_index -= 1
    else:
        app.current_index = len(app.image_list) - 1  # Cycle to last image
        
    # Sync left list selection and trigger UI update
    app.tree.selection_set(str(app.current_index))
    app.tree.see(str(app.current_index))
    app.update_display_area()
