import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# Version information - prioritize pyproject.toml for development mode
try:
    from pathlib import Path
    import re
    import sys
    
    # Try multiple locations for pyproject.toml
    possible_paths = [
        Path(__file__).parent.parent / "pyproject.toml",  # Development
        Path(sys._MEIPASS) / "pyproject.toml" if hasattr(sys, '_MEIPASS') else None,  # PyInstaller
    ]
    
    pyproject_path = None
    for path in possible_paths:
        if path and path.exists():
            pyproject_path = path
            break
    
    if pyproject_path:
        content = pyproject_path.read_text()
        match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        __version__ = match.group(1) if match else "unknown"
    else:
        # Fallback to importlib.metadata if pyproject.toml not found
        try:
            from importlib.metadata import version
            __version__ = version("simpn")
        except Exception:
            __version__ = "unknown"
except Exception:
    # Last resort fallback
    try:
        from importlib.metadata import version
        __version__ = version("simpn")
    except Exception:
        __version__ = "unknown"
