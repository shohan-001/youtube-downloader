import tkinter as tk
import customtkinter as ctk
import threading
import sys
import os
import shutil
from tkinter import filedialog, messagebox
import yt_dlp
import re
import time
import random
import zipfile
try:
    from PIL import Image
    from io import BytesIO
    import urllib.request
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Set theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PlaylistSelectionDialog(ctk.CTkToplevel):
    def __init__(self, parent, video_list, title="Select Videos"):
        super().__init__(parent)
        self.title(title)
        self.geometry("600x600")
        self.result = None
        
        self.video_list = video_list # List of dicts: {'id': 1, 'title': '...'}
        self.check_vars = []
        
        # Header
        self.label = ctk.CTkLabel(self, text=f"Select Videos to Download ({len(video_list)} found)", font=ctk.CTkFont(size=16, weight="bold"))
        self.label.pack(pady=10)
        
        # Buttons Frame
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=20, pady=5)
        
        self.select_all_btn = ctk.CTkButton(self.btn_frame, text="Select All", width=100, command=self.select_all)
        self.select_all_btn.pack(side="left", padx=5)
        
        self.deselect_all_btn = ctk.CTkButton(self.btn_frame, text="Deselect All", width=100, command=self.deselect_all)
        self.deselect_all_btn.pack(side="left", padx=5)
        
        # Scrollable List
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        for i, video in enumerate(self.video_list):
            var = ctk.BooleanVar(value=True) # Default selected
            self.check_vars.append(var)
            idx = i + 1
            title = video.get('title', 'Unknown')
            chk = ctk.CTkCheckBox(self.scroll_frame, text=f"{idx}. {title}", variable=var)
            chk.pack(anchor="w", pady=2)
            
        # Action Buttons
        self.confirm_btn = ctk.CTkButton(self, text="Confirm Selection", command=self.confirm)
        self.confirm_btn.pack(pady=20)
        
    def select_all(self):
        for var in self.check_vars: var.set(True)
        
    def deselect_all(self):
        for var in self.check_vars: var.set(False)
        
    def confirm(self):
        selected_indices = []
        for i, var in enumerate(self.check_vars):
            if var.get():
                selected_indices.append(i + 1) # 1-based index for yt-dlp
        self.result = selected_indices
        self.destroy()

class MyLogger:
    def __init__(self, gui):
        self.gui = gui
    
    def debug(self, msg):
        if not msg.startswith('[debug] '):
            self.gui.log_message(msg)
    
    def info(self, msg):
        self.gui.log_message(msg)

    def warning(self, msg):
        self.gui.log_message(f"[Warning] {msg}")

    def error(self, msg):
        self.gui.log_message(f"[Error] {msg}")

class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("YouTube Downloader Pro v1.3.2")
        self.geometry("800x800")
        self.resizable(True, True)
        self.minsize(500, 500)

        # Variables
        self.url_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="video")
        self.quality_var = tk.StringVar(value="Best")
        self.status_var = tk.StringVar(value="Ready")
        self.playlist_option_var = tk.StringVar(value="video") # 'video', 'playlist', 'select'
        self.download_folder = os.getcwd()
        
        # Video info storage
        self.current_video_title = None
        self.current_video_channel = None
        self.current_video_title = None
        self.current_video_channel = None
        self.current_video_duration = None
        
        # Control Flags
        self.check_cancel = False

        # Cookies file path
        self.cookies_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies.txt')

        # Create UI
        self.create_widgets()
        
        # Check FFmpeg
        self.check_ffmpeg()

    def create_widgets(self):
        # Allow grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # Main scrollable frame expands

        # === Header (Fixed at top) ===
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="🎬 YouTube Downloader Pro v1.3.2",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.title_label.pack(side="left")
        
        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Download videos and playlists easily",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        )
        self.subtitle_label.pack(side="left", padx=(15, 0))
        
        # Theme toggle button
        self.theme_mode = "Dark"
        self.theme_btn = ctk.CTkButton(
            self.header_frame,
            text="🌙",
            width=40,
            height=30,
            command=self.toggle_theme,
            fg_color="transparent",
            hover_color=("gray80", "gray25")
        )
        self.theme_btn.pack(side="right")
        
        # History Button
        self.history_btn = ctk.CTkButton(
            self.header_frame,
            text="📜",
            width=40,
            height=30,
            command=self.show_history,
            fg_color="transparent",
            hover_color=("gray80", "gray25")
        )
        self.history_btn.pack(side="right", padx=(0, 5))

        # === Scrollable Main Frame ===
        self.main_scrollable = ctk.CTkScrollableFrame(self)
        self.main_scrollable.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
        self.main_scrollable.grid_columnconfigure(0, weight=1)

        # === URL Input ===
        self.url_frame = ctk.CTkFrame(self.main_scrollable, corner_radius=10)
        self.url_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        self.url_label = ctk.CTkLabel(
            self.url_frame,
            text="🔗 YouTube URL:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.url_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        self.url_entry = ctk.CTkEntry(
            self.url_frame,
            textvariable=self.url_var,
            placeholder_text="Paste video or playlist URL here...",
            height=40,
            font=ctk.CTkFont(size=13),
            corner_radius=8
        )
        self.url_entry.pack(fill="x", padx=15, pady=(0, 15), expand=True)

        # === Options Frame ===
        self.options_container = ctk.CTkFrame(self.main_scrollable, fg_color="transparent")
        self.options_container.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.options_container.grid_columnconfigure(0, weight=1)
        self.options_container.grid_columnconfigure(1, weight=1)

        # Mode Selection Card
        self.mode_card = ctk.CTkFrame(self.options_container, corner_radius=10)
        self.mode_card.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="ew")

        self.mode_label = ctk.CTkLabel(
            self.mode_card,
            text="📹 Download Mode",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.mode_label.pack(anchor="w", padx=15, pady=(15, 10))

        self.mode_radio_frame = ctk.CTkFrame(self.mode_card, fg_color="transparent")
        self.mode_radio_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.radio_video = ctk.CTkRadioButton(
            self.mode_radio_frame,
            text="🎥 Video (MP4)",
            variable=self.mode_var,
            value="video",
            command=self.update_quality_options
        )
        self.radio_video.pack(side="left", padx=(0, 20))

        self.radio_audio = ctk.CTkRadioButton(
            self.mode_radio_frame,
            text="🎵 Audio (MP3)",
            variable=self.mode_var,
            value="audio",
            command=self.update_quality_options
        )
        self.radio_audio.pack(side="left")

        # Quality Selection Card
        self.quality_card = ctk.CTkFrame(self.options_container, corner_radius=10)
        self.quality_card.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="ew")

        self.quality_label = ctk.CTkLabel(
            self.quality_card,
            text="⚙️ Quality",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.quality_label.pack(anchor="w", padx=15, pady=(15, 10))

        self.quality_menu = ctk.CTkOptionMenu(
            self.quality_card,
            variable=self.quality_var,
            values=["Best", "2160p", "1440p", "1080p", "720p", "480p", "360p"],
            corner_radius=8,
            width=150
        )
        self.quality_menu.pack(padx=15, pady=(0, 15))

        # === Video Info Card (Hidden by default) ===
        self.video_info_card = ctk.CTkFrame(self.main_scrollable, corner_radius=10, fg_color=("gray95", "gray17"))
        
        self.video_info_label = ctk.CTkLabel(
            self.video_info_card,
            text="📹 Video Information",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.video_info_label.pack(anchor="w", padx=15, pady=(15, 10))

        self.video_info_container = ctk.CTkFrame(self.video_info_card, fg_color="transparent")
        self.video_info_container.pack(fill="x", padx=15, pady=(0, 15))

        self.video_title_label = ctk.CTkLabel(
            self.video_info_container,
            text="Title: -",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            wraplength=600
        )
        self.video_title_label.pack(anchor="w", pady=(0, 5))

        self.video_meta_label = ctk.CTkLabel(
            self.video_info_container,
            text="Channel: - | Duration: -",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        self.video_meta_label.pack(anchor="w")

        self.video_filename_label = ctk.CTkLabel(
            self.video_info_container,
            text="File: -",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#3498DB",
            anchor="w",
            wraplength=600
        )
        self.video_filename_label.pack(anchor="w", pady=(2, 0))

        # === Playlist Options (Hidden by default) ===
        self.playlist_frame = ctk.CTkFrame(self.main_scrollable, corner_radius=10, fg_color=("gray95", "gray17"))
        
        self.playlist_label = ctk.CTkLabel(
            self.playlist_frame,
            text="📋 Playlist Detected:",
            text_color="#3B8ED0",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.playlist_label.pack(side="left", padx=15, pady=12)
        
        self.dl_single_btn = ctk.CTkRadioButton(
            self.playlist_frame,
            text="Download Video Only",
            variable=self.playlist_option_var,
            value="video"
        )
        self.dl_single_btn.pack(side="left", padx=(0, 15))
        
        self.dl_playlist_btn = ctk.CTkRadioButton(
            self.playlist_frame,
            text="Download Entire Playlist",
            variable=self.playlist_option_var,
            value="playlist"
        )
        self.dl_playlist_btn.pack(side="left", padx=(0, 15))
        
        self.select_videos_btn = ctk.CTkButton(
            self.playlist_frame,
            text="Select Videos...",
            width=100,
            command=self.fetch_playlist_and_select,
            fg_color="gray",
            hover_color="gray25"
        )
        self.select_videos_btn.pack(side="left", padx=(0, 15))
        
        # === Settings Card ===
        self.settings_card = ctk.CTkFrame(self.main_scrollable, corner_radius=10)
        self.settings_card.grid(row=3, column=0, padx=20, pady=8, sticky="ew")

        self.settings_label = ctk.CTkLabel(
            self.settings_card,
            text="⚙️ Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.settings_label.pack(anchor="w", padx=15, pady=(15, 15))

        # Auth section
        self.auth_section = ctk.CTkFrame(self.settings_card, fg_color="transparent")
        self.auth_section.pack(fill="x", padx=15, pady=(0, 10))

        self.auth_label = ctk.CTkLabel(
            self.auth_section,
            text="🔐 Authentication:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.auth_label.pack(side="left", padx=(0, 10))

        self.cookie_source_var = tk.StringVar(value="None")
        self.cookie_source_menu = ctk.CTkOptionMenu(
            self.auth_section,
            variable=self.cookie_source_var,
            values=["None", "Chrome", "Firefox", "Edge", "Opera", "Brave", "Select File..."],
            command=self.on_cookie_source_change,
            width=150,
            corner_radius=8
        )
        self.cookie_source_menu.pack(side="left", padx=5)

        self.browse_btn = ctk.CTkButton(
            self.auth_section,
            text="Browse...",
            width=80,
            command=self.browse_cookie_file,
            corner_radius=8
        )
        self.auth_path_label = ctk.CTkLabel(self.auth_section, text="", text_color="gray", font=ctk.CTkFont(size=11))

        # Save location section
        self.save_section = ctk.CTkFrame(self.settings_card, fg_color="transparent")
        self.save_section.pack(fill="x", padx=15, pady=(10, 15))

        self.save_loc_label = ctk.CTkLabel(
            self.save_section,
            text="📁 Save To:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.save_loc_label.pack(side="left", padx=(0, 10))

        self.save_loc_path_label = ctk.CTkLabel(
            self.save_section,
            text=self.download_folder if hasattr(self, 'download_folder') else "Default",
            font=ctk.CTkFont(size=11)
        )
        self.save_loc_path_label.pack(side="left", fill="x", expand=True, padx=5)
        self.update_save_loc_label()

        self.save_loc_btn = ctk.CTkButton(
            self.save_section,
            text="Change...",
            width=80,
            command=self.browse_download_folder,
            corner_radius=8
        )
        self.save_loc_btn.pack(side="right", padx=(10, 0))
        
        # Keep reference to auth_frame and save_loc_frame for compatibility with existing code
        self.auth_frame = self.settings_card
        self.save_loc_frame = self.settings_card
        
        # === Download Button & Status ===
        self.action_frame = ctk.CTkFrame(self.main_scrollable, fg_color="transparent")
        self.action_frame.grid(row=5, column=0, padx=20, pady=12, sticky="ew")

        self.download_btn = ctk.CTkButton(
            self.action_frame,
            text="⬇️ Start Download",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            corner_radius=12,
            fg_color=("#3B8ED0", "#1F6AA5"),
            hover_color=("#2E7BC7", "#185A8A"),
            command=self.start_download_thread
        )
        self.download_btn.pack(fill="x", pady=(0, 10))

        self.cancel_btn = ctk.CTkButton(
            self.action_frame,
            text="⏹️ Cancel Download",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            corner_radius=12,
            fg_color="red",
            hover_color="darkred",
            command=self.cancel_download
        )
        # self.cancel_btn.pack(fill="x", pady=(0, 10)) # Hidden initially
        
        # Open Download Folder Button (Initially Hidden/Disabled or Just Disabled)
        self.open_folder_btn = ctk.CTkButton(
            self.action_frame,
            text="📂 Open Download Folder",
            font=ctk.CTkFont(size=14),
            height=40,
            fg_color="green",
            hover_color="darkgreen",
            state="disabled",
            command=self.open_download_folder
        )
        # We can pack it but keep it disabled, or pack_forget until needed. 
        # Making it visible but disabled is better UX for discovery.
        self.open_folder_btn.pack(fill="x", pady=(0, 0))
        
        # === Stats Frame ===
        self.stats_frame = ctk.CTkFrame(self.main_scrollable, corner_radius=10)
        self.stats_frame.grid(row=6, column=0, padx=20, pady=8, sticky="ew")

        # Speed Stat Card
        self.speed_card = ctk.CTkFrame(self.stats_frame, corner_radius=8, fg_color=("gray90", "gray17"))
        self.speed_card.pack(side="left", fill="both", expand=True, padx=5, pady=10)

        self.speed_icon = ctk.CTkLabel(self.speed_card, text="⚡", font=ctk.CTkFont(size=20))
        self.speed_icon.pack(pady=(10, 0))

        self.speed_label = ctk.CTkLabel(self.speed_card, text="Speed", font=ctk.CTkFont(size=11), text_color="gray")
        self.speed_label.pack()

        self.stat_speed = ctk.CTkLabel(self.speed_card, text="-", font=ctk.CTkFont(size=14, weight="bold"))
        self.stat_speed.pack(pady=(0, 10))

        # ETA Stat Card
        self.eta_card = ctk.CTkFrame(self.stats_frame, corner_radius=8, fg_color=("gray90", "gray17"))
        self.eta_card.pack(side="left", fill="both", expand=True, padx=5, pady=10)

        self.eta_icon = ctk.CTkLabel(self.eta_card, text="⏱️", font=ctk.CTkFont(size=20))
        self.eta_icon.pack(pady=(10, 0))

        self.eta_label = ctk.CTkLabel(self.eta_card, text="ETA", font=ctk.CTkFont(size=11), text_color="gray")
        self.eta_label.pack()

        self.stat_eta = ctk.CTkLabel(self.eta_card, text="-", font=ctk.CTkFont(size=14, weight="bold"))
        self.stat_eta.pack(pady=(0, 10))

        # Size Stat Card
        self.size_card = ctk.CTkFrame(self.stats_frame, corner_radius=8, fg_color=("gray90", "gray17"))
        self.size_card.pack(side="left", fill="both", expand=True, padx=5, pady=10)

        self.size_icon = ctk.CTkLabel(self.size_card, text="💾", font=ctk.CTkFont(size=20))
        self.size_icon.pack(pady=(10, 0))

        self.size_label = ctk.CTkLabel(self.size_card, text="Size", font=ctk.CTkFont(size=11), text_color="gray")
        self.size_label.pack()

        self.stat_size = ctk.CTkLabel(self.size_card, text="-", font=ctk.CTkFont(size=14, weight="bold"))
        self.stat_size.pack(pady=(0, 10))

        # === Progress Bar ===
        self.progress_card = ctk.CTkFrame(self.main_scrollable, corner_radius=10)
        self.progress_card.grid(row=7, column=0, padx=20, pady=8, sticky="ew")

        self.progress_label = ctk.CTkLabel(
            self.progress_card,
            text="Download Progress",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.progress_label.pack(anchor="w", padx=15, pady=(15, 10))

        self.progress_container = ctk.CTkFrame(self.progress_card, fg_color="transparent")
        self.progress_container.pack(fill="x", padx=15, pady=(0, 10))

        self.progress_bar = ctk.CTkProgressBar(self.progress_container, height=20, corner_radius=10)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.progress_bar.set(0)

        self.progress_percent = ctk.CTkLabel(
            self.progress_container,
            text="0%",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=50
        )
        self.progress_percent.pack(side="right")

        self.progress_status = ctk.CTkLabel(
            self.progress_card,
            text="Ready",
            text_color="gray",
            font=ctk.CTkFont(size=11)
        )
        self.progress_status.pack(anchor="w", padx=15, pady=(0, 15))

        # === Console / Log ===
        self.log_frame = ctk.CTkFrame(self, corner_radius=10)
        self.log_frame.grid(row=8, column=0, padx=20, pady=(0, 20), sticky="nsew")

        self.log_header = ctk.CTkFrame(self.log_frame, fg_color="transparent")
        self.log_header.pack(fill="x", padx=10, pady=(10, 5))

        self.log_label = ctk.CTkLabel(
            self.log_header,
            text="📋 Console Log",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.log_label.pack(side="left")

        self.log_clear_btn = ctk.CTkButton(
            self.log_header,
            text="Clear",
            width=60,
            height=25,
            font=ctk.CTkFont(size=11),
            command=self.clear_log,
            corner_radius=8
        )
        self.log_clear_btn.pack(side="right")

        self.log_textbox = ctk.CTkTextbox(
            self.log_frame,
            font=("Consolas", 11),
            wrap="word",
            corner_radius=8,
            height=150
        )
        self.log_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.log_textbox.configure(state="disabled")

        # Bind URL change to detect playlist
        self.url_var.trace_add("write", self.on_url_change)
        
        # Initial Auth State
        self.custom_cookie_file = None
        self.selected_playlist_items = None # Format: "1,2,5" (string) or list of indices
        self.download_history = [] # List of {"title": "...", "date": "..."}
        
        # Load Config
        self.load_config()

        # Row configuration - Main scrollable area expands (row 1), NOT log frame (row 8)
        self.grid_rowconfigure(1, weight=1) 
        self.grid_rowconfigure(8, weight=0) 

    def get_config_path(self):
        # Use APPDATA for reliable storage
        app_data = os.getenv('APPDATA')
        if not app_data:
            app_data = os.path.expanduser("~") # Fallback to user home
        
        config_dir = os.path.join(app_data, "YT-Downloader")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        return os.path.join(config_dir, "config.json")

    def load_config(self):
        self.config_file = self.get_config_path()
        self.log_message(f"[Config] Checking for config at: {self.config_file}")
        
        if os.path.exists(self.config_file):
            try:
                import json
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                self.log_message(f"[Config] Loaded data: {data}")
                    
                saved_source = data.get('cookie_source', 'None')
                saved_file = data.get('cookie_file', '')
                saved_folder = data.get('download_folder', '')
                
                # Restore Cookie Source
                if saved_source:
                    self.cookie_source_var.set(saved_source)
                    self.cookie_source_menu.set(saved_source)
                    
                    if saved_source == "Select File..." and saved_file and os.path.exists(saved_file):
                        self.custom_cookie_file = saved_file
                        basename = os.path.basename(saved_file)
                        self.browse_btn.pack(side="left", padx=5)
                        self.auth_path_label.pack(side="left", padx=5)
                        self.auth_path_label.configure(text=basename if len(basename) < 20 else basename[:17]+"...")
                
                # Restore Download Folder
                if saved_folder and os.path.exists(saved_folder):
                    self.download_folder = saved_folder
                    if hasattr(self, 'save_loc_path_label'):
                         self.update_save_loc_label()
                
                # Restore History
                self.download_history = data.get('download_history', [])
                
            except Exception as e:
                self.log_message(f"[Config] Error loading config: {e}")

    def save_config(self):
        try:
            if not hasattr(self, 'config_file'):
                self.config_file = self.get_config_path()

            import json
            data = {
                'cookie_source': self.cookie_source_var.get(),
                'cookie_file': self.custom_cookie_file if self.custom_cookie_file else '',
                'download_folder': self.download_folder if hasattr(self, 'download_folder') else '',
                'download_history': self.download_history
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f)
            self.log_message(f"[Config] Settings saved.") 
        except Exception as e:
            self.log_message(f"[Config] Error saving config: {e}")

    def add_to_history(self, title):
        """Add a video title to history"""
        import datetime
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Avoid duplicates at top
        if self.download_history and self.download_history[0]['title'] == title:
            return
            
        self.download_history.insert(0, {'title': title, 'date': now})
        
        # Limit to 10
        if len(self.download_history) > 10:
            self.download_history.pop()
            
        self.save_config()

    def show_history(self):
        """Show simple history dialog"""
        if not self.download_history:
            messagebox.showinfo("History", "No downloads yet.")
            return
            
        history_text = ""
        for item in self.download_history:
            # Truncate title
            title = item['title']
            if len(title) > 40: title = title[:37] + "..."
            history_text += f"[{item['date']}] {title}\n"
            
        messagebox.showinfo("Download History (Last 10)", history_text)

    def browse_download_folder(self):
        folder = filedialog.askdirectory(title="Select Download Folder")
        if folder:
            self.download_folder = folder
            self.update_save_loc_label()
            self.save_config()

    def update_save_loc_label(self):
        if hasattr(self, 'save_loc_path_label'):
             path = self.download_folder
             if len(path) > 40:
                 path = "..." + path[-37:]
             self.save_loc_path_label.configure(text=path)
    
    def toggle_theme(self):
        """Toggle between dark and light theme"""
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Dark":
            ctk.set_appearance_mode("Light")
            self.theme_btn.configure(text="☀️")
            self.theme_mode = "Light"
        else:
            ctk.set_appearance_mode("Dark")
            self.theme_btn.configure(text="🌙")
            self.theme_mode = "Dark"
    
    def clear_log(self):
        """Clear the log textbox"""
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
    
    def validate_youtube_url(self, url):
        """Validate if URL is a valid YouTube URL"""
        url = url.strip()
        if not url:
            return False
        youtube_patterns = [
            r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+',
            r'^[a-zA-Z0-9_-]{11}$'
        ]
        for pattern in youtube_patterns:
            if re.match(pattern, url):
                return True
        return False
    
    def fetch_video_info(self, url):
        """Fetch video information without downloading"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'noplaylist': True,  # Only get single video info
            }
            
            # Add cookies if available
            cookie_source = self.cookie_source_var.get()
            if cookie_source == "Select File..." and self.custom_cookie_file and os.path.exists(self.custom_cookie_file):
                ydl_opts['cookiefile'] = self.custom_cookie_file
            elif cookie_source in ["Chrome", "Firefox", "Edge", "Opera", "Brave"]:
                browser_map = {
                    "Chrome": "chrome", "Firefox": "firefox", "Edge": "edge",
                    "Opera": "opera", "Brave": "brave"
                }
                browser_key = browser_map.get(cookie_source)
                if browser_key:
                    ydl_opts['cookiesfrombrowser'] = (browser_key,)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    # Handle playlist URLs - get first video
                    if 'entries' in info and info['entries']:
                        info = info['entries'][0]
                    
                    title = info.get('title', 'Unknown')
                    channel = info.get('channel', info.get('uploader', 'Unknown'))
                    duration = info.get('duration', 0) or 0
                    
                    # Format duration
                    hours = duration // 3600
                    minutes = (duration % 3600) // 60
                    seconds = duration % 60
                    if hours > 0:
                        duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
                    else:
                        duration_str = f"{minutes}:{seconds:02d}"
                    
                    # Fetch thumbnail
                    thumbnail_data = None
                    if HAS_PIL and 'thumbnail' in info:
                        try:
                            thumb_url = info['thumbnail']
                            with urllib.request.urlopen(thumb_url) as u:
                                thumbnail_data = u.read()
                        except:
                            pass

                    # Extract Available Qualities
                    available_qualities = ["Best"]
                    if 'formats' in info:
                        formats = info['formats']
                        heights = set()
                        for f in formats:
                            # Filter for video streams
                            if f.get('vcodec') != 'none' and f.get('height'):
                                heights.add(f['height'])
                        
                        sorted_heights = sorted(list(heights), reverse=True)
                        available_qualities.extend([f"{h}p" for h in sorted_heights])

                    return {
                        'title': title,
                        'channel': channel,
                        'duration': duration_str,
                        'thumbnail_data': thumbnail_data,
                        'available_qualities': available_qualities
                    }
        except Exception as e:
            self.log_message(f"[Info] Could not fetch video info: {str(e)[:50]}")
            return None
        return None
    
    def sanitize_filename(self, name):
        """Sanitize filename to match yt-dlp behavior roughly"""
        # Replace forbidden chars
        name = re.sub(r'[\\/*?:"<>|]', '', name)
        # Remove leading/trailing spaces and dots
        return name.strip('. ')

    def display_video_info(self, info):
        """Display video information in the info card"""
        if not info:
            self.video_info_card.grid_forget()
            self.current_video_title = None
            return
        
        self.current_video_title = info['title']
        self.current_video_channel = info['channel']
        self.current_video_duration = info['duration']
        
        # Update labels
        title_text = info['title']
        if len(title_text) > 70:
            title_text = title_text[:67] + "..."
        self.video_title_label.configure(text=f"Title: {title_text}")
        self.video_meta_label.configure(text=f"Channel: {info['channel']} | Duration: {info['duration']}")
        
        # Update File Name Preview
        sanitized_title = self.sanitize_filename(info['title'])
        ext = "mp4" if self.mode_var.get() == "video" else "mp3"
        filename = f"{sanitized_title}.{ext}"
        if len(filename) > 60:
             filename = filename[:57] + "..."
        self.video_filename_label.configure(text=f"File: {filename}")
        
        # Update Quality Options if available
        if 'available_qualities' in info and info['available_qualities']:
            # Only update if in Video mode
            if self.mode_var.get() == "video":
                qualities = info['available_qualities']
                self.quality_menu.configure(values=qualities)
                self.quality_menu.set(qualities[0]) if qualities else None

        # Display Thumbnail
        if HAS_PIL and info.get('thumbnail_data'):
            try:
                img_data = info['thumbnail_data']
                pil_image = Image.open(BytesIO(img_data))
                # Resize (keep aspect ratio approx 16:9)
                ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(160, 90))
                
                # Create label if not exists
                if not hasattr(self, 'video_thumbnail_label'):
                    self.video_thumbnail_label = ctk.CTkLabel(self.video_info_container, text="")
                    self.video_thumbnail_label.pack(side="left", padx=(0, 15), anchor="n")
                    
                    # Repack others to right
                    # We need to restructure slightly: Container -> [Thumb] [TextFrame]
                    # But simpler: Just pack Thumb left, and pack other labels inside a new frame?
                    # Current structure: video_info_container -> title, meta, filename
                    
                    # HACK: If we haven't structured it, let's repack everything
                    self.video_title_label.pack_forget()
                    self.video_meta_label.pack_forget()
                    self.video_filename_label.pack_forget()
                    
                    self.info_text_frame = ctk.CTkFrame(self.video_info_container, fg_color="transparent")
                    self.info_text_frame.pack(side="left", fill="both", expand=True)
                    
                    self.video_title_label.pack(in_=self.info_text_frame, anchor="w", pady=(0, 5))
                    self.video_meta_label.pack(in_=self.info_text_frame, anchor="w")
                    self.video_filename_label.pack(in_=self.info_text_frame, anchor="w", pady=(2, 0))

                self.video_thumbnail_label.configure(image=ctk_image)
                self.video_thumbnail_label.image = ctk_image # Keep reference
                
            except Exception as e:
                self.log_message(f"[Error] Could not load thumbnail: {e}")
        
        # Show the card (adjust row based on playlist detection)
        
        # Show the card (adjust row based on playlist detection)
        url = self.url_var.get()
        if 'list=' in url and not 'start_radio=' in url:
            # Playlist detected - show after playlist frame
            self.video_info_card.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
            # Shift settings and other elements down
            self.settings_card.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
            self.action_frame.grid(row=6, column=0, padx=20, pady=20, sticky="ew")
            self.stats_frame.grid(row=7, column=0, padx=20, pady=10, sticky="ew")
            self.progress_card.grid(row=8, column=0, padx=20, pady=10, sticky="ew")
            self.log_frame.grid(row=9, column=0, padx=20, pady=(0, 20), sticky="ew")
        else:
            # Single video - show after options
            self.video_info_card.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
            # Shift settings and other elements down
            self.settings_card.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
            self.action_frame.grid(row=5, column=0, padx=20, pady=20, sticky="ew")
            self.stats_frame.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
            self.progress_card.grid(row=7, column=0, padx=20, pady=10, sticky="ew")
            self.log_frame.grid(row=8, column=0, padx=20, pady=(0, 20), sticky="ew") 

    def check_ffmpeg(self):
        # 1. Check PATH
        if shutil.which('ffmpeg'):
            self.log_message("[System] FFmpeg found in PATH.")
            self.ffmpeg_path = "ffmpeg"
            return

        # 2. Check Local Bin
        app_data = os.getenv('APPDATA')
        if not app_data: app_data = os.path.expanduser("~")
        self.local_bin_dir = os.path.join(app_data, "YT-Downloader", "bin")
        local_ffmpeg = os.path.join(self.local_bin_dir, "ffmpeg.exe")
        
        if os.path.exists(local_ffmpeg):
            self.log_message(f"[System] FFmpeg local override: {local_ffmpeg}")
            self.ffmpeg_path = local_ffmpeg
            return

        # 3. Not Found
        self.ffmpeg_path = None
        self.log_message("[WARNING] FFmpeg not found! Audio conversion will fail.")
        self.show_ffmpeg_warning()

    def show_ffmpeg_warning(self):
        self.ffmpeg_btn = ctk.CTkButton(
            self.header_frame,
            text="⚠️ Install FFmpeg",
            fg_color="orange",
            hover_color="darkorange",
            text_color="black",
            command=self.install_ffmpeg_thread,
            width=120
        )
        self.ffmpeg_btn.pack(side="right", padx=10)
        
    def install_ffmpeg_thread(self):
        if messagebox.askyesno("Install FFmpeg", "Download and install FFmpeg (~130MB)?\nThis is required for Audio conversion and High Quality video."):
            threading.Thread(target=self.install_ffmpeg, daemon=True).start()

    def install_ffmpeg(self):
        self.ffmpeg_btn.configure(state="disabled", text="Downloading...")
        try:
            url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
            if not os.path.exists(self.local_bin_dir):
                os.makedirs(self.local_bin_dir)
            
            zip_path = os.path.join(self.local_bin_dir, "ffmpeg.zip")
            
            # Progress reporting
            def report_hook(count, block_size, total_size):
                percent = int(count * block_size * 100 / total_size)
                if percent % 10 == 0:
                    self.ffmpeg_btn.configure(text=f"DL: {percent}%")
            
            self.log_message("[FFmpeg] Downloading binaries (gyan.dev)...")
            urllib.request.urlretrieve(url, zip_path, report_hook)
            
            self.log_message("[FFmpeg] Download complete. Extracting...")
            self.ffmpeg_btn.configure(text="Extracting...")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Search for ffmpeg.exe
                ffmpeg_src = None
                for file in zip_ref.namelist():
                    if file.endswith("bin/ffmpeg.exe"):
                        ffmpeg_src = file
                        break
                
                if ffmpeg_src:
                    source = zip_ref.open(ffmpeg_src)
                    target = open(os.path.join(self.local_bin_dir, "ffmpeg.exe"), "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)
                    self.log_message("[FFmpeg] Extracted ffmpeg.exe")
                else:
                    raise Exception("ffmpeg.exe not found in zip")
                    
            os.remove(zip_path)
            self.ffmpeg_path = os.path.join(self.local_bin_dir, "ffmpeg.exe")
            self.log_message("[FFmpeg] Installation Successful!")
            self.ffmpeg_btn.configure(text="✅ Installed", fg_color="green")
            self.after(3000, lambda: self.ffmpeg_btn.destroy())
            
        except Exception as e:
            self.log_message(f"[FFmpeg] Error: {e}")
            self.ffmpeg_btn.configure(text="⚠️ Retry", state="normal")

    def log_message(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def update_quality_options(self):
        mode = self.mode_var.get()
        if mode == "video":
            values = ["Best", "2160p", "1440p", "1080p", "720p", "480p", "360p"]
            self.quality_var.set("Best")
        else:
            values = ["320 kbps", "256 kbps", "192 kbps", "128 kbps", "96 kbps", "64 kbps"]
            self.quality_var.set("320 kbps")
        
        self.quality_menu.configure(values=values)
        
        # Update filename preview if video info is shown
        if self.current_video_title and hasattr(self, 'video_filename_label'):
            sanitized_title = self.sanitize_filename(self.current_video_title)
            ext = "mp4" if mode == "video" else "mp3"
            filename = f"{sanitized_title}.{ext}"
            if len(filename) > 60:
                 filename = filename[:57] + "..."
            self.video_filename_label.configure(text=f"File: {filename}")

    def on_url_change(self, *args):
        url = self.url_var.get()
        
        # Hide video info card initially
        self.video_info_card.grid_forget()
        self.current_video_title = None
        
        # Validate URL and fetch info in background
        if url and self.validate_youtube_url(url):
            # Fetch video info in a thread to avoid blocking UI
            def fetch_info():
                info = self.fetch_video_info(url)
                if info:
                    # Update UI in main thread
                    self.after(0, lambda: self.display_video_info(info))
            
            thread = threading.Thread(target=fetch_info, daemon=True)
            thread.start()
        
        if 'list=' in url and not 'start_radio=' in url:
            # Show playlist frame and shift other elements down
            self.playlist_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
            self.settings_card.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
            self.action_frame.grid(row=5, column=0, padx=20, pady=20, sticky="ew")
            self.stats_frame.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
            self.progress_card.grid(row=7, column=0, padx=20, pady=10, sticky="ew")
            self.log_frame.grid(row=8, column=0, padx=20, pady=(0, 20), sticky="nsew")
            
            # Check for Radio playlist
            if 'list=RD' in url:
                self.dl_playlist_btn.configure(state="disabled", text="Playlist (Radio - Not Downloadable)")
                self.playlist_option_var.set("video")
            else:
                self.dl_playlist_btn.configure(state="normal", text="Download Entire Playlist")
            
            
        else:
            self.playlist_frame.grid_forget()
            # Standard UI (no playlist)
            self.settings_card.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
            self.action_frame.grid(row=5, column=0, padx=20, pady=20, sticky="ew")
            self.stats_frame.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
            self.progress_card.grid(row=7, column=0, padx=20, pady=10, sticky="ew")
            self.log_frame.grid(row=8, column=0, padx=20, pady=(0, 20), sticky="nsew")
            

    def on_cookie_source_change(self, choice):
        try:
            self.log_message(f"[Debug] Cookie source changed to: {choice}")
            if choice == "Select File...":
                self.browse_btn.pack(side="left", padx=5)
                self.auth_path_label.pack(side="left", padx=5)
                if not self.auth_path_label.cget("text"):
                    self.browse_cookie_file()
            else:
                self.browse_btn.pack_forget()
                self.auth_path_label.pack_forget()
                self.custom_cookie_file = None
            
            self.save_config()
        except Exception as e:
            self.log_message(f"[CRITICAL ERROR] on_cookie_source_change failed: {e}")
            messagebox.showerror("Error", f"Failed to change source: {e}")

    def browse_cookie_file(self):
        try:
            filename = filedialog.askopenfilename(title="Select Cookies File", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
            if filename:
                self.custom_cookie_file = filename
                basename = os.path.basename(filename)
                self.auth_path_label.configure(text=basename if len(basename) < 20 else basename[:17]+"...")
                self.save_config()
            elif not self.custom_cookie_file:
                self.cookie_source_var.set("None")
                self.on_cookie_source_change("None")
        except Exception as e:
             self.log_message(f"[CRITICAL ERROR] browse_cookie_file failed: {e}")
             messagebox.showerror("Error", f"Failed to browse file: {e}")

    def open_download_folder(self):
        """Open the current download folder in file explorer"""
        path = self.download_folder
        if not os.path.exists(path):
            messagebox.showerror("Error", "Download folder does not exist!")
            return
            
        try:
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', path])
            else:
                subprocess.Popen(['xdg-open', path])
        except Exception as e:
            self.log_message(f"[Error] Could not open folder: {e}")

    def fetch_playlist_and_select(self):
        url = self.url_var.get().strip()
        if not url:
            return
            
        self.select_videos_btn.configure(text="Loading...", state="disabled")
        
        def fetch_task():
            try:
                ydl_opts = {
                    'quiet': True,
                    'extract_flat': True, # Fast check
                    'no_warnings': True,
                }
                
                # Check cookies
                cookie_source = self.cookie_source_var.get()
                if cookie_source == "Select File..." and self.custom_cookie_file and os.path.exists(self.custom_cookie_file):
                    ydl_opts['cookiefile'] = self.custom_cookie_file
                elif cookie_source in ["Chrome", "Firefox", "Edge", "Opera", "Brave"]:
                     browser_map = {"Chrome": "chrome", "Firefox": "firefox", "Edge": "edge", "Opera": "opera", "Brave": "brave"}
                     key = browser_map.get(cookie_source)
                     if key: ydl_opts['cookiesfrombrowser'] = (key,)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if 'entries' in info:
                        # It is a playlist
                        entries = list(info['entries'])
                        self.after(0, lambda: self.show_selection_dialog(entries))
                    else:
                        # Single video?
                        self.log_message("[Info] Not a playlist or no entries found.")
                        self.after(0, lambda: self.select_videos_btn.configure(text="Select Videos...", state="normal"))
                        
            except Exception as e:
                self.log_message(f"[Error] Failed to fetch playlist: {e}")
                self.after(0, lambda: self.select_videos_btn.configure(text="Select Videos...", state="normal"))

        threading.Thread(target=fetch_task, daemon=True).start()

    def show_selection_dialog(self, video_list):
        self.select_videos_btn.configure(text="Select Videos...", state="normal")
        
        dialog = PlaylistSelectionDialog(self, video_list, title="Select Videos to Download")
        # Center the dialog
        dialog.geometry(f"+{self.winfo_x()+50}+{self.winfo_y()+50}")
        dialog.grab_set() # Modal
        self.wait_window(dialog)
        
        if dialog.result is not None:
             self.selected_playlist_items = dialog.result
             count = len(self.selected_playlist_items)
             if count == 0:
                 self.select_videos_btn.configure(text="Nothing Selected", fg_color="gray")
                 self.selected_playlist_items = None
             elif count == len(video_list):
                 self.select_videos_btn.configure(text="All Selected", fg_color="green")
                 self.selected_playlist_items = None # Reset to download all
             else:
                 self.select_videos_btn.configure(text=f"Selected ({count})", fg_color="green")
                 self.playlist_option_var.set("playlist") # Force playlist mode
        else:
             # Cancelled
             pass

    def cancel_download(self):
        self.check_cancel = True
        self.log_message("[User] Cancel requested...")
        self.progress_status.configure(text="Cancelling...", text_color="red")
        
    def start_download_thread(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please provide a URL")
            return
            
        # Reset cancel flag
        self.check_cancel = False

        # Toggle Buttons
        self.download_btn.pack_forget()
        self.cancel_btn.pack(fill="x", pady=(0, 10))
        self.cancel_btn.configure(state="normal", text="⏹️ Cancel Download")

        # Disable Open Folder button while downloading
        if hasattr(self, 'open_folder_btn'):
            self.open_folder_btn.configure(state="disabled")
            
        self.progress_bar.set(0)
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        self.progress_percent.configure(text="0%")
        self.progress_status.configure(text="Starting download...", text_color="gray")
        # Reset stats
        self.stat_speed.configure(text="-")
        self.stat_eta.configure(text="-")
        self.stat_size.configure(text="-")
        
        thread = threading.Thread(target=self.run_download)
        thread.daemon = True
        thread.start()

    def run_download(self):
        try:
            url = self.url_var.get().strip()
            mode = self.mode_var.get()
            quality = self.quality_var.get()
            playlist_choice = self.playlist_option_var.get()
            cookie_source = self.cookie_source_var.get()
            
            # Determine if we are downloading playlist
            download_playlist = False
            if 'list=' in url and playlist_choice == 'playlist':
                download_playlist = True
            
            # Configure Options
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [self.progress_hook],
                'postprocessor_hooks': [self.post_processor_hook],
                'logger': MyLogger(self),
                'noplaylist': not download_playlist,
                'paths': {'home': self.download_folder} if hasattr(self, 'download_folder') and self.download_folder else {},
                # VPS Options
                'geo_bypass': True,
                'retries': 10,
                'sleep_interval': 1,
                'concurrent_fragment_downloads': 5, # Speed boost
                'http_chunk_size': 10485760, # 10MB chunks
            }
            
            # Add FFmpeg location if detected
            if hasattr(self, 'ffmpeg_path') and self.ffmpeg_path:
                 ydl_opts['ffmpeg_location'] = self.ffmpeg_path
            
            # Apply Playlist Selection
            if download_playlist and self.selected_playlist_items:
                 items_str = ",".join(map(str, self.selected_playlist_items))
                 ydl_opts['playlist_items'] = items_str
                 self.log_message(f"[Playlist] Downloading selected items: {items_str}")

            # Set Download Path
            if hasattr(self, 'download_folder') and self.download_folder and os.path.exists(self.download_folder):
                ydl_opts['paths'] = {'home': self.download_folder}
                self.log_message(f"[System] Saving to: {self.download_folder}")
            else:
                 self.log_message(f"[System] Saving to default folder")

            # === Authentication Logic ===
            if cookie_source == "Select File..." and self.custom_cookie_file:
                if os.path.exists(self.custom_cookie_file):
                    ydl_opts['cookiefile'] = self.custom_cookie_file
                    self.log_message(f"[Auth] Using Cookie File: {os.path.basename(self.custom_cookie_file)}")
                else:
                    self.log_message(f"[Warning] Selected cookie file not found!")
            
            elif cookie_source in ["Chrome", "Firefox", "Edge", "Opera", "Brave"]:
                browser_map = {
                    "Chrome": "chrome", "Firefox": "firefox", "Edge": "edge", 
                    "Opera": "opera", "Brave": "brave"
                }
                browser_key = browser_map.get(cookie_source)
                if browser_key:
                    ydl_opts['cookiesfrombrowser'] = (browser_key,)
                    self.log_message(f"[Auth] Extracting cookies from {cookie_source}...")
            
            elif os.path.exists(self.cookies_file) and cookie_source == "None":
                 pass

            # Video Mode
            if mode == "video":
                # Check for dynamic "Height + p" format (e.g. "540p", "480p")
                height_match = re.match(r'(\d+)p', quality)
                if height_match:
                    h = height_match.group(1)
                    format_str = f'bestvideo[height<={h}]+bestaudio/best[height<={h}]/best'
                elif quality == 'Best':
                    format_str = 'bestvideo+bestaudio/best'
                else:
                    # Fallback
                    format_str = 'bestvideo+bestaudio/best'
                
                ydl_opts.update({
                    'format': format_str,
                    'merge_output_format': 'mp4',
                    'outtmpl': '%(playlist_title)s/%(title)s.%(ext)s' if download_playlist else '%(title)s.%(ext)s',
                })
                title_msg = f": {self.current_video_title}" if self.current_video_title else ""
                self.log_message(f"[Start] Downloading Video ({quality}){title_msg}...")
                if self.current_video_title:
                    title_display = self.current_video_title[:50] + "..." if len(self.current_video_title) > 50 else self.current_video_title
                    self.progress_status.configure(text=f"Downloading: {title_display}", text_color="gray")

            # Audio Mode
            else:
                quality_val = quality.split()[0] # "320 kbps" -> "320"
                audio_map = {'320': '0', '256': '1', '192': '2', '128': '5', '96': '6', '64': '8'}
                
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'outtmpl': '%(playlist_title)s/%(title)s.%(ext)s' if download_playlist else '%(title)s.%(ext)s',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': audio_map.get(quality_val, '0'),
                    }],
                })
                title_msg = f": {self.current_video_title}" if self.current_video_title else ""
                self.log_message(f"[Start] Downloading Audio ({quality}){title_msg}...")
                if self.current_video_title:
                    self.progress_status.configure(text=f"Downloading: {self.current_video_title[:50]}...", text_color="gray")

            # Start Download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.log_message(f"Processing: {url}")
                ydl.download([url])
            
            title_msg = f" - {self.current_video_title}" if self.current_video_title else ""
            self.log_message(f"[Success] Download Completed!{title_msg}")
            self.progress_bar.set(1.0)
            self.progress_percent.configure(text="100%")
            
            completed_text = "Download completed!"
            if self.current_video_title:
                completed_text = f"Downloaded: {self.current_video_title[:40]}"
                if len(self.current_video_title) > 40:
                    completed_text += "..."
            self.progress_status.configure(text=completed_text, text_color="#2ECC71")
            
            # Enable Open Folder Button
            if hasattr(self, 'open_folder_btn'):
                self.open_folder_btn.configure(state="normal")
            
            # Add to History
            if self.current_video_title:
                self.add_to_history(self.current_video_title)
            
            messagebox.showinfo("Success", f"Download Completed Successfully!\n\n{self.current_video_title if self.current_video_title else 'File downloaded'}")

        except Exception as e:
            error_msg = str(e)
            self.log_message(f"[Error] {error_msg}")
            
            # Check for specific browser cookie error
            if "Could not copy" in error_msg and "cookie database" in error_msg:
                messagebox.showerror("Browser Error", 
                    f"Could not access {self.cookie_source_var.get()} cookies.\n\n"
                    "Please CLOSE your browser completely and try again.\n"
                    "(The database is locked while the browser is open)"
                )
            
            # Check for DPAPI/Decryption error
            elif "decrypt" in error_msg and "DPAPI" in error_msg:
                messagebox.showerror("Encryption Error", 
                    f"Could not decrypt {self.cookie_source_var.get()} cookies.\n\n"
                    "Chrome's encryption is blocking access.\n"
                    "Workarounds:\n"
                    "1. Try using Firefox (it works better)\n"
                    "2. Or select 'Select File...' and use a manually exported cookies.txt"
                )
            else:
                messagebox.showerror("Error", f"Download Failed:\n{error_msg}")
        
        finally:
            self.download_btn.pack(fill="x", pady=(0, 10))
            self.cancel_btn.pack_forget()
            
            self.download_btn.configure(state="normal", text="⬇️ Start Download")
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")

    def progress_hook(self, d):
        if self.check_cancel:
            raise Exception("Download Cancelled by User")

        if d['status'] == 'downloading':
            try:
                # Update progress bar
                if 'total_bytes' in d:
                    p = d['downloaded_bytes'] / d['total_bytes']
                    self.progress_bar.set(p)
                elif 'total_bytes_estimate' in d:
                    p = d['downloaded_bytes'] / d['total_bytes_estimate']
                    self.progress_bar.set(p)

                # Update stats labels
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                
                # Size formatting
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                if total_bytes:
                    size_mb = total_bytes / 1024 / 1024
                    size_str = f"{size_mb:.1f} MiB"
                else:
                    size_str = "N/A"

                # Update stat cards (new format)
                self.stat_speed.configure(text=speed if speed != 'N/A' else "-")
                self.stat_eta.configure(text=eta if eta != 'N/A' else "-")
                self.stat_size.configure(text=size_str if size_str != 'N/A' else "-")
                
                # Update progress percentage
                percent = int(p * 100)
                self.progress_percent.configure(text=f"{percent}%")
                
                # STATUS MESSAGE logic
                status_msg = "Downloading..."
                
                # Check for playlist info
                if 'playlist_index' in d and 'playlist_count' in d:
                    idx = d['playlist_index']
                    count = d['playlist_count']
                    status_msg = f"[Video {idx}/{count}] Downloading..."
                
                self.progress_status.configure(text=status_msg, text_color="gray")
                
                self.progress_bar.configure(mode="determinate")
            except Exception as e:
                # print(e)
                pass
        
        elif d['status'] == 'finished':
            self.log_message("Download finished. Processing/Converting...")
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
            self.stat_speed.configure(text="-")
            self.stat_eta.configure(text="Complete")
            self.progress_status.configure(text="Processing...", text_color="#F39C12")


    def post_processor_hook(self, d):
        if d['status'] == 'started':
            self.progress_status.configure(text="Processing / Converting...", text_color="#F39C12")
            # If we know the specific post-processor, we can be more specific
            # e.g. "Merging video and audio..." or "Converting to MP3..."
            
        elif d['status'] == 'finished':
             self.progress_status.configure(text="Finalizing...", text_color="#F39C12")

if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()
