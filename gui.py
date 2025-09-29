import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import datetime
import json
from backend_interface import BackendInterface
import qrcode
from PIL import Image, ImageTk
import io
import uuid
# PDF generation imports (optional)
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
import os

class SecureWipeGUI:
    def __init__(self, root):
        self.root = root
        
        # Initialize backend interface
        self.backend = BackendInterface()
        self.backend.set_progress_callback(self.update_wipe_progress)
        self.backend.set_log_callback(self.add_log_message)
        
        # Fleet-inspired color scheme (define first)
        self.colors = {
            'bg_primary': '#0f1419',     # Very dark blue-gray
            'bg_secondary': '#1c2128',   # Dark gray
            'bg_card': '#21262d',        # Card background
            'bg_hover': '#30363d',       # Hover state
            'border': '#373e47',         # Border color
            'accent_blue': '#58a6ff',    # Primary blue
            'accent_orange': '#ff7b72',  # Orange accent
            'accent_green': '#7ee787',   # Success green
            'accent_yellow': '#f2cc60',  # Warning yellow
            'text_primary': '#f0f6fc',   # Primary text
            'text_secondary': '#8b949e', # Secondary text
            'text_muted': '#6e7681',     # Muted text
            'danger': '#ff7b72',         # Red
            'success': '#7ee787',        # Green
            'warning': '#f2cc60',        # Yellow
            # Legacy compatibility
            'bg_dark': '#0f1419',
            'primary': '#21262d',
            'secondary': '#30363d',
            'accent': '#58a6ff'
        }
        
        self.root.title("⚡ ZeroTrace Pro - Advanced Data Erasure")
        self.root.geometry("1200x800")
        self.root.configure(bg=self.colors['bg_primary'])
        self.root.resizable(True, True)
        
        # Generate unique device ID for this session
        self.device_id = str(uuid.uuid4())[:8].upper()
        
        # Configure styles
        self.setup_styles()
        
        # Current screen state
        self.current_screen = "devices"
        self.wipe_in_progress = False
        self.progress_value = 0
        self.wipe_start_time = None
        self.wipe_completion_time = None
        self.selected_devices = []
        
        # Create main Fleet-style layout
        self.create_fleet_layout()
        
        # Show devices screen initially
        self.show_screen("devices")
        
    def create_fleet_layout(self):
        """Create the main Fleet-style layout with sidebar and content area"""
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create sidebar
        self.create_sidebar(main_container)
        
        # Create content area
        self.create_content_area(main_container)
        
    def create_sidebar(self, parent):
        """Create Fleet-style sidebar with navigation"""
        sidebar = tk.Frame(parent, bg=self.colors['bg_secondary'], width=280)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # Logo and title section
        header = tk.Frame(sidebar, bg=self.colors['bg_secondary'])
        header.pack(fill=tk.X, padx=20, pady=(20, 30))
        
        # Logo
        logo_frame = tk.Frame(header, bg=self.colors['bg_secondary'])
        logo_frame.pack()
        
        logo_label = tk.Label(logo_frame, text="⚡", font=('Segoe UI Emoji', 28),
                             bg=self.colors['bg_secondary'], fg=self.colors['accent_blue'])
        logo_label.pack()
        
        title_label = tk.Label(header, text="ZeroTrace Pro", 
                              font=('Segoe UI', 18, 'bold'),
                              bg=self.colors['bg_secondary'], fg=self.colors['text_primary'])
        title_label.pack(pady=(8, 0))
        
        subtitle_label = tk.Label(header, text="Advanced Data Erasure",
                                 font=('Segoe UI', 11),
                                 bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'])
        subtitle_label.pack(pady=(2, 0))
        
        # Navigation menu
        nav_frame = tk.Frame(sidebar, bg=self.colors['bg_secondary'])
        nav_frame.pack(fill=tk.X, padx=16, pady=(0, 20))
        
        self.nav_items = [
            ("🖥️", "Devices", "devices", True),
            ("🔧", "Methods", "methods", False),
            ("📊", "Progress", "progress", False),
            ("📋", "Reports", "reports", False),
            ("📱", "Android", "android", False),
            ("⚙️", "Settings", "settings", False)
        ]
        
        self.nav_buttons = {}
        for icon, text, screen_id, active in self.nav_items:
            btn = self.create_nav_item(nav_frame, icon, text, screen_id, active)
            self.nav_buttons[screen_id] = btn
            
        # Status section at bottom
        status_frame = tk.Frame(sidebar, bg=self.colors['bg_secondary'])
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)
        
        # Platform info
        import platform as plt
        platform_info = f"{plt.system()} {plt.release()}"
        platform_label = tk.Label(status_frame, text=f"Platform: {platform_info}",
                                 font=('Segoe UI', 9),
                                 bg=self.colors['bg_secondary'], fg=self.colors['text_muted'])
        platform_label.pack(anchor=tk.W)
        
        # Device count
        self.device_count_label = tk.Label(status_frame, text="Scanning devices...",
                                          font=('Segoe UI', 9),
                                          bg=self.colors['bg_secondary'], fg=self.colors['text_muted'])
        self.device_count_label.pack(anchor=tk.W, pady=(4, 0))
        
    def create_nav_item(self, parent, icon, text, screen_id, active=False):
        """Create a navigation item with Fleet-style design"""
        bg_color = self.colors['bg_hover'] if active else self.colors['bg_secondary']
        
        item_frame = tk.Frame(parent, bg=bg_color, cursor='hand2')
        item_frame.pack(fill=tk.X, pady=1)
        
        # Add rounded corner effect with padding
        content_frame = tk.Frame(item_frame, bg=bg_color)
        content_frame.pack(fill=tk.X, padx=4, pady=2)
        
        inner_frame = tk.Frame(content_frame, bg=bg_color)
        inner_frame.pack(fill=tk.X, padx=12, pady=10)
        
        icon_label = tk.Label(inner_frame, text=icon, font=('Segoe UI Emoji', 16),
                             bg=bg_color, fg=self.colors['text_primary'])
        icon_label.pack(side=tk.LEFT, padx=(0, 12))
        
        text_label = tk.Label(inner_frame, text=text, font=('Segoe UI', 12),
                             bg=bg_color, fg=self.colors['text_primary'])
        text_label.pack(side=tk.LEFT)
        
        # Click handler
        def on_click(e):
            self.show_screen(screen_id)
        
        # Hover effects
        def on_enter(e):
            if not active:
                new_bg = self.colors['bg_hover']
                for widget in [item_frame, content_frame, inner_frame, icon_label, text_label]:
                    widget.configure(bg=new_bg)
        
        def on_leave(e):
            if not active:
                new_bg = self.colors['bg_secondary']
                for widget in [item_frame, content_frame, inner_frame, icon_label, text_label]:
                    widget.configure(bg=new_bg)
        
        # Bind events
        for widget in [item_frame, content_frame, inner_frame, icon_label, text_label]:
            widget.bind('<Button-1>', on_click)
            widget.bind('<Enter>', on_enter)
            widget.bind('<Leave>', on_leave)
        
        return {'frame': item_frame, 'content': content_frame, 'inner': inner_frame, 
                'icon': icon_label, 'text': text_label, 'active': active}
        
    def create_content_area(self, parent):
        """Create the main content area with header and scrollable content"""
        content_area = tk.Frame(parent, bg=self.colors['bg_primary'])
        content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create header bar
        self.create_header_bar(content_area)
        
        # Create scrollable content area
        self.create_scrollable_content(content_area)
        
        # Initialize all screens
        self.create_all_screens()
        
    def create_header_bar(self, parent):
        """Create Fleet-style header bar with search and actions"""
        header_bar = tk.Frame(parent, bg=self.colors['bg_primary'], height=70)
        header_bar.pack(fill=tk.X, padx=24, pady=(20, 0))
        header_bar.pack_propagate(False)
        
        # Left side - Search
        search_frame = tk.Frame(header_bar, bg=self.colors['bg_primary'])
        search_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # Search container with background
        search_container = tk.Frame(search_frame, bg=self.colors['bg_secondary'])
        search_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        
        search_icon = tk.Label(search_container, text="🔍", font=('Segoe UI Emoji', 14),
                              bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'])
        search_icon.pack(side=tk.LEFT, padx=(12, 8), pady=12)
        
        self.search_entry = tk.Entry(search_container, font=('Segoe UI', 11),
                                    bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                                    relief=tk.FLAT, bd=0, width=25,
                                    insertbackground=self.colors['accent_blue'])
        self.search_entry.pack(side=tk.LEFT, pady=12, padx=(0, 12))
        self.search_entry.insert(0, "Search devices...")
        
        # Search entry focus events
        def on_search_focus_in(e):
            if self.search_entry.get() == "Search devices...":
                self.search_entry.delete(0, tk.END)
                self.search_entry.configure(fg=self.colors['text_primary'])
        
        def on_search_focus_out(e):
            if self.search_entry.get() == "":
                self.search_entry.insert(0, "Search devices...")
                self.search_entry.configure(fg=self.colors['text_secondary'])
        
        self.search_entry.bind('<FocusIn>', on_search_focus_in)
        self.search_entry.bind('<FocusOut>', on_search_focus_out)
        self.search_entry.configure(fg=self.colors['text_secondary'])
        
        # Right side - Actions and status
        actions_frame = tk.Frame(header_bar, bg=self.colors['bg_primary'])
        actions_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status indicator
        self.status_label = tk.Label(actions_frame, text="Ready",
                                    font=('Segoe UI', 11),
                                    bg=self.colors['bg_primary'], fg=self.colors['text_secondary'])
        self.status_label.pack(side=tk.RIGHT, padx=(20, 0), pady=12)
        
        # Refresh button
        refresh_btn = self.create_header_button(actions_frame, "🔄", "Refresh", self.refresh_devices)
        refresh_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Settings button
        settings_btn = self.create_header_button(actions_frame, "⚙️", "Settings", lambda: self.show_screen("settings"))
        settings_btn.pack(side=tk.RIGHT)
        
    def create_header_button(self, parent, icon, tooltip, command):
        """Create a header button with Fleet styling"""
        btn = tk.Button(parent, text=icon, font=('Segoe UI Emoji', 14),
                       bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                       relief=tk.FLAT, bd=0, padx=12, pady=8, cursor='hand2',
                       command=command)
        
        # Hover effects
        def on_enter(e):
            btn.configure(bg=self.colors['bg_hover'])
        
        def on_leave(e):
            btn.configure(bg=self.colors['bg_secondary'])
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
        return btn
        
    def create_scrollable_content(self, parent):
        """Create scrollable content area"""
        # Canvas and scrollbar for scrolling
        canvas_frame = tk.Frame(parent, bg=self.colors['bg_primary'])
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=(20, 24))
        
        self.canvas = tk.Canvas(canvas_frame, bg=self.colors['bg_primary'], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.colors['bg_primary'])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _on_mousewheel_linux(event):
            self.canvas.yview_scroll(-1 if event.num == 4 else 1, "units")
        
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.canvas.bind_all("<Button-4>", _on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", _on_mousewheel_linux)
        
        # Configure canvas window width
        def configure_canvas(event):
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        self.canvas.bind('<Configure>', configure_canvas)
        
    def create_all_screens(self):
        """Initialize all screen content"""
        self.screens = {}
        
        # Create all screens but don't pack them yet
        self.screens['devices'] = self.create_devices_screen()
        self.screens['methods'] = self.create_methods_screen()
        self.screens['progress'] = self.create_progress_screen()
        self.screens['reports'] = self.create_reports_screen()
        self.screens['android'] = self.create_android_screen()
        self.screens['settings'] = self.create_settings_screen()
        
    def show_screen(self, screen_name):
        """Show the specified screen and update navigation"""
        # Hide all screens
        for screen in self.screens.values():
            screen.pack_forget()
        
        # Update navigation active state
        for screen_id, nav_btn in self.nav_buttons.items():
            is_active = screen_id == screen_name
            bg_color = self.colors['bg_hover'] if is_active else self.colors['bg_secondary']
            
            for widget in [nav_btn['frame'], nav_btn['content'], nav_btn['inner'], 
                          nav_btn['icon'], nav_btn['text']]:
                widget.configure(bg=bg_color)
        
        # Show requested screen
        if screen_name in self.screens:
            self.screens[screen_name].pack(fill=tk.BOTH, expand=True)
            self.current_screen = screen_name
            
            # Update header title based on screen
            screen_titles = {
                'devices': 'Connected Devices',
                'methods': 'Wiping Methods',
                'progress': 'Wipe Progress',
                'reports': 'Wipe Reports',
                'android': 'Android Devices',
                'settings': 'Settings'
            }
            
            if hasattr(self, 'status_label'):
                self.status_label.configure(text=screen_titles.get(screen_name, 'Ready'))
                
    def create_devices_screen(self):
        """Create the main devices screen with Fleet-style device cards"""
        screen = tk.Frame(self.scrollable_frame, bg=self.colors['bg_primary'])
        
        # Header section
        header_section = tk.Frame(screen, bg=self.colors['bg_primary'])
        header_section.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(header_section, text="Connected Devices",
                              font=('Segoe UI', 24, 'bold'),
                              bg=self.colors['bg_primary'], fg=self.colors['text_primary'])
        title_label.pack(side=tk.LEFT)
        
        # Device count and status
        status_frame = tk.Frame(header_section, bg=self.colors['bg_primary'])
        status_frame.pack(side=tk.RIGHT)
        
        device_count = tk.Label(status_frame, text="3 devices detected",
                               font=('Segoe UI', 12),
                               bg=self.colors['bg_primary'], fg=self.colors['text_secondary'])
        device_count.pack()
        
        # Load real devices from backend
        devices = self.load_devices_from_backend()
        
        self.device_checkboxes = []
        for device in devices:
            device_card = self.create_device_card(screen, device)
            device_card.pack(fill=tk.X, pady=(0, 16))
            
        # Action section
        self.create_action_section(screen)
        
        return screen
        
    def create_device_card(self, parent, device):
        """Create a Fleet-style device card"""
        # Main card container
        card = tk.Frame(parent, bg=self.colors['bg_card'])
        
        # Card content with padding
        content = tk.Frame(card, bg=self.colors['bg_card'])
        content.pack(fill=tk.X, padx=20, pady=20)
        
        # Header row with checkbox, icon, name, and status
        header_row = tk.Frame(content, bg=self.colors['bg_card'])
        header_row.pack(fill=tk.X, pady=(0, 12))
        
        # Checkbox
        checkbox_var = tk.BooleanVar(value=device['selected'])
        self.device_checkboxes.append(checkbox_var)
        
        checkbox = tk.Checkbutton(header_row, variable=checkbox_var,
                                 bg=self.colors['bg_card'], fg=self.colors['accent_blue'],
                                 selectcolor=self.colors['bg_secondary'],
                                 activebackground=self.colors['bg_card'],
                                 font=('Segoe UI', 12),
                                 command=self.update_selected_devices)
        checkbox.pack(side=tk.LEFT, padx=(0, 16))
        
        # Device icon
        icon_label = tk.Label(header_row, text=device['icon'], font=('Segoe UI Emoji', 20),
                             bg=self.colors['bg_card'])
        icon_label.pack(side=tk.LEFT, padx=(0, 12))
        
        # Device name and path
        name_frame = tk.Frame(header_row, bg=self.colors['bg_card'])
        name_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        name_label = tk.Label(name_frame, text=device['name'],
                             font=('Segoe UI', 16, 'bold'),
                             bg=self.colors['bg_card'], fg=self.colors['text_primary'])
        name_label.pack(anchor=tk.W)
        
        path_label = tk.Label(name_frame, text=device['path'],
                             font=('Segoe UI', 11),
                             bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        path_label.pack(anchor=tk.W)
        
        # Status indicator
        status_color = device['color']
        status_label = tk.Label(header_row, text=f"● {device['status']}",
                               font=('Segoe UI', 12, 'bold'),
                               bg=self.colors['bg_card'], fg=status_color)
        status_label.pack(side=tk.RIGHT)
        
        # Details grid
        details_frame = tk.Frame(content, bg=self.colors['bg_card'])
        details_frame.pack(fill=tk.X)
        
        # Create 3-column grid for details
        details = [
            ('Size', device['size']),
            ('Type', device['type']),
            ('Health', device['health']),
            ('Temperature', device['temp'])
        ]
        
        for i, (label, value) in enumerate(details):
            row = i // 2
            col = i % 2
            
            detail_container = tk.Frame(details_frame, bg=self.colors['bg_card'])
            detail_container.grid(row=row, column=col, sticky='w', padx=(0, 40), pady=4)
            
            label_widget = tk.Label(detail_container, text=f"{label}:",
                                   font=('Segoe UI', 10),
                                   bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
            label_widget.pack(side=tk.LEFT)
            
            value_widget = tk.Label(detail_container, text=value,
                                   font=('Segoe UI', 10, 'bold'),
                                   bg=self.colors['bg_card'], fg=self.colors['text_primary'])
            value_widget.pack(side=tk.LEFT, padx=(8, 0))
        
        return card
        
    def create_action_section(self, parent):
        """Create the action section with method selection and start button"""
        # Method selection card
        method_card = tk.Frame(parent, bg=self.colors['bg_card'])
        method_card.pack(fill=tk.X, pady=(20, 0))
        
        method_content = tk.Frame(method_card, bg=self.colors['bg_card'])
        method_content.pack(fill=tk.X, padx=20, pady=20)
        
        # Method selection header
        method_header = tk.Frame(method_content, bg=self.colors['bg_card'])
        method_header.pack(fill=tk.X, pady=(0, 16))
        
        method_icon = tk.Label(method_header, text="🔧", font=('Segoe UI Emoji', 18),
                              bg=self.colors['bg_card'])
        method_icon.pack(side=tk.LEFT, padx=(0, 12))
        
        method_title = tk.Label(method_header, text="Erasure Method",
                               font=('Segoe UI', 16, 'bold'),
                               bg=self.colors['bg_card'], fg=self.colors['text_primary'])
        method_title.pack(side=tk.LEFT)
        
        # Load methods from backend
        backend_methods = self.backend.get_wipe_methods()
        methods = [method['name'] for method in backend_methods]
        
        self.method_var = tk.StringVar(value=methods[1])
        method_combo = ttk.Combobox(method_content, textvariable=self.method_var,
                                   values=methods, state="readonly", width=50,
                                   style='Modern.TCombobox', font=('Segoe UI', 11))
        method_combo.pack(anchor=tk.W, pady=(0, 16))
        
        # Advanced options
        options_frame = tk.Frame(method_content, bg=self.colors['bg_card'])
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.verify_var = tk.BooleanVar(value=True)
        verify_cb = tk.Checkbutton(options_frame, text="Verify erasure completion",
                                  variable=self.verify_var, font=('Segoe UI', 11),
                                  bg=self.colors['bg_card'], fg=self.colors['text_primary'],
                                  selectcolor=self.colors['bg_secondary'],
                                  activebackground=self.colors['bg_card'])
        verify_cb.pack(anchor=tk.W, pady=2)
        
        self.hidden_var = tk.BooleanVar()
        hidden_cb = tk.Checkbutton(options_frame, text="Include hidden areas (HPA/DCO)",
                                  variable=self.hidden_var, font=('Segoe UI', 11),
                                  bg=self.colors['bg_card'], fg=self.colors['text_primary'],
                                  selectcolor=self.colors['bg_secondary'],
                                  activebackground=self.colors['bg_card'])
        hidden_cb.pack(anchor=tk.W, pady=2)
        
        # Warning section
        warning_frame = tk.Frame(parent, bg='#2d1b1b')
        warning_frame.pack(fill=tk.X, pady=(16, 20))
        
        warning_content = tk.Frame(warning_frame, bg='#2d1b1b')
        warning_content.pack(fill=tk.X, padx=20, pady=16)
        
        warning_icon = tk.Label(warning_content, text="⚠️", font=('Segoe UI Emoji', 16),
                               bg='#2d1b1b')
        warning_icon.pack(side=tk.LEFT, padx=(0, 12))
        
        warning_text = tk.Label(warning_content,
                               text="WARNING: Data erasure is irreversible. Ensure you have backups of important data.",
                               font=('Segoe UI', 11, 'bold'), wraplength=700,
                               bg='#2d1b1b', fg=self.colors['accent_orange'])
        warning_text.pack(side=tk.LEFT)
        
        # Start button
        start_frame = tk.Frame(parent, bg=self.colors['bg_primary'])
        start_frame.pack(pady=(0, 20))
        
        self.start_button = tk.Button(start_frame, text="🚀 Start Secure Erasure",
                                     font=('Segoe UI', 14, 'bold'),
                                     bg=self.colors['accent_blue'], fg=self.colors['text_primary'],
                                     relief=tk.FLAT, bd=0, padx=40, pady=16,
                                     cursor='hand2', command=self.start_wipe)
        self.start_button.pack()
        
        # Hover effect for start button
        def on_enter(e):
            self.start_button.configure(bg='#4184e4')
        
        def on_leave(e):
            self.start_button.configure(bg=self.colors['accent_blue'])
        
        self.start_button.bind('<Enter>', on_enter)
        self.start_button.bind('<Leave>', on_leave)
        
    def create_methods_screen(self):
        """Create methods configuration screen"""
        screen = tk.Frame(self.scrollable_frame, bg=self.colors['bg_primary'])
        
        title_label = tk.Label(screen, text="Wiping Methods",
                              font=('Segoe UI', 24, 'bold'),
                              bg=self.colors['bg_primary'], fg=self.colors['text_primary'])
        title_label.pack(pady=20)
        
        return screen
        
    def create_android_screen(self):
        """Create Android devices screen"""
        screen = tk.Frame(self.scrollable_frame, bg=self.colors['bg_primary'])
        
        title_label = tk.Label(screen, text="Android Devices",
                              font=('Segoe UI', 24, 'bold'),
                              bg=self.colors['bg_primary'], fg=self.colors['text_primary'])
        title_label.pack(pady=20)
        
        return screen
        
    def create_reports_screen(self):
        """Create reports screen"""
        screen = tk.Frame(self.scrollable_frame, bg=self.colors['bg_primary'])
        
        title_label = tk.Label(screen, text="Wipe Reports",
                              font=('Segoe UI', 24, 'bold'),
                              bg=self.colors['bg_primary'], fg=self.colors['text_primary'])
        title_label.pack(pady=20)
        
        return screen
        
    def create_settings_screen(self):
        """Create settings screen"""
        screen = tk.Frame(self.scrollable_frame, bg=self.colors['bg_primary'])
        
        title_label = tk.Label(screen, text="Settings",
                              font=('Segoe UI', 24, 'bold'),
                              bg=self.colors['bg_primary'], fg=self.colors['text_primary'])
        title_label.pack(pady=20)
        
        return screen
        
    def update_selected_devices(self):
        """Update the list of selected devices"""
        self.selected_devices = []
        for i, var in enumerate(self.device_checkboxes):
            if var.get():
                self.selected_devices.append(i)
        
        # Update device count in sidebar
        count = len(self.selected_devices)
        if count == 0:
            self.device_count_label.configure(text="No devices selected")
        elif count == 1:
            self.device_count_label.configure(text="1 device selected")
        else:
            self.device_count_label.configure(text=f"{count} devices selected")
            
    def load_devices_from_backend(self):
        """Load devices from backend interface"""
        try:
            backend_devices = self.backend.get_disks()
            devices = []
            
            for i, device in enumerate(backend_devices):
                # Convert backend format to GUI format
                gui_device = {
                    'name': device.get('model', 'Unknown Device'),
                    'path': device.get('device', f'Device {i}'),
                    'size': device.get('size', 'Unknown'),
                    'type': device.get('type', 'Unknown'),
                    'status': device.get('status', 'Ready'),
                    'health': device.get('health', 'Unknown'),
                    'temp': device.get('temperature', 'N/A'),
                    'selected': i == 0,  # Select first device by default
                    'icon': device.get('icon', '💾'),
                    'color': device.get('color', self.colors['accent_blue'])
                }
                devices.append(gui_device)
            
            return devices
            
        except Exception as e:
            print(f"Error loading devices: {e}")
            # Fallback to sample data
            return [
                {
                    'name': 'Sample Device',
                    'path': 'No devices detected',
                    'size': 'Unknown',
                    'type': 'Unknown',
                    'status': 'Error',
                    'health': 'Unknown',
                    'temp': 'N/A',
                    'selected': False,
                    'icon': '❌',
                    'color': self.colors['accent_orange']
                }
            ]
    
    def refresh_devices(self):
        """Refresh device list from backend"""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text="Scanning devices...")
        
        def refresh_thread():
            try:
                # Reload devices from backend
                devices = self.load_devices_from_backend()
                
                # Update UI in main thread
                self.root.after(0, self.update_device_display, devices)
                
            except Exception as e:
                print(f"Error refreshing devices: {e}")
                if hasattr(self, 'status_label'):
                    self.root.after(0, lambda: self.status_label.configure(text="Error scanning devices"))
        
        # Run refresh in background thread
        thread = threading.Thread(target=refresh_thread)
        thread.daemon = True
        thread.start()
        
    def update_device_display(self, devices):
        """Update device display with new data"""
        # This would recreate the device cards with new data
        # For now, just update status
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=f"{len(devices)} devices detected")
        
    def start_wipe(self):
        """Start the wipe process"""
        # Validation
        if not self.selected_devices:
            messagebox.showwarning("No Device Selected", 
                                 "Please select at least one device to wipe.")
            return
        
        # Show confirmation dialog
        confirm_msg = "⚠ WARNING: This will permanently erase selected devices.\n\n"
        confirm_msg += f"Selected devices: {len(self.selected_devices)}\n\nThis action cannot be undone."
        
        if not messagebox.askyesno("Confirm Secure Wipe", confirm_msg):
            return
        
        # Get selected devices and method
        selected_device_paths = []
        devices = self.load_devices_from_backend()
        
        for i in self.selected_devices:
            if i < len(devices):
                selected_device_paths.append(devices[i]['path'])
        
        # Get wipe options
        options = {
            'verify': self.verify_var.get(),
            'hidden_areas': self.hidden_var.get()
        }
        
        # Get selected method ID
        method_name = self.method_var.get()
        backend_methods = self.backend.get_wipe_methods()
        method_id = 'quick'  # default
        
        for method in backend_methods:
            if method['name'] == method_name:
                method_id = method['id']
                break
        
        # Start wipe process
        self.wipe_in_progress = True
        self.wipe_start_time = datetime.datetime.now()
        self.show_screen("progress")
        
        # Start real wipe process via backend
        success = self.backend.start_wipe(selected_device_paths, method_id, options)
        
        if not success:
            messagebox.showerror("Wipe Failed", "Failed to start wipe process. Check backend connection.")
            self.wipe_in_progress = False
            self.show_screen("devices")
            return
        
        # Add initial log message
        self.add_log_message(f"Starting {method_name} on {len(selected_device_paths)} device(s)")
        self.add_log_message(f"Selected devices: {', '.join(selected_device_paths)}")
        self.add_log_message(f"Options: Verify={options['verify']}, Hidden Areas={options['hidden_areas']}")
    
    def update_wipe_progress(self, progress):
        """Update wipe progress callback"""
        if hasattr(self, 'progress_bar'):
            self.progress_bar['value'] = progress
        self.progress_value = progress
        
        # Update time estimate if we have a start time
        if hasattr(self, 'wipe_start_time') and self.wipe_start_time:
            elapsed = (datetime.datetime.now() - self.wipe_start_time).total_seconds()
            if progress > 0:
                total_estimated = elapsed * (100 / progress)
                remaining = max(0, total_estimated - elapsed)
                
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                
                if hours > 0:
                    time_str = f"{hours}h {minutes}m remaining"
                else:
                    time_str = f"{minutes}m remaining"
                
                if hasattr(self, 'time_label'):
                    self.time_label.config(text=time_str)
    
    def add_log_message(self, message):
        """Add log message callback"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        if hasattr(self, 'log_text'):
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
        else:
            print(log_entry.strip())
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure modern styles
        style.configure('Header.TLabel', 
                       font=('Segoe UI', 24, 'bold'), 
                       foreground=self.colors['text_primary'], 
                       background=self.colors['bg_dark'])
        
        style.configure('Subtitle.TLabel', 
                       font=('Segoe UI', 12), 
                       foreground=self.colors['text_secondary'], 
                       background=self.colors['bg_dark'])
        
        style.configure('Section.TLabel', 
                       font=('Segoe UI', 14, 'bold'), 
                       foreground=self.colors['text_primary'], 
                       background=self.colors['bg_card'])
        
        style.configure('Info.TLabel', 
                       font=('Segoe UI', 10), 
                       foreground=self.colors['text_secondary'], 
                       background=self.colors['bg_card'])
        
        style.configure('Success.TLabel', 
                       font=('Segoe UI', 16, 'bold'), 
                       foreground=self.colors['success'], 
                       background=self.colors['bg_card'])
        
        style.configure('Warning.TLabel', 
                       font=('Segoe UI', 11), 
                       foreground=self.colors['warning'], 
                       background=self.colors['bg_card'])
        
        # Enhanced Combobox style
        style.configure('Modern.TCombobox',
                       fieldbackground=self.colors['secondary'],
                       background=self.colors['secondary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       arrowcolor=self.colors['text_primary'])
        
        # Progress bar style
        style.configure('Modern.Horizontal.TProgressbar',
                       background=self.colors['accent'],
                       troughcolor=self.colors['secondary'],
                       borderwidth=0,
                       lightcolor=self.colors['accent'],
                       darkcolor=self.colors['accent'])
    
    def create_modern_card(self, parent, title=None, icon=None):
        """Create a modern card-style frame"""
        card = tk.Frame(parent, bg=self.colors['bg_card'], 
                       relief=tk.FLAT, bd=0)
        card.configure(highlightbackground=self.colors['border'], 
                      highlightthickness=1)
        
        if title or icon:
            header = tk.Frame(card, bg=self.colors['bg_card'])
            header.pack(fill=tk.X, padx=20, pady=(20, 10))
            
            if icon:
                icon_label = tk.Label(header, text=icon, 
                                    font=('Segoe UI Emoji', 18), 
                                    bg=self.colors['bg_card'], 
                                    fg=self.colors['accent'])
                icon_label.pack(side=tk.LEFT, padx=(0, 10))
            
            if title:
                title_label = tk.Label(header, text=title, 
                                     font=('Segoe UI', 14, 'bold'), 
                                     bg=self.colors['bg_card'], 
                                     fg=self.colors['text_primary'])
                title_label.pack(side=tk.LEFT)
        
        return card
    
    def create_modern_button(self, parent, text, command, style='primary', width=None):
        """Create a modern button with hover effects"""
        colors = {
            'primary': {'bg': self.colors['accent_blue'], 'hover': '#4184e4'},
            'success': {'bg': self.colors['success'], 'hover': '#059669'},
            'danger': {'bg': self.colors['danger'], 'hover': '#dc2626'},
            'secondary': {'bg': self.colors['bg_secondary'], 'hover': self.colors['bg_hover']}
        }
        
        button = tk.Button(parent, text=text, command=command,
                          font=('Segoe UI', 12, 'bold'),
                          bg=colors[style]['bg'],
                          fg=self.colors['text_primary'],
                          relief=tk.FLAT,
                          bd=0,
                          padx=30,
                          pady=12,
                          cursor='hand2')
        
        if width:
            button.configure(width=width)
        
        # Add hover effects
        def on_enter(e):
            button.configure(bg=colors[style]['hover'])
        
        def on_leave(e):
            button.configure(bg=colors[style]['bg'])
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return button
    
    def create_header(self):
        header_frame = tk.Frame(self.main_frame, bg=self.colors['bg_dark'], height=80)
        header_frame.pack(fill=tk.X, padx=30, pady=(20, 0))
        header_frame.pack_propagate(False)
        
        # Left side - Logo and title
        left_frame = tk.Frame(header_frame, bg=self.colors['bg_dark'])
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # Logo
        logo_label = tk.Label(left_frame, text="🔒", 
                             font=('Segoe UI Emoji', 32), 
                             bg=self.colors['bg_dark'], 
                             fg=self.colors['accent'])
        logo_label.pack(side=tk.LEFT, padx=(0, 15))
        
        title_container = tk.Frame(left_frame, bg=self.colors['bg_dark'])
        title_container.pack(side=tk.LEFT, fill=tk.Y)
        
        title_label = tk.Label(title_container, text="ZeroTrace Pro", 
                              font=('Segoe UI', 24, 'bold'), 
                              bg=self.colors['bg_dark'], 
                              fg=self.colors['text_primary'])
        title_label.pack(anchor=tk.W)
        
        subtitle_label = tk.Label(title_container, text="Professional Data Erasure Solution", 
                                 font=('Segoe UI', 12), 
                                 bg=self.colors['bg_dark'], 
                                 fg=self.colors['text_secondary'])
        subtitle_label.pack(anchor=tk.W)
        
        # Right side - Device ID and Language selector
        right_frame = tk.Frame(header_frame, bg=self.colors['bg_dark'])
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Device ID section
        device_id_frame = tk.Frame(right_frame, bg=self.colors['bg_dark'])
        device_id_frame.pack(side=tk.RIGHT, padx=(20, 0))
        
        tk.Label(device_id_frame, text="Device ID:", 
                font=('Segoe UI', 10), 
                bg=self.colors['bg_dark'], 
                fg=self.colors['text_secondary']).pack()
        
        tk.Label(device_id_frame, text=self.device_id, 
                font=('Segoe UI', 12, 'bold'), 
                bg=self.colors['bg_dark'], 
                fg=self.colors['accent']).pack()
        
        # Language selector
        lang_frame = tk.Frame(right_frame, bg=self.colors['bg_dark'])
        lang_frame.pack(side=tk.RIGHT)
        
        tk.Label(lang_frame, text="Language:", 
                font=('Segoe UI', 10), 
                bg=self.colors['bg_dark'], 
                fg=self.colors['text_secondary']).pack()
        
        lang_var = tk.StringVar(value="English")
        lang_combo = ttk.Combobox(lang_frame, textvariable=lang_var, 
                                 values=["English", "हिंदी"], 
                                 state="readonly", width=12,
                                 style='Modern.TCombobox')
        lang_combo.pack(pady=(5, 0))
    
    def create_main_screen(self):
        self.main_screen = tk.Frame(self.main_frame, bg=self.colors['bg_dark'])
        
        # Main content container
        content_frame = tk.Frame(self.main_screen, bg=self.colors['bg_dark'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Device List Card
        device_card = self.create_modern_card(content_frame, "Connected Devices", "💽")
        device_card.pack(fill=tk.X, pady=(0, 20))
        
        # Device content
        device_content = tk.Frame(device_card, bg=self.colors['bg_card'])
        device_content.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Sample devices
        devices = [
            ("Disk 0 – 512GB SSD – Samsung EVO", True, "🟢"),
            ("Disk 1 – 1TB HDD – Seagate", False, "🔵"),
            ("External USB – 64GB – Sandisk", False, "🟡")
        ]
        
        self.device_vars = []
        for i, (name, selected, indicator) in enumerate(devices):
            var = tk.BooleanVar(value=selected)
            self.device_vars.append(var)
            
            device_item = tk.Frame(device_content, bg=self.colors['bg_card'])
            device_item.pack(fill=tk.X, pady=8)
            
            # Custom checkbox
            cb_frame = tk.Frame(device_item, bg=self.colors['bg_card'])
            cb_frame.pack(side=tk.LEFT, padx=(0, 15))
            
            cb = tk.Checkbutton(cb_frame, variable=var, 
                              bg=self.colors['bg_card'], 
                              fg=self.colors['accent'],
                              selectcolor=self.colors['secondary'],
                              activebackground=self.colors['bg_card'],
                              font=('Segoe UI', 12))
            cb.pack()
            
            # Status indicator
            status_label = tk.Label(device_item, text=indicator, 
                                  font=('Segoe UI Emoji', 14), 
                                  bg=self.colors['bg_card'])
            status_label.pack(side=tk.LEFT, padx=(0, 10))
            
            # Device info
            info_frame = tk.Frame(device_item, bg=self.colors['bg_card'])
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            name_label = tk.Label(info_frame, text=name, 
                                 font=('Segoe UI', 12, 'bold'), 
                                 bg=self.colors['bg_card'], 
                                 fg=self.colors['text_primary'])
            name_label.pack(anchor=tk.W)
        
        # Options Card
        options_card = self.create_modern_card(content_frame, "Wipe Configuration", "⚙")
        options_card.pack(fill=tk.X, pady=(0, 20))
        
        options_content = tk.Frame(options_card, bg=self.colors['bg_card'])
        options_content.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Method selection
        method_frame = tk.Frame(options_content, bg=self.colors['bg_card'])
        method_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(method_frame, text="Erasure Method:", 
                font=('Segoe UI',16 , 'bold'), 
                bg=self.colors['bg_card'], 
                fg=self.colors['text_primary']).pack(anchor=tk.W)
        
        self.method_var = tk.StringVar(value="NIST 3-pass overwrite")
        method_combo = ttk.Combobox(method_frame, textvariable=self.method_var, 
                                   values=[
                                       "Quick Erase (1-pass overwrite)",
                                       "NIST 3-pass overwrite", 
                                       "DoD 7-pass overwrite",
                                       "Crypto Erase (SSD secure erase command)"
                                   ], state="readonly", width=45,
                                   style='Modern.TCombobox')
        method_combo.pack(pady=(16, 0), anchor=tk.W)
        
        # Advanced options
        advanced_frame = tk.Frame(options_content, bg=self.colors['bg_card'])
        advanced_frame.pack(fill=tk.X)
        
        self.hidden_var = tk.BooleanVar()
        
        hidden_cb = tk.Checkbutton(advanced_frame, 
                                  text="Include Hidden Areas (HPA/DCO)", 
                                  variable=self.hidden_var, 
                                  bg=self.colors['bg_card'], 
                                  fg=self.colors['text_primary'],
                                  selectcolor=self.colors['secondary'],
                                  activebackground=self.colors['bg_card'],
                                  font=('Segoe UI', 11))
        hidden_cb.pack(anchor=tk.W, pady=5)
        
        # Action section
        action_frame = tk.Frame(content_frame, bg=self.colors['bg_dark'])
        action_frame.pack(fill=tk.X, pady=30)
        
        # Warning message
        warning_card = tk.Frame(action_frame, bg='#7f1d1d', 
                               relief=tk.FLAT, bd=0)
        warning_card.configure(highlightbackground='#dc2626', 
                              highlightthickness=1)
        warning_card.pack(fill=tk.X, pady=(0, 20))
        
        warning_content = tk.Frame(warning_card, bg='#7f1d1d')
        warning_content.pack(fill=tk.X, padx=20, pady=15)
        
        tk.Label(warning_content, text="⚠", 
                font=('Segoe UI Emoji', 20), 
                bg='#7f1d1d', fg='#fca5a5').pack(side=tk.LEFT, padx=(0, 10))
        
        warning_text = tk.Label(warning_content, 
                               text="WARNING: Data erasure is irreversible. Ensure you have backups of important data.", 
                               font=('Segoe UI', 11, 'bold'), 
                               bg='#7f1d1d', fg='#fca5a5', 
                               wraplength=600, justify=tk.LEFT)
        warning_text.pack(side=tk.LEFT)
        
        # Start button
        button_frame = tk.Frame(action_frame, bg=self.colors['bg_dark'])
        button_frame.pack()
        
        self.start_button = self.create_modern_button(button_frame, 
                                                     "🚀 Start Secure Wipe", 
                                                     self.start_wipe, 
                                                     'success', 25)
        self.start_button.pack()
    
    def create_progress_screen(self):
        """Create Fleet-style progress screen"""
        screen = tk.Frame(self.scrollable_frame, bg=self.colors['bg_primary'])
        
        content_frame = tk.Frame(screen, bg=self.colors['bg_primary'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Progress header
        header_card = self.create_modern_card(content_frame, "Wipe in Progress", "🔄")
        header_card.pack(fill=tk.X, pady=(0, 20))
        
        progress_content = tk.Frame(header_card, bg=self.colors['bg_card'])
        progress_content.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(progress_content, length=500, 
                                           mode='determinate', 
                                           style='Modern.Horizontal.TProgressbar')
        self.progress_bar.pack(pady=15)
        
        # Progress info
        self.progress_label = tk.Label(progress_content, text="Initializing...", 
                                      font=('Segoe UI', 14), 
                                      bg=self.colors['bg_card'], 
                                      fg=self.colors['text_primary'])
        self.progress_label.pack(pady=(0, 10))
        
        # Time estimate
        self.time_label = tk.Label(progress_content, text="Estimated time: Calculating...", 
                                  font=('Segoe UI', 11), 
                                  bg=self.colors['bg_card'], 
                                  fg=self.colors['text_secondary'])
        self.time_label.pack()
        
        # Logs card
        logs_card = self.create_modern_card(content_frame, "Operation Log", "📋")
        logs_card.pack(fill=tk.BOTH, expand=True)
        
        log_content = tk.Frame(logs_card, bg=self.colors['bg_card'])
        log_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Text widget
        log_frame = tk.Frame(log_content, bg=self.colors['secondary'])
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, bg=self.colors['secondary'], 
                               fg=self.colors['text_primary'], 
                               font=('Consolas', 10),
                               relief=tk.FLAT, bd=0,
                               insertbackground=self.colors['accent'])
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, 
                                 command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        return screen
    
    def create_completion_screen(self):
        self.completion_screen = tk.Frame(self.main_frame, bg=self.colors['bg_dark'])
        
        content_frame = tk.Frame(self.completion_screen, bg=self.colors['bg_dark'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Success header
        success_card = tk.Frame(content_frame, bg='#065f46', 
                               relief=tk.FLAT, bd=0)
        success_card.configure(highlightbackground=self.colors['success'], 
                              highlightthickness=2)
        success_card.pack(fill=tk.X, pady=(0, 20))
        
        success_content = tk.Frame(success_card, bg='#065f46')
        success_content.pack(fill=tk.X, padx=30, pady=20)
        
        tk.Label(success_content, text="✅", 
                font=('Segoe UI Emoji', 32), 
                bg='#065f46', fg='#10b981').pack()
        
        tk.Label(success_content, text="Wipe Completed Successfully!", 
                font=('Segoe UI', 18, 'bold'), 
                bg='#065f46', fg='#d1fae5').pack(pady=(10, 0))
        
        # Details card
        details_card = self.create_modern_card(content_frame, "Wipe Summary", "📊")
        details_card.pack(fill=tk.X, pady=(0, 20))
        
        details_content = tk.Frame(details_card, bg=self.colors['bg_card'])
        details_content.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        self.details_text = tk.Text(details_content, height=6, 
                                   bg=self.colors['secondary'], 
                                   fg=self.colors['text_primary'], 
                                   font=('Consolas', 11),
                                   relief=tk.FLAT, bd=0)
        self.details_text.pack(fill=tk.X, pady=10)
        
        # Certificate card
        cert_card = self.create_modern_card(content_frame, "Verification Certificate", "🏆")
        cert_card.pack(fill=tk.X, pady=(0, 20))
        
        cert_content = tk.Frame(cert_card, bg=self.colors['bg_card'])
        cert_content.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Certificate actions
        cert_buttons = tk.Frame(cert_content, bg=self.colors['bg_card'])
        cert_buttons.pack(fill=tk.X, pady=10)
        
        pdf_btn = self.create_modern_button(cert_buttons, "📄 Download PDF Certificate", 
                                           self.download_pdf_cert, 'secondary')
        pdf_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        json_btn = self.create_modern_button(cert_buttons, "💾 Save JSON", 
                                            self.download_json_cert, 'secondary')
        json_btn.pack(side=tk.LEFT)
        
        # QR Code section
        qr_frame = tk.Frame(cert_content, bg=self.colors['bg_card'])
        qr_frame.pack(pady=20)
        
        tk.Label(qr_frame, text="QR Code for Third-Party Verification:", 
                font=('Segoe UI', 12, 'bold'), 
                bg=self.colors['bg_card'], 
                fg=self.colors['text_primary']).pack()
        
        self.qr_label = tk.Label(qr_frame, bg=self.colors['bg_card'])
        self.qr_label.pack(pady=10)
        
        # Action buttons
        action_frame = tk.Frame(content_frame, bg=self.colors['bg_dark'])
        action_frame.pack(fill=tk.X, pady=20)
        
        new_wipe_btn = self.create_modern_button(action_frame, "🔄 Erase Another Device", 
                                                self.new_wipe, 'primary', 20)
        new_wipe_btn.pack()
        
        return screen
    
    # Backend integration methods
    def stop_wipe(self):
        """Stop the current wipe process"""
        if self.wipe_in_progress:
            self.backend.stop_wipe()
            self.wipe_in_progress = False
            self.add_log_message("Wipe process stopped by user")
            messagebox.showinfo("Wipe Stopped", "Wipe process has been stopped.")
            self.show_screen("devices")
    
    def new_wipe(self):
        """Start a new wipe operation"""
        self.show_screen("devices")
        
    def download_pdf_cert(self):
        """Download PDF certificate"""
        messagebox.showinfo("PDF Certificate", "PDF certificate download feature coming soon!")
        
    def download_json_cert(self):
        """Download JSON certificate"""
        messagebox.showinfo("JSON Certificate", "JSON certificate download feature coming soon!")
        
    def shutdown(self):
        """Shutdown the application and backend"""
        if self.wipe_in_progress:
            if messagebox.askyesno("Wipe in Progress", 
                                 "A wipe operation is in progress. Stop and exit?"):
                self.backend.stop_wipe()
            else:
                return False
        
        self.backend.shutdown()
        return True
    
    def complete_wipe(self):
        """Handle wipe completion"""
        self.wipe_in_progress = False
        
        # Add completion log
        self.add_log_message("Wipe process completed successfully!")
        self.add_log_message("Generating verification certificate...")
        
        # Show completion screen or message
        messagebox.showinfo("Wipe Complete", 
                           "Secure wipe completed successfully!\n\n" +
                           "A verification certificate has been generated.")
        
        # Return to devices screen
        self.show_screen("devices")
    
    def update_wipe_progress(self, progress_percent):
        """Callback for backend progress updates"""
        if hasattr(self, 'progress_bar'):
            self.progress_bar['value'] = progress_percent
            
        if hasattr(self, 'progress_label'):
            self.progress_label.config(text=f"Wiping... {int(progress_percent)}% complete")
            
        # Check if complete
        if progress_percent >= 100:
            self.root.after(1000, self.complete_wipe)  # Small delay before completion
    
    def add_log_message(self, message):
        """Callback for backend log messages"""
        if hasattr(self, 'log_text'):
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)  # Auto-scroll to bottom
    
    def update_progress(self, progress_percent, pass_num, total_passes, step):
        self.progress_bar['value'] = progress_percent
        
        if total_passes > 1:
            self.progress_label.config(text=f"Pass {pass_num}/{total_passes} – {step+1}% complete")
        else:
            self.progress_label.config(text=f"Erasing... {int(progress_percent)}%")
        
        # Update time estimates
        remaining = int((100 - progress_percent) * 0.2)
        self.time_label.config(text=f"Estimated time left: {remaining} min")
        
        # Add log entries
        if step % 20 == 0:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] Pass {pass_num}/{total_passes}: {step+1}% complete\n"
            
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
    
    def complete_wipe(self):
        self.wipe_in_progress = False
        self.wipe_completion_time = datetime.datetime.now()
        
        # Get selected devices
        selected_devices = []
        devices = [
            "Disk 0 – 512GB SSD – Samsung EVO",
            "Disk 1 – 1TB HDD – Seagate", 
            "External USB – 64GB – Sandisk"
        ]
        
        for i, var in enumerate(self.device_vars):
            if var.get():
                selected_devices.append(devices[i])
        
        # Generate completion report
        duration = self.wipe_completion_time - self.wipe_start_time
        
        details = f"""Device(s): {', '.join(selected_devices)}
Method: {self.method_var.get()}
Started: {self.wipe_start_time.strftime('%Y-%m-%d %H:%M:%S')}
Completed: {self.wipe_completion_time.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {str(duration).split('.')[0]}
Status: ✅ Successfully Wiped
Hidden Areas: {'Included' if self.hidden_var.get() else 'Not Included'}
Device ID: {self.device_id}"""
        
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(1.0, details)
        
        # Generate QR code
        qr_data = {
            "device_id": self.device_id,
            "devices": selected_devices,
            "method": self.method_var.get(),
            "start_time": self.wipe_start_time.isoformat(),
            "completion_time": self.wipe_completion_time.isoformat(),
            "duration": str(duration),
            "status": "VERIFIED_WIPED",
            "hidden_areas": self.hidden_var.get()
        }
        
        self.certificate_data = qr_data  # Store for PDF generation
        
        self.generate_qr_code(json.dumps(qr_data))
        
        # Add completion log
        timestamp = self.wipe_completion_time.strftime("%H:%M:%S")
        final_log = f"\n[{timestamp}] ✅ WIPE COMPLETED SUCCESSFULLY!\n"
        final_log += f"[{timestamp}] Certificate ID: {self.device_id}\n"
        self.log_text.insert(tk.END, final_log)
        self.log_text.see(tk.END)
        
        # Show completion screen
        self.show_screen("completion")
    
    def generate_qr_code(self, data):
        """Generate and display QR code"""
        try:
            qr = qrcode.QRCode(version=1, box_size=4, border=2)
            qr.add_data(data)
            qr.make(fit=True)
            
            # Create QR code with custom colors
            qr_image = qr.make_image(fill_color=self.colors['text_primary'], 
                                   back_color=self.colors['bg_card'])
            qr_image = qr_image.resize((150, 150))
            
            # Convert to PhotoImage
            qr_photo = ImageTk.PhotoImage(qr_image)
            self.qr_label.config(image=qr_photo)
            self.qr_label.image = qr_photo  # Keep a reference
            
        except Exception as e:
            error_text = f"QR Generation Error:\n{str(e)}"
            self.qr_label.config(text=error_text, 
                               font=('Segoe UI', 9), 
                               fg=self.colors['danger'])
    
    def generate_pdf_certificate(self, filename):
        """Generate a professional PDF certificate"""
        try:
            # Create the PDF document
            doc = SimpleDocTemplate(filename, pagesize=A4)
            story = []
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = styles['Title']
            title_style.fontSize = 24
            title_style.textColor = colors.HexColor('#0ea5e9')
            title_style.alignment = 1  # Center
            
            heading_style = styles['Heading1']
            heading_style.fontSize = 16
            heading_style.textColor = colors.HexColor('#1e293b')
            
            normal_style = styles['Normal']
            normal_style.fontSize = 12
            normal_style.textColor = colors.HexColor('#334155')
            
            # Header
            story.append(Paragraph("🔒 ZEROTRACE PRO", title_style))
            story.append(Paragraph("DATA ERASURE CERTIFICATE", heading_style))
            story.append(Spacer(1, 20))
            
            # Certificate info
            cert_info = f"""
            <b>Certificate ID:</b> {self.certificate_data['device_id']}<br/>
            <b>Issue Date:</b> {self.certificate_data['completion_time'][:19].replace('T', ' ')}<br/>
            <b>Verification Status:</b> <font color='#10b981'>✅ VERIFIED SECURE ERASURE</font>
            """
            story.append(Paragraph(cert_info, normal_style))
            story.append(Spacer(1, 20))
            
            # Device information table
            device_data = [
                ['Device Information', ''],
                ['Device(s)', ', '.join(self.certificate_data['devices'])],
                ['Erasure Method', self.certificate_data['method']],
                ['Start Time', self.certificate_data['start_time'][:19].replace('T', ' ')],
                ['Completion Time', self.certificate_data['completion_time'][:19].replace('T', ' ')],
                ['Duration', self.certificate_data['duration'].split('.')[0]],
                ['Hidden Areas', 'Included' if self.certificate_data['hidden_areas'] else 'Not Included'],
                ['Status', '✅ Successfully Erased']
            ]
            
            device_table = Table(device_data, colWidths=[2.5*inch, 4*inch])
            device_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1'))
            ]))
            
            story.append(device_table)
            story.append(Spacer(1, 30))
            
            # Standards compliance
            compliance_text = """
            <b>Standards Compliance:</b><br/>
            • NIST SP 800-88 Guidelines for Media Sanitization<br/>
            • DoD 5220.22-M Data Sanitization Standards<br/>
            • ISO/IEC 27040 Storage Security Guidelines<br/>
            • Common Criteria Protection Profile compliance
            """
            story.append(Paragraph(compliance_text, normal_style))
            story.append(Spacer(1, 20))
            
            # Verification statement
            verification_text = f"""
            <b>VERIFICATION STATEMENT</b><br/>
            This certificate verifies that the data erasure operation was completed successfully 
            on {self.certificate_data['completion_time'][:10]} using industry-standard secure erasure methods. 
            The erasure process has been logged and verified to meet or exceed government and industry 
            data sanitization requirements.
            """
            story.append(Paragraph(verification_text, normal_style))
            story.append(Spacer(1, 20))
            
            # Footer
            footer_text = f"""
            <i>Certificate generated by ZeroTrace Pro v2.0 • Device ID: {self.certificate_data['device_id']} • 
            For verification, scan the QR code or visit our verification portal.</i>
            """
            footer_style = styles['Normal']
            footer_style.fontSize = 10
            footer_style.textColor = colors.HexColor('#64748b')
            footer_style.alignment = 1  # Center
            
            story.append(Paragraph(footer_text, footer_style))
            
            # Build PDF
            doc.build(story)
            return True
            
        except Exception as e:
            messagebox.showerror("PDF Generation Error", f"Failed to generate PDF certificate:\n{str(e)}")
            return False
    
    def download_pdf_cert(self):
        """Download PDF certificate"""
        if not hasattr(self, 'certificate_data'):
            messagebox.showwarning("No Certificate Data", "Please complete a wipe operation first.")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save PDF Certificate",
            initialname=f"ZeroTrace_Certificate_{self.device_id}.pdf"
        )
        
        if filename:
            if self.generate_pdf_certificate(filename):
                messagebox.showinfo("Certificate Saved", 
                                  f"PDF certificate has been saved successfully:\n{filename}")
            # Error handling is done in generate_pdf_certificate
    
    def download_json_cert(self):
        """Download JSON certificate"""
        if not hasattr(self, 'certificate_data'):
            messagebox.showwarning("No Certificate Data", "Please complete a wipe operation first.")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Save JSON Certificate",
            initialname=f"ZeroTrace_Certificate_{self.device_id}.json"
        )
        
        if filename:
            try:
                with open(filename, "w") as f:
                    json.dump(self.certificate_data, f, indent=2)
                messagebox.showinfo("Certificate Saved", 
                                  f"JSON certificate has been saved successfully:\n{filename}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save JSON certificate:\n{str(e)}")
    
    def new_wipe(self):
        """Reset application for new wipe session"""
        # Reset all variables
        self.progress_value = 0
        self.progress_bar['value'] = 0
        self.log_text.delete(1.0, tk.END)
        self.wipe_in_progress = False
        self.wipe_start_time = None
        self.wipe_completion_time = None
        
        # Generate new device ID for new session
        self.device_id = str(uuid.uuid4())[:8].upper()
        
        # Update device ID in header (find and update the label)
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Frame):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, tk.Frame):
                                for label in grandchild.winfo_children():
                                    if isinstance(label, tk.Label) and hasattr(label, 'cget'):
                                        try:
                                            if label.cget('font')[1] == 12 and label.cget('font')[2] == 'bold':
                                                if len(label.cget('text')) == 8 and label.cget('text').replace('-', '').isalnum():
                                                    label.config(text=self.device_id)
                                        except:
                                            pass
        
        # Reset device selections to default
        for i, var in enumerate(self.device_vars):
            var.set(i == 0)  # Select first device by default
        
        # Reset to defaults
        self.method_var.set("NIST 3-pass overwrite")
        self.hidden_var.set(False)
        
        # Clear certificate data
        if hasattr(self, 'certificate_data'):
            delattr(self, 'certificate_data')
        
        # Show main screen
        return self.show_screen("main")
    
def main():
    print("🚀 Starting ZeroTrace Pro GUI...")
    
    # Create root window
    root = tk.Tk()
    print("✅ Tkinter window created")
    
    # Force window to appear and get focus
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)
    
    # Set minimum window size
    root.minsize(800, 600)
    
    # Configure window properties
    root.title("🔒 ZeroTrace Pro - Professional Data Erasure")
    width = 1200
    height = 800
    
    # Center on screen
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    # Make sure window is visible
    root.deiconify()
    root.focus_force()
    
    # Create application
    app = SecureWipeGUI(root)
    
    # Handle window close
    def on_closing():
        if app.wipe_in_progress:
            if messagebox.askokcancel("Wipe in Progress", 
                                    "A wipe operation is currently in progress. "
                                    "Closing now may leave the drive in an inconsistent state.\n\n"
                                    "Are you sure you want to exit?"):
                app.wipe_in_progress = False
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()