#!/usr/bin/env python3
"""
Image Converter - Convert between all common image formats
Supports PNG, JPG, WebP, BMP, GIF, TIFF, ICO, and many more formats
Supports both folder-based and drag-and-drop modes
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, font
import threading
import math
import urllib.request
import tempfile

# Try to import tkinterdnd2 for drag-and-drop support
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    # Fallback to regular Tk if tkinterdnd2 not available
    TkinterDnD = tk


class ImageConverter:
    """Handles image conversion between all common image formats"""
    
    # All common image formats supported by Pillow
    SUPPORTED_FORMATS = {
        '.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif', '.tiff', '.tif',
        '.ico', '.jfif', '.jpe', '.jp2', '.jpx', '.j2k', '.j2c', '.pcx',
        '.ppm', '.pgm', '.pbm', '.pnm', '.svg', '.heic', '.heif', '.avif'
    }
    
    # Formats that support transparency (convert to PNG to preserve)
    TRANSPARENCY_FORMATS = {'.png', '.gif', '.webp', '.tiff', '.tif', '.ico'}
    
    # Lossy formats (can convert to WebP)
    LOSSY_FORMATS = {'.jpg', '.jpeg', '.jfif', '.jpe', '.jp2', '.jpx', '.j2k', '.j2c', '.webp'}
    
    # Formats that should convert to PNG (for transparency or compatibility)
    PNG_TARGET_FORMATS = {'.gif', '.bmp', '.tiff', '.tif', '.ico', '.pcx', '.ppm', '.pgm', '.pbm', '.pnm'}
    
    def __init__(self, output_dir=None, quality=100):
        """
        Initialize converter
        
        Args:
            output_dir: Output directory (None = same as input)
            quality: WebP quality (1-100, default 100)
        """
        self.output_dir = output_dir
        self.quality = quality
    
    def is_supported(self, file_path):
        """Check if file is a supported image format"""
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_FORMATS
    
    def get_output_path(self, input_path, target_format):
        """
        Determine output file path
        
        Args:
            input_path: Input file path
            target_format: Target format ('.webp', '.png', '.jpg')
        
        Returns:
            Output file path
        """
        input_path = Path(input_path)
        
        if self.output_dir:
            output_path = Path(self.output_dir) / input_path.name
        else:
            output_path = input_path.parent / input_path.name
        
        # Change extension
        output_path = output_path.with_suffix(target_format)
        
        # Avoid overwriting if same format
        if output_path == input_path:
            output_path = output_path.parent / f"{input_path.stem}_converted{target_format}"
        
        return output_path
    
    def convert_image(self, input_path, target_format=None):
        """
        Convert a single image
        
        Args:
            input_path: Path to input image
            target_format: Target format (None = auto-detect based on input)
        
        Returns:
            (success: bool, output_path: Path, message: str)
        """
        try:
            input_path = Path(input_path)
            
            if not input_path.exists():
                return False, None, f"File not found: {input_path}"
            
            if not self.is_supported(input_path):
                return False, None, f"Unsupported format: {input_path.suffix}"
            
            # Determine target format
            if target_format is None:
                ext = input_path.suffix.lower()
                # Smart format selection:
                # - WebP/AVIF/HEIC → PNG (modern formats to universal)
                # - Formats with transparency → PNG (preserve transparency)
                # - Lossy formats → WebP (better compression)
                # - Others → PNG (universal compatibility)
                if ext in {'.webp', '.avif', '.heic', '.heif'}:
                    target_format = '.png'
                elif ext in self.TRANSPARENCY_FORMATS:
                    target_format = '.png'  # Preserve transparency
                elif ext in self.LOSSY_FORMATS:
                    target_format = '.webp'  # Better compression
                elif ext in self.PNG_TARGET_FORMATS:
                    target_format = '.png'  # Convert to PNG
                elif ext == '.svg':
                    # SVG is vector, convert to PNG
                    target_format = '.png'
                else:
                    # Default to PNG for unknown formats
                    target_format = '.png'
            
            # Open and convert image
            with Image.open(input_path) as img:
                # Convert RGBA to RGB for JPG output
                if target_format == '.jpg' and img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode == 'P':
                    img = img.convert('RGB')
                
                # Get output path
                output_path = self.get_output_path(input_path, target_format)
                
                # Ensure output directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Save with appropriate options based on format
                format_map = {
                    '.webp': ('WEBP', {'quality': self.quality, 'method': 6}),
                    '.png': ('PNG', {'optimize': True}),
                    '.jpg': ('JPEG', {'quality': self.quality, 'optimize': True}),
                    '.jpeg': ('JPEG', {'quality': self.quality, 'optimize': True}),
                    '.bmp': ('BMP', {}),
                    '.gif': ('GIF', {'optimize': True}),
                    '.tiff': ('TIFF', {'compression': 'lzw'}),
                    '.tif': ('TIFF', {'compression': 'lzw'}),
                    '.ico': ('ICO', {}),
                    '.jfif': ('JPEG', {'quality': self.quality, 'optimize': True}),
                    '.jpe': ('JPEG', {'quality': self.quality, 'optimize': True}),
                }
                
                if target_format in format_map:
                    pil_format, save_options = format_map[target_format]
                    img.save(output_path, pil_format, **save_options)
                else:
                    # Try to save with format name directly
                    try:
                        pil_format = target_format[1:].upper()  # Remove dot and uppercase
                        img.save(output_path, pil_format)
                    except Exception:
                        return False, None, f"Unsupported target format: {target_format}"
            
            return True, output_path, f"Converted: {input_path.name} → {output_path.name}"
        
        except Exception as e:
            return False, None, f"Error converting {input_path.name}: {str(e)}"
    
    def convert_folder(self, folder_path, target_format=None, recursive=False):
        """
        Convert all images in a folder
        
        Args:
            folder_path: Path to folder
            target_format: Target format (None = auto-detect)
            recursive: Search subdirectories
        
        Returns:
            List of (success, output_path, message) tuples
        """
        folder_path = Path(folder_path)
        results = []
        
        if not folder_path.is_dir():
            return [(False, None, f"Not a directory: {folder_path}")]
        
        # Find all images
        pattern = '**/*' if recursive else '*'
        image_files = []
        for ext in self.SUPPORTED_FORMATS:
            image_files.extend(folder_path.glob(f"{pattern}{ext}"))
            image_files.extend(folder_path.glob(f"{pattern}{ext.upper()}"))
        
        if not image_files:
            return [(False, None, "No supported images found in folder")]
        
        # Convert each image
        for img_file in image_files:
            result = self.convert_image(img_file, target_format)
            results.append(result)
        
        return results


class ConverterGUI:
    """GUI application with drag-and-drop support - Big Daddy Converter"""
    
    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.title("Big Daddy Converter")
        self.root.geometry("1000x750")
        self.root.resizable(True, True)
        
        # Set window icon
        try:
            icon_path = Path(__file__).parent / "icon.png"
            if icon_path.exists():
                if sys.platform == "win32":
                    self.root.iconbitmap(str(icon_path))
                else:
                    # For cross-platform support (PIL already imported at top)
                    icon_image = Image.open(icon_path)
                    icon_photo = ImageTk.PhotoImage(icon_image)
                    self.root.iconphoto(True, icon_photo)
        except Exception:
            # If icon loading fails, continue without icon
            pass
        
        # Color scheme - Pure black modern theme
        self.colors = {
            'bg': '#000000',
            'glass': '#0a0a0a',
            'glass_light': '#0f0f0f',
            'accent': '#ffffff',
            'accent_hover': '#cccccc',
            'text': '#ffffff',
            'text_dim': '#666666',
            'border': '#1a1a1a',
            'selected': '#ffffff',
            'hover': '#1a1a1a',
            'scrollbar': '#333333',
            'scrollbar_hover': '#555555'
        }
        
        # Selection state
        self.drag_start_index = None
        self.is_dragging = False
        
        # Store output file sizes after conversion (file_path -> output_size_bytes)
        self.output_file_sizes = {}
        
        # Configure root window
        self.root.configure(bg=self.colors['bg'])
        
        # Try to set window title bar to dark mode and black color (Windows 10/11)
        try:
            if sys.platform == 'win32':
                import ctypes
                from ctypes import wintypes
                
                # Get window handle - need to wait for window to be created
                self.root.update_idletasks()
                hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                if not hwnd:
                    hwnd = self.root.winfo_id()
                
                # Set dark mode for title bar
                DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                value = ctypes.c_int(1)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    DWMWA_USE_IMMERSIVE_DARK_MODE,
                    ctypes.byref(value),
                    ctypes.sizeof(value)
                )
                
                # Try to set title bar color to black (Windows 11)
                try:
                    DWMWA_CAPTION_COLOR = 35
                    # Black color in BGR format (0x000000)
                    black_color = 0x000000
                    color_value = ctypes.c_uint32(black_color)
                    ctypes.windll.dwmapi.DwmSetWindowAttribute(
                        hwnd,
                        DWMWA_CAPTION_COLOR,
                        ctypes.byref(color_value),
                        ctypes.sizeof(color_value)
                    )
                except:
                    pass  # Color setting might not be supported on older Windows
        except Exception:
            pass  # Fallback if API not available
        
        # Schedule title bar update after window is fully created
        self.root.after(100, self.update_title_bar_color)
    
    def update_title_bar_color(self):
        """Update title bar color after window is created"""
        try:
            if sys.platform == 'win32':
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                if not hwnd:
                    hwnd = self.root.winfo_id()
                
                # Set title bar color to black (Windows 11)
                DWMWA_CAPTION_COLOR = 35
                black_color = 0x000000
                color_value = ctypes.c_uint32(black_color)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    DWMWA_CAPTION_COLOR,
                    ctypes.byref(color_value),
                    ctypes.sizeof(color_value)
                )
        except:
            pass
        
        self.converter = ImageConverter()
        self.pending_files = []  # List of files waiting to be converted
        self.selected_files = set()  # Set of selected file indices
        self.is_converting = False
        self.should_stop = False
        self.conversion_thread = None
        
        # Thumbnail management
        self.thumbnail_size = 150
        self.thumbnails = {}  # Cache of thumbnail images
        self.thumbnail_photos = {}  # Cache of PhotoImage objects
        self.hover_tooltip = None
        self.hover_widget = None
        
        # Load Montserrat font
        self.font_family = self.load_montserrat_font()
        
        self.setup_styles()
        self.setup_ui()
    
    def load_montserrat_font(self):
        """Load Montserrat or Lato font from Google Fonts or use fallback"""
        # Try Montserrat first, then Lato
        font_options = ["Montserrat", "Lato"]
        
        for font_name in font_options:
            try:
                test_font = tk.font.Font(family=font_name, size=10)
                if test_font.actual()['family'] == font_name:
                    return font_name
            except:
                continue
        
        # Try common system fonts that are similar
        fallback_fonts = ["Segoe UI", "Arial", "Helvetica", "sans-serif"]
        for font_name in fallback_fonts:
            try:
                test_font = tk.font.Font(family=font_name, size=10)
                if test_font.actual()['family'] == font_name:
                    return font_name
            except:
                continue
        
        return "TkDefaultFont"  # Ultimate fallback
    
    def setup_styles(self):
        """Setup custom styles for black glass theme"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles
        style.configure('Glass.TFrame', background=self.colors['glass'], borderwidth=0)
        style.configure('Glass.TLabelFrame', background=self.colors['glass'], 
                       foreground=self.colors['text'], borderwidth=1, relief='flat')
        style.configure('Glass.TLabelFrame.Label', background=self.colors['glass'], 
                       foreground=self.colors['text'], font=('Segoe UI', 10, 'bold'))
        
        style.configure('Glass.TLabel', background=self.colors['glass'], 
                       foreground=self.colors['text'], font=(self.font_family, 10))
        style.configure('Title.TLabel', background=self.colors['bg'], 
                       foreground=self.colors['text'], font=(self.font_family, 24, 'bold'))
        style.configure('Subtitle.TLabel', background=self.colors['bg'], 
                       foreground=self.colors['text_dim'], font=(self.font_family, 9))
        
        # Rounded button style with dark grey border
        style.configure('Rounded.TButton', 
                       background=self.colors['bg'],
                       foreground=self.colors['text'],
                       borderwidth=2,
                       relief=tk.SOLID,
                       focuscolor='none',
                       padding=10,
                       font=(self.font_family, 10, 'bold'))
        style.map('Rounded.TButton',
                 background=[('active', '#ff4444'),
                           ('pressed', '#ff6666'),
                           ('!active', self.colors['bg'])],
                 foreground=[('active', '#000000'),
                           ('pressed', '#000000'),
                           ('!active', self.colors['text'])],
                 bordercolor=[('!active', self.colors['border']),
                            ('active', self.colors['border']),
                            ('pressed', self.colors['border'])])
        
        # Start button (primary) - red
        style.configure('Primary.TButton',
                       background='#ff4444',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=12,
                       font=(self.font_family, 11, 'bold'))
        style.map('Primary.TButton',
                 background=[('active', '#ff6666'),
                           ('disabled', self.colors['glass'])],
                 foreground=[('disabled', self.colors['text_dim'])])
        
        # Stop button (danger)
        style.configure('Danger.TButton',
                       background='#ff4444',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=12,
                       font=(self.font_family, 11, 'bold'))
        style.map('Danger.TButton',
                 background=[('active', '#ff6666'),
                           ('disabled', self.colors['glass'])],
                 foreground=[('disabled', self.colors['text_dim'])])
        
        # Scale style
        style.configure('Glass.Horizontal.TScale',
                       background=self.colors['glass'],
                       troughcolor=self.colors['glass'],
                       borderwidth=0,
                       sliderthickness=15)
    
    def setup_ui(self):
        """Setup the user interface with modern black glass theme"""
        # Main container with padding
        main_container = tk.Frame(self.root, bg=self.colors['bg'], padx=20, pady=20)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Title section
        title_frame = tk.Frame(main_container, bg=self.colors['bg'])
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Title with red "BIG" and "CONVERTER" parts, no spacing
        title_container = tk.Frame(title_frame, bg=self.colors['bg'])
        title_container.pack(anchor='w')
        
        # Create extra bold font - use larger size for extra bold effect
        title_font = font.Font(family=self.font_family, size=28, weight='bold')
        
        title_part1 = tk.Label(title_container, text="BIG", 
                               bg=self.colors['bg'], fg='#ff4444',
                               font=title_font)
        title_part1.pack(side=tk.LEFT, padx=0)
        
        title_part2 = tk.Label(title_container, text="DADDY", 
                               bg=self.colors['bg'], fg=self.colors['text'],
                               font=title_font)
        title_part2.pack(side=tk.LEFT, padx=0)
        
        title_part3 = tk.Label(title_container, text="CONVERTER", 
                               bg=self.colors['bg'], fg='#ff4444',
                               font=title_font)
        title_part3.pack(side=tk.LEFT, padx=0)
        
        subtitle_label = ttk.Label(title_frame, 
                                   text="All Image Formats • Drag & Drop • Batch Convert",
                                   style='Subtitle.TLabel')
        subtitle_label.pack(anchor='w', pady=(5, 0))
        
        # Main content area with glass effect
        content_frame = tk.Frame(main_container, bg=self.colors['bg'], padx=15, pady=15)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Thumbnail grid area with rounded corners and grey background
        grid_container_outer = tk.Frame(content_frame, bg=self.colors['bg'])
        grid_container_outer.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        grid_container = self.create_rounded_frame(grid_container_outer, self.colors['glass'], 
                                                   border_color=self.colors['border'])
        
        # Canvas with scrollbar for thumbnail grid
        canvas_frame = tk.Frame(grid_container, bg=self.colors['glass'])
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a frame to hold canvas and scrollbar side by side
        canvas_scroll_frame = tk.Frame(canvas_frame, bg=self.colors['glass'])
        canvas_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        self.thumbnail_canvas = tk.Canvas(canvas_scroll_frame, bg=self.colors['glass'], 
                                          highlightthickness=0, borderwidth=0)
        
        # Custom rounded scrollbar - only vertical
        scrollbar_v = self.create_rounded_scrollbar(canvas_scroll_frame, tk.VERTICAL, 
                                                    self.thumbnail_canvas.yview)
        
        self.thumbnail_canvas.configure(yscrollcommand=scrollbar_v.set_scroll)
        
        # Scrollable frame inside canvas
        self.thumbnail_frame = tk.Frame(self.thumbnail_canvas, bg=self.colors['glass'])
        self.canvas_window = self.thumbnail_canvas.create_window((0, 0), 
                                                                 window=self.thumbnail_frame,
                                                                 anchor='nw')
        
        # Configure scroll region - only update when there are files
        def update_scroll_region(event=None):
            if self.pending_files:
                bbox = self.thumbnail_canvas.bbox('all')
                if bbox:
                    # Ensure scroll region includes full content height so scrollbar stays visible
                    x1, y1, x2, y2 = bbox
                    # Add small padding to bottom to ensure scrollbar is always accessible
                    canvas_height = self.thumbnail_canvas.winfo_height() or 600
                    if y2 < canvas_height:
                        y2 = canvas_height
                    self.thumbnail_canvas.configure(scrollregion=(x1, y1, x2, y2))
                else:
                    canvas_width = self.thumbnail_canvas.winfo_width() or 800
                    canvas_height = self.thumbnail_canvas.winfo_height() or 600
                    self.thumbnail_canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
            else:
                # No scrolling when empty - set to canvas size
                canvas_width = self.thumbnail_canvas.winfo_width() or 800
                canvas_height = self.thumbnail_canvas.winfo_height() or 600
                self.thumbnail_canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
        
        self.thumbnail_frame.bind('<Configure>', update_scroll_region)
        
        # Pack canvas and scrollbar - no horizontal scrollbar
        self.thumbnail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # Enable mouse wheel scrolling - only bind to canvas, not all widgets
        def on_mousewheel(event):
            # Only scroll if mouse is over the canvas
            if event.widget == self.thumbnail_canvas or event.widget == self.thumbnail_frame:
                if event.delta:
                    self.thumbnail_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                else:
                    if event.num == 4:
                        self.thumbnail_canvas.yview_scroll(-1, "units")
                    elif event.num == 5:
                        self.thumbnail_canvas.yview_scroll(1, "units")
                return "break"
        
        # Bind mouse wheel only to canvas and frame (not all widgets)
        self.thumbnail_canvas.bind("<MouseWheel>", on_mousewheel)
        self.thumbnail_canvas.bind("<Button-4>", on_mousewheel)
        self.thumbnail_canvas.bind("<Button-5>", on_mousewheel)
        self.thumbnail_frame.bind("<MouseWheel>", on_mousewheel)
        self.thumbnail_frame.bind("<Button-4>", on_mousewheel)
        self.thumbnail_frame.bind("<Button-5>", on_mousewheel)
        
        # Enable drag and drop on canvas
        if DND_AVAILABLE:
            try:
                self.thumbnail_canvas.drop_target_register(DND_FILES)
                self.thumbnail_canvas.dnd_bind('<<Drop>>', self.on_drop)
            except Exception:
                pass
        
        # Control buttons for thumbnails
        control_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(control_frame, text="Clear All", 
                  command=self.clear_file_list, style='Rounded.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Remove Selected", 
                  command=self.remove_selected_files, style='Rounded.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Select All", 
                  command=self.select_all_files, style='Rounded.TButton').pack(side=tk.LEFT, padx=5)
        
        # Settings row
        settings_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        settings_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Format selection
        format_label = ttk.Label(settings_frame, text="Convert to:", style='Glass.TLabel')
        format_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Format dropdown - all supported formats
        self.target_format_var = tk.StringVar(value="PNG")
        format_options = ["PNG", "JPG", "WebP", "BMP", "GIF", "TIFF", "ICO", "SVG", "HEIC", "AVIF"]
        
        # Create styled combobox - dropdown will auto-scroll if needed
        format_combobox = ttk.Combobox(settings_frame, textvariable=self.target_format_var,
                                       values=format_options, state="readonly", width=10,
                                       font=(self.font_family, 10))
        format_combobox.pack(side=tk.LEFT, padx=5)
        
        # Prevent text selection when clicking on combobox
        def prevent_combobox_selection(event):
            # Clear any text selection immediately
            format_combobox.selection_clear()
            return None
        
        format_combobox.bind('<Button-1>', prevent_combobox_selection, add='+')
        format_combobox.bind('<FocusIn>', prevent_combobox_selection)
        
        # Style the combobox - black theme with white arrow, no border
        style = ttk.Style()
        style.configure('TCombobox', 
                       fieldbackground=self.colors['glass'],
                       background=self.colors['glass'], 
                       foreground=self.colors['text'],
                       borderwidth=0,
                       relief=tk.FLAT,
                       arrowcolor=self.colors['text'],  # White arrow
                       bordercolor=self.colors['glass'],
                       darkcolor=self.colors['glass'],
                       lightcolor=self.colors['glass'],
                       troughcolor=self.colors['glass'])
        style.map('TCombobox',
                 fieldbackground=[('readonly', self.colors['glass']),
                                ('active', self.colors['glass']),
                                ('focus', self.colors['glass'])],
                 background=[('readonly', self.colors['glass']),
                           ('active', self.colors['glass']),
                           ('focus', self.colors['glass'])],
                 foreground=[('readonly', self.colors['text']),
                           ('active', self.colors['text']),
                           ('focus', self.colors['text'])],
                 arrowcolor=[('readonly', self.colors['text']),
                           ('active', self.colors['text']),
                           ('focus', self.colors['text'])],
                 bordercolor=[('readonly', self.colors['glass']),
                            ('active', self.colors['glass']),
                            ('focus', self.colors['glass'])],
                 borderwidth=[('readonly', 0), ('active', 0), ('focus', 0)],
                 darkcolor=[('readonly', self.colors['glass']),
                          ('active', self.colors['glass'])],
                 lightcolor=[('readonly', self.colors['glass']),
                           ('active', self.colors['glass'])],
                 troughcolor=[('readonly', self.colors['glass']),
                            ('active', self.colors['glass'])])
        
        # Also style the combobox entry field - remove all borders
        style.configure('TCombobox.field', 
                       fieldbackground=self.colors['glass'],
                       borderwidth=0,
                       relief=tk.FLAT,
                       bordercolor=self.colors['glass'])
        style.map('TCombobox.field',
                 fieldbackground=[('readonly', self.colors['glass']),
                                ('focus', self.colors['glass'])],
                 bordercolor=[('readonly', self.colors['glass']),
                            ('focus', self.colors['glass'])],
                 borderwidth=[('readonly', 0), ('focus', 0)])
        
        # Update thumbnails when format changes
        def update_thumbnails_on_format_change(*args):
            """Update thumbnail estimated sizes when format changes"""
            # Use after_idle with a small delay to ensure value is fully updated
            def do_update():
                if hasattr(self, 'thumbnail_frame') and hasattr(self, 'pending_files') and self.pending_files:
                    self.update_thumbnail_grid()
            self.root.after(50, do_update)  # Small delay to ensure value is set
        
        self.target_format_var.trace('w', update_thumbnails_on_format_change)
        
        # Quality setting with typable entry field
        quality_label = ttk.Label(settings_frame, text="Quality:", style='Glass.TLabel')
        quality_label.pack(side=tk.LEFT, padx=(20, 10))
        
        self.quality_var = tk.StringVar(value="100")
        
        # Quality entry field
        quality_entry = tk.Entry(settings_frame, textvariable=self.quality_var,
                                bg=self.colors['glass'], fg=self.colors['text'],
                                insertbackground=self.colors['text'],
                                font=(self.font_family, 10),
                                relief=tk.FLAT, bd=1, highlightthickness=1,
                                highlightbackground=self.colors['border'],
                                highlightcolor=self.colors['accent'],
                                width=5, justify=tk.CENTER)
        quality_entry.pack(side=tk.LEFT, padx=5)
        
        # Prevent text selection when clicking on entry
        def prevent_entry_selection(event):
            # Clear any text selection immediately
            quality_entry.select_clear()
            # Set cursor to end to prevent selection
            quality_entry.icursor(tk.END)
            return None
        
        # Hide cursor when clicking outside
        def hide_cursor(event=None):
            quality_entry.config(insertwidth=0)
        
        # Show cursor when focusing
        def show_cursor(event=None):
            quality_entry.config(insertwidth=2)
        
        quality_entry.bind('<Button-1>', prevent_entry_selection, add='+')
        quality_entry.bind('<FocusOut>', hide_cursor)
        quality_entry.bind('<FocusIn>', show_cursor)
        
        # Remove focus when clicking outside the entry
        def remove_focus_on_click(event):
            widget = event.widget
            # If click is not on quality_entry or its children, remove focus
            if widget != quality_entry:
                try:
                    # Check if the click is inside quality_entry
                    x, y = widget.winfo_pointerxy()
                    entry_x = quality_entry.winfo_rootx()
                    entry_y = quality_entry.winfo_rooty()
                    entry_width = quality_entry.winfo_width()
                    entry_height = quality_entry.winfo_height()
                    
                    if not (entry_x <= x <= entry_x + entry_width and 
                           entry_y <= y <= entry_y + entry_height):
                        self.root.focus_set()
                except:
                    pass
        
        # Bind to root and main containers
        self.root.bind('<Button-1>', remove_focus_on_click, add='+')
        main_container = settings_frame.master
        if main_container:
            main_container.bind('<Button-1>', remove_focus_on_click, add='+')
        
        # Add mouse wheel scrolling to quality entry
        def on_quality_scroll(event):
            """Increment or decrement quality value on mouse wheel"""
            try:
                current = int(self.quality_var.get())
                if event.delta > 0 or event.num == 4:  # Scroll up
                    new_value = min(100, current + 1)
                else:  # Scroll down
                    new_value = max(1, current - 1)
                self.quality_var.set(str(new_value))
            except (ValueError, AttributeError):
                self.quality_var.set("100")
        
        # Bind mouse wheel events
        quality_entry.bind('<MouseWheel>', on_quality_scroll)
        quality_entry.bind('<Button-4>', on_quality_scroll)  # Linux scroll up
        quality_entry.bind('<Button-5>', on_quality_scroll)  # Linux scroll down
        
        # Validate quality input (1-100)
        def validate_quality(*args):
            try:
                value = self.quality_var.get()
                if value:
                    quality = int(value)
                    if quality < 1:
                        self.quality_var.set("1")
                    elif quality > 100:
                        self.quality_var.set("100")
            except ValueError:
                # If not a valid number, set to default
                if self.quality_var.get() and not self.quality_var.get().isdigit():
                    self.quality_var.set("100")
        
        self.quality_var.trace('w', validate_quality)
        
        # Update thumbnails when quality changes
        # Store a flag to prevent multiple rapid updates
        self._updating_thumbnails = False
        
        def update_thumbnails_on_quality_change(*args):
            """Update thumbnail estimated sizes when quality changes"""
            # Skip if already updating or during validation
            if self._updating_thumbnails:
                return
            
            # Check if value is valid before updating
            try:
                quality_val = self.quality_var.get()
                if quality_val and quality_val.isdigit():
                    quality_int = int(quality_val)
                    if 1 <= quality_int <= 100:
                        self._updating_thumbnails = True
                        def do_update():
                            if hasattr(self, 'thumbnail_frame') and hasattr(self, 'pending_files') and self.pending_files:
                                self.update_thumbnail_grid()
                            self._updating_thumbnails = False
                        self.root.after(100, do_update)  # Delay to ensure value is set
            except:
                pass
        
        self.quality_var.trace('w', update_thumbnails_on_quality_change)
        
        # Output directory
        output_label = ttk.Label(settings_frame, text="Output:", style='Glass.TLabel')
        output_label.pack(side=tk.LEFT, padx=(20, 10))
        
        self.output_var = tk.StringVar(value="Same folder as input")
        output_path_label = ttk.Label(settings_frame, textvariable=self.output_var, 
                                     style='Glass.TLabel', foreground=self.colors['text_dim'])
        output_path_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(settings_frame, text="Browse", 
                  command=self.browse_output, style='Rounded.TButton').pack(side=tk.LEFT, padx=5)
        
        # Action buttons
        button_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(button_frame, text="Select Files", 
                  command=self.select_files, style='Rounded.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Select Folder", 
                  command=self.select_folder, style='Rounded.TButton').pack(side=tk.LEFT, padx=5)
        
        # Start/Stop buttons
        self.start_button = ttk.Button(button_frame, text="Start Conversion", 
                                       command=self.start_conversion, 
                                       state=tk.DISABLED, style='Primary.TButton')
        self.start_button.pack(side=tk.LEFT, padx=10)
        
        self.stop_button = ttk.Button(button_frame, text="Stop", 
                                     command=self.stop_conversion, 
                                     state=tk.DISABLED, style='Danger.TButton')
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Log/Status area with rounded corners and grey background
        log_frame_outer = tk.Frame(content_frame, bg=self.colors['bg'])
        log_frame_outer.pack(fill=tk.BOTH, expand=True)
        
        log_frame = self.create_rounded_frame(log_frame_outer, self.colors['glass'],
                                              border_color=self.colors['border'])
        
        log_title = ttk.Label(log_frame, text="Status Log", 
                             style='Glass.TLabel', font=(self.font_family, 10, 'bold'))
        log_title.pack(anchor='w', padx=10, pady=(10, 5))
        
        log_container = tk.Frame(log_frame, bg=self.colors['glass'])
        log_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.log_text = tk.Text(log_container, height=6, wrap=tk.WORD,
                               bg=self.colors['glass'], fg=self.colors['text'],
                               insertbackground=self.colors['text'],
                               selectbackground=self.colors['accent'],
                               selectforeground='white',
                               font=(self.font_family, 9),
                               relief=tk.FLAT, bd=0, padx=10, pady=10)
        log_scrollbar = self.create_rounded_scrollbar(log_container, tk.VERTICAL, 
                                                      self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set_scroll)
        
        # Bind mouse wheel to log text only (prevent propagation to image window)
        def on_log_wheel(event):
            """Handle mouse wheel scrolling in log text"""
            if event.delta:
                # Windows/Mac
                self.log_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.num == 4:
                # Linux scroll up
                self.log_text.yview_scroll(-1, "units")
            elif event.num == 5:
                # Linux scroll down
                self.log_text.yview_scroll(1, "units")
            return "break"  # Stop event propagation
        
        self.log_text.bind('<MouseWheel>', on_log_wheel)
        self.log_text.bind('<Button-4>', on_log_wheel)  # Linux scroll up
        self.log_text.bind('<Button-5>', on_log_wheel)  # Linux scroll down
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        self.log("Ready. Drag and drop images or folders to convert.")
        
        # Bind canvas resize
        self.thumbnail_canvas.bind('<Configure>', self.on_canvas_configure)
    
    def create_rounded_frame(self, parent, bg_color, border_color='#1a1a1a', radius=10):
        """Create a frame with rounded corners using a canvas"""
        # Container frame - pack it into parent first
        container = tk.Frame(parent, bg=bg_color)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for rounded rectangle
        canvas = tk.Canvas(container, bg=bg_color, highlightthickness=0, 
                          borderwidth=0, relief=tk.FLAT)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        def draw_rounded_rect(event=None):
            """Draw rounded rectangle border"""
            canvas.delete("border")
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            
            if w > 1 and h > 1:
                # Draw rounded rectangle border
                # Top-left corner
                canvas.create_arc(0, 0, radius*2, radius*2, 
                                 start=90, extent=90, 
                                 outline=border_color, width=2, fill="", tags="border")
                # Top-right corner
                canvas.create_arc(w-radius*2, 0, w, radius*2, 
                                 start=0, extent=90, 
                                 outline=border_color, width=2, fill="", tags="border")
                # Bottom-right corner
                canvas.create_arc(w-radius*2, h-radius*2, w, h, 
                                 start=270, extent=90, 
                                 outline=border_color, width=2, fill="", tags="border")
                # Bottom-left corner
                canvas.create_arc(0, h-radius*2, radius*2, h, 
                                 start=180, extent=90, 
                                 outline=border_color, width=2, fill="", tags="border")
                # Top line
                canvas.create_line(radius, 0, w-radius, 0, 
                                  fill=border_color, width=2, tags="border")
                # Right line
                canvas.create_line(w, radius, w, h-radius, 
                                  fill=border_color, width=2, tags="border")
                # Bottom line
                canvas.create_line(w-radius, h, radius, h, 
                                  fill=border_color, width=2, tags="border")
                # Left line
                canvas.create_line(0, h-radius, 0, radius, 
                                  fill=border_color, width=2, tags="border")
        
        canvas.bind('<Configure>', draw_rounded_rect)
        container.after_idle(draw_rounded_rect)
        
        # Inner frame for content
        inner_frame = tk.Frame(container, bg=bg_color)
        inner_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Store inner frame reference
        container.inner_frame = inner_frame
        
        return inner_frame
    
    def create_rounded_scrollbar(self, parent, orient, command):
        """Create a custom rounded scrollbar without arrows - red thumb on black background"""
        scrollbar_width = 10
        scrollbar_radius = 5
        
        # Container frame - pure black, no grey
        container = tk.Frame(parent, bg='#000000', width=scrollbar_width)
        
        # Canvas for drawing the scrollbar - pure black background
        canvas = tk.Canvas(container, bg='#000000', 
                          highlightthickness=0, borderwidth=0,
                          width=scrollbar_width)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Track scrollbar state
        class ScrollbarState:
            def __init__(self):
                self.start_pos = 0.0
                self.end_pos = 0.0
                self.dragging = False
                self.last_y = 0
                self.last_x = 0
        
        state = ScrollbarState()
        
        def update_scrollbar(*args):
            """Update scrollbar position based on scroll command"""
            try:
                first, last = float(args[0]), float(args[1])
                state.start_pos = first
                state.end_pos = last
                redraw_scrollbar()
            except:
                pass
        
        def redraw_scrollbar():
            """Redraw the scrollbar - only thumb, no trough/background"""
            canvas.delete("scrollbar")
            canvas.delete("trough")
            
            if orient == tk.VERTICAL:
                w = canvas.winfo_width()
                h = canvas.winfo_height()
                
                if w > 1 and h > 1:  # Only draw if canvas is sized
                    # Calculate thumb position and size
                    if state.end_pos > state.start_pos:
                        thumb_start = int(h * state.start_pos)
                        thumb_height = int(h * (state.end_pos - state.start_pos))
                        thumb_height = max(40, thumb_height)  # Minimum thumb size
                        
                        # Draw simple square rectangle thumb - no background
                        y1 = thumb_start
                        y2 = thumb_start + thumb_height
                        
                        # Simple square rectangle - red color
                        canvas.create_rectangle(
                            0, y1,
                            w, y2,
                            fill='#ff4444',  # Red scrollbar
                            outline="", 
                            tags="scrollbar"
                        )
            else:  # HORIZONTAL
                w = canvas.winfo_width()
                h = canvas.winfo_height()
                
                if w > 1 and h > 1:
                    # Calculate thumb position
                    if state.end_pos > state.start_pos:
                        thumb_start = int(w * state.start_pos)
                        thumb_width = int(w * (state.end_pos - state.start_pos))
                        thumb_width = max(40, thumb_width)
                        
                        # Draw simple square rectangle thumb - no background
                        x1 = thumb_start
                        x2 = thumb_start + thumb_width
                        
                        # Simple square rectangle - red color
                        canvas.create_rectangle(
                            x1, 0,
                            x2, h,
                            fill='#ff4444',  # Red scrollbar
                            outline="", 
                            tags="scrollbar"
                        )
        
        def on_click(event):
            """Handle click on scrollbar"""
            if orient == tk.VERTICAL:
                y = event.y
                h = canvas.winfo_height()
                click_pos = y / h if h > 0 else 0
                
                # Jump to clicked position
                if click_pos < state.start_pos:
                    command("moveto", str(max(0, click_pos - (state.end_pos - state.start_pos) / 2)))
                elif click_pos > state.end_pos:
                    command("moveto", str(min(1 - (state.end_pos - state.start_pos), click_pos)))
                else:
                    state.dragging = True
                    state.last_y = y
            else:  # HORIZONTAL
                x = event.x
                w = canvas.winfo_width()
                click_pos = x / w if w > 0 else 0
                
                if click_pos < state.start_pos:
                    command("moveto", str(max(0, click_pos - (state.end_pos - state.start_pos) / 2)))
                elif click_pos > state.end_pos:
                    command("moveto", str(min(1 - (state.end_pos - state.start_pos), click_pos)))
                else:
                    state.dragging = True
                    state.last_x = x
        
        def on_drag(event):
            """Handle dragging the scrollbar"""
            if state.dragging:
                if orient == tk.VERTICAL:
                    h = canvas.winfo_height()
                    if h > 0:
                        delta = (event.y - state.last_y) / h
                        new_pos = max(0, min(1 - (state.end_pos - state.start_pos), 
                                           state.start_pos + delta))
                        command("moveto", str(new_pos))
                        state.last_y = event.y
                else:  # HORIZONTAL
                    w = canvas.winfo_width()
                    if w > 0:
                        delta = (event.x - state.last_x) / w
                        new_pos = max(0, min(1 - (state.end_pos - state.start_pos), 
                                           state.start_pos + delta))
                        command("moveto", str(new_pos))
                        state.last_x = event.x
        
        def on_release(event):
            """Handle mouse release"""
            state.dragging = False
        
        def on_enter(event):
            """Handle mouse enter - highlight scrollbar"""
            canvas.itemconfig("scrollbar", fill='#ff6666')  # Lighter red on hover
        
        def on_leave(event):
            """Handle mouse leave - restore scrollbar color"""
            canvas.itemconfig("scrollbar", fill='#ff4444')  # Red
            state.dragging = False
        
        # Bind events
        canvas.bind("<Button-1>", on_click)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        
        # Update scrollbar when canvas is resized
        canvas.bind("<Configure>", lambda e: redraw_scrollbar())
        
        # Store update function and set_scroll method
        container.set_scroll = update_scrollbar
        container.update_scrollbar = redraw_scrollbar
        
        # Initial draw
        container.after_idle(redraw_scrollbar)
        
        return container
    
    def create_custom_slider(self, parent, variable, min_val, max_val, length):
        """Create a custom styled quality slider"""
        slider_frame = tk.Frame(parent, bg=self.colors['bg'], height=40, width=length)
        slider_frame.pack_propagate(False)
        
        # Canvas for drawing the slider
        canvas = tk.Canvas(slider_frame, bg=self.colors['bg'], 
                          highlightthickness=0, borderwidth=0,
                          height=40, width=length)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        slider_height = 8
        thumb_size = 24
        
        def draw_slider():
            canvas.delete("all")
            # Force update to get actual dimensions
            canvas.update_idletasks()
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            
            # Use configured length if canvas not yet sized
            if w < 10 or w == 1:
                w = length
            if h < 10 or h == 1:
                h = 40
            
            # Current value
            current_val = variable.get()
            normalized = (current_val - min_val) / (max_val - min_val)
            thumb_x = int(normalized * (w - thumb_size) + thumb_size // 2)
            
            # Draw track (background) - black with subtle border
            track_y = h // 2
            canvas.create_rectangle(
                0, track_y - slider_height // 2,
                w, track_y + slider_height // 2,
                fill='#000000',  # Black background
                outline='#333333',  # Subtle border for visibility
                width=1,
                tags="track"
            )
            
            # Draw filled portion - red
            canvas.create_rectangle(
                0, track_y - slider_height // 2,
                thumb_x, track_y + slider_height // 2,
                fill='#ff4444',  # Red
                outline="",
                tags="filled"
            )
            
            # Draw thumb (rounded circle) - red with white outline for visibility
            thumb_y = track_y
            canvas.create_oval(
                thumb_x - thumb_size // 2, thumb_y - thumb_size // 2,
                thumb_x + thumb_size // 2, thumb_y + thumb_size // 2,
                fill='#ff4444',  # Red
                outline='#ffffff',  # White outline for visibility
                width=2,
                tags="thumb"
            )
        
        def on_click(event):
            w = canvas.winfo_width()
            if w > 0:
                normalized = max(0, min(1, (event.x - thumb_size // 2) / (w - thumb_size)))
                new_val = int(min_val + normalized * (max_val - min_val))
                variable.set(new_val)
                draw_slider()
        
        def on_drag(event):
            w = canvas.winfo_width()
            if w > 0:
                normalized = max(0, min(1, (event.x - thumb_size // 2) / (w - thumb_size)))
                new_val = int(min_val + normalized * (max_val - min_val))
                variable.set(new_val)
                draw_slider()
        
        def on_enter(event):
            canvas.itemconfig("thumb", fill='#ff6666', outline='#ffffff')  # Lighter red on hover
            canvas.itemconfig("filled", fill='#ff6666')
        
        def on_leave(event):
            canvas.itemconfig("thumb", fill='#ff4444', outline='#ffffff')  # Red
            canvas.itemconfig("filled", fill='#ff4444')
        
        # Bind events
        canvas.bind("<Button-1>", on_click)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        
        # Update when variable changes
        def on_var_change(*args):
            draw_slider()
        variable.trace('w', on_var_change)
        
        # Initial draw - force multiple redraws to ensure visibility
        def force_draw():
            draw_slider()
            canvas.update_idletasks()
            draw_slider()  # Redraw after update
        
        canvas.bind("<Configure>", lambda e: draw_slider())
        slider_frame.after(10, force_draw)
        slider_frame.after(100, draw_slider)
        slider_frame.after(200, draw_slider)
        
        return slider_frame
    
    def log(self, message):
        """Add message to log"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.delete(1.0, tk.END)
    
    def on_canvas_configure(self, event):
        """Update canvas window width when canvas is resized"""
        canvas_width = event.width
        # Account for scrollbar width (10px + 5px padding)
        scrollbar_space = 15
        self.thumbnail_canvas.itemconfig(self.canvas_window, width=canvas_width - scrollbar_space)
    
    def estimate_output_size(self, input_path, quality):
        """Estimate output file size based on input and quality"""
        try:
            input_path = Path(input_path)
            if not input_path.exists():
                return None
            
            input_size = input_path.stat().st_size
            
            # Get target format from user selection
            format_selection = self.target_format_var.get()
            # Use user-selected format
            target_format = f".{format_selection.lower()}"
            
            # Rough estimation based on format and quality
            # These are approximate ratios based on typical compression
            if target_format == '.webp':
                # WebP typically reduces size by 25-50% depending on quality
                # Higher quality = larger file
                quality_factor = quality / 100.0
                # Estimate: 0.4 to 0.8 of original size depending on quality
                reduction_factor = 0.5 + (quality_factor * 0.3)
                estimated_size = int(input_size * reduction_factor)
            elif target_format == '.png':
                # PNG size varies - can be smaller or larger depending on content
                # For most images, estimate 1.2-2x original
                estimated_size = int(input_size * 1.5)
            elif target_format in {'.jpg', '.jpeg'}:
                # JPEG with quality setting
                quality_factor = quality / 100.0
                reduction_factor = 0.5 + (quality_factor * 0.3)
                estimated_size = int(input_size * reduction_factor)
            else:
                # Other formats - rough estimate
                estimated_size = int(input_size * 1.2)
            
            return estimated_size
        except:
            return None
    
    def get_image_info(self, file_path):
        """Get image information for tooltip"""
        try:
            file_path = Path(file_path)
            file_size = file_path.stat().st_size
            size_mb = file_size / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{file_size / 1024:.2f} KB"
            
            with Image.open(file_path) as img:
                width, height = img.size
                format_name = img.format or "Unknown"
            
            # Get estimated output size
            try:
                quality_val = int(self.quality_var.get())
            except (ValueError, AttributeError):
                quality_val = 100
            estimated_size = self.estimate_output_size(file_path, quality_val)
            info_text = f"{file_path.name}\n\nSize: {width} × {height} px\nFile Size: {size_str}\nFormat: {format_name}"
            
            if estimated_size:
                est_mb = estimated_size / (1024 * 1024)
                est_str = f"{est_mb:.2f} MB" if est_mb >= 1 else f"{estimated_size / 1024:.2f} KB"
                
                # Get target format from user selection
                format_selection = self.target_format_var.get()
                target_format = format_selection
                
                info_text += f"\n\nEst. Output: ~{est_str} ({target_format})"
            
            return info_text
        except Exception as e:
            return f"{Path(file_path).name}\n\nError: {str(e)}"
    
    def create_thumbnail(self, file_path, index):
        """Create a thumbnail widget for an image"""
        # Thumbnail container frame
        thumb_frame = tk.Frame(self.thumbnail_frame, bg=self.colors['glass'],
                               relief=tk.FLAT, bd=0, width=self.thumbnail_size + 20,
                               height=self.thumbnail_size + 90)
        thumb_frame.pack_propagate(False)
        thumb_frame.file_path = file_path  # Store file path for later updates
        
        # Check if selected
        is_selected = index in self.selected_files
        border_color = self.colors['selected'] if is_selected else self.colors['border']
        thumb_frame.config(highlightbackground=border_color, highlightthickness=2)
        
        # Thumbnail image
        thumb_label = None
        try:
            if file_path not in self.thumbnails:
                with Image.open(file_path) as img:
                    # Create thumbnail
                    img.thumbnail((self.thumbnail_size, self.thumbnail_size), Image.Resampling.LANCZOS)
                    self.thumbnails[file_path] = img.copy()
            
            # Convert to PhotoImage
            if file_path not in self.thumbnail_photos:
                photo = ImageTk.PhotoImage(self.thumbnails[file_path])
                self.thumbnail_photos[file_path] = photo
            else:
                photo = self.thumbnail_photos[file_path]
            
            thumb_label = tk.Label(thumb_frame, image=photo, bg=self.colors['glass'],
                                  cursor='hand2')
            thumb_label.image = photo  # Keep a reference
            thumb_label.pack(pady=5)
        except Exception:
            # Error loading image - show placeholder
            error_label = tk.Label(thumb_frame, text="❌\nError", 
                                  bg=self.colors['glass'], fg=self.colors['text_dim'],
                                  font=(self.font_family, 10), cursor='hand2')
            error_label.pack(expand=True)
            thumb_label = error_label
        
        # File name label (truncated)
        file_name = Path(file_path).name
        if len(file_name) > 20:
            file_name = file_name[:17] + "..."
        
        name_label = tk.Label(thumb_frame, text=file_name, bg=self.colors['glass'],
                             fg=self.colors['text'], font=(self.font_family, 8),
                             wraplength=self.thumbnail_size)
        name_label.pack(pady=(0, 2))
        
        # Original file size label
        try:
            input_size = Path(file_path).stat().st_size
            input_mb = input_size / (1024 * 1024)
            input_str = f"{input_mb:.2f} MB" if input_mb >= 1 else f"{input_size / 1024:.1f} KB"
            original_size_label = tk.Label(thumb_frame, text=input_str, 
                                          bg=self.colors['glass'], fg=self.colors['text_dim'],
                                          font=(self.font_family, 8),
                                          wraplength=self.thumbnail_size)
            original_size_label.pack(pady=(0, 1))
        except:
            original_size_label = None
        
        # Converted file size label - show actual output size if converted, otherwise estimated
        if file_path in self.output_file_sizes:
            # Show actual converted file size
            output_size = self.output_file_sizes[file_path]
            est_mb = output_size / (1024 * 1024)
            est_str = f"{est_mb:.2f} MB" if est_mb >= 1 else f"{output_size / 1024:.1f} KB"
            size_label = tk.Label(thumb_frame, text=est_str, 
                                 bg=self.colors['glass'], fg='#ff4444',
                                 font=(self.font_family, 8, 'bold'),
                                 wraplength=self.thumbnail_size)
            size_label.pack(pady=(0, 5))
        else:
            # Show estimated file size
            try:
                quality_val = int(self.quality_var.get())
            except (ValueError, AttributeError):
                quality_val = 100
            estimated_size = self.estimate_output_size(file_path, quality_val)
            if estimated_size:
                est_mb = estimated_size / (1024 * 1024)
                est_str = f"{est_mb:.2f} MB" if est_mb >= 1 else f"{estimated_size / 1024:.1f} KB"
                size_label = tk.Label(thumb_frame, text=f"~{est_str}", 
                                     bg=self.colors['glass'], fg=self.colors['text'],
                                     font=(self.font_family, 8),
                                     wraplength=self.thumbnail_size)
                size_label.pack(pady=(0, 5))
            else:
                # Empty label for spacing if no estimate
                size_label = tk.Label(thumb_frame, text="", bg=self.colors['glass'],
                                    font=(self.font_family, 8), height=1)
                size_label.pack(pady=(0, 5))
        
        # Bind events
        def on_click(event):
            if event.state & 0x1:  # Ctrl key - toggle individual selection
                if index in self.selected_files:
                    self.selected_files.remove(index)
                else:
                    self.selected_files.add(index)
                self.drag_start_index = index
            elif event.state & 0x4:  # Shift key - select range
                if self.drag_start_index is not None:
                    start = min(self.drag_start_index, index)
                    end = max(self.drag_start_index, index)
                    self.selected_files.update(range(start, end + 1))
                else:
                    self.selected_files = {index}
                    self.drag_start_index = index
            else:
                # Single select
                self.selected_files = {index}
                self.drag_start_index = index
            self.update_thumbnail_grid()
        
        
        def on_enter(event):
            # Show tooltip
            self.show_tooltip(thumb_frame, file_path)
        
        def on_leave(event):
            # Hide tooltip
            self.hide_tooltip()
        
        def on_button_press(event):
            # Start drag selection (only if not Ctrl or Shift)
            if not (event.state & 0x1) and not (event.state & 0x4):
                self.is_dragging = True
                self.drag_start_index = index
                if index not in self.selected_files:
                    self.selected_files = {index}
                    self.update_thumbnail_grid()
        
        def on_drag_motion(event):
            if self.is_dragging and self.drag_start_index is not None:
                # Select range from start to current index
                start = min(self.drag_start_index, index)
                end = max(self.drag_start_index, index)
                self.selected_files.update(range(start, end + 1))
                self.update_thumbnail_grid()
        
        def on_button_release(event):
            self.is_dragging = False
        
        # Bind click events - use Button-1 for all clicks including Shift
        thumb_frame.bind('<Button-1>', on_click)
        if thumb_label:
            thumb_label.bind('<Button-1>', on_click)
        name_label.bind('<Button-1>', on_click)
        
        # Also bind Shift-Button-1 explicitly for range selection
        thumb_frame.bind('<Shift-Button-1>', on_click)
        if thumb_label:
            thumb_label.bind('<Shift-Button-1>', on_click)
        name_label.bind('<Shift-Button-1>', on_click)
        
        # Bind drag events for selection (only when not using Shift/Ctrl)
        thumb_frame.bind('<ButtonPress-1>', on_button_press)
        thumb_frame.bind('<B1-Motion>', on_drag_motion)
        thumb_frame.bind('<ButtonRelease-1>', on_button_release)
        if thumb_label:
            thumb_label.bind('<ButtonPress-1>', on_button_press)
            thumb_label.bind('<B1-Motion>', on_drag_motion)
            thumb_label.bind('<ButtonRelease-1>', on_button_release)
        name_label.bind('<ButtonPress-1>', on_button_press)
        name_label.bind('<B1-Motion>', on_drag_motion)
        name_label.bind('<ButtonRelease-1>', on_button_release)
        
        # Bind hover events
        thumb_frame.bind('<Enter>', on_enter)
        thumb_frame.bind('<Leave>', on_leave)
        if thumb_label:
            thumb_label.bind('<Enter>', on_enter)
            thumb_label.bind('<Leave>', on_leave)
        
        return thumb_frame
    
    def update_thumbnail_size(self, file_path, output_size):
        """Update thumbnail to show actual output file size after conversion"""
        # Refresh the entire grid to show updated sizes
        self.update_thumbnail_grid()
    
    def show_tooltip(self, widget, file_path):
        """Show tooltip with image details"""
        self.hide_tooltip()  # Remove any existing tooltip
        
        info = self.get_image_info(file_path)
        self.hover_widget = widget
        
        # Get widget position
        widget.update_idletasks()
        x = widget.winfo_rootx() + widget.winfo_width() + 10
        y = widget.winfo_rooty()
        
        # Create tooltip window
        self.hover_tooltip = tk.Toplevel(self.root)
        self.hover_tooltip.wm_overrideredirect(True)
        self.hover_tooltip.wm_geometry(f"+{x}+{y}")
        self.hover_tooltip.configure(bg=self.colors['bg'], 
                                    highlightbackground=self.colors['border'],
                                    highlightthickness=1)
        
        tooltip_label = tk.Label(self.hover_tooltip, text=info,
                               bg=self.colors['bg'], fg=self.colors['text'],
                               font=(self.font_family, 9), justify=tk.LEFT, padx=10, pady=8)
        tooltip_label.pack()
    
    def hide_tooltip(self):
        """Hide tooltip"""
        if self.hover_tooltip:
            self.hover_tooltip.destroy()
            self.hover_tooltip = None
        self.hover_widget = None
    
    def _update_thumbnails_if_ready(self):
        """Helper to update thumbnails only if UI is ready"""
        if hasattr(self, 'thumbnail_frame') and hasattr(self, 'pending_files') and self.pending_files:
            self.update_thumbnail_grid()
    
    def update_thumbnail_grid(self):
        """Update the thumbnail grid display"""
        # Clear existing thumbnails
        for widget in self.thumbnail_frame.winfo_children():
            widget.destroy()
        
        if not self.pending_files:
            # Show placeholder - centered
            placeholder = tk.Label(self.thumbnail_frame, 
                                  text="Drag and drop images or folders here...",
                                  bg=self.colors['glass'], fg=self.colors['text_dim'],
                                  font=(self.font_family, 12))
            placeholder.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        else:
            # Calculate grid layout
            cols = max(1, (self.thumbnail_canvas.winfo_width() or 800) // (self.thumbnail_size + 40))
            
            # Create thumbnails in grid
            self.thumbnail_widgets = {}  # Store widget references for drag selection
            for i, file_path in enumerate(self.pending_files):
                thumb = self.create_thumbnail(file_path, i)
                row = i // cols
                col = i % cols
                thumb.grid(row=row, column=col, padx=10, pady=10, sticky='nw')
                self.thumbnail_widgets[i] = thumb
        
        # Bind canvas drag for cross-thumbnail selection
        self.thumbnail_canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.thumbnail_canvas.bind('<ButtonRelease-1>', lambda e: setattr(self, 'is_dragging', False))
        
        # Update scroll region - only if there are files
        self.thumbnail_frame.update_idletasks()
        if self.pending_files:
            bbox = self.thumbnail_canvas.bbox('all')
            if bbox:
                # Ensure scroll region includes full content height so scrollbar stays visible
                x1, y1, x2, y2 = bbox
                # Add small padding to bottom to ensure scrollbar is always accessible
                canvas_height = self.thumbnail_canvas.winfo_height() or 600
                if y2 < canvas_height:
                    y2 = canvas_height
                self.thumbnail_canvas.configure(scrollregion=(x1, y1, x2, y2))
            else:
                canvas_width = self.thumbnail_canvas.winfo_width() or 800
                canvas_height = self.thumbnail_canvas.winfo_height() or 600
                self.thumbnail_canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
        else:
            # No scrolling when empty - set to canvas size
            canvas_width = self.thumbnail_canvas.winfo_width() or 800
            canvas_height = self.thumbnail_canvas.winfo_height() or 600
            self.thumbnail_canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
        self.update_start_button_state()
    
    def on_canvas_drag(self, event):
        """Handle dragging across canvas to select multiple thumbnails"""
        if self.is_dragging and self.drag_start_index is not None:
            # Convert canvas coordinates to frame coordinates
            canvas_x = self.thumbnail_canvas.canvasx(event.x)
            canvas_y = self.thumbnail_canvas.canvasy(event.y)
            
            # Find which thumbnail widget is under cursor
            for idx, thumb_widget in self.thumbnail_widgets.items():
                try:
                    # Get widget position relative to frame
                    thumb_x = thumb_widget.winfo_x()
                    thumb_y = thumb_widget.winfo_y()
                    thumb_w = thumb_widget.winfo_width()
                    thumb_h = thumb_widget.winfo_height()
                    
                    # Check if point is within thumbnail bounds
                    if (thumb_x <= canvas_x <= thumb_x + thumb_w and 
                        thumb_y <= canvas_y <= thumb_y + thumb_h):
                        # Select range from start to this index
                        start = min(self.drag_start_index, idx)
                        end = max(self.drag_start_index, idx)
                        self.selected_files.update(range(start, end + 1))
                        self.update_thumbnail_grid()
                        break
                except:
                    continue
    
    def clear_file_list(self):
        """Clear the file list"""
        self.pending_files.clear()
        self.selected_files.clear()
        self.thumbnails.clear()
        self.thumbnail_photos.clear()
        self.hide_tooltip()
        self.update_thumbnail_grid()
    
    def remove_selected_files(self):
        """Remove selected files from list"""
        if not self.selected_files:
            messagebox.showinfo("No Selection", "Please select images to remove.")
            return
        
        # Remove selected files (in reverse order to maintain indices)
        indices_to_remove = sorted(self.selected_files, reverse=True)
        for idx in indices_to_remove:
            if 0 <= idx < len(self.pending_files):
                removed_file = self.pending_files.pop(idx)
                # Clear thumbnail cache
                if removed_file in self.thumbnails:
                    del self.thumbnails[removed_file]
                if removed_file in self.thumbnail_photos:
                    del self.thumbnail_photos[removed_file]
        
        self.selected_files.clear()
        self.update_thumbnail_grid()
    
    def select_all_files(self):
        """Select all files"""
        self.selected_files = set(range(len(self.pending_files)))
        self.update_thumbnail_grid()
    
    def update_start_button_state(self):
        """Update start button state based on pending files and conversion status"""
        if self.is_converting:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.stop_button.config(state=tk.DISABLED)
            # Enable if there are files (selected or all)
            files_to_convert = self.get_files_to_convert()
            if files_to_convert:
                self.start_button.config(state=tk.NORMAL)
            else:
                self.start_button.config(state=tk.DISABLED)
    
    def get_files_to_convert(self):
        """Get list of files to convert (selected or all)"""
        if self.selected_files:
            return [self.pending_files[i] for i in self.selected_files if 0 <= i < len(self.pending_files)]
        return self.pending_files.copy()
    
    def add_files_to_list(self, file_paths):
        """Add files to the pending list"""
        new_files = []
        for path_str in file_paths:
            path = Path(path_str)
            if path.is_file():
                if self.converter.is_supported(path):
                    if path not in self.pending_files:
                        new_files.append(path)
                        self.pending_files.append(path)
                else:
                    self.log(f"Skipped (unsupported): {path.name}")
            elif path.is_dir():
                # Add all images from folder
                for ext in self.converter.SUPPORTED_FORMATS:
                    for img_file in path.glob(f"*{ext}"):
                        if img_file not in self.pending_files:
                            new_files.append(img_file)
                            self.pending_files.append(img_file)
                    for img_file in path.glob(f"*{ext.upper()}"):
                        if img_file not in self.pending_files:
                            new_files.append(img_file)
                            self.pending_files.append(img_file)
        
        if new_files:
            self.update_thumbnail_grid()
            self.log(f"Added {len(new_files)} file(s) to queue. Total: {len(self.pending_files)}")
        else:
            messagebox.showwarning("No Images", "No new supported images found.")
    
    def browse_output(self):
        """Browse for output directory"""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_var.set(folder)
            self.converter.output_dir = folder
        else:
            self.output_var.set("Same folder as input")
            self.converter.output_dir = None
    
    def select_files(self):
        """Select files to add to queue"""
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.webp"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("WebP files", "*.webp"),
                ("All files", "*.*")
            ]
        )
        if files:
            self.add_files_to_list(files)
    
    def select_folder(self):
        """Select folder to add to queue"""
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            self.add_files_to_list([folder])
    
    def on_drop(self, event):
        """Handle drag and drop - add files to queue"""
        if DND_AVAILABLE:
            try:
                # Parse dropped files
                files = self.root.tk.splitlist(event.data)
                self.add_files_to_list(files)
            except Exception as e:
                self.log(f"Error processing dropped files: {e}")
                messagebox.showerror("Error", f"Failed to process dropped files: {e}")
        else:
            messagebox.showinfo("Info", "Drag-and-drop requires tkinterdnd2.\nPlease use the file selection buttons.")
    
    def start_conversion(self):
        """Start converting files in a separate thread"""
        if self.is_converting or not self.pending_files:
            return
        
        self.is_converting = True
        self.should_stop = False
        self.update_start_button_state()
        
        # Start conversion in a separate thread
        self.conversion_thread = threading.Thread(target=self.convert_files_thread, daemon=True)
        self.conversion_thread.start()
    
    def stop_conversion(self):
        """Stop the current conversion"""
        if self.is_converting:
            self.should_stop = True
            self.log("\n⏹ Stopping conversion...")
    
    def log_thread_safe(self, message):
        """Thread-safe logging helper"""
        self.root.after(0, lambda: self.log(message))
    
    def convert_files_thread(self):
        """Convert files in a separate thread"""
        try:
            quality_value = int(self.quality_var.get())
            # Ensure quality is between 1 and 100
            quality_value = max(1, min(100, quality_value))
            self.converter.quality = quality_value
        except (ValueError, AttributeError):
            self.converter.quality = 100  # Default if invalid
        
        # Get target format from user selection
        format_selection = self.target_format_var.get()
        # Convert format name to extension (e.g., "PNG" -> ".png")
        target_format = f".{format_selection.lower()}"
        
        files_to_convert = self.get_files_to_convert()
        total_files = len(files_to_convert)
        
        # Use root.after for thread-safe GUI updates
        self.log_thread_safe(f"\n{'='*50}")
        self.log_thread_safe(f"Starting conversion of {total_files} image(s)...")
        self.log_thread_safe(f"Target Format: {format_selection}")
        self.log_thread_safe(f"Quality: {self.converter.quality}")
        self.log_thread_safe(f"{'='*50}")
        
        success_count = 0
        skipped_count = 0
        
        for i, file_path in enumerate(files_to_convert, 1):
            if self.should_stop:
                self.log_thread_safe(f"\n⏹ Conversion stopped by user")
                break
            
            # Update status (thread-safe)
            self.log_thread_safe(f"[{i}/{total_files}] Processing: {file_path.name}")
            
            # Convert the file with user-selected format
            success, output_path, message = self.converter.convert_image(file_path, target_format)
            
            if success:
                success_count += 1
                # Get output file size
                if output_path and Path(output_path).exists():
                    output_size = Path(output_path).stat().st_size
                    self.output_file_sizes[file_path] = output_size
                    # Update thumbnail on main thread
                    self.root.after(0, self.update_thumbnail_size, file_path, output_size)
                self.log_thread_safe(f"  ✓ {message}")
            else:
                skipped_count += 1
                self.log_thread_safe(f"  ✗ {message}")
        
        # Update UI on main thread
        self.root.after(0, self.conversion_complete, success_count, skipped_count, total_files)
    
    def conversion_complete(self, success_count, skipped_count, total_files):
        """Called when conversion completes (runs on main thread)"""
        self.is_converting = False
        self.should_stop = False
        self.selected_files.clear()  # Clear selections after conversion
        self.update_thumbnail_grid()  # Refresh grid to update selection borders
        self.update_start_button_state()
        
        self.log(f"\n{'='*50}")
        self.log(f"✓ Conversion Complete!")
        self.log(f"  Success: {success_count}")
        self.log(f"  Failed: {skipped_count}")
        self.log(f"  Total: {total_files}")
        self.log(f"{'='*50}")
        
        # Files remain in the list - user can clear manually if desired
        # This allows re-converting if needed
        
        messagebox.showinfo("Conversion Complete", 
                          f"Converted {success_count} of {total_files} images.\n"
                          f"Failed: {skipped_count}")
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()


def folder_mode(folder_path, output_dir=None, quality=90, recursive=False):
    """Folder-based conversion mode"""
    converter = ImageConverter(output_dir=output_dir, quality=quality)
    
    # If output_dir not specified, create 'converted' subfolder
    if output_dir is None:
        output_dir = Path(folder_path) / "converted"
        converter.output_dir = output_dir
    
    print(f"Converting images in: {folder_path}")
    print(f"Output directory: {output_dir}")
    print(f"Quality: {quality}")
    print("-" * 50)
    
    results = converter.convert_folder(folder_path, recursive=recursive)
    
    success_count = 0
    for success, output_path, message in results:
        print(message)
        if success:
            success_count += 1
    
    print("-" * 50)
    print(f"✓ Completed: {success_count}/{len(results)} images converted successfully")
    return success_count == len(results)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Convert images between PNG/JPG and WebP formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # GUI mode (default)
  python image_converter.py
  
  # Convert folder
  python image_converter.py --folder ./images
  
  # Convert folder with custom output
  python image_converter.py --folder ./images --output ./output
  
  # Convert folder recursively
  python image_converter.py --folder ./images --recursive
        """
    )
    
    parser.add_argument('--folder', '-f', type=str,
                       help='Folder containing images to convert')
    parser.add_argument('--output', '-o', type=str,
                       help='Output directory (default: ./converted)')
    parser.add_argument('--quality', '-q', type=int, default=90,
                       help='WebP/JPEG quality 1-100 (default: 90)')
    parser.add_argument('--recursive', '-r', action='store_true',
                       help='Process subdirectories recursively')
    
    args = parser.parse_args()
    
    # Validate quality
    if not 1 <= args.quality <= 100:
        print("Error: Quality must be between 1 and 100")
        sys.exit(1)
    
    # Run in appropriate mode
    if args.folder:
        success = folder_mode(args.folder, args.output, args.quality, args.recursive)
        sys.exit(0 if success else 1)
    else:
        # GUI mode
        app = ConverterGUI()
        app.run()


if __name__ == "__main__":
    main()

