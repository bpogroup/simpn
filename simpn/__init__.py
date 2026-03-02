import sys
import warnings
import os

# Check for Python 3.14+ and warn about limited functionality
if sys.version_info >= (3, 14):
    print(
        f"simpn is running on Python {sys.version_info.major}.{sys.version_info.minor}.\n"
        "Visualization features are not available on Python 3.14+ because pygame and PyQt6 are not yet compatible.\n"
        "Core simulation functionality will work, but any code that uses visualization will fail.",
        file=sys.stderr
    )

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
