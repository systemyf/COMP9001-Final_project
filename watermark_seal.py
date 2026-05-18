import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

# ==============================================================================
# 1. 尝试导入 Pillow 图像处理库 (Pillow Core Imports & Fallback)
# ==============================================================================
try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# ==============================================================================
# 2. 开启高分屏 DPI 感知 (Windows High-DPI Support)
# ==============================================================================
if sys.platform.startswith('win'):
    try:
        import ctypes
        # Windows 8.1 及更高版本支持的 API
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            # 较旧的 Windows 版本
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

# ==============================================================================
# 2.5 现代悬浮中文提示组件 (Modern Hover ToolTip Engine)
# ==============================================================================
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
        # 计算提示框弹出的绝对物理坐标（显示在控件正下方）
        x = self.widget.winfo_rootx() + (self.widget.winfo_width() - 150) // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        
        # 边界处理防止超出屏幕左侧
        if x < 10:
            x = 10
            
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True) # 移除原生标题栏
        tw.wm_geometry(f"+{x}+{y}")
        
        # 极具质感的深色扁平化卡片设计 (#0F172A = Slate 900)
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
        
        # 加一层细致的 Slate 灰色描边 (#334155 = Slate 700)
        tw.configure(bg="#334155")
        tw.lift() # 提升层级保证浮在窗口最上面

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

# ==============================================================================
# 3. WatermarkSeal 主应用程序类 (Model-View-Controller)
# ==============================================================================
class WatermarkSealApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WatermarkSeal - Image Watermark Tool (Protect Your Images)")
        
        # 默认分辨率 1280x720 (720p)
        self.root.geometry("1280x720")
        
        # 限制窗口最小尺寸为 1280x720 (720p)
        self.root.minsize(1280, 720)
        
        # 限制窗口在手动拉大时，必须保持 16:9 的等比例拉伸
        self.root.aspect(16, 9, 16, 9)
        
        # 激活窗口尺寸变化时的自动缩放状态变量
        self.auto_fit_enabled = True
        
        # 初始化模拟数据与状态变量
        self.image_list = [
            "scenery_mountain.jpeg",
            "vacation_2026_01.png",
            "family_portrait.jpg",
            "city_night_view.png",
            "cute_cat_sleeping.jpg",
            "delicious_food_table.jpg",
            "document_scan_page1.png",
            "office_workspace_setup.jpg",
            "forest_pathway_autumn.jpeg",
            "ocean_sunset_horizon.jpg",
            "vintage_car_retro.png",
            "architecture_minimalist.jpg"
        ]
        
        # 保存每个图片对应的磁盘物理路径映射 (文件名 -> 绝对路径)。模拟文件映射为 None
        self.image_paths = {}
        
        self.current_index = 0
        self.zoom_factor = 100       # 百分比缩放
        self.rotation_angle = 0      # 角度缩放
        
        # 水印特定属性 (Watermark/Seal properties)
        self.watermark_enabled = False
        self.watermark_text = "WatermarkSeal 预览版"
        
        # 配置现代视觉主题样式 (Theme & Styles)
        self._setup_styles()
        
        # 3. 菜单栏创建
        self._create_menu_bar()
        
        # 4. 整体布局构建
        self._create_layout()
        
        # 5. 填充并初始化数据
        self._populate_image_list()
        self.update_display_area()

    def _setup_styles(self):
        """配置应用程序的全局 CSS/样式系统"""
        self.style = ttk.Style()
        self.style.theme_use('clam')  # 使用 clam 主题以便于更深度的视觉定制
        
        # 颜色板定义 (Slate Modern Palette)
        self.colors = {
            "primary": "#0EA5E9",       # 天空蓝 (Watermark 专属亮蓝)
            "primary_hover": "#0284C7", 
            "bg_sidebar": "#F8FAFC",    # 浅灰色/侧边栏背景 (Slate 50)
            "bg_operation": "#F1F5F9",  # 浅灰蓝/操作区背景 (Slate 100)
            "bg_display": "#FFFFFF",    # 纯白/显示区域背景
            "border_color": "#E2E8F0",  # 精细灰色边框 (Slate 200)
            "text_main": "#1E293B",     # 深灰黑 (Slate 800)
            "text_muted": "#64748B"     # 弱化文本色 (Slate 500)
        }
        
        # Treeview (图片列表) 样式定制
        self.style.configure("Treeview",
                             background="#FFFFFF",
                             foreground=self.colors["text_main"],
                             rowheight=36,  # 适度增加行高以显尊贵
                             fieldbackground="#FFFFFF",
                             font=("Segoe UI", 10))
        self.style.map('Treeview',
                       background=[('selected', self.colors["primary"])],
                       foreground=[('selected', '#FFFFFF')])
        
        # TButton (操作区按钮) 样式定制
        self.style.configure("TButton",
                             font=("Segoe UI", 9, "medium" if sys.platform != "win32" else "normal"),
                             background="#FFFFFF",
                             foreground=self.colors["text_main"],
                             borderwidth=1,
                             bordercolor=self.colors["border_color"],
                             padding=(12, 8),
                             anchor="center") # 强行显式居中对齐所有文字与图标
        self.style.map("TButton",
                       background=[("active", self.colors["bg_operation"])],
                       bordercolor=[("active", self.colors["primary"])])

    # ==============================================================================
    # 3. 菜单栏构建 (Menu Bar)
    # ==============================================================================
    def _create_menu_bar(self):
        menu_bar = tk.Menu(self.root)
        
        # File 菜单
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open File...", command=self.on_open_file)
        file_menu.add_command(label="Open Folder...", command=self.on_open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit)
        
        # Help 菜单
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About...", command=self.on_about)
        
        # 挂载到主菜单栏
        menu_bar.add_cascade(label="File", menu=file_menu)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menu_bar)

    # ==============================================================================
    # 4. 布局结构 (Layout Division)
    # ==============================================================================
    def _create_layout(self):
        # 创建水平分栏控件 (PanedWindow)，允许用户手动拖拽滑块来调节左侧图片列表的宽度
        self.paned_window = tk.PanedWindow(
            self.root, 
            orient=tk.HORIZONTAL, 
            bg=self.colors["border_color"],
            bd=0, 
            sashwidth=4, 
            sashpad=1
        )
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # 4.1 图像列表 (左侧通栏): 占位初始 250px 宽，拖拽时限制最小宽度为 180px
        self.left_sidebar = tk.Frame(
            self.paned_window, 
            bg=self.colors["bg_sidebar"],
            highlightbackground=self.colors["border_color"],
            highlightthickness=1
        )
        self.paned_window.add(self.left_sidebar, minsize=200, width=350)
        
        # 侧边栏标题栏
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
        ToolTip(sidebar_title_label, "图片资源列表 (双击列表项可进行预览)")

        # 在侧边栏放置带滚动条的列表占位
        list_container = tk.Frame(self.left_sidebar, bg="#FFFFFF")
        list_container.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        self.tree = ttk.Treeview(list_container, show="tree", selectmode="browse")
        self.scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 绑定点击选择事件
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # 4.2 右侧主区域：占据剩余宽度，限制最小宽度为 600px
        self.right_container = tk.Frame(
            self.paned_window, 
            bg=self.colors["border_color"]
        )
        self.paned_window.add(self.right_container, minsize=600)
        
        # 4.2.1 上方“操作区”：高度固定 80px
        self.op_frame = tk.Frame(
            self.right_container, 
            height=80, 
            bg=self.colors["bg_operation"],
            highlightbackground=self.colors["border_color"],
            highlightthickness=1
        )
        self.op_frame.pack(side=tk.TOP, fill=tk.X)
        self.op_frame.pack_propagate(False) # 强制高度固定
        
        self._build_operation_buttons()

        # 4.2.2 下方“图片显示区”：自动填满所有剩余空间
        self.display_frame = tk.Frame(
            self.right_container, 
            bg=self.colors["bg_display"],
            highlightbackground=self.colors["border_color"],
            highlightthickness=1
        )
        self.display_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        # 绑定显示区域大小改变事件，用于实现等比放大拉伸时的动态流式图片重绘
        self.display_frame.bind("<Configure>", self.on_frame_resize)
        
        # 4.2.2.1 传统的文字提示占位 container（仅在没有 Pillow 或者未加载图片时显示）
        self._build_display_placeholder()
        
        # 4.2.2.2 专门用于实际渲染 Pillow 图片的图像标签
        self.real_image_label = tk.Label(self.display_frame, bg=self.colors["bg_display"])
        
        # 添加底部状态栏增加高级感 (Status Bar)
        self.status_bar = tk.Frame(self.right_container, height=25, bg=self.colors["bg_sidebar"])
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = tk.Label(
            self.status_bar,
            text=" Ready",
            font=("Segoe UI", 9),
            fg=self.colors["text_muted"],
            bg=self.colors["bg_sidebar"]
        )
        self.status_label.pack(side=tk.LEFT, padx=10)

    # ==============================================================================
    # 5. 操作区按钮与核心逻辑的注入点 (Operation Area Elements)
    # ==============================================================================
    def _create_toolbar_button(self, parent, text, command, tooltip_text):
        """创建一个完美垂直居中、自带悬浮效果与手型指针的现代扁平化标准按钮"""
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
        
        # 精致的悬浮变色与高光效果
        def on_enter(e):
            btn.config(bg=self.colors["bg_operation"])
        def on_leave(e):
            btn.config(bg="#FFFFFF")
            
        btn.bind("<Enter>", on_enter, add="+")
        btn.bind("<Leave>", on_leave, add="+")
        
        # 挂载悬浮提示气泡
        ToolTip(btn, tooltip_text)
        return btn

    def _build_operation_buttons(self):
        """在此设计工具栏操作按钮并绑定相应的业务方法"""
        btn_container = tk.Frame(self.op_frame, bg=self.colors["bg_operation"])
        btn_container.pack(side=tk.LEFT, fill=tk.Y, padx=15)
        
        # 1. 上一张 (Prev)
        self.btn_prev = self._create_toolbar_button(btn_container, "⏮ Prev", self.on_prev_image, "⏮ 上一张图片")
        self.btn_prev.pack(side=tk.LEFT, padx=4, pady=18)
        
        # 2. 下一张 (Next)
        self.btn_next = self._create_toolbar_button(btn_container, "Next ⏭", self.on_next_image, "下一张图片 ⏭")
        self.btn_next.pack(side=tk.LEFT, padx=4, pady=18)
        
        # 间隔装饰线
        separator1 = tk.Frame(btn_container, width=1, bg=self.colors["border_color"])
        separator1.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=20)
        
        # 3. 放大 (Zoom In)
        self.btn_zoom_in = self._create_toolbar_button(btn_container, "➕ Zoom In", self.on_zoom_in, "放大图片 (每次 +10%)")
        self.btn_zoom_in.pack(side=tk.LEFT, padx=4, pady=18)
        
        # 4. 缩小 (Zoom Out)
        self.btn_zoom_out = self._create_toolbar_button(btn_container, "➖ Zoom Out", self.on_zoom_out, "缩小图片 (每次 -10%)")
        self.btn_zoom_out.pack(side=tk.LEFT, padx=4, pady=18)
        
        # 5. 旋转 (Rotate)
        self.btn_rotate = self._create_toolbar_button(btn_container, "🔄 Rotate", self.on_rotate, "顺时针旋转 90 度")
        self.btn_rotate.pack(side=tk.LEFT, padx=4, pady=18)
        
        # 6. 重置/自适应 (Reset/Fit)
        self.btn_fit = self._create_toolbar_button(btn_container, "🏠 Fit Screen", self.on_fit_view, "适应屏幕大小，重置旋转与缩放")
        self.btn_fit.pack(side=tk.LEFT, padx=4, pady=18)

        # 间隔装饰线
        separator2 = tk.Frame(btn_container, width=1, bg=self.colors["border_color"])
        separator2.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=20)

        # 7. 水印印章功能 (Watermark Seal toggle)
        self.btn_watermark = self._create_toolbar_button(btn_container, "🏷️ Add Watermark", self.on_toggle_watermark, "开启/修改半透明文字水印印章")
        self.btn_watermark.pack(side=tk.LEFT, padx=4, pady=18)

    # ==============================================================================
    # 6. 图片显示区 UI 细节 (Image Display Area Details)
    # ==============================================================================
    def _build_display_placeholder(self):
        """创建图片显示区的占位内容"""
        # 使用一个主垂直容器使文字在屏幕中央优雅展示
        self.display_center_container = tk.Frame(self.display_frame, bg=self.colors["bg_display"])
        self.display_center_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # 仿真大图标
        self.icon_label = tk.Label(
            self.display_center_container,
            text="🖼️",
            font=("Segoe UI", 48),
            fg="#94A3B8",
            bg=self.colors["bg_display"]
        )
        self.icon_label.pack(pady=5)
        
        # 图片信息展示大标题
        self.img_title_label = tk.Label(
            self.display_center_container,
            text="No Image Loaded",
            font=("Segoe UI", 14, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["bg_display"]
        )
        self.img_title_label.pack(pady=5)
        
        # 图片属性展示小标题
        self.img_meta_label = tk.Label(
            self.display_center_container,
            text="Scale: 100%  |  Rotate: 0°  |  Watermark: Disabled",
            font=("Segoe UI", 10),
            fg=self.colors["text_muted"],
            bg=self.colors["bg_display"]
        )
        self.img_meta_label.pack(pady=5)
        
        # 开发者提示备注
        self.developer_tip_label = tk.Label(
            self.display_center_container,
            text="Tip: Double-click items in the left list to preview, or use the top toolbar to zoom, rotate and stamp watermarks.",
            font=("Segoe UI", 8, "italic"),
            fg="#CBD5E1",
            bg=self.colors["bg_display"]
        )
        self.developer_tip_label.pack(pady=10)

    # ==============================================================================
    # 7. 内存精美图像生成器 (In-Memory Image Painter for Mock Files)
    # ==============================================================================
    def _generate_mock_image(self, name):
        """当本地没有真实物理图片时，用 Pillow 在内存中画一张精致的风景画进行渲染和水印演示"""
        # 创建 800x600 的背景图 (深邃 Slate 蓝)
        img = Image.new("RGB", (800, 600), color="#1E293B")
        draw = ImageDraw.Draw(img)
        
        # 绘制橙黄色的朝阳
        draw.ellipse([580, 60, 680, 160], fill="#F59E0B")
        
        # 绘制远山群峰
        draw.polygon([(80, 600), (320, 220), (560, 600)], fill="#334155")
        draw.polygon([(360, 600), (580, 300), (800, 600)], fill="#475569")
        
        # 绘制暗色近景地面
        draw.rectangle([0, 520, 800, 600], fill="#0F172A")
        
        # 绘制科技网格装饰线条
        for y in range(520, 600, 15):
            draw.line([(0, y), (800, y)], fill="#1E293B", width=1)
            
        # 渲染图章及标题文本
        try:
            # 尝试载入 Arial 字体，否则使用系统默认
            font_title = ImageFont.truetype("arial.ttf", 32)
            font_sub = ImageFont.truetype("arial.ttf", 16)
        except OSError:
            font_title = ImageFont.load_default()
            font_sub = ImageFont.load_default()
            
        draw.text((40, 50), f"Demo Picture: {name}", fill="#F8FAFC", font=font_title)
        draw.text((40, 95), "Type: In-Memory Simulated Canvas (Pillow Generated)", fill="#38BDF8", font=font_sub)
        draw.text((40, 125), "Size: 800 x 600 pixels  |  Press Zoom/Rotate to manipulate", fill="#94A3B8", font=font_sub)
        draw.text((40, 150), "Click 'Add Watermark' button to overlay real transparent seal", fill="#64748B", font=font_sub)
        
        return img

    # ==============================================================================
    # 8. 数据绑定与真实图像渲染内核 (Real-time Pillow Rendering Kernel)
    # ==============================================================================
    def _populate_image_list(self):
        """渲染左侧模拟文件树"""
        for index, img_name in enumerate(self.image_list):
            # 将每个图片文件作为行插入 Treeview
            self.tree.insert("", "end", iid=str(index), text=f" {img_name}")
            
        # 默认选中第一张图片
        if self.image_list:
            self.tree.selection_set("0")
            self.current_index = 0

    def update_display_area(self):
        """核心图形引擎：利用 Pillow 库执行真实的解码、旋转、缩放与水印叠加"""
        if not self.image_list:
            # 没任何图片，显示最初的纯文本占位
            self.real_image_label.pack_forget()
            self.display_center_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            self.img_title_label.config(text="No Available Images")
            self.img_meta_label.config(text="Please open a file/folder or choose a valid image directory")
            self.status_label.config(text=" Idle")
            return
            
        current_file = self.image_list[self.current_index]
        path = self.image_paths.get(current_file)
        
        img = None
        is_simulated = False
        
        # 1. 尝试使用 Pillow 读取文件或内存生成图片
        if PILLOW_AVAILABLE:
            try:
                if path and os.path.exists(path):
                    img = Image.open(path)
                else:
                    # 磁盘无此文件，触发【内存精美画作画板】生成演示图片！
                    img = self._generate_mock_image(current_file)
                    is_simulated = True
            except Exception as e:
                messagebox.showerror("读取错误", f"Pillow 解码图片失败: {str(e)}")
                return
                
        # 2. 如果 Pillow 可用且图片加载正常，执行像素级操作
        if PILLOW_AVAILABLE and img is not None:
            # 彻底隐藏之前的非图片文字提示
            self.display_center_container.place_forget()
            
            # 2.1 执行旋转操作
            if self.rotation_angle != 0:
                # -self.rotation_angle 代表顺时针
                img = img.rotate(-self.rotation_angle, expand=True)
                
            # 2.2 执行缩放操作 (LANCZOS 高保真滤镜)
            w_orig, h_orig = img.size
            new_w = int(w_orig * self.zoom_factor / 100)
            new_h = int(h_orig * self.zoom_factor / 100)
            new_w = max(1, new_w)
            new_h = max(1, new_h)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # 2.3 动态水印图章覆盖 (Dynamic Semitransparent Watermark Drawing)
            watermark_status = "Disabled"
            if self.watermark_enabled:
                # 转换为支持 RGBA 透明通道的模式
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                
                # 创建等大小的透明水印图层
                watermark_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(watermark_layer)
                
                # 动态计算水印字号 (自适应图像大小)
                font_size = max(14, int(min(img.size) * 0.05))
                
                try:
                    if sys.platform.startswith('win'):
                        font = ImageFont.truetype("msyh.ttc", font_size) # 微软雅黑
                    elif sys.platform.startswith('darwin'):
                        font = ImageFont.truetype("PingFang.ttc", font_size)
                    else:
                        font = ImageFont.truetype("DejaVuSans.ttf", font_size)
                except OSError:
                    try:
                        font = ImageFont.truetype("arial.ttf", font_size)
                    except OSError:
                        font = ImageFont.load_default()
                
                # 在画面正中心绘制半透明亮蓝色天际线水印 (128为半透明度)
                draw.text(
                    (img.size[0] / 2, img.size[1] / 2), 
                    self.watermark_text, 
                    fill=(14, 165, 233, 128), 
                    anchor="mm", 
                    font=font
                )
                
                # 将透明层拼合进原始图像
                img = Image.alpha_composite(img, watermark_layer)
                watermark_status = "Enabled"
                
            # 2.4 转成 RGB 模式以渲染至 tkinter
            if img.mode == "RGBA":
                img = img.convert("RGB")
                
            # 将 PIL 转换成 PhotoImage
            photo = ImageTk.PhotoImage(img)
            self.real_image_label.config(image=photo)
            self.real_image_label.image = photo  # 保持强引用，防止 GC 垃圾回收导致图片变空白
            self.real_image_label.pack(fill=tk.BOTH, expand=True)
            
            # 2.5 更新底部状态栏信息
            source_type = "Memory Paint" if is_simulated else "Disk File"
            self.status_label.config(
                text=f" 📂 Status: Rendered Successfully | Source: {source_type} | Size: {w_orig}x{h_orig} | Zoom: {self.zoom_factor}% | Rotate: {self.rotation_angle}° | Watermark: {watermark_status}"
            )
        else:
            # 3. 回退模式：若未安装 Pillow，以极其优雅的框架开发模拟渲染展示
            self.real_image_label.pack_forget()
            self.display_center_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            
            self.img_title_label.config(text=f"Simulated File: {current_file}")
            self.img_meta_label.config(
                text=f"Warning: Pillow library not found! Running in simulated mode.  |  Zoom: {self.zoom_factor}%  |  Rotate: {self.rotation_angle}°"
            )
            self.status_label.config(
                text=" ⚠️ Warning: Please run 'pip install pillow' in terminal to enable real image loading, scaling, rotation, and watermarking!"
            )

    # ==============================================================================
    # 9. 操作区预留函数实现 (Interactive Logic Methods)
    # ==============================================================================
    def on_prev_image(self):
        """上一张图片"""
        if not self.image_list:
            return
        if self.current_index > 0:
            self.current_index -= 1
        else:
            self.current_index = len(self.image_list) - 1 # 循环滚屏
            
        # 同步选中左侧列表，触发 UI 更新
        self.tree.selection_set(str(self.current_index))
        self.tree.see(str(self.current_index))
        self.update_display_area()

    def on_next_image(self):
        """下一张图片"""
        if not self.image_list:
            return
        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
        else:
            self.current_index = 0 # 循环滚屏
            
        # 同步选中左侧列表，触发 UI 更新
        self.tree.selection_set(str(self.current_index))
        self.tree.see(str(self.current_index))
        self.update_display_area()

    def on_zoom_in(self):
        """放大 10% (同时锁定当前手动比例)"""
        self.auto_fit_enabled = False
        if self.zoom_factor < 500:
            self.zoom_factor += 10
            self.update_display_area()
            
    def on_zoom_out(self):
        """缩小 10% (同时锁定当前手动比例)"""
        self.auto_fit_enabled = False
        if self.zoom_factor > 10:
            self.zoom_factor -= 10
            self.update_display_area()

    def on_rotate(self):
        """顺时针旋转 90 度"""
        self.rotation_angle = (self.rotation_angle + 90) % 360
        self.update_display_area()

    def on_fit_view(self, called_from_resize=False):
        """计算自适应比例使图片完全显示在视窗内，并重置旋转角度（若是改变窗口大小触发则保留旋转）"""
        if not called_from_resize:
            self.rotation_angle = 0
            self.auto_fit_enabled = True # 重新激活自动拟合状态
            
        if not self.image_list:
            self.zoom_factor = 100
            self.update_display_area()
            return
            
        current_file = self.image_list[self.current_index]
        path = self.image_paths.get(current_file)
        
        # 只有在 Pillow 可用且能够获得尺寸时进行精密计算
        if PILLOW_AVAILABLE:
            try:
                # 获取图像原始尺寸
                if path and os.path.exists(path):
                    img = Image.open(path)
                else:
                    img = self._generate_mock_image(current_file)
                
                # 如果有旋转，我们需要拿到旋转后的包围框尺寸来计算自适应！避免旋转后发生溢出
                if self.rotation_angle != 0:
                    img = img.rotate(-self.rotation_angle, expand=True)
                    
                img_w, img_h = img.size
                
                # 获取当前显示区 Frame 的实际宽度和高度
                frame_w = self.display_frame.winfo_width()
                frame_h = self.display_frame.winfo_height()
                
                # 处理未渲染出来前的默认值 1 的情形
                if frame_w <= 1: frame_w = 800
                frame_h -= 30 # 留出状态栏的余地
                if frame_h <= 1: frame_h = 500
                
                # 预留 40 像素的内边距 padding
                target_w = frame_w - 40
                target_h = frame_h - 40
                
                # 计算比率
                ratio_w = target_w / img_w
                ratio_h = target_h / img_h
                best_ratio = min(ratio_w, ratio_h)
                
                # 将比率转为 zoom_factor 百分比 (限制在 10% 到 500% 之间)
                self.zoom_factor = max(10, min(500, int(best_ratio * 100)))
            except Exception:
                self.zoom_factor = 100
        else:
            self.zoom_factor = 100
            
        self.update_display_area()

    def on_frame_resize(self, event):
        """当显示区域窗口尺寸发生变化时，如果开启了自适应，则动态等比重绘图片"""
        if getattr(self, 'auto_fit_enabled', False):
            # 直接触发带有 resize 标签的拟合刷新
            self.on_fit_view(called_from_resize=True)

    def on_toggle_watermark(self):
        """开启/关闭水印印章，并支持自定义输入文字"""
        self.watermark_enabled = not self.watermark_enabled
        
        if self.watermark_enabled:
            # 弹出一个轻量的 Tkinter 原生输入对话框，供用户录入自定义文字
            custom_text = simpledialog.askstring(
                "设置水印文字", 
                "请输入您要叠加的水印/防伪图章文字：", 
                initialvalue=self.watermark_text
            )
            if custom_text:
                self.watermark_text = custom_text
                
        self.update_display_area()

    def on_tree_select(self, event):
        """处理侧边栏点击选择事件"""
        selected_items = self.tree.selection()
        if selected_items:
            self.current_index = int(selected_items[0])
            self.update_display_area()

    # ==============================================================================
    # 10. 菜单栏关联的回调处理 (Menu Actions for Loading Physical Files)
    # ==============================================================================
    def on_open_file(self):
        """File -> 打开并导入物理文件"""
        file_path = filedialog.askopenfilename(
            title="选择要导入 WatermarkSeal 的图片",
            filetypes=[("支持的图像格式", "*.jpg *.jpeg *.png *.bmp *.gif"), ("所有文件", "*.*")]
        )
        if file_path:
            file_name = os.path.basename(file_path)
            
            # 将该图片的完整路径载入映射表
            self.image_paths[file_name] = file_path
            
            # 若列表中还没有此图片，则插入并同步
            if file_name not in self.image_list:
                self.image_list.append(file_name)
                new_id = str(len(self.image_list) - 1)
                self.tree.insert("", "end", iid=new_id, text=f" {file_name}")
            else:
                new_id = str(self.image_list.index(file_name))
                
            # 聚焦选中并定位到此文件
            self.tree.selection_set(new_id)
            self.tree.see(new_id)
            
            # 执行自适应尺寸展现
            self.on_fit_view()

    def on_open_folder(self):
        """File -> 打开并导入物理文件夹"""
        folder_path = filedialog.askdirectory(title="选择导入 WatermarkSeal 的图片文件夹")
        if folder_path:
            try:
                files = os.listdir(folder_path)
                image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
                found_images = [f for f in files if f.lower().endswith(image_extensions)]
                
                if found_images:
                    # 清空原有的图片列表与路径映射
                    self.image_list = []
                    self.image_paths = {}
                    self.tree.delete(*self.tree.get_children())
                    
                    # 重新填充数据
                    for index, img_name in enumerate(found_images):
                        full_path = os.path.join(folder_path, img_name)
                        self.image_list.append(img_name)
                        self.image_paths[img_name] = full_path
                        self.tree.insert("", "end", iid=str(index), text=f" {img_name}")
                    
                    # 选中第一个
                    self.tree.selection_set("0")
                    self.current_index = 0
                    
                    # 执行自适应尺寸展现
                    self.on_fit_view()
                    messagebox.showinfo("文件夹导入", f"WatermarkSeal 成功导入 {len(found_images)} 张物理图片！")
                else:
                    messagebox.showwarning("无图片", f"选定的文件夹中没有找到支持的图片格式(*.jpg, *.png等)。")
            except Exception as e:
                messagebox.showerror("读取错误", f"读取文件夹失败: {str(e)}")

    def on_exit(self):
        """File -> 退出"""
        if messagebox.askokcancel("退出 WatermarkSeal", "确定要关闭 WatermarkSeal 水印浏览器吗？"):
            self.root.destroy()

    def on_about(self):
        """Help -> 关于"""
        pillow_status = "已载入 (真实渲染模式启用)" if PILLOW_AVAILABLE else "未找到 (开发仿真模式已就绪)"
        messagebox.showinfo(
            "关于 WatermarkSeal",
            "WatermarkSeal - 桌面水印图片浏览器\n"
            "版本: v1.0.0\n"
            "引擎: Pillow (PIL) 图像处理内核\n"
            f"图像状态: {pillow_status}\n\n"
            "产品特色:\n"
            "• 真实图像内核：完全打通了图像旋转、缩放、多格式文件解码渲染\n"
            "• 物理水印叠加：开启后直接在图像层中动态合并半透明防伪文字水印\n"
            "• 内存风景生成：在没有本地图片的情况下，自动在内存中画风景画演示\n"
            "• 视窗智能拟合：自适应屏幕按钮能瞬间精确缩放任何分辨率的大图\n"
            "• 清晰度升级：配备 Windows 高分屏 DPI 精密级别感知渲染机制"
        )

# ==============================================================================
# 11. 程序入口点 (Main Entry Point)
# ==============================================================================
def main():
    root = tk.Tk()
    app = WatermarkSealApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
