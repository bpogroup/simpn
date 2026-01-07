# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [('simpn/assets', 'simpn/assets'), ('pyproject.toml', '.')]
binaries = []
hiddenimports = ['sortedcontainers', 'pygame', 'numpy', 'python-igraph', 'igraph', 'imageio']

# Collect matplotlib
tmp_ret = collect_all('matplotlib')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Collect PyQt6 on Windows, avoid on macOS due to symlink issues
if sys.platform != 'darwin':
    tmp_ret = collect_all('PyQt6')
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
else:
    hiddenimports += ['PyQt6']


a = Analysis(
    ['simpn/visualisation/base.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# Windows: Single file executable
# macOS: One-folder mode (required for proper .app bundle)
if sys.platform == 'win32':
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name='SimPN',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='simpn/assets/SimPN.ico',
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='SimPN',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='simpn/assets/SimPN.icns',
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='SimPN',
    )

# BUNDLE is only for macOS
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='SimPN.app',
        icon='simpn/assets/SimPN.icns',
        bundle_identifier='com.bpogroup.simpn',
    )
