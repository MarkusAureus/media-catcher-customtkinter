# Media Catcher

Media Catcher is a modern, user-friendly GUI application built on top of yt-dlp that allows you to easily download videos and audio from over 1000 supported platforms and websites. With its intuitive interface and powerful features, downloading media has never been easier.

## ✨ Features

- **Download Videos & Audio** - From over 1000 supported platforms and websites.
- **Playlist Support** - Download entire playlists or individual videos.
- **Multiple Audio Formats** - MP3, WAV, AAC with quality options (64K-320K)
- **Video Quality Selection** - From 240p to 1080p or best available
- **Subtitle Download** - Support for multiple languages (English, Slovak, Czech, German, French, Spanish, Russian, Japanese, Chinese)
- **Beautiful Themes** - Blueberry (default), Matrix, and YT Theme. (Only dark mode)
- **Real-time Progress** - Progress bar with percentage and status updates.
- **Stop Function** - Cancel downloads at any time with the Stop button.
- **Custom Output Folder** - Save downloads to any location.
- **Built with CustomTkinter** - Modern, responsive interface.

## 📱 Screenshot
![](screenshot_1.png)
![](screenshot_2.png)
![](screenshot_3.png)
![](screenshot_4.png)

## 📋 Requirements

- Python 3.10+
- yt-dlp
- ffmpeg (for media processing)
- CustomTkinter
- Pillow (optional, for icon support)
- tkinter (usually comes with Python)

## 🚀 Installation

### Option 1: Install from Snap Store (Linux)
```bash
# Coming soon after approval
snap install media-catcher
```

### Option 2: Run from Source

1. Clone the repository:
```bash
git clone https://github.com/yourusername/media-catcher.git
cd media-catcher
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Make sure ffmpeg is installed:
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# Fedora
sudo dnf install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

4. Run the application:
```bash
python media_catcher.py
```

## 🎯 Usage

1. **Launch the application**
   ```bash
   media-catcher  # if installed via snap
   # or
   python media_catcher.py  # if running from source
   ```

2. **Enter URLs**
   - Paste one or more video/playlist URLs
   - Separate multiple URLs with new lines

3. **Choose Download Mode**
   - **Audio**: Downloads audio only in your chosen format
   - **Video**: Downloads video with audio

4. **Select Options**
   - For audio: Choose format (MP3/WAV/AAC) and quality
   - For video: Choose quality and optionally enable subtitles
   - Check "Download entire playlist" for playlist URLs

5. **Set Output Folder**
   - Click "Select Output Folder" to choose where to save files
   - Default: ~/Downloads

6. **Start Download**
   - Click "Download" to begin
   - Monitor progress with the progress bar
   - Use "Stop" button to cancel if needed

## 🎨 Themes

Switch between themes using the dropdown at the bottom:
- **Blueberry**: Modern dark theme with blue accents
- **Matrix**: Green on black terminal-style theme  
- **YT Theme**: YouTube-inspired red and white theme

## 📁 File Structure

```
media-catcher/
├── media_catcher.py      # Main application file
├── themes.json           # Theme configurations
├── media-catcher.png     # Application icon
├── media-catcher.desktop # Desktop entry file
├── requirements.txt      # Python dependencies
├── LICENSE.txt          # MIT License
├── README.md            # This file
└── snap/
    └── snapcraft.yaml   # Snap package configuration
```

## 🛠️ Troubleshooting

**Issue: "No module named 'customtkinter'"**
- Solution: Run `pip install customtkinter`

**Issue: "ffmpeg not found"**
- Solution: Install ffmpeg for your system (see installation section)

**Issue: Download fails**
- Make sure you have internet connection
- Check if the URL is valid and accessible
- Try updating yt-dlp: `pip install --upgrade yt-dlp`

**Issue: GUI doesn't appear**
- Make sure tkinter is installed
- On Linux: `sudo apt-get install python3-tk`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The powerful download engine
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern GUI framework
- [FFmpeg](https://ffmpeg.org/) - Media processing

## ⚠️ Disclaimer

This tool is for educational purposes and personal use only. Please respect copyright laws and the terms of service of the websites you download from. Only download content you have permission to download.

