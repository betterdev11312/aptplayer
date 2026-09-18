# -*- mode: python ; coding: utf-8 -*-
"""Build do AptPlayer (PyInstaller).

Gera um executavel unico. Os dados do usuario (biblioteca, cache, capas)
ficam em %LOCALAPPDATA%\AptPlayer - ver core/paths.py.
"""

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("ui", "ui"),
        ("icon/app.png", "icon"),
        ("icon/app.ico", "icon"),
    ],
    hiddenimports=[
        "webview.platforms.edgechromium",
        "webview.platforms.winforms",
        "clr_loader",
        "yt_dlp",
        "yt_dlp.extractor",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "PIL", "pytest", "setuptools"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AptPlayer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,          # sem janela preta de terminal
    icon="icon/app.ico",
)
