import customtkinter as ctk
import subprocess
import os
import threading
import re
from tkinter import filedialog
import json
from urllib.parse import urlparse
import tkinter as tk

# === Load Themes ===
with open("themes.json", "r") as f:
    THEMES = json.load(f)
    THEMES["Blueberry"] = THEMES.pop("Dark", THEMES.get("Dark"))  # Rename "Dark" to "Blueberry"
    THEMES.pop("Light", None)  # Remove Light theme if exists

# === Global variables for process control ===
current_process = None
is_downloading = False
stop_requested = False

def apply_theme(theme_name):
    theme = THEMES.get(theme_name, THEMES["Blueberry"])
    ctk.set_appearance_mode(theme["appearance"])
    bg = theme.get("bg_color")
    if bg and bg.lower() != "default":
        app.configure(fg_color=bg)
    return theme

def update_widget_styles():
    color = theme_settings["button_color"]
    hover = theme_settings["hover_color"]
    theme_name = combo_theme.get()

    text_color_btn = "black" if theme_name in ["Matrix", "YT Theme"] else "white"
    text_color_entry = "white"  # Force white text for dropdowns in Blueberry theme

    download_button.configure(fg_color=color, hover_color=hover, text_color=text_color_btn)
    folder_button.configure(fg_color=color, hover_color=hover, text_color=text_color_btn)
    clear_button.configure(text_color="white")
    stop_button.configure(fg_color="#dc3545", hover_color="#c82333", text_color="white")  # Red color for stop button

    combo_mode.configure(button_color=color, text_color=text_color_entry)
    combo_audio_format.configure(button_color=color, text_color=text_color_entry)
    combo_quality_audio.configure(button_color=color, text_color=text_color_entry)
    combo_quality_video.configure(button_color=color, text_color=text_color_entry)
    combo_sub_lang.configure(button_color=color, text_color=text_color_entry)
    combo_theme.configure(button_color=color, text_color=text_color_entry)

def on_theme_change(choice):
    global theme_settings
    theme_settings = apply_theme(choice)
    update_widget_styles()

# === GUI Initialization ===
app = ctk.CTk()
app.geometry("700x700")
app.resizable(False, False)
app.title("Media Catcher")

# === Set Application Icon ===
# Icon paths for different use cases
icon_path = "media-catcher.png"  # Main icon file
icon_path_absolute = os.path.abspath(icon_path)

# Set window icon for the application
if os.path.exists(icon_path):
    try:
        # Using tkinter PhotoImage for PNG support
        icon = tk.PhotoImage(file=icon_path)
        app.iconphoto(True, icon)
    except Exception as e:
        print(f"Warning: Could not set application icon from {icon_path}: {e}")
else:
    print(f"Warning: Icon file not found at {icon_path}")

# === Apply Default Theme ===
selected_theme = "Blueberry"
theme_settings = apply_theme(selected_theme)

output_dir = os.path.expanduser("~/Downloads")

# === Helper Functions ===
def is_youtube_url(url):
    hostname = urlparse(url).hostname or ""
    return any(domain in hostname for domain in ["youtube.com", "youtu.be"])

def is_playlist_url(url):
    """Check if URL is a playlist URL (not individual video from playlist)"""
    # True playlist URL: https://www.youtube.com/playlist?list=...
    # Individual video from playlist: https://www.youtube.com/watch?v=...&list=...
    return "playlist?list=" in url and "watch?v=" not in url

def is_video_from_playlist(url):
    """Check if URL is individual video from playlist"""
    return "watch?v=" in url and "&list=" in url

def get_video_index_from_url(url):
    """Extract video index from playlist URL"""
    import re
    match = re.search(r'[&?]index=(\d+)', url)
    return int(match.group(1)) if match else 1

def toggle_quality_options(choice):
    if choice == "Audio":
        combo_audio_format.pack(pady=5)
        update_audio_quality_options(combo_audio_format.get())
        combo_quality_audio.pack(pady=5)
        combo_quality_video.pack_forget()
        checkbox_subtitles.pack_forget()
        combo_sub_lang.pack_forget()
    else:
        combo_audio_format.pack_forget()
        combo_quality_audio.pack_forget()
        combo_quality_video.pack(pady=5)
        checkbox_subtitles.pack(pady=5)
        combo_sub_lang.pack(pady=5)
        update_video_quality_state()

def update_video_quality_state():
    if checkbox_subtitles.get():
        combo_quality_video.set("Best available")
        combo_quality_video.configure(state="disabled")
    else:
        combo_quality_video.configure(state="normal")

def update_audio_quality_options(format_choice):
    if format_choice in ["mp3", "aac"]:
        combo_quality_audio.configure(values=["320K", "192K", "128K", "64K"])
        combo_quality_audio.set("192K")
        combo_quality_audio.configure(state="normal")
    elif format_choice == "wav":
        combo_quality_audio.set("N/A (lossless)")
        combo_quality_audio.configure(values=["N/A (lossless)"])
        combo_quality_audio.configure(state="disabled")

def choose_folder():
    global output_dir
    folder = filedialog.askdirectory()
    if folder:
        output_dir = folder
        label_output.configure(text=f"Saving to: {output_dir}")

def get_playlist_urls(playlist_url):
    try:
        result = subprocess.run([
            "yt-dlp", "--flat-playlist", "--print", "%(url)s", playlist_url
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        raw_urls = result.stdout.strip().split("\n")
        return [url.strip() for url in raw_urls if url.strip()]
    except Exception as e:
        print(f"Playlist error: {e}")
        return []

def get_playlist_count(playlist_url):
    """Get number of videos in playlist"""
    try:
        result = subprocess.run([
            "yt-dlp", "--flat-playlist", "--print", "%(title)s", playlist_url
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        videos = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
        return len(videos)
    except Exception as e:
        print(f"Playlist count error: {e}")
        return 0

def stop_download():
    """Stop the current download process"""
    global current_process, stop_requested
    stop_requested = True
    
    if current_process and current_process.poll() is None:
        try:
            # Terminate the process
            current_process.terminate()
            # Wait a moment for graceful termination
            threading.Timer(0.5, lambda: current_process.kill() if current_process.poll() is None else None).start()
            
            status_label.configure(text="⏹️ Download stopped by user", text_color="orange")
            progress_bar.set(0)
            progress_label.configure(text="Progress: 0%")
        except Exception as e:
            print(f"Error stopping process: {e}")
    
    # Update button states
    download_button.configure(state="normal")
    stop_button.configure(state="disabled")

def run_download():
    global current_process, is_downloading, stop_requested
    
    # Reset stop flag
    stop_requested = False
    
    urls_text = entry_url.get("1.0", "end").strip()
    
    # OPRAVA: Ignoruj placeholder text
    if urls_text == "🔗 Enter URL(s) or playlist link here..." or not urls_text:
        status_label.configure(text="❌ Please enter a valid URL", text_color="red")
        return
    
    user_urls = [line.strip() for line in urls_text.splitlines() if line.strip()]
    
    # Skontroluj či sú zadané URL
    if not user_urls:
        status_label.configure(text="❌ Please enter a valid URL", text_color="red")
        return
    
    # Update button states
    is_downloading = True
    download_button.configure(state="disabled")
    stop_button.configure(state="normal")
    
    mode = combo_mode.get()
    download_playlist = checkbox_playlist.get()
    download_subs = checkbox_subtitles.get()
    subtitle_lang = combo_sub_lang.get().split()[0]

    all_urls = []
    download_info = []  # Informácie o sťahovaní pre každú URL
    
    # OPRAVA: Spracovanie URL podľa nastavenia checkboxu
    for url in user_urls:
        if is_playlist_url(url) and download_playlist:
            # Ak je URL celého playlistu a checkbox je označený, stiahni celý playlist
            playlist_count = get_playlist_count(url)
            if playlist_count > 0:
                all_urls.append(url)
                download_info.append({"url": url, "count": playlist_count, "type": "full_playlist"})
            else:
                # Ak sa nepodarilo získať playlist, pridaj originálnu URL
                all_urls.append(url)
                download_info.append({"url": url, "count": 1, "type": "single"})
        elif is_playlist_url(url) and not download_playlist:
            # Ak je URL celého playlistu ale checkbox nie je označený, stiahni len prvé video
            status_label.configure(text="⚠️ Playlist detected - downloading first video only", text_color="orange")
            app.update()
            all_urls.append(url)
            download_info.append({"url": url, "count": 1, "type": "single"})
        elif is_video_from_playlist(url) and download_playlist:
            # Ak je URL konkrétneho videa z playlistu a checkbox je označený,
            # stiahni od tohto videa až po koniec playlistu
            video_index = get_video_index_from_url(url)
            total_count = get_playlist_count(url)
            remaining_count = max(1, total_count - video_index + 1)
            status_label.configure(text=f"📋 Downloading playlist from video #{video_index} to end", text_color="cyan")
            app.update()
            all_urls.append(url)
            download_info.append({"url": url, "count": remaining_count, "type": "partial_playlist", "start_index": video_index})
        elif is_video_from_playlist(url) and not download_playlist:
            # Ak je URL konkrétneho videa z playlistu ale checkbox nie je označený,
            # stiahni len toto video
            clean_url = url.split('&list=')[0] if '&list=' in url else url
            all_urls.append(clean_url)
            download_info.append({"url": clean_url, "count": 1, "type": "single"})
        else:
            # Pre jednotlivé videá alebo iné URL
            all_urls.append(url)
            download_info.append({"url": url, "count": 1, "type": "single"})

    # Spočítaj celkový počet videí na stiahnutie
    total_videos = sum(info["count"] for info in download_info)

    current_video = 0
    
    for index, (url, info) in enumerate(zip(all_urls, download_info), start=1):
        # Check if stop was requested
        if stop_requested:
            break
            
        if info["type"] in ["full_playlist", "partial_playlist"]:
            status_label.configure(text=f"⬇️ Starting playlist download...", text_color="white")
        else:
            current_video += 1
            status_label.configure(text=f"⬇️ Downloading ({current_video}/{total_videos})...", text_color="white")
        app.update()

        output_path = os.path.join(output_dir, "%(title)s.%(ext)s")
        cmd = ["yt-dlp", url, "-o", output_path, "--newline"]

        # OPRAVA: Pridanie parametra pre obmedzenie playlistu
        if is_playlist_url(url) and not download_playlist:
            # Pre skutočné playlist URL - stiahni len prvé video
            cmd.append("--playlist-items")
            cmd.append("1")
        elif is_video_from_playlist(url) and download_playlist:
            # Pre video z playlistu s označeným checkboxom - stiahni od tohto videa po koniec
            video_index = get_video_index_from_url(url)
            cmd.append("--playlist-start")
            cmd.append(str(video_index))
            # Ponechaj playlist parametre v URL

        if mode == "Audio":
            audio_format = combo_audio_format.get()
            cmd += ["-x", "--audio-format", audio_format, "--force-overwrites"]
            if audio_format in ["mp3", "aac"]:
                quality = combo_quality_audio.get()
                quality_map = {"320K": "0", "192K": "2", "128K": "5", "64K": "9"}
                cmd += ["--audio-quality", quality_map.get(quality, "2")]
        else:
            cmd += ["--merge-output-format", "mp4"]
            if is_youtube_url(url):
                if download_subs:
                    cmd += ["-f", "bestvideo+bestaudio", "--write-auto-sub", "--sub-lang", subtitle_lang, "--convert-subs", "srt", "--sub-format", "srt"]
                else:
                    quality_id = combo_quality_video.get()
                    if quality_id == "Best available":
                        cmd += ["-f", "bestvideo+bestaudio"]
                    else:
                        video_code = quality_id.split()[0]
                        cmd += ["-f", f"{video_code}+140"]
            else:
                cmd += ["-f", "best"]

        try:
            progress_bar.set(0)
            progress_label.configure(text="Progress: 0%")
            app.update()

            current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            current_playlist_video = 0
            
            for line in current_process.stdout:
                # Check if stop was requested
                if stop_requested:
                    break
                    
                # OPRAVA: Počítaj dokončené videá namiesto začiatku
                if info["type"] in ["full_playlist", "partial_playlist"]:
                    if 'has already been downloaded' in line or '[download] 100%' in line:
                        current_playlist_video += 1
                        overall_current = current_video + current_playlist_video
                        status_label.configure(text=f"⬇️ Completed video {overall_current}/{total_videos}", text_color="white")
                        app.update()
                
                # Progress bar update
                match = re.search(r'\[download\]\s+(\d{1,3}\.?\d*)%', line)
                if match:
                    try:
                        percent = float(match.group(1))
                        progress_bar.set(percent / 100)
                        progress_label.configure(text=f"Progress: {percent:.1f}%")
                        app.update()
                    except ValueError:
                        pass
                    
            stdout, stderr = current_process.communicate()
            
            if stop_requested:
                break
                
            if current_process.returncode == 0:
                if info["type"] in ["full_playlist", "partial_playlist"]:
                    # OPRAVA: Aktualizuj current_video o skutočný počet stiahnutých videí
                    current_video += info["count"]
                    status_label.configure(text=f"✅ Playlist completed ({current_video}/{total_videos})", text_color="green")
                else:
                    status_label.configure(text=f"✅ Done ({current_video}/{total_videos})", text_color="green")
            else:
                error_message = stderr.strip() or "Unknown error"
                if info["type"] in ["full_playlist", "partial_playlist"]:
                    current_video += info["count"]
                status_label.configure(text=f"❌ Error: {error_message[:100]}...", text_color="red")
        except Exception as e:
            if info["type"] in ["full_playlist", "partial_playlist"]:
                current_video += info["count"]
            status_label.configure(text=f"❌ Exception: {str(e)}", text_color="red")
    
    # Reset states after download completes
    is_downloading = False
    download_button.configure(state="normal")
    stop_button.configure(state="disabled")
    current_process = None

# === GUI Setup ===
title_label = ctk.CTkLabel(app, text="", font=ctk.CTkFont(size=20, weight="bold"))
title_label.pack(pady=(10, 5))

entry_url = ctk.CTkTextbox(app, width=500, height=100)
entry_url.pack(pady=(10, 10))

# Placeholder handling
placeholder_text = "🔗 Enter URL(s) or playlist link here..."
is_placeholder_active = True

def show_placeholder():
    global is_placeholder_active
    if is_placeholder_active:
        entry_url.delete("1.0", "end")
        entry_url.insert("1.0", placeholder_text)
        entry_url.configure(text_color="gray")

def hide_placeholder():
    global is_placeholder_active
    if is_placeholder_active:
        entry_url.delete("1.0", "end")
        entry_url.configure(text_color="white")
        is_placeholder_active = False

def on_entry_click(event):
    global is_placeholder_active
    if is_placeholder_active:
        hide_placeholder()

def on_focus_out(event):
    global is_placeholder_active
    current_text = entry_url.get("1.0", "end-1c").strip()
    if not current_text:
        is_placeholder_active = True
        show_placeholder()

def on_key_press(event):
    global is_placeholder_active
    if is_placeholder_active:
        hide_placeholder()

# Initialize with placeholder
show_placeholder()

# Bind events
entry_url.bind("<Button-1>", on_entry_click)
entry_url.bind("<FocusOut>", on_focus_out)
entry_url.bind("<Key>", on_key_press)
entry_url.bind("<Control-a>", lambda event: (entry_url.tag_add("sel", "1.0", "end"), "break"))

combo_mode = ctk.CTkComboBox(app, values=["Audio", "Video"], command=toggle_quality_options)
combo_mode.set("Audio")
combo_mode.pack(pady=5)

checkbox_playlist = ctk.CTkCheckBox(app, text="Download entire playlist")
checkbox_playlist.pack(pady=5)

folder_button = ctk.CTkButton(app, text="Select Output Folder", command=choose_folder)
folder_button.pack(pady=5)

label_output = ctk.CTkLabel(app, text=f"Saving to: {output_dir}")
label_output.pack(pady=5)

# Create a frame for Download and Stop buttons
button_frame = ctk.CTkFrame(app, fg_color="transparent")
button_frame.pack(pady=5)

download_button = ctk.CTkButton(button_frame, text="Download", command=lambda: threading.Thread(target=run_download).start())
download_button.pack(side="left", padx=5)

stop_button = ctk.CTkButton(button_frame, text="Stop", command=stop_download, state="disabled",
                           fg_color="#dc3545", hover_color="#c82333")
stop_button.pack(side="left", padx=5)

def clear_and_reset():
    global is_placeholder_active
    entry_url.delete("1.0", "end")
    is_placeholder_active = True
    show_placeholder()

clear_button = ctk.CTkButton(app, text="Clear", command=clear_and_reset, fg_color="#444", hover_color="#666")
clear_button.pack(pady=5)

combo_audio_format = ctk.CTkComboBox(app, values=["mp3", "wav", "aac"], command=update_audio_quality_options)
combo_quality_audio = ctk.CTkComboBox(app, values=["320K", "192K", "128K", "64K"])

combo_quality_video = ctk.CTkComboBox(app, values=["Best available", "137 (1080p)", "136 (720p)", "135 (480p)", "134 (360p)", "133 (240p)"])
combo_quality_video.set("Best available")

checkbox_subtitles = ctk.CTkCheckBox(app, text="Download subtitles", command=update_video_quality_state)
combo_sub_lang = ctk.CTkComboBox(app, values=["en (English)", "sk (Slovak)", "cs (Czech)", "de (German)", "fr (French)", "es (Spanish)", "ru (Russian)", "ja (Japanese)", "zh (Chinese)"])

combo_theme = ctk.CTkComboBox(app, values=list(THEMES.keys()), command=on_theme_change)
combo_theme.set(selected_theme)
combo_theme.pack(pady=10)

progress_bar = ctk.CTkProgressBar(app, width=400)
progress_bar.set(0)
progress_bar.pack(pady=5)

progress_label = ctk.CTkLabel(app, text="Progress: 0%")
progress_label.pack()

status_label = ctk.CTkLabel(app, text="")
status_label.pack(pady=5)

# === Final Initialization ===
toggle_quality_options("Audio")
update_widget_styles()

app.mainloop()