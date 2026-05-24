import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from PIL import Image, ImageTk, ImageDraw, ImageFont

# ==============================================================================
# Import operations modules
from operations.prev_image import on_prev_image
from operations.next_image import on_next_image
from operations.zoom_in import on_zoom_in
from operations.zoom_out import on_zoom_out
from operations.rotate import on_rotate
from operations.fit_view import on_fit_view
# Import image processing modules
from image_processing.save_watermarked import on_save_watermarked_image

# ==============================================================================
# Windows High-DPI Support
if sys.platform.startswith('win'):
    try:
        import ctypes
        # API supported on Windows 8.1 and later
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            # Older Windows versions
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

# ==============================================================================
# use to show help when mouse move on some areas
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        # Calculate the absolute physical coordinates for the tooltip popup (displayed directly below the control)
        x = self.widget.winfo_rootx() + (self.widget.winfo_width() - 150) // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        
        # Boundary handling to prevent going beyond the left edge of the screen
        if x < 10:
            x = 10
            
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True) # Remove native title bar
        tw.wm_geometry(f"+{x}+{y}")
        
        # Highly textured dark flat card design (#0F172A = Slate 900)
        label = tk.Label(
            tw, 
            text=self.text, 
            justify=tk.LEFT,
            background="#0F172A", 
            foreground="#F8FAFC", 
            relief=tk.FLAT, 
            borderwidth=0,
            padx=10,
            pady=5,
            font=("Segoe UI", 9)
        )
        label.pack(ipadx=1)
        
        # Add a fine slate gray border (#334155 = Slate 700)
        tw.configure(bg="#334155")
        tw.lift() # Elevate layer to ensure it floats on top of the window

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

# ==============================================================================
# 3. WatermarkSeal Main Winodws
class WatermarkSealApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WatermarkSeal - Image Watermark Tool (Protect Your Images)")
        
        # Default resolution 
        self.root.geometry("1280x720")
        
        # Limit minimum window size
        self.root.minsize(1280, 720)
        
        # Ensure that when manually resizing the window, it must maintain a 16:9 aspect ratio
        self.root.aspect(16, 9, 16, 9)
        
        # Activate automatic scaling state variable when window size changes
        self.auto_fit_enabled = True
        
        # Initialize image list and state variables
        self.image_list = []
        self.image_paths = {}
        
        self.current_index = 0
        self.zoom_factor = 100       # Percentage scaling
        self.rotation_angle = 0      # Angle rotation
        
        # Configure modern visual theme styles (Theme & Styles)
        self._setup_styles()
        
        # Menu bar creation
        self._create_menu_bar()
        
        # Overall layout construction
        self._create_layout()
        
        # Initialize display area as empty
        self.update_display_area()

    def _setup_styles(self):
        """Configure global CSS/style system for the application"""
        self.style = ttk.Style()
        # Use clam theme for deeper visual customization
        
        # Color palette definition (Slate Modern Palette)
        self.colors = {
            "primary": "#0EA5E9",       # Sky Blue (Watermark exclusive bright blue)
            "primary_hover": "#0284C7", 
            "bg_sidebar": "#F8FAFC",    # Light gray/sidebar background (Slate 50)
            "bg_operation": "#F1F5F9",  # Light gray-blue/operation area background (Slate 100)
            "bg_display": "#FFFFFF",    # Pure white/display area background
            "border_color": "#E2E8F0",  # Fine gray border (Slate 200)
            "text_main": "#1E293B",     # Dark gray-black (Slate 800)
            "text_muted": "#64748B"     # Muted text color (Slate 500)
        }
        
        # Treeview (image list) style customization
        self.style.configure("Treeview",
                             background="#FFFFFF",
                             foreground=self.colors["text_main"],
                             rowheight=36,  # Moderately increase row height for elegance
                             fieldbackground="#FFFFFF",
                             font=("Segoe UI", 10))
        self.style.map('Treeview',
                       background=[('selected', self.colors["primary"])],
                       foreground=[('selected', '#FFFFFF')])
        
        # TButton (operation area buttons) style customization
        self.style.configure("TButton",
                             font=("Segoe UI", 9, "medium" if sys.platform != "win32" else "normal"),
                             background="#FFFFFF",
                             foreground=self.colors["text_main"],
                             borderwidth=1,
                             bordercolor=self.colors["border_color"],
                             padding=(12, 8),
                             anchor="center") # Force explicit center alignment for all text and icons
        self.style.map("TButton",
                       background=[("active", self.colors["bg_operation"])],
                       bordercolor=[("active", self.colors["primary"])])

    # ===========================
    # Menu Bar Construction
    def _create_menu_bar(self):
        menu_bar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open File...", command=self.on_open_file)
        file_menu.add_command(label="Open Folder...", command=self.on_open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit)
        
        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About...", command=self.on_about)
        
        # Mount to main menu bar
        menu_bar.add_cascade(label="File", menu=file_menu)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menu_bar)

    # ===========================
    # Structure Layout 
    def _create_layout(self):
        # Create horizontal paned window control
        # Allowing users to manually drag the slider to adjust the width of the left image list
        self.paned_window = tk.PanedWindow(
            self.root, 
            orient=tk.HORIZONTAL, 
            bg=self.colors["border_color"],
            bd=0, 
            sashwidth=4, 
            sashpad=1
        )
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Image List (Left Sidebar)
        self.left_sidebar = tk.Frame(
            self.paned_window, 
            bg=self.colors["bg_sidebar"],
            highlightbackground=self.colors["border_color"],
            highlightthickness=1
        )
        self.paned_window.add(self.left_sidebar, minsize=200, width=350)
        
        # Sidebar title bar
        sidebar_title_frame = tk.Frame(self.left_sidebar, bg=self.colors["bg_sidebar"], height=40)
        sidebar_title_frame.pack(side=tk.TOP, fill=tk.X)
        sidebar_title_frame.pack_propagate(False)
        
        sidebar_title_label = tk.Label(
            sidebar_title_frame,
            text="📁 Image List",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["bg_sidebar"]
        )
        sidebar_title_label.pack(side=tk.LEFT, padx=12)
        ToolTip(sidebar_title_label, "Image Resource List (Click to preview)")

        # Sidebar inside
        list_container = tk.Frame(self.left_sidebar, bg="#FFFFFF")
        list_container.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        self.tree = ttk.Treeview(list_container, show="tree", selectmode="browse")
        self.scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind click selection on Siderbar event
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Right main area
        self.right_container = tk.Frame(
            self.paned_window, 
            bg=self.colors["border_color"]
        )
        self.paned_window.add(self.right_container, minsize=600)
        
        # Operation Area
        self.op_frame = tk.Frame(
            self.right_container, 
            height=80, 
            bg=self.colors["bg_operation"],
            highlightbackground=self.colors["border_color"],
            highlightthickness=1
        )
        self.op_frame.pack(side=tk.TOP, fill=tk.X)
        self.op_frame.pack_propagate(False)
        
        self._build_operation_buttons()

        # Image Display Area
        self.display_frame = tk.Frame(
            self.right_container, 
            bg=self.colors["bg_display"],
            highlightbackground=self.colors["border_color"],
            highlightthickness=1
        )
        self.display_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        # ==================
        # display area size
        self.display_frame.bind("<Configure>", self.on_frame_resize)
        
        # display here no imgs
        self._build_display_placeholder()
        
        # here is imgs to hide 
        self.real_image_label = tk.Label(self.display_frame, bg=self.colors["bg_display"])
        # ==================
        # Status Bar
        self.status_bar = tk.Frame(self.right_container, height=25, bg=self.colors["bg_sidebar"])
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # ----change if load img
        self.status_label = tk.Label(
            self.status_bar,
            text=" Ready",
            font=("Segoe UI", 9),
            fg=self.colors["text_muted"],
            bg=self.colors["bg_sidebar"]
        )
        self.status_label.pack(side=tk.LEFT, padx=10)

    # ================================================
    # UI of Operation Area Buttons 
    def _create_toolbar_button(self, parent, text, command, tooltip_text):
        """Create a perfectly vertically centered modern flat standard button with hover effects and hand cursor"""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 9),
            bg="#FFFFFF",
            fg=self.colors["text_main"],
            activebackground=self.colors["bg_operation"],
            activeforeground=self.colors["text_main"],
            relief=tk.SOLID,
            bd=1,
            highlightthickness=0,
            padx=12,
            pady=8,
            cursor="hand2"
        )
        # Exquisite hover color change and highlight effect
        def on_enter(e):
            btn.config(bg=self.colors["bg_operation"])
        def on_leave(e):
            btn.config(bg="#FFFFFF")
        
        btn.bind("<Enter>", on_enter, add="+")
        btn.bind("<Leave>", on_leave, add="+")
        # Mount hover tooltip bubble
        ToolTip(btn, tooltip_text)
        return btn

    def _build_operation_buttons(self):
        """Design toolbar operation buttons here and bind corresponding business methods"""
        btn_container = tk.Frame(self.op_frame, bg=self.colors["bg_operation"])
        btn_container.pack(side=tk.LEFT, fill=tk.Y, padx=15)
        
        # 1. Previous Image
        self.btn_prev = self._create_toolbar_button(btn_container, "⏮ Prev", lambda: on_prev_image(self), "⏮ Previous Image")
        self.btn_prev.pack(side=tk.LEFT, padx=4, pady=18)
        
        # 2. Next Image
        self.btn_next = self._create_toolbar_button(btn_container, "Next ⏭", lambda: on_next_image(self), "Next Image ⏭")
        self.btn_next.pack(side=tk.LEFT, padx=4, pady=18)
        
        # Separator decoration line
        separator1 = tk.Frame(btn_container, width=1, bg=self.colors["border_color"])
        separator1.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=20)
        
        # 3. Zoom In
        self.btn_zoom_in = self._create_toolbar_button(btn_container, "➕ Zoom In", lambda: on_zoom_in(self), "Zoom In (by 10% each time)")
        self.btn_zoom_in.pack(side=tk.LEFT, padx=4, pady=18)
        
        # 4. Zoom Out
        self.btn_zoom_out = self._create_toolbar_button(btn_container, "➖ Zoom Out", lambda: on_zoom_out(self), "Zoom Out (by 10% each time)")
        self.btn_zoom_out.pack(side=tk.LEFT, padx=4, pady=18)
        
        # 5. Rotate
        self.btn_rotate = self._create_toolbar_button(btn_container, "🔄 Rotate", lambda: on_rotate(self), "Rotate Clockwise by 90°")
        self.btn_rotate.pack(side=tk.LEFT, padx=4, pady=18)
        
        # 6. Fit to Screen
        self.btn_fit = self._create_toolbar_button(btn_container, "🏠 Fit Screen", lambda: on_fit_view(self), "Fit to Screen, Reset Rotation & Zoom")
        self.btn_fit.pack(side=tk.LEFT, padx=4, pady=18)

        # Separator decoration line
        separator2 = tk.Frame(btn_container, width=1, bg=self.colors["border_color"])
        separator2.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=20)
        # =============================================================
        # 7. Save with Watermark
        self.btn_watermark = self._create_toolbar_button(btn_container, "💾 Save with Watermark", lambda: on_save_watermarked_image(self), "Save current image with watermark to desktop")
        self.btn_watermark.pack(side=tk.LEFT, padx=4, pady=18)

    # ==========================================================================
    # Image Display Area UI
    def _build_display_placeholder(self):
        """Create placeholder content for the image display area"""
        # Use a main vertical container to elegantly display text in the center of the screen
        self.display_center_container = tk.Frame(self.display_frame, bg=self.colors["bg_display"])
        self.display_center_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Simulated large icon
        self.icon_label = tk.Label(
            self.display_center_container,
            text="🖼️",
            font=("Segoe UI", 48),
            fg="#94A3B8",
            bg=self.colors["bg_display"]
        )
        self.icon_label.pack(pady=5)
        
        # Large title for image information display
        self.img_title_label = tk.Label(
            self.display_center_container,
            text="No Image Loaded",
            font=("Segoe UI", 14, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["bg_display"]
        )
        self.img_title_label.pack(pady=5)
        
        # Small title for image attribute display
        self.img_meta_label = tk.Label(
            self.display_center_container,
            text="Scale: 100%  |  Rotate: 0°",
            font=("Segoe UI", 10),
            fg=self.colors["text_muted"],
            bg=self.colors["bg_display"]
        )
        self.img_meta_label.pack(pady=5)
        
        # Developer tip note
        self.developer_tip_label = tk.Label(
            self.display_center_container,
            text="Tip: Use File menu to import images (File > Open File or File > Open Folder)",
            font=("Segoe UI", 8, "italic"),
            fg="#CBD5E1",
            bg=self.colors["bg_display"]
        )
        self.developer_tip_label.pack(pady=10)

    # ==============================================================================
    # Real Image Rendering Kernel
    def update_display_area(self):
        """Show imgs"""
        if not self.image_list:
            # no images to display, show placeholder
            self.real_image_label.pack_forget()
            self.display_center_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            self.img_title_label.config(text="No Available Images")
            self.img_meta_label.config(text="Please open a file/folder or choose a valid image directory")
            self.status_label.config(text=" Nothing Loaded")
            return
        # =======================================================================
        # if have images, hide placeholder and show real image label
        current_file = self.image_list[self.current_index]
        path = self.image_paths.get(current_file)
        
        img = None
        is_simulated = False
        
        # Load image using Pillow
        try:
            if path and os.path.exists(path):
                img = Image.open(path)
            else:
                messagebox.showerror("File Not Found", f"Cannot find image file: {current_file}")
                return
        except Exception as e:
            messagebox.showerror("Error Loading Image", f"Failed to decode image: {str(e)}")
            return
            
        # Image loaded normally, execute pixel-level operations
        if img is not None:
            # Hide previous non-image text prompts
            self.display_center_container.place_forget()
            # Execute rotation operation
            if self.rotation_angle != 0:
                # self.rotation_angle represents clockwise rotation
                img = img.rotate(-self.rotation_angle, expand=True)
            # Execute scaling operation (LANCZOS high-fidelity filter)
            w_orig, h_orig = img.size
            new_w = int(w_orig * self.zoom_factor / 100)
            new_h = int(h_orig * self.zoom_factor / 100)
            new_w = max(1, new_w)
            new_h = max(1, new_h)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # Convert to RGB mode for rendering to tkinter
            if img.mode == "RGBA":
                img = img.convert("RGB")
                
            # Convert PIL to PhotoImage
            photo = ImageTk.PhotoImage(img)
            self.real_image_label.config(image=photo)
            self.real_image_label.image = photo  # Keep strong reference to prevent GC garbage collection from causing blank images
            self.real_image_label.pack(fill=tk.BOTH, expand=True)
            
            # Update bottom status bar information
            source_type = "Memory Paint" if is_simulated else "Disk File"
            self.status_label.config(
                text=f" 📂 Status: Rendered Successfully | Source: {source_type} | Size: {w_orig}x{h_orig} | Zoom: {self.zoom_factor}% | Rotate: {self.rotation_angle}°"
            )

    # ==================
    # when I change the size of windows
    
    def on_frame_resize(self, event):
        """When the display area window size changes, if auto-fit is enabled, dynamically redraw the image proportionally"""
        if getattr(self, 'auto_fit_enabled', False):
            # Directly trigger fit refresh with resize tag
            on_fit_view(self, called_from_resize=True)

    def on_tree_select(self, event):
        """Handle sidebar click selection event"""
        selected_items = self.tree.selection()
        if selected_items:
            self.current_index = int(selected_items[0])
            self.update_display_area()

    # ===========
    # Menu Bar 
    def on_open_file(self):
        """File -> Open and import physical file"""
        file_path = filedialog.askopenfilename(
            title="Choose WatermarkSeal image file",
            filetypes=[("all the supported image formats", "*.jpg *.jpeg *.png *.bmp *.gif"), ("all files", "*.*")]
        )
        if file_path:
            file_name = os.path.basename(file_path)
            
            # Load the full path of this image into the mapping table
            self.image_paths[file_name] = file_path
            
            # If this image is not yet in the list, insert and synchronize
            if file_name not in self.image_list:
                self.image_list.append(file_name)
                new_id = str(len(self.image_list) - 1)
                self.tree.insert("", "end", iid=new_id, text=f" {file_name}")
            else:
                new_id = str(self.image_list.index(file_name))
                
            # Focus selection and locate to this file
            self.tree.selection_set(new_id)
            self.tree.see(new_id)
            
            # Execute adaptive size display
            on_fit_view(self)

    def on_open_folder(self):
        """File -> Open and import physical folder"""
        folder_path = filedialog.askdirectory(title="Choose WatermarkSeal image folder")
        if folder_path:
            try:
                files = os.listdir(folder_path)
                image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
                found_images = [f for f in files if f.lower().endswith(image_extensions)]
                
                if found_images:
                    # Clear the original image list and path mapping
                    self.image_list = []
                    self.image_paths = {}
                    self.tree.delete(*self.tree.get_children())
                    
                    # Refill data
                    for index, img_name in enumerate(found_images):
                        full_path = os.path.join(folder_path, img_name)
                        self.image_list.append(img_name)
                        self.image_paths[img_name] = full_path
                        self.tree.insert("", "end", iid=str(index), text=f" {img_name}")
                    
                    # Select the first one
                    self.tree.selection_set("0")
                    self.current_index = 0
                    
                    # Execute adaptive size display
                    on_fit_view(self)
                    messagebox.showinfo("Load Folder", f"WatermarkSeal successfully loaded {len(found_images)} image files!")
                else:
                    messagebox.showwarning("No Images Found", f"Please select a folder containing image files (*.jpg, *.png, etc.)")
            except Exception as e:
                messagebox.showerror("Error Reading Folder", f"Error reading folder: {str(e)}")

    def on_exit(self):
        """Exit application"""
        if messagebox.askokcancel("Exit WatermarkSeal", "Are you sure you want to exit WatermarkSeal?"):
            self.root.destroy()

    def on_about(self):
        """Help"""
        messagebox.showinfo(
            "About WatermarkSeal",
            "A software for adding watermarks to images\n"
            "Built by Jianfeng Yuan\n"
            "COMP9001 2026-05\n"
        )

# =====================================================
# Main function
def main():
    root = tk.Tk()
    app = WatermarkSealApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
