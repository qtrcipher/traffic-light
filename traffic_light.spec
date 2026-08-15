# PyInstaller spec: one-file, windowed ("traffic-light") for Windows & Linux.
#
# The compiled translation catalog (*.qm) is gitignored — build it first:
#     pyside6-lrelease src/traffic_light/i18n/traffic_light_ar.ts
# then:
#     pyinstaller traffic_light.spec
#
# Data files land under <bundle>/traffic_light/... and are found at runtime by
# the sys._MEIPASS-aware lookup in src/traffic_light/app.py (_resource).

from pathlib import Path

SRC = Path("src/traffic_light")

a = Analysis(
    [str(SRC / "app.py")],
    pathex=["src"],
    binaries=[],
    datas=[
        (str(SRC / "assets"), "traffic_light/assets"),
        (str(SRC / "i18n" / "traffic_light_ar.qm"), "traffic_light/i18n"),
    ],
    hiddenimports=[],
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
    name="traffic-light",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
)
