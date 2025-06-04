# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['desktop_app\\modern_client.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['cv2', 'pyzbar', 'pyzbar.pyzbar', 'qrcode', 'qrcode.image.pil', 'PIL', 'PIL.Image', 'numpy', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'requests', 'aiohttp', 'psutil', 'pynput', 'json', 'threading', 'queue', 'datetime', 'platform', 'logging'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
)
