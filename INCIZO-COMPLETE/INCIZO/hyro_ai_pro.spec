# -*- mode: python ; coding: utf-8 -*-
# HYRO AI PRO — PyInstaller Build Spec
# Run: pyinstaller hyro_ai_pro.spec

a = Analysis(
    ['hyro_ai_pro.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'anthropic',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageGrab',
        'pyautogui',
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'tkinter.messagebox',
        'tkinter.filedialog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='HYRO_AI_PRO',
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
    icon=None,
)
