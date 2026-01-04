# YouTube Video/Audio Downloader

A powerful YouTube downloader that supports both **video (MP4)** and **audio (MP3)** downloads. Available as a **modern GUI application** and a command-line tool.

<div align="center">
  <img src="https://img.shields.io/badge/GUI-CustomTkinter-blue.svg" alt="GUI">
  <img src="https://img.shields.io/badge/Python-3.7+-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-orange.svg" alt="License">
</div>

## 📥 Download (No Python Required)

**[Download Latest Version (v1.0)](https://github.com/shohan-001/youtube-downloader/releases)**

Just download `YT-Downloader.exe` and run it! (FFmpeg required for MP3)

## Features

- 🖥️ **Modern GUI** - Easy to use interface with dark mode
- ✅ **Download Videos** in MP4 format (4K, 2K, 1080p, etc.)
- ✅ **Download Audio** in MP3 format (320kbps, 256kbps, etc.)
- ✅ **Playlist Support** - Download entire playlists or single videos
- ✅ **Smart URL Handling** - Auto-detects complex URLs
- ✅ **Cookie Support** - For age-restricted content
- ✅ **VPS Friendly** - CLI version optimized for servers


## Installation (Source Code)

If you prefer to run from source:

## Supported URL Formats

The script automatically handles all common YouTube URL formats:

| Format | Example |
|--------|---------|
| Standard Video | `https://www.youtube.com/watch?v=VIDEO_ID` |
| Short URL | `https://youtu.be/VIDEO_ID` |
| Playlist | `https://www.youtube.com/playlist?list=PLAYLIST_ID` |
| Video in Playlist | `https://www.youtube.com/watch?v=VIDEO_ID&list=PLAYLIST_ID` |
| Radio/Mix | `https://www.youtube.com/watch?v=VIDEO_ID&list=RD...&start_radio=1` |
| Share Link | `https://youtu.be/VIDEO_ID?si=TRACKING_ID` |
| Embed | `https://www.youtube.com/embed/VIDEO_ID` |
| Just Video ID | `VIDEO_ID` (11 characters) |

> **Playlist Detection:** When you paste a URL with a playlist, you'll be asked whether to download just the single video, the entire playlist, or select specific videos.

## Requirements

- Python 3.7 or higher
- FFmpeg (required for MP3 conversion)
- yt-dlp

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/shohan-001/youtube-downloader.git
cd youtube-downloader
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install FFmpeg

**Windows:**
```bash
# Using winget
winget install --id=Gyan.FFmpeg -e

# Or using chocolatey
choco install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

### 4. Set Up Cookies (Optional but Recommended)

Cookies are required for:
- Age-restricted videos
- Private/unlisted videos
- Avoiding bot detection

**How to export cookies:**

1. Install a browser extension:
   - Chrome: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

2. Go to [youtube.com](https://youtube.com) and make sure you're logged in

3. Click the extension icon and export cookies

4. Save the file as `cookies.txt` in the same folder as the script

## Usage

### Running the GUI
```bash
python youtube_downloader_gui.py
```

### Running the CLI (Command Line)
```bash
python youtube_downloader.py
```

You will be prompted to:
1. Enter the YouTube URL
2. Choose download mode (Video or Audio)
3. Select quality

### With URL as Argument

```bash
python youtube_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Example Session

```
======================================================================
       YouTube Video/Audio Downloader
======================================================================
Using cookies from: D:\youtube-downloader\cookies.txt

Enter YouTube URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ

Processing URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
Extracting video information...

Title: Rick Astley - Never Gonna Give You Up
Duration: 3:33
Channel: Rick Astley

======================================================================
Download Mode:
======================================================================
1. VIDEO (MP4)
2. AUDIO (MP3)
======================================================================

Select mode (1 for Video, 2 for Audio) [default: 1]: 2

----------------------------------------------------------------------
Audio Quality Options (MP3):
----------------------------------------------------------------------
1. 320 kbps (Best quality)
2. 256 kbps (High quality)
3. 192 kbps (Good quality)
4. 128 kbps (Medium quality)
5. 96 kbps (Low quality)
6. 64 kbps (Very low quality)
----------------------------------------------------------------------

Select audio quality (1-6) [default: 1]: 1

Waiting 2.3s before starting download...

Downloading AUDIO and converting to MP3 (320 kbps)...
Progress: 100.0% | Speed: 1.25 MB/s
Download finished, processing...

[SUCCESS] Audio download and conversion completed!
```

### Playlist Download Example

```
======================================================================
       YouTube Video/Audio Downloader
          Supports Videos & Playlists
======================================================================
Using cookies from: D:\youtube-downloader\cookies.txt

Enter YouTube URL (video or playlist): https://www.youtube.com/playlist?list=PLxxxxxxxx

[INFO] Playlist URL detected
======================================================================
Playlist Options:
======================================================================
1. Download entire playlist
2. Select specific videos
======================================================================

Select option (1-2) [default: 1]: 2

Extracting information...

Playlist: My Awesome Playlist
Videos: 25
Channel: Some Channel

Videos in playlist:
--------------------------------------------------
  1. First Video Title...
  2. Second Video Title...
  3. Third Video Title...
  ... and 22 more videos

Enter video numbers to download (1-25, e.g., 1,3,5-10): 1-5,10

======================================================================
Download Mode:
======================================================================
1. VIDEO (MP4)
2. AUDIO (MP3)
======================================================================

Select mode (1 for Video, 2 for Audio) [default: 1]: 2

Downloading PLAYLIST AUDIO and converting to MP3 (320 kbps)...
```

## Quality Options

### Video Quality
| Option | Resolution | Description |
|--------|------------|-------------|
| 1 | Best | Highest available quality |
| 2 | 2160p | 4K Ultra HD |
| 3 | 1440p | 2K QHD |
| 4 | 1080p | Full HD |
| 5 | 720p | HD |
| 6 | 480p | SD |
| 7 | 360p | Low |

### Audio Quality (MP3)
| Option | Bitrate | Description |
|--------|---------|-------------|
| 1 | 320 kbps | Best quality |
| 2 | 256 kbps | High quality |
| 3 | 192 kbps | Good quality |
| 4 | 128 kbps | Medium quality |
| 5 | 96 kbps | Low quality |
| 6 | 64 kbps | Very low quality |

## VPS Usage

This script includes VPS-friendly options to help bypass YouTube's bot detection:

- Geo-bypass enabled
- Retry mechanisms for failed downloads
- Sleep intervals between requests
- Browser-like HTTP headers

**Tips for VPS:**
1. Always use cookies exported from your local machine
2. Keep yt-dlp updated: `pip install --upgrade yt-dlp`
3. If downloads fail, try updating cookies

## Troubleshooting

### "Sign in to confirm you're not a bot"
- Make sure you have a valid `cookies.txt` file
- Re-export cookies from your browser
- Update yt-dlp: `pip install --upgrade yt-dlp`

### "FFmpeg not found"
- Install FFmpeg following the instructions above
- Make sure FFmpeg is in your system PATH
- Restart your terminal after installation

### "Video unavailable"
- Check if the video is accessible in your region
- Some videos may be private or deleted
- Try using a VPN if geo-restricted

## File Structure

```
youtube-downloader/
├── youtube_downloader.py  # Main script
├── requirements.txt       # Python dependencies
├── cookies.txt           # Your cookies (create this yourself)
├── README.md             # This file
├── LICENSE               # MIT License
└── .gitignore           # Git ignore file
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for personal use only. Please respect YouTube's Terms of Service and copyright laws. Only download content you have the right to download.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The amazing YouTube downloader library
- [FFmpeg](https://ffmpeg.org/) - For audio/video processing
