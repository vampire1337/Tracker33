# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\mihai\\Heist_master_PC\\Documents\\GitHub\\Tracker33\\desktop_app\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\mihai\\Heist_master_PC\\Documents\\GitHub\\Tracker33\\desktop_app\\config.ini', '.')],
    hiddenimports=['PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.QtNetwork', 'pynput', 'pynput.keyboard', 'pynput.mouse', 'psutil', 'requests', 'win32gui', 'win32process', 'win32con', 'win32api'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Tracker33',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\mihai\\Heist_master_PC\\Documents\\GitHub\\Tracker33\\desktop_app\\icon.ico'],
)
