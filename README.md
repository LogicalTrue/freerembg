# FreeRembg 🚀

FreeRembg is an automated, portable desktop utility developed in Python for high-performance batch background removal from both images and video streams. It is designed to streamline digital asset pipelines, making it an ideal tool for content creators, UI/UX designers, and software developers who need to process massive multimedia datasets efficiently.

## 🚀 Key Features

* **Automated Recursive Processing:** Intelligently explores subdirectories (utilizing `os.walk`), processing complex folder structures without losing the original directory tree layout in the output destination.
* **Collision Mitigation (Anti-Overwrite):** Implements unique hashes based on **UUIDv4** for file renaming, guaranteeing absolute uniqueness for generated assets and preventing accidental file overwriting during massive batch operations.
* **Portable Frame Extractor:** Features a built-in video frame extraction engine optimized via FFmpeg binaries to handle video-to-frame workflows seamlessly.
* **Standalone & Distributable:** Engineered to be packaged with PyInstaller by embedding binary dependencies, eliminating the need for end-users to configure system environment variables (PATH) or external dependencies.

## 🛠️ Project Architecture

The codebase is strictly structured under the separation of concerns principle to ensure clean maintenance, readability, and scalability:

* `src/main.py`: Application entry point.
* `src/ui.py`: Graphical User Interface (GUI) handled via Tkinter and styled with `sv_ttk` (Dark/Light mode support).
* `src/processing_logic.py`: Core business logic (handling image segmentation via `rembg` and video stream manipulation).
* `src/utils.py`: Helper functions and user configuration persistence.

## 📦 Development Setup

To clone this repository and run it in a local development environment, you will need to:

1. Install the Python dependencies: `pip install rembg pillow sv_ttk pyinstaller`
2. Download the static binary for `ffmpeg.exe` (Windows Static Build) and place it inside an `/assets` directory in the root of the project.