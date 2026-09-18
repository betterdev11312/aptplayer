# -*- mode: python ; coding: utf-8 -*-
"""Build do instalador. Requer dist/AptPlayer.exe ja compilado."""

a = Analysis(
    ["installer.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("dist/AptPlayer.exe", "."),
        ("icon/app.ico", "."),
        ("icon/app.png", "."),
    ],
    hiddenimports=[
        "webview.platforms.edgechromium",
        "webview.platforms.winforms",
        "clr_loader",
    ],
    excludes=["tkinter", "matplotlib", "numpy", "PIL", "yt_dlp", "requests"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="AptPlayer-Setup",
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon="icon/app.ico",
)
