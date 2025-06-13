# -----------------------------------------------------------------------------
# -- MEDIA CATCHER - A CUSTOMTKINTER-BASED YT-DLP FRONTEND                   --
# -- Author: Markus Aureus                                                   --
# -- Date: [Date of Last Edit]                                               --
# -- Description: A modern-looking desktop application for downloading media --
# --              using yt-dlp. Built with CustomTkinter for a themed UI.    --
# -----------------------------------------------------------------------------

# --- Standard Library Imports ---
import customtkinter as ctk
import subprocess
import os
import threading
import re
import json
from tkinter import filedialog
from urllib.parse import urlparse
import tkinter as tk # Used for PhotoImage to support PNG icons

# --- Theme and Configuration Loading ---

# Load themes from an external JSON file for easy customization.
try:
    with open("themes.json", "r") as f:
        THEMES = json.load(f)
except FileNotFoundError:
    print("Warning: themes.json not found. Using fallback themes.")
    THEMES = { # Hardcoded themes if the JSON file is missing
        "Dark": {"appearance": "Dark", "bg_color": "#1a1a2e", "button_color": "#A066D7", "hover_color": "#8847C0"},
        "YT Theme": {"appearance": "Dark", "bg_color": "#0f0f0f", "button_color": "#FF0000", "hover_color": "#CC0000"},
        "Matrix": {"appearance": "Dark", "bg_color": "#000000", "button_color": "#00FF00", "hover_color": "#00CC00"},
        "Ocean": {"appearance": "Dark", "bg_color": "#0d1117", "button_color": "#58a6ff", "hover_color": "#1f6feb"},
        "Sunset": {"appearance": "Dark", "bg_color": "#1a1625", "button_color": "#ff6b6b", "hover_color": "#ee5a6f"}
    }

# For consistency, rename the "Dark" theme to "Blueberry" if it exists.
if "Dark" in THEMES:
    THEMES["Blueberry"] = THEMES.pop("Dark")
if "Light" in THEMES:
    THEMES.pop("Light") # Remove the "Light" theme if present

# --- Global variables for process and state management ---
current_process = None
is_downloading = False
stop_requested = False

# --- Core Application Functions ---

def apply_theme(theme_name):
    """Applies the selected theme to the application window."""
    theme = THEMES.get(theme_name, THEMES["Blueberry"]) # Default to Blueberry if not found
    ctk.set_appearance_mode(theme["appearance"])
    bg_color = theme.get("bg_color")
    # Only set a custom background if it's not 'default'.
    if bg_color and bg_color.lower() != "default":
        app.configure(fg_color=bg_color)
    return theme

def update_widget_styles():
    """Updates the colors of all relevant widgets based on the current theme."""
    color = theme_settings["button_color"]
    hover = theme_settings["hover_color"]
    
    # Configure buttons with theme colors
    download_button.configure(fg_color=color, hover_color=hover)
    folder_button.configure(fg_color=color, hover_color=hover)
    
    # Special colors for Stop and Clear buttons
    stop_button.configure(fg_color="#dc3545", hover_color="#c82333")
    clear_button.configure(text_color="white")

    # Configure all ComboBox (dropdown) widgets
    for combo in [combo_mode, combo_audio_format, combo_quality_audio, 
                  combo_quality_video, combo_sub_lang, combo_theme]:
        combo.configure(button_color=color)

def on_theme_change(choice):
    """Callback function for when the user selects a new theme."""
    global theme_settings
    theme_settings = apply_theme(choice)
    update_widget_styles()

# --- GUI Initialization ---
app = ctk.CTk()
app.geometry("700x700")
app.resizable(False, False)
app.title("Media Catcher")

# Set application icon, handling potential errors.
try:
    icon_path = "media-catcher.png"
    if os.path.exists(icon_path):
        icon = tk.PhotoImage(file=icon_path)
        app.iconphoto(True, icon)
    else:
        print("Warning: Icon file 'media-catcher.png' not found.")
except Exception as e:
    print(f"Warning: Could not set application icon. Error: {e}")

# Apply the default theme on startup.
theme_settings = apply_theme("Blueberry")
output_dir = os.path.expanduser("~/Downloads")

# --- Helper Functions (URL Parsing and UI Logic) ---

def is_youtube_url(url):
    """Checks if the URL belongs to YouTube."""
    hostname = urlparse(url).hostname or ""
    return any(domain in hostname for domain in ["youtube.com", "youtu.be"])

def is_playlist_url(url):
    """Checks if the URL is for a full playlist, not a video within one."""
    return "playlist?list=" in url and "watch?v=" not in url

def is_video_from_playlist(url):
    """Checks if the URL is for a video that is part of a playlist."""
    return "watch?v=" in url and "&list=" in url

def get_video_index_from_url(url):
    """Extracts the 'index' parameter from a YouTube video URL."""
    match = re.search(r'[&?]index=(\d+)', url)
    return int(match.group(1)) if match else 1

def toggle_quality_options(choice):
    """Shows or hides UI elements based on whether Audio or Video mode is selected."""
    if choice == "Audio":
        combo_audio_format.pack(pady=5)
        update_audio_quality_options(combo_audio_format.get())
        combo_quality_audio.pack(pady=5)
        # Hide video-specific options
        for widget in [combo_quality_video, checkbox_subtitles, combo_sub_lang]:
            widget.pack_forget()
    else: # Video mode
        combo_quality_video.pack(pady=5)
        checkbox_subtitles.pack(pady=5)
        combo_sub_lang.pack(pady=5)
        update_video_quality_state()
        # Hide audio-specific options
        for widget in [combo_audio_format, combo_quality_audio]:
            widget.pack_forget()

def update_video_quality_state():
    """Disables the quality dropdown if subtitles are checked, as yt-dlp needs to pick the best streams."""
    is_subs_checked = checkbox_subtitles.get()
    combo_quality_video.configure(state="disabled" if is_subs_checked else "normal")
    if is_subs_checked:
        combo_quality_video.set("Best available")

def update_audio_quality_options(format_choice):
    """Disables the quality dropdown for lossless formats like WAV."""
    if format_choice == "wav":
        combo_quality_audio.configure(values=["N/A (lossless)"], state="disabled")
        combo_quality_audio.set("N/A (lossless)")
    else:
        combo_quality_audio.configure(values=["320K", "192K", "128K", "64K"], state="normal")
        combo_quality_audio.set("192K")

def choose_folder():
    """Opens a system dialog to choose the output directory."""
    global output_dir
    folder = filedialog.askdirectory(initialdir=output_dir)
    if folder:
        output_dir = folder
        label_output.configure(text=f"Saving to: {output_dir}")

def get_playlist_count(playlist_url):
    """Runs a quick yt-dlp command to get the number of items in a playlist."""
    try:
        # Using '--flat-playlist' is fast as it avoids fetching full metadata.
        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--print", "%(title)s", playlist_url],
            capture_output=True, text=True, check=True
        )
        return len([line for line in result.stdout.strip().split("\n") if line.strip()])
    except Exception as e:
        print(f"Error getting playlist count: {e}")
        return 0

def stop_download():
    """Stops the current download by terminating the yt-dlp subprocess."""
    global current_process, stop_requested
    stop_requested = True
    
    if current_process and current_process.poll() is None:
        try:
            current_process.terminate() # Send SIGTERM
            # Force kill after a short delay if it hasn't terminated.
            threading.Timer(0.5, lambda: current_process.kill() if current_process.poll() is None else None).start()
            status_label.configure(text="⏹️ Download stopped by user", text_color="orange")
        except Exception as e:
            print(f"Error stopping process: {e}")
    
    # Reset UI state
    download_button.configure(state="normal")
    stop_button.configure(state="disabled")

# --- Main Download Logic ---

def run_download():
    """
    The core download function. This is run in a separate thread to keep the UI responsive.
    It constructs and executes the yt-dlp command based on user selections.
    """
    global current_process, is_downloading, stop_requested
    stop_requested = False
    
    urls_text = entry_url.get("1.0", "end").strip()
    
    # Validate user input
    if not urls_text or is_placeholder_active:
        status_label.configure(text="❌ Please enter a valid URL", text_color="red")
        return
    
    user_urls = [line.strip() for line in urls_text.splitlines() if line.strip()]
    if not user_urls:
        status_label.configure(text="❌ Please enter a valid URL", text_color="red")
        return
    
    # Update UI to downloading state
    is_downloading = True
    download_button.configure(state="disabled")
    stop_button.configure(state="normal")
    
    # Gather settings from UI
    mode = combo_mode.get()
    download_playlist = checkbox_playlist.get()
    download_subs = checkbox_subtitles.get()
    subtitle_lang = combo_sub_lang.get().split()[0]

    # --- Pre-computation of URLs and video counts ---
    all_urls, download_info = [], []
    for url in user_urls:
        if is_playlist_url(url) and download_playlist:
            count = get_playlist_count(url)
            all_urls.append(url)
            download_info.append({"count": count, "type": "full_playlist"})
        elif is_video_from_playlist(url) and download_playlist:
            start_index = get_video_index_from_url(url)
            total_count = get_playlist_count(url)
            remaining = max(1, total_count - start_index + 1)
            status_label.configure(text=f"📋 Downloading playlist from video #{start_index}", text_color="cyan")
            all_urls.append(url)
            download_info.append({"count": remaining, "type": "partial_playlist", "start_index": start_index})
        else: # Handle single videos or un-checked playlists
            clean_url = url.split('&list=')[0] if is_video_from_playlist(url) else url
            all_urls.append(clean_url)
            download_info.append({"count": 1, "type": "single"})

    total_videos = sum(info["count"] for info in download_info)
    videos_completed = 0
    
    # --- Main Download Loop ---
    for url, info in zip(all_urls, download_info):
        if stop_requested: break
        
        status_label.configure(text=f"⬇️ Preparing ({videos_completed+1}/{total_videos})...", text_color="white")
        app.update_idletasks() # Force UI update

        # --- Construct yt-dlp command ---
        cmd = ["yt-dlp", url, "-o", os.path.join(output_dir, "%(title)s.%(ext)s"), "--newline"]
        
        # Add playlist-specific arguments
        if info["type"] == "partial_playlist":
            cmd.extend(["--playlist-start", str(info["start_index"])])
        elif info["type"] == "single" and is_playlist_url(url):
            cmd.extend(["--playlist-items", "1"]) # Download only first item

        if mode == "Audio":
            audio_format = combo_audio_format.get()
            cmd.extend(["-x", "--audio-format", audio_format, "--force-overwrites"])
            if audio_format in ["mp3", "aac"]:
                quality_map = {"320K": "0", "192K": "2", "128K": "5", "64K": "9"}
                cmd.extend(["--audio-quality", quality_map.get(combo_quality_audio.get(), "2")])
        else: # Video Mode
            cmd.extend(["--merge-output-format", "mp4"])
            if is_youtube_url(url):
                if download_subs:
                    cmd.extend(["-f", "bestvideo+bestaudio", "--write-auto-sub", "--sub-lang", subtitle_lang, "--convert-subs", "srt"])
                else:
                    quality = combo_quality_video.get()
                    format_code = f"{quality.split()[0]}+140" if quality != "Best available" else "bestvideo+bestaudio"
                    cmd.extend(["-f", format_code])
            else: # For other sites, 'best' is more reliable
                cmd.append("-f best")

        # --- Execute and Monitor Process ---
        try:
            progress_bar.set(0)
            progress_label.configure(text="Progress: 0%")
            current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
            
            for line in current_process.stdout:
                if stop_requested: break
                
                match = re.search(r'\[download\]\s+([\d.]+)%', line)
                if match:
                    percent = float(match.group(1))
                    progress_bar.set(percent / 100)
                    progress_label.configure(text=f"Progress: {percent:.1f}%")
                    status_label.configure(text=f"⬇️ Downloading ({videos_completed+1}/{total_videos})...")
                    app.update_idletasks()
            
            stdout, stderr = current_process.communicate()
            if stop_requested: break

            if current_process.returncode == 0:
                videos_completed += info["count"]
                status_label.configure(text=f"✅ Done ({videos_completed}/{total_videos})", text_color="green")
            else:
                status_label.configure(text=f"❌ Error: {stderr.strip()[:100]}...", text_color="red")
        
        except Exception as e:
            status_label.configure(text=f"❌ Exception: {str(e)}", text_color="red")
    
    # --- Final State Reset ---
    if not stop_requested:
        status_label.configure(text="🎉 All downloads finished!", text_color="green")
    
    is_downloading = False
    download_button.configure(state="normal")
    stop_button.configure(state="disabled")
    current_process = None

# === GUI Element Creation and Layout ===

title_label = ctk.CTkLabel(app, text="Media Catcher", font=ctk.CTkFont(size=20, weight="bold"))
title_label.pack(pady=(10, 5))

entry_url = ctk.CTkTextbox(app, width=500, height=100)
entry_url.pack(pady=(10, 10))

# --- Placeholder Text Logic for URL Entry ---
placeholder_text = "🔗 Enter URL(s), one per line..."
is_placeholder_active = True

def on_entry_click(event):
    if is_placeholder_active:
        entry_url.delete("1.0", "end")
        entry_url.configure(text_color="white") # Or theme-appropriate text color
        entry_url.focus_set()

def on_focus_out(event):
    global is_placeholder_active
    if not entry_url.get("1.0", "end-1c").strip():
        entry_url.delete("1.0", "end")
        entry_url.insert("1.0", placeholder_text)
        entry_url.configure(text_color="gray")
        is_placeholder_active = True
    else:
        is_placeholder_active = False

# Initially set the placeholder
entry_url.insert("1.0", placeholder_text)
entry_url.configure(text_color="gray")
entry_url.bind("<FocusIn>", on_entry_click)
entry_url.bind("<FocusOut>", on_focus_out)

# --- Create and Pack UI Widgets ---

combo_mode = ctk.CTkComboBox(app, values=["Audio", "Video"], command=toggle_quality_options)
combo_mode.set("Audio")
combo_mode.pack(pady=5)

checkbox_playlist = ctk.CTkCheckBox(app, text="Download entire playlist")
checkbox_playlist.pack(pady=5)

folder_button = ctk.CTkButton(app, text="Select Output Folder", command=choose_folder)
folder_button.pack(pady=5)

label_output = ctk.CTkLabel(app, text=f"Saving to: {output_dir}")
label_output.pack(pady=5)

# --- Button Frame for Download/Stop ---
button_frame = ctk.CTkFrame(app, fg_color="transparent")
button_frame.pack(pady=5)

download_button = ctk.CTkButton(button_frame, text="Download", command=lambda: threading.Thread(target=run_download).start())
download_button.pack(side="left", padx=5)

stop_button = ctk.CTkButton(button_frame, text="Stop", command=stop_download, state="disabled")
stop_button.pack(side="left", padx=5)

# Clear button and its function
def clear_and_reset():
    entry_url.delete("1.0", "end")
    on_focus_out(None) # Reset placeholder if empty
clear_button = ctk.CTkButton(app, text="Clear", command=clear_and_reset, fg_color="#444", hover_color="#666")
clear_button.pack(pady=5)

# --- Dynamic Option Widgets (initially packed/unpacked by toggle_quality_options) ---
combo_audio_format = ctk.CTkComboBox(app, values=["mp3", "wav", "aac"], command=update_audio_quality_options)
combo_quality_audio = ctk.CTkComboBox(app, values=["320K", "192K", "128K", "64K"])
combo_quality_video = ctk.CTkComboBox(app, values=["Best available", "137 (1080p)", "136 (720p)", "135 (480p)", "134 (360p)"])
checkbox_subtitles = ctk.CTkCheckBox(app, text="Download subtitles", command=update_video_quality_state)
combo_sub_lang = ctk.CTkComboBox(app, values=["en (English)", "sk (Slovak)", "cs (Czech)", "de (German)", "fr (French)", "es (Spanish)"])

# --- Theme Selector and Progress Indicators ---
combo_theme = ctk.CTkComboBox(app, values=list(THEMES.keys()), command=on_theme_change)
combo_theme.set("Blueberry")
combo_theme.pack(pady=10)

progress_bar = ctk.CTkProgressBar(app, width=400)
progress_bar.set(0)
progress_bar.pack(pady=5)

progress_label = ctk.CTkLabel(app, text="Progress: 0%")
progress_label.pack()

status_label = ctk.CTkLabel(app, text="Ready")
status_label.pack(pady=5)

# === Final Initialization and Main Loop ---
toggle_quality_options("Audio") # Set initial state for audio options
update_widget_styles()          # Apply initial theme styles to all widgets

app.mainloop() # Start the application event loop
