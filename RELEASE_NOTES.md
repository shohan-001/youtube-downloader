# YouTube Downloader Release Notes

## v1.3.2 (Late Polish & Features)
*   **One-Click FFmpeg Install 🪄**: First-class support for missing FFmpeg. The app detects if it's missing and offers to auto-download and install it (from gyan.dev) to a local folder. No more manual PATH variables!
*   **Repo Cleanup**: Moved internal planning documents to valid folders, keeping the release clean.

## v1.3.1 (Performance & Controls)
*   **Super Fast Download Speeds**: Enabled parallel downloading! The app now downloads files in multiple chunks simultaneously (5x threads), maximizing your bandwidth usage.
*   **Download Controls ⏯️**: You can now **Cancel** a running download properly. Click "Stop" to halt the process safely. To "Pause", simply Cancel and start again later (it resumes automatically).
*   **Flexible Window Resizing**: The application window is no longer stiff. You can resize it freely (down to 500x500), making it perfect for laptops and multitasking.
*   **Visual Versioning**: The version number (`v1.3.2`) is now clearly displayed in the window title and header.
*   **Trust & Metadata**: The executable now contains proper version metadata (Copyright, Product Name) to reduce "Unknown Publisher" warnings and improve trust.

## v1.3.0 (Major GUI Update)
*   **Completely New UI**: Modern, dark-themed interface built with `customtkinter`.
*   **Video Information Card**: Now fetches and displays Video Title, Channel Name, Duration, and Thumbnail before downloading!
*   **Status Dashboard**: Real-time progress bar, speed meter, ETA, and file size display.
*   **Smart Logging**: Integrated log window to see exactly what's happening.
*   **Threaded Downloads**: The GUI no longer freezes while downloading.
*   **Settings Persistence**: Remembers your "Cookie Source" preference.
