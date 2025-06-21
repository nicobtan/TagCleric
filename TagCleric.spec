# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_app.py'],
    pathex=[],
    binaries=[],
    datas=[('lang', 'lang'), ('TagClericIcon.ico', '.'), ('utils.py', '.'), ('language_manager.py', '.'), ('google_drive_handler.py', '.'), ('file_system_handler.py', '.'), ('app_view.py', '.'), ('app_logic.py', '.')],
    hiddenimports=['moviepy.editor', 'requests', 'google.cloud.vision', 'google.cloud.language_v1', 'google.generativeai'],
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
    name='TagCleric',
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
    icon=['TagClericIcon.ico'],
)
