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
    excludes=["tkinter", "matplotlib", "numpy", "PIL", "yt_dlp", "requests",
              "cryptography", "Cryptodome", "secretstorage"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="AptPlayer-Setup",
    debug=False,
    strip=False,
    upx=False,   # UPX dispara falso positivo em antivirus
    console=False,
    icon="icon/app.ico",
    version="version_info.txt",
)
