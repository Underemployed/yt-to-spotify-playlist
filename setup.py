from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": [
        "flask",
        "spotipy",
        "requests",
        "cryptography",
        "webbrowser",
        "threading"
    ],
    "include_files": [
        ("templates", "templates")
    ],
    "excludes": ["tkinter"]
}

setup(
    name="YT to Spotify",
    version="1.0",
    description="YouTube to Spotify Playlist Converter",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "main.py",
            target_name="YTtoSpotify.exe",
            base="Win32GUI",
        )
    ]
)
